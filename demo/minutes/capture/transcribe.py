"""녹음 WAV → 전사 JSON. 표준 라이브러리만 쓴다 — macOS·Windows·WSL 에서 같은 코드.

    python capture/transcribe.py <job 폴더>          # <job>/audio.wav → <job>/transcript.json

- 입력은 16 kHz·mono·16bit WAV(브라우저 녹음기가 이 형식으로 쓴다).
- 모델은 로컬 Ollama(기본 `gemma4:e2b`). 오디오를 한 번에 길게 넣으면 **겉보기 멀쩡하게 문장을 빠뜨린다**
  (2026-11-16 실측: 78초 한 번에 → 안건 번호 여섯 곳·마지막 문장 누락, 25초 조각 → 한 문단을 세 번 되풀이하고
  「안건 5번」 누락). 15초 조각에서는 되풀이·누락이 없었다. 그래서 MAX_SEC 이하로 자른다.
- 한 조각 안에서 같은 문장이 되풀이되면 `suspect_repeat` 를 남긴다. 고치지 않는다 — 실제로 되풀이해 말했을 수도 있다.
- 자르는 곳은 소리가 없는 지점이다. 고정 시간으로 자르면 낱말이 쪼개져 「마지막」 이 「난」 이 됐다.
  MAX_SEC 안에 쉼이 없으면 그 자리에서 자르고 그 조각에 `hard_cut` 표시를 남긴다.
- 원음과 맞춰 볼 수 있게 조각마다 시작·끝 시각을 남긴다. 모델 출력은 윤문하지 않고 그대로 둔다.
- 빈 응답·요청 실패는 그 조각을 `error` 로 남기고 전체 상태를 `failed` 로 한다 — 성공한 전사로 넘기지 않는다.

이 전사기가 보장하지 않는 것: 받아 적은 글이 원음과 같은지(오독은 그대로 나온다), 화자가 누구인지.
"""
from __future__ import annotations

import array
import base64
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MINUTES_STT_MODEL", "gemma4:e2b")
MAX_SEC = 15.0        # 한 번에 넣는 최대 길이
MIN_SEC = 4.0         # 이보다 짧게는 자르지 않는다(쉼마다 잘게 쪼개지 않게)
FRAME_SEC = 0.05      # 소리 크기를 재는 단위
SILENT_DBFS = -45.0   # 이보다 작으면 쉼
SILENT_MIN_SEC = 0.3  # 이만큼 이어져야 쉼으로 본다
# 지시문은 영어로 둔다. 2026-11-16 실제 Meet 녹음에서 한국어 지시문 「처음부터 끝까지 빠짐없이 받아 적은 문장만 출력한다」 가
# 전사 결과에 그대로 섞여 나왔다 — 영어면 한국어 발화와 갈라 보기 쉽고, ECHO 로 잡는다.
PROMPT = ("Transcribe the Korean speech in this audio verbatim, in Korean. "
          "Output only the transcribed words. If there is no speech, output nothing.")
ECHO = ("transcribe", "verbatim", "output only", "받아 적", "출력한다", "빠짐없이")


def read_wav(path: Path) -> tuple[array.array, int]:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise SystemExit(f"{path}: 16bit mono WAV 가 아니다 (채널 {w.getnchannels()}, 폭 {w.getsampwidth()})")
        rate = w.getframerate()
        pcm = array.array("h", w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        pcm.byteswap()
    return pcm, rate


def frame_dbfs(pcm: array.array, rate: int) -> list[float]:
    n = max(1, int(rate * FRAME_SEC))
    out = []
    for i in range(0, len(pcm), n):
        chunk = pcm[i:i + n]
        rms = math.sqrt(sum(s * s for s in chunk) / len(chunk)) if chunk else 0.0
        out.append(20 * math.log10(rms / 32768) if rms > 0 else -120.0)
    return out


def cut_points(db: list[float]) -> list[tuple[int, int, bool]]:
    """(시작 프레임, 끝 프레임, hard_cut) 목록. 쉼의 한가운데에서 자른다."""
    silent_min = int(SILENT_MIN_SEC / FRAME_SEC)
    mids, run = [], 0
    for i, d in enumerate(db + [0.0]):
        if d < SILENT_DBFS:
            run += 1
            continue
        if run >= silent_min:
            mids.append(i - run // 2 - 1)
        run = 0
    max_f, min_f = int(MAX_SEC / FRAME_SEC), int(MIN_SEC / FRAME_SEC)
    spans, start = [], 0
    while len(db) - start > max_f:
        cands = [m for m in mids if start + min_f <= m <= start + max_f]
        if cands:
            spans.append((start, cands[-1], False))
            start = cands[-1]
        else:
            spans.append((start, start + max_f, True))
            start += max_f
    spans.append((start, len(db), False))
    return spans


def to_wav_bytes(pcm: array.array, rate: int) -> bytes:
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        data = pcm
        if sys.byteorder == "big":
            data = array.array("h", pcm)
            data.byteswap()
        w.writeframes(data.tobytes())
    return buf.getvalue()


def repeats(text: str) -> bool:
    """같은 문장(10자 이상)이 세 번 이상 나오면 True — 모델의 되풀이 고리일 수 있다."""
    import re
    sents = [x.strip() for x in re.split(r"[.!?\n]+", text) if len(x.strip()) >= 10]
    return any(sents.count(x) >= 3 for x in set(sents))


def ask(wav: bytes, sec: float) -> str:
    # Ollama 0.40 은 오디오를 메시지의 images 칸으로 받는다(audio 칸은 무시된다 — 2026-11-16 실측).
    body = {"model": MODEL, "stream": False, "think": False, "options": {"temperature": 0, "num_predict": int(40 + sec * 15)},
            "messages": [{"role": "user", "content": PROMPT, "images": [base64.b64encode(wav).decode()]}]}
    req = urllib.request.Request(f"{OLLAMA}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return (json.load(r).get("message") or {}).get("content", "").strip()


def transcribe(job: Path) -> dict:
    pcm, rate = read_wav(job / "audio.wav")
    db = frame_dbfs(pcm, rate)
    per = int(rate * FRAME_SEC)
    segs, failed = [], False
    t0 = time.time()
    for a, b, hard in cut_points(db):
        seg = {"start": round(a * FRAME_SEC, 2), "end": round(min(b * per, len(pcm)) / rate, 2), "hard_cut": hard}
        if max(db[a:b] or [-120.0]) < SILENT_DBFS:
            seg.update(text="", silent=True)
        else:
            try:
                seg["text"] = ask(to_wav_bytes(pcm[a * per:b * per], rate), seg["end"] - seg["start"])
                if repeats(seg["text"]):
                    seg["suspect_repeat"] = True
                if any(e in seg["text"].lower() for e in ECHO):
                    seg["prompt_echo"] = True       # 지시문이 결과에 섞였다 — 지우지 않고 표시만
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                seg.update(text="", error=str(e))
                failed = True
        segs.append(seg)
    spoken = [s for s in segs if not s.get("silent")]
    if spoken and not any(s["text"] for s in spoken):
        failed = True
    return {
        "status": "failed" if failed else ("silent" if not spoken else "done"),
        "model": MODEL, "audio_sec": round(len(pcm) / rate, 2), "elapsed_sec": round(time.time() - t0, 1),
        "segments": segs,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    job = Path(sys.argv[1])
    out = transcribe(job)
    tmp = job / "transcript.json.part"
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(job / "transcript.json")
    print(f"{out['status']}: {len(out['segments'])}조각 · 음성 {out['audio_sec']}초 · 처리 {out['elapsed_sec']}초")
    return 0 if out["status"] == "done" else 1


if __name__ == "__main__":
    sys.exit(main())

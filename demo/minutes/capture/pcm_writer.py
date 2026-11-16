"""16 kHz mono Int16 PCM 을 받는 대로 WAV 에 이어 쓴다 — 회의 녹음 확장이 보낸 소리를 수신기(receive.py)가 넘긴다.

    w = PcmWriter(job / "audio.wav")
    w.push(base64_pcm)     # 1초마다
    w.close()

- `recording` 은 소리가 실제로 들어온 뒤에야 True 가 된다(무음이 아닌 표본이 왔을 때).
  녹음을 켰다는 사실만으로 녹음 중이라고 표시하지 않는다.
- 상태는 `<job>/record.json` 에 받을 때마다 남는다.

보장하지 않는 것: 회의 안의 모든 사람 소리가 들어왔는지(확장은 탭 소리만 받는다 — 내 마이크는 없다).
"""
from __future__ import annotations

import array
import base64
import json
import sys
import time
import wave
from pathlib import Path

RATE = 16000
LOUD = 300   # Int16 절댓값 — 이보다 큰 표본이 있어야 「소리가 들어왔다」


class PcmWriter:
    def __init__(self, wav_path: Path):
        self.path = Path(wav_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.w = wave.open(str(self.path), "wb")
        self.w.setnchannels(1)
        self.w.setsampwidth(2)
        self.w.setframerate(RATE)
        self.samples = 0
        self.tracks = 0
        self.first_sound = None
        self.started = time.time()
        self.closed = False

    @property
    def recording(self) -> bool:
        return self.first_sound is not None and not self.closed

    def push(self, b64: str, tracks: int = 1) -> None:
        if self.closed:
            return
        pcm = array.array("h", base64.b64decode(b64))
        if sys.byteorder == "big":
            pcm.byteswap()
        if self.first_sound is None and any(abs(s) > LOUD for s in pcm):
            self.first_sound = round(self.samples / RATE, 2)
        self.w.writeframes(base64.b64decode(b64))
        self.samples += len(pcm)
        self.tracks = tracks
        self._save()

    def status(self) -> dict:
        return {"recording": self.recording, "closed": self.closed, "seconds": round(self.samples / RATE, 1),
                "tracks": self.tracks, "first_sound_at": self.first_sound}

    def _save(self) -> None:
        tmp = self.path.with_name("record.json.part")
        tmp.write_text(json.dumps(self.status(), ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path.with_name("record.json"))

    def close(self) -> dict:
        if not self.closed:
            self.closed = True
            self.w.close()      # wave 가 머리의 길이를 이때 고쳐 쓴다
            self._save()
        return self.status()

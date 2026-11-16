"""전사 JSON → 기존 녹취록 형식 → inbox. 표준 라이브러리만 쓴다.

    python capture/publish.py <job 폴더> --meeting "주간 회의" --when "2026-11-16(월) 10:00" [--attendees "김지현, 박도윤"]

- 기존 수집(`scripts/collect.py`)·검수(`review.py`)가 읽는 `[HH:MM:SS] 화자: 발화` 형식으로 쓴다.
  시각은 조각의 시작 시각이다 — 원음에서 그 자리를 찾아 들을 수 있다.
- 화자는 `미확인` 으로 쓴다. 이 전사에는 화자 구분이 없다. 그럴듯한 이름을 붙이지 않는다.
- 전사 상태가 `done` 이 아니면 넣지 않는다(실패·무음을 빈 회의록으로 넘기지 않는다).
- 다 쓴 뒤 이름을 바꿔 inbox 에 넣는다 — 감시(`scripts/watch.sh`)가 반쯤 쓴 파일을 집지 않게.
- 같은 job 을 두 번 넣지 않는다. 다시 넣으려면 `--again`(새 전사 판으로 새 요청이 열린다).

이 변환이 보장하지 않는 것: 전사가 원음과 같은지, 참석 명단이 실제 참석과 같은지.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEAKER = "미확인"


def hms(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def render(tr: dict, meeting: str, when: str, attendees: str | None) -> str:
    head = [f"회의: {meeting}", f"일시: {when}"]
    if attendees:
        head.append(f"참석: {attendees}")
    head.append(f"기록: 회의 녹음을 로컬 모델({tr['model']})로 받아 적음 · 화자 구분 없음")
    lines = []
    for s in tr["segments"]:
        text = " ".join(s.get("text", "").split())   # 줄바꿈만 한 줄로. 낱말은 고치지 않는다
        if text:
            lines.append(f"[{hms(s['start'])}] {SPEAKER}: {text}")
    return "\n".join(head) + "\n\n" + "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job", type=Path)
    ap.add_argument("--meeting", required=True)
    ap.add_argument("--when", required=True)
    ap.add_argument("--attendees")
    ap.add_argument("--inbox", type=Path, default=ROOT / "inbox")
    ap.add_argument("--again", action="store_true")
    a = ap.parse_args()

    tr = json.loads((a.job / "transcript.json").read_text(encoding="utf-8"))
    if tr.get("status") != "done":
        print(f"넣지 않음: 전사 상태 {tr.get('status')}", file=sys.stderr)
        return 1
    marks = ("hard_cut", "suspect_repeat", "prompt_echo")     # 원음을 다시 들어 볼 곳
    flags = [f"{hms(s['start'])} " + ",".join(k for k in marks if s.get(k))
             for s in tr["segments"] if any(s.get(k) for k in marks)]
    job_file = a.job / "job.json"
    job = json.loads(job_file.read_text(encoding="utf-8")) if job_file.exists() else {}
    if job.get("published") and not a.again:
        print(f"이미 넣음: {job['published']}  (다시 넣으려면 --again)", file=sys.stderr)
        return 1

    a.inbox.mkdir(parents=True, exist_ok=True)
    name = f"{a.job.name}-v{len(job.get('history', [])) + 1}.txt"
    tmp = a.inbox / (name + ".part")
    tmp.write_text(render(tr, a.meeting, a.when, a.attendees), encoding="utf-8")
    tmp.replace(a.inbox / name)

    job.setdefault("history", []).append({"published": name, "model": tr["model"], "flags": flags})
    job["published"] = name
    job_file.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"넣음: inbox/{name}" + (f"  · 들어 볼 곳 {'; '.join(flags)}" if flags else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

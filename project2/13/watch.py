"""폴더를 지켜보다가 새 영수증이 들어오면 runner 를 한 번 실행한다(폴더 trigger).

    uv run python watch.py inbox/                  # 2초마다 inbox/ 를 본다 — 끝낼 때는 Ctrl+C
    uv run python watch.py inbox/ --once           # 지금 들어 있는 새 파일만 처리하고 끝낸다
    uv run python watch.py inbox/ --once --answers fixtures/answers   # Claude 대신 저장해 둔 응답(<이름>.json)

영수증 하나마다:
1. done/ · review/ 에 같은 이름이 있으면 photo-2.png 처럼 새 이름으로 바꾼다 — 보관한 사진을 덮어쓰지 않고, 가계부의 영수증 칸에도 새 이름이 적힌다
2. 경로를 current.txt 에 적고, 지난 영수증의 state.json · human_queue/ · entry.json 을 지운다
3. runner.py 로 graph.yaml 을 실행한다 — 읽기(read) → 형식 검사와 기록(add)
4. runner 가 0 으로 끝나면 영수증을 done/ 으로, 아니면 review/ 로 옮기고 이유를 review/<이름>.txt 에 적는다

처리한 영수증은 inbox/ 를 떠나므로 다음 번에는 새로 들어온 파일만 남는다.
같은 영수증을 다시 넣으면 다시 처리한다 — 두 번 들어온 영수증을 막는 일은 이 파일이 하지 않는다.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

DONE = Path("done")
REVIEW = Path("review")
CURRENT = Path("current.txt")


def new_files(inbox):
    """inbox 안의 파일 — 이름이 . 으로 시작하는 것(.gitkeep 같은)은 뺀다."""
    return sorted(p for p in inbox.iterdir() if p.is_file() and not p.name.startswith("."))


def unique(receipt):
    """done/ · review/ 에 같은 이름(review/ 는 <이름>.txt 도)이 있으면 photo-2.png … 로 바꿔 그 경로를 돌려준다."""
    name, n = receipt.name, 1
    while any(p.exists() for p in (DONE / name, REVIEW / name, REVIEW / f"{Path(name).stem}.txt")) \
            or (n > 1 and (receipt.parent / name).exists()):
        n += 1
        name = f"{receipt.stem}-{n}{receipt.suffix}"
    if name == receipt.name:
        return receipt
    print(f"[watch] 같은 이름이 done/ · review/ 에 있습니다 — {receipt.name} → {name}", flush=True)
    return receipt.rename(receipt.with_name(name))


def why_human():
    """runner 가 human_queue/ 에 남긴 이유를 모은다."""
    items = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path("human_queue").glob("*.json"))]
    return "\n".join(f"[{i['step']}] {i['why']}" for i in items) or "runner 가 이유를 남기지 않았습니다"


def handle(receipt, answers):
    stem = receipt.stem                         # 저장해 둔 응답은 처음 이름으로 찾는다
    receipt = unique(receipt)                   # 이름이 겹치면 새 이름으로
    CURRENT.write_text(receipt.as_posix(), encoding="utf-8")
    for old in (Path("state.json"), Path("entry.json")):
        old.unlink(missing_ok=True)
    shutil.rmtree("human_queue", ignore_errors=True)
    cmd = [sys.executable, "runner.py", "graph.yaml"]
    if answers:
        cmd += ["--answer", str(Path(answers) / f"{stem}.json")]
    print(f"[watch] 새 영수증 {receipt.name} — runner 를 실행합니다", flush=True)
    code = subprocess.run(cmd).returncode
    if code == 0:
        DONE.mkdir(exist_ok=True)
        shutil.move(receipt, DONE / receipt.name)
        print(f"[watch] {receipt.name} → done/", flush=True)
    else:
        REVIEW.mkdir(exist_ok=True)
        shutil.move(receipt, REVIEW / receipt.name)
        why = why_human() if code == 3 else f"runner 가 exit code {code} 로 끝났습니다"
        (REVIEW / f"{receipt.stem}.txt").write_text(why + "\n", encoding="utf-8")
        print(f"[watch] {receipt.name} → review/ — 이유는 review/{receipt.stem}.txt", flush=True)
    CURRENT.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inbox")
    ap.add_argument("--once", action="store_true", help="지금 있는 새 파일만 처리하고 끝낸다")
    ap.add_argument("--answers", help="claude 를 부르지 않고 이 폴더의 <영수증 이름>.json 을 응답으로 쓴다")
    ap.add_argument("--every", type=float, default=2, help="몇 초마다 볼지")
    a = ap.parse_args()
    inbox = Path(a.inbox)
    if not inbox.is_dir():
        sys.exit(f"{inbox} 폴더가 없습니다")
    if a.once:
        files = new_files(inbox)
        if not files:
            print(f"[watch] {inbox} 에 새 파일이 없습니다", flush=True)
        for f in files:
            handle(f, a.answers)
        return 0
    print(f"[watch] {inbox} 를 {a.every:g}초마다 봅니다 — 끝낼 때는 Ctrl+C", flush=True)
    sizes = {}
    while True:
        for f in new_files(inbox):
            size = f.stat().st_size
            if sizes.get(f) == size:            # 두 번 연속 크기가 같으면 복사가 끝난 것으로 본다
                handle(f, a.answers)
                sizes.pop(f)
            else:
                sizes[f] = size
        time.sleep(a.every)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[watch] 멈췄습니다")
        sys.exit(0)

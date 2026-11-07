"""가계부에 이미 있는 영수증인지 본다 — 같은 파일은 content hash 로, 같은 영수증은 내용으로.

    uv run python dedup.py seen                                # 지금 영수증(current.txt)의 content hash 가 가계부에 있나
    uv run python dedup.py score entry.json --threshold 70     # 읽은 내용이 가계부의 어느 줄과 얼마나 같나
    uv run python dedup.py hash receipts/r01.png               # 파일 하나의 content hash 보기

seen  — content hash 는 파일 내용을 sha256 에 넣어 얻은 값이다. 가계부의 「content hash」 칸에 같은 값이 있으면
        같은 파일이 이미 기록된 것이다 → exit code 4(할 일 없음 — runner 가 남은 단계를 건너뛰고 0 으로 끝낸다)
score — 날짜 · 가게 · 금액을 가계부의 줄마다 견주어 중복 의심 점수(0~100)를 매긴다.
        가장 높은 점수가 threshold 를 넘으면 → exit code 3(사람에게), 넘지 않으면 → exit code 0
"""
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

LEDGER = Path("ledger.xlsx")
RECEIPT = Path("current.txt")      # watch.py 가 지금 처리하는 영수증 경로를 적어 둔다
HASH_COL = 7                       # 「content hash」 칸 — ledger.py 가 7번째 칸에 적는다


def content_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def as_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        return None


def score(a, b):
    """두 기록(date · store · amount)이 같은 영수증일 점수. 날짜 40 · 금액 40 · 가게 20."""
    s = 0
    da, db = as_date(a.get("date")), as_date(b.get("date"))
    if da and db:
        gap = abs((da - db).days)
        s += 40 if gap == 0 else 20 if gap == 1 else 0      # 하루 차이는 잘못 읽었을 수 있다
    if a.get("amount") not in (None, "") and a.get("amount") == b.get("amount"):
        s += 40
    sa = str(a.get("store") or "").replace(" ", "")
    sb = str(b.get("store") or "").replace(" ", "")
    if sa and sb:
        s += 20 if sa == sb else 0                            # 띄어쓰기만 다르면 같은 가게
    elif sa or sb:
        s += 10                                               # 한쪽이 비었으면 반만
    return s


def rows():
    """가계부의 줄을 (행 번호, 기록, content hash) 로 돌려준다."""
    if not LEDGER.exists():
        return []
    ws = load_workbook(LEDGER).active
    out = []
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        r = list(r) + [None] * HASH_COL
        out.append((i, {"date": r[0], "store": r[1], "amount": r[2]}, r[HASH_COL - 1]))
    return out


def show(rec):
    d = as_date(rec.get("date"))
    a = rec.get("amount")
    return f"{d or rec.get('date')} · {rec.get('store') or '(가게 없음)'} · {a:,}원" if type(a) is int else \
        f"{d or rec.get('date')} · {rec.get('store') or '(가게 없음)'} · {a}"


def seen():
    if not RECEIPT.exists():
        print("current.txt 가 없습니다 — watch.py 가 영수증 경로를 적어 둡니다", file=sys.stderr)
        return 1
    h = content_hash(RECEIPT.read_text(encoding="utf-8").strip())
    for i, rec, saved in rows():
        if saved == h:
            print(f"같은 파일 — ledger.xlsx {i}행에 이미 기록되어 있습니다(content hash {h[:12]}…)")
            return 4
    return 0


def check(path, threshold):
    entry = json.loads(Path(path).read_text(encoding="utf-8"))
    best = max(((score(entry, rec), i, rec) for i, rec, _ in rows()), default=None, key=lambda t: t[0])
    if best and best[0] > threshold:
        print(f"중복 의심 — 점수 {best[0]}(threshold {threshold}) · ledger.xlsx {best[1]}행 {show(best[2])}")
        return 3
    print(f"중복 의심 없음 — 가장 높은 점수 {best[0] if best else 0}(threshold {threshold})")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["seen"]:
        sys.exit(seen())
    if len(args) == 2 and args[0] == "hash":
        print(content_hash(args[1]), args[1])
        sys.exit(0)
    if len(args) == 4 and args[0] == "score" and args[2] == "--threshold":
        sys.exit(check(args[1], int(args[3])))
    sys.exit("쓰는 법: uv run python dedup.py seen · score entry.json --threshold 70 · hash <파일>")

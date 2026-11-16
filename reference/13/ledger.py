"""가계부 ledger.xlsx 에 한 줄을 더하기 전에 형식을 검사한다.

    uv run python ledger.py add entry.json     # 검사를 통과하면 한 줄 더하기
    uv run python ledger.py show               # 가계부에 적힌 줄 보기

검사하는 것(판단하지 않고 모양만 본다):
- 빈 칸 — date · store · amount · category · payment 가 모두 채워졌나(공백뿐인 글자도 빈 칸). 비었으면 unread 에 적힌 이유를 함께 찍는다
- 형식 — date · store · category · payment 는 글자, unread 는 칸마다 이유를 적는 객체,
          date 는 달력에 있는 YYYY-MM-DD, amount 는 0 보다 큰 정수,
          category 는 skill 의 분류 표에 있는 이름, payment 는 카드 또는 현금

exit code — 0: 기록함 · 3: 기록하지 않음(이유를 한 줄씩 찍는다 — runner 가 human_queue 에 남긴다) · 1: 실행 오류
"""
import json
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook

LEDGER = Path("ledger.xlsx")
SKILL = Path(".claude/skills/ledger-rules/SKILL.md")
RECEIPT = Path("current.txt")                 # watch.py 가 지금 처리하는 영수증 경로를 적어 둔다
FIELDS = ["date", "store", "amount", "category", "payment"]
HEADER = ["날짜", "가게", "금액", "분류", "결제", "영수증"]
PAYMENTS = {"카드", "현금"}


def categories():
    """분류 이름은 skill 의 「## 분류」 표에서 읽는다 — 이름을 두 곳에 따로 적지 않는다."""
    if not SKILL.exists():
        sys.exit(f"{SKILL} 이 없습니다 — examples/SKILL.md 를 복사했는지 보세요")
    names, inside = [], False
    for line in SKILL.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## 분류"
        elif inside and line.startswith("|"):
            first = line.strip("|").split("|")[0].strip()
            if first and first != "분류" and not set(first) <= set("-: "):
                names.append(first)
    return names


def check(entry):
    """기록하면 안 되는 이유를 모아 돌려준다. 비어 있으면 통과."""
    problems = []
    unread = entry.get("unread", {})
    if not isinstance(unread, dict):
        problems.append(f"형식 — unread: {unread!r} — 칸마다 이유를 적는 객체가 아닙니다")
        unread = {}
    filled = {}                                   # 채웠고 자료형이 맞는 칸
    for f in FIELDS:
        v = entry.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            problems.append(f"빈 칸 — {f}: {unread.get(f, '이유가 적혀 있지 않습니다')}")
        elif f != "amount" and not isinstance(v, str):
            problems.append(f"형식 — {f}: {v!r} — 글자가 아닙니다")
        else:
            filled[f] = v
    d = filled.get("date")
    if d:
        try:
            if len(str(d)) != 10:
                raise ValueError
            date.fromisoformat(str(d))
        except ValueError:
            problems.append(f"형식 — date: {d} — 달력에 있는 YYYY-MM-DD 날짜가 아닙니다")
    a = filled.get("amount")
    if a is not None and (type(a) is not int or a <= 0):
        problems.append(f"형식 — amount: {a!r} — 0 보다 큰 정수가 아닙니다")
    c = filled.get("category")
    if c and c not in categories():
        problems.append(f"형식 — category: {c} — skill 의 분류 표에 없는 이름입니다")
    p = filled.get("payment")
    if p and p not in PAYMENTS:
        problems.append(f"형식 — payment: {p} — 카드 · 현금 가운데 하나가 아닙니다")
    return problems


def add(path):
    try:
        entry = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(entry, dict):
            raise ValueError
    except ValueError:
        print("형식 — JSON 한 줄로 읽을 수 없습니다")
        return 3
    problems = check(entry)
    if problems:
        print("\n".join(problems))
        return 3
    receipt = RECEIPT.read_text(encoding="utf-8").strip() if RECEIPT.exists() else ""
    row = [date.fromisoformat(entry["date"]), entry["store"], entry["amount"],
           entry["category"], entry["payment"], Path(receipt).name]
    if LEDGER.exists():
        wb = load_workbook(LEDGER)
    else:
        wb = Workbook()
        wb.active.title = "가계부"
        wb.active.append(HEADER)
        for col, width in zip("ABCDEF", [12, 18, 10, 8, 8, 12]):   # 날짜가 ### 로 가려지지 않게
            wb.active.column_dimensions[col].width = width
    ws = wb.active
    ws.append(row)
    ws.cell(ws.max_row, 1).number_format = "yyyy-mm-dd"
    ws.cell(ws.max_row, 3).number_format = "#,##0"
    wb.save(LEDGER)
    saved = [c.value or "" for c in load_workbook(LEDGER).active[ws.max_row]]   # 다시 열어 적힌 값을 확인
    if saved[1:] != row[1:] or saved[0].date() != row[0]:
        print(f"ledger.xlsx 에 적힌 값이 다릅니다: {saved}", file=sys.stderr)
        return 1
    print(f"기록 — {entry['date']} · {entry['store']} · {entry['amount']:,}원 · {entry['category']} · {entry['payment']}"
          f" → ledger.xlsx {ws.max_row}행")
    return 0


def show():
    if not LEDGER.exists():
        print("ledger.xlsx 가 아직 없습니다")
        return 0
    for row in load_workbook(LEDGER).active.iter_rows(values_only=True):
        cells = [v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else f"{v:,}" if type(v) is int else str(v or "")
                 for v in row]
        print(" | ".join(cells))
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["add"] and len(sys.argv) == 3:
        sys.exit(add(sys.argv[2]))
    if sys.argv[1:] == ["show"]:
        sys.exit(show())
    sys.exit("쓰는 법: uv run python ledger.py add entry.json · uv run python ledger.py show")

"""카드 명세서와 가계부를 한 줄씩 맞춰 일치 · 누락 · 중복을 찾는다(reconciliation).

    uv run python reconcile.py statements/2026-10.csv                                   # 내 가계부 ledger.xlsx 와
    uv run python reconcile.py statements/2026-10.csv --ledger practice/ledger-2026-10.csv   # 연습용 10월 가계부와

맞추는 법
- 명세서의 달에 든 가계부의 카드 줄만 맞춘다. 현금 줄은 명세서에 없으니 맞추지 않는다
- 명세서의 취소 줄은 같은 가맹점 · 같은 금액의 승인 줄과 짝을 지어 함께 뺀다
- 열쇠는 날짜와 금액이다. 가게 이름은 명세서(가맹점 이름)와 영수증이 다를 수 있어 열쇠로 쓰지 않는다
- 일치 — 명세서 한 줄에 가계부 한 줄
- 누락 — 명세서에는 있는데 가계부에 없는 줄
- 중복 — 명세서 한 줄에 가계부 두 줄 이상
- 가계부에만 — 가계부에는 있는데 명세서에 없는 줄. 날짜가 하루 안이고 금액이나 가게가 같은 명세서 줄을 함께 보인다

exit code — 0: 모두 일치 · 3: 사람이 볼 줄이 있음 · 1: 실행 오류
"""
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

LEDGER = Path("ledger.xlsx")


def day(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v).strip())


def won(n):
    return f"{n:,}원"


def read_statement(path):
    with open(path, encoding="utf-8", newline="") as f:
        lines = [{"date": day(r["이용일"]), "store": r["가맹점"], "amount": int(r["금액"]), "kind": r["구분"]}
                 for r in csv.DictReader(f)]
    paid = [x for x in lines if x["kind"] == "승인"]
    cancels = []
    for c in (x for x in lines if x["kind"] == "취소"):
        twin = next((p for p in paid if p["store"] == c["store"] and p["amount"] == c["amount"]), None)
        if twin:
            paid.remove(twin)
            cancels.append(twin)
    return lines, paid, cancels


def read_ledger(path):
    """(행 번호, 기록) — 행 번호는 Excel 에서 보이는 번호(머리가 1행)."""
    path = Path(path)
    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as f:
            raw = [[r["날짜"], r["가게"], int(r["금액"]), r["결제"]] for r in csv.DictReader(f)]
    else:
        from openpyxl import load_workbook
        raw = [[r[0], r[1], r[2], r[4]] for r in load_workbook(path).active.iter_rows(min_row=2, values_only=True)]
    return [(i, {"date": day(d), "store": s or "", "amount": a, "payment": p})
            for i, (d, s, a, p) in enumerate(raw, start=2)]


def main(args):
    if not args or len(args) not in (1, 3) or (len(args) == 3 and args[1] != "--ledger"):
        print("쓰는 법: uv run python reconcile.py statements/2026-10.csv [--ledger 가계부 파일]", file=sys.stderr)
        return 1
    ledger_path = Path(args[2]) if len(args) == 3 else LEDGER
    if not ledger_path.exists():
        print(f"{ledger_path} 가 없습니다", file=sys.stderr)
        return 1
    lines, paid, cancels = read_statement(args[0])
    months = {(x["date"].year, x["date"].month) for x in lines}
    rows = [(i, r) for i, r in read_ledger(ledger_path) if (r["date"].year, r["date"].month) in months]
    card = [(i, r) for i, r in rows if r["payment"] == "카드"]
    cash = len(rows) - len(card)

    by_key_s, by_key_l = defaultdict(list), defaultdict(list)
    for x in paid:
        by_key_s[(x["date"], x["amount"])].append(x)
    for i, r in card:
        by_key_l[(r["date"], r["amount"])].append((i, r))

    match, missing, dup, only = 0, [], [], []
    for key in sorted(set(by_key_s) | set(by_key_l)):
        s, l = by_key_s.get(key, []), by_key_l.get(key, [])
        match += min(len(s), len(l))
        if len(s) > len(l):
            missing += s[len(l):]
        elif len(l) > len(s) and s:
            dup.append((key, l))
        elif not s:
            only += l

    print(f"카드 명세서 {args[0]} — 승인 {len(lines) - len(cancels)}줄 · 취소 {len(cancels)}줄")
    print(f"가계부 {ledger_path} — 카드 {len(card)}줄" + (f"(현금 {cash}줄은 맞추지 않음)" if cash else ""))
    print()
    print(f"일치 {match}줄")
    for c in cancels:
        print(f"취소 1쌍 — {c['date']} · {c['store']} · {won(c['amount'])} 승인과 취소(가계부에 없어야 맞음)")
    if missing:
        print(f"누락 {len(missing)}줄 — 명세서에는 있고 가계부에는 없음")
        for x in missing:
            print(f"  {x['date']} · {x['store']} · {won(x['amount'])}")
    if dup:
        print(f"중복 {sum(len(l) - len(by_key_s[k]) for k, l in dup)}줄 — 명세서 한 줄에 가계부 여러 줄")
        for (d, a), l in dup:
            print(f"  {d} · {won(a)} — 가계부 " + " · ".join(f"{i}행" for i, _ in l))
    if only:
        print(f"가계부에만 {len(only)}줄 — 가계부에는 있고 명세서에는 없음")
        for i, r in only:
            near = [x for x in paid if abs((x["date"] - r["date"]).days) <= 1 and
                    (x["amount"] == r["amount"] or x["store"].replace(" ", "") == r["store"].replace(" ", ""))]
            hint = "".join(f" — 명세서 {x['date']} {x['store']} {won(x['amount'])} 줄과 견주어 보세요" for x in near[:1])
            print(f"  {r['date']} · {r['store']} · {won(r['amount'])}(가계부 {i}행){hint}")
    look = len(missing) + sum(len(l) - len(by_key_s[k]) for k, l in dup) + len(only)
    print()
    if look:
        print(f"사람이 볼 줄 {look} · exit code 3")
        return 3
    print("모두 일치 · exit code 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

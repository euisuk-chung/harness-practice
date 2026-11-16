"""카드 명세서와 가계부를 한 줄씩 맞춰 일치 · 누락 · 중복을 찾는다(reconciliation).

    uv run python reconcile.py statements/2026-10.csv                                   # 내 가계부 ledger.xlsx 와
    uv run python reconcile.py statements/2026-10.csv --ledger practice/ledger-2026-10.csv   # 연습용 10월 가계부와

명세서의 모양 — UTF-8 CSV(Excel 의 「CSV UTF-8」 도 된다). 첫 줄은 칸 이름 이용일,가맹점,금액,구분
- 이용일은 2026-10-03 처럼 하이픈으로 나눈 날짜, 금액은 쉼표 없는 양의 정수, 구분은 승인 또는 취소
- 모양이 다르면 「명세서 N행 · 칸 · 값」 을 찍고 exit code 1 — 짐작해서 승인으로 세지 않는다

맞추는 법
- 명세서의 달에 든 가계부의 카드 줄만 맞춘다. 현금 줄은 명세서에 없으니 맞추지 않는다
- 명세서의 취소 줄은 같은 가맹점 · 같은 금액의 승인 줄과 짝을 지어 함께 뺀다.
  그런 승인이 없거나(짝 없는 취소 · 부분 취소) 둘 이상이면 고르지 않고 「판정 불가」 로 남긴다
- 열쇠는 날짜와 금액이다. 가게 이름은 명세서(가맹점 이름)와 영수증이 다를 수 있어 열쇠로 쓰지 않는다
- 일치 — 명세서 한 줄에 가계부 한 줄
- 누락 — 명세서에는 있는데 가계부에 없는 줄
- 중복 — 명세서 한 줄에 가계부 두 줄 이상
- 가계부에만 — 가계부에는 있는데 명세서에 없는 줄. 날짜가 하루 안이고 금액이나 가게가 같은 명세서 줄을 함께 보인다
- 판정 불가 — 짝을 고를 수 없는 취소 줄. 사람이 명세서를 보고 정한다

exit code — 0: 모두 일치 · 3: 사람이 볼 줄이 있음 · 1: 실행 오류
"""
import csv
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

LEDGER = Path("ledger.xlsx")
COLUMNS = ["이용일", "가맹점", "금액", "구분"]
KINDS = ("승인", "취소")


class Bad(Exception):
    """명세서를 읽을 수 없다 — 몇 행 · 어느 칸 · 무슨 값인지 담는다."""


def day(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v).strip())


def won(n):
    return f"{n:,}원"


def statement_line(n, r):
    """명세서 n행 하나를 읽는다. 모양이 다르면 Bad."""
    v = {c: (r.get(c) or "").strip() for c in COLUMNS}
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v["이용일"]):
        raise Bad(f"명세서 {n}행 · 이용일 · {v['이용일']!r} — 2026-10-03 처럼 하이픈으로 나눈 날짜가 아닙니다")
    try:
        d = date.fromisoformat(v["이용일"])
    except ValueError:
        raise Bad(f"명세서 {n}행 · 이용일 · {v['이용일']!r} — 달력에 없는 날짜입니다")
    if not re.fullmatch(r"[0-9]+", v["금액"]) or int(v["금액"]) == 0:
        raise Bad(f"명세서 {n}행 · 금액 · {v['금액']!r} — 쉼표 없는 양의 정수가 아닙니다")
    if v["구분"] not in KINDS:
        raise Bad(f"명세서 {n}행 · 구분 · {v['구분']!r} — 승인 · 취소 가운데 하나가 아닙니다")
    return {"date": d, "store": v["가맹점"], "amount": int(v["금액"]), "kind": v["구분"]}


def read_statement(path):
    """명세서의 줄 · 짝 없는 승인 · 짝지은 취소 · 짝을 고를 수 없는 취소(취소, 후보 승인들)."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:     # -sig — Excel 「CSV UTF-8」 맨 앞의 표시(BOM)를 걷는다
            reader = csv.DictReader(f)
            absent = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if absent:
                raise Bad(f"명세서 1행 · 칸 이름 · {','.join(reader.fieldnames or [])!r} — {' · '.join(absent)} 칸이 없습니다")
            lines = [statement_line(reader.line_num, r) for r in reader]     # line_num — 파일에서 몇째 줄인지(칸 이름 줄이 1행)
    except UnicodeDecodeError:
        raise Bad("명세서를 UTF-8 로 읽을 수 없습니다 — Excel 에서 「CSV UTF-8」 로 다시 저장합니다")
    paid = [x for x in lines if x["kind"] == "승인"]
    cancels, unsure = [], []
    for c in (x for x in lines if x["kind"] == "취소"):
        twins = [p for p in paid if p["store"] == c["store"] and p["amount"] == c["amount"]]
        if len(twins) == 1:
            paid.remove(twins[0])
            cancels.append(twins[0])
        else:                                     # 없거나 여럿 — 어느 승인을 취소했는지 고르지 않는다
            unsure.append((c, twins))
    return lines, paid, cancels, unsure


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
    for path in (Path(args[0]), ledger_path):
        if not path.is_file():
            print(f"{path} 가 없습니다", file=sys.stderr)
            return 1
    try:
        lines, paid, cancels, unsure = read_statement(args[0])
    except Bad as e:
        print(e, file=sys.stderr)
        return 1
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

    kinds = [x["kind"] for x in lines]
    print(f"카드 명세서 {args[0]} — 승인 {kinds.count('승인')}줄 · 취소 {kinds.count('취소')}줄")
    print(f"가계부 {ledger_path} — 카드 {len(card)}줄" + (f"(현금 {cash}줄은 맞추지 않음)" if cash else ""))
    print()
    print(f"일치 {match}줄")
    for c in cancels:
        print(f"취소 1쌍 — {c['date']} · {c['store']} · {won(c['amount'])} 승인과 취소(가계부에 없어야 맞음)")
    if unsure:
        print(f"판정 불가 {len(unsure)}줄 — 어느 승인의 취소인지 고르지 못함")
        for c, twins in unsure:
            why = (f"같은 가맹점 · 같은 금액의 승인이 {len(twins)}줄({' · '.join(str(p['date']) for p in twins)})" if twins
                   else "같은 가맹점 · 같은 금액의 승인이 없음(짝 없는 취소 · 부분 취소)")
            print(f"  {c['date']} · {c['store']} · {won(c['amount'])} 취소 — {why}")
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
    look = len(missing) + sum(len(l) - len(by_key_s[k]) for k, l in dup) + len(only) + len(unsure)
    print()
    if look:
        print(f"사람이 볼 줄 {look} · exit code 3")
        return 3
    print("모두 일치 · exit code 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

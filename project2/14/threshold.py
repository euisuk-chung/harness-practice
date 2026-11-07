"""정답이 표시된 연습 묶음으로 threshold 를 바꿔 보며 review 로 가는 수와 틀린 판정을 센다.

    uv run python threshold.py                 # threshold 50 · 60 · 70 · 80 · 90 의 표
    uv run python threshold.py --at 70         # threshold 70 에서 쌍마다 어디로 갔나

practice/pairs.csv 의 한 줄은 「가계부에 이미 있는 줄」과 「새로 들어온 영수증」 한 쌍이다.
정답 칸은 사람이 정했다 — 같은 결제를 두 번 적게 되는 쌍이 「중복」(positive), 아니면 「아님」.
점수는 dedup.py 의 score 를 그대로 쓴다. 점수가 threshold 를 넘으면 review 로 가고, 넘지 않으면 dup 단계를 통과한다
(통과한 뒤의 형식 검사는 여기서 세지 않는다).
- false positive — 중복이 아닌데 review 로 간 쌍(사람이 괜히 본다)
- false negative — 중복인데 review 로 가지 않은 쌍(가계부에 두 번 적힌다)
"""
import csv
import sys
import unicodedata
from pathlib import Path

from dedup import score

PAIRS = Path("practice/pairs.csv")


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def rjust(s, n):
    return " " * (n - width(s)) + s


def load():
    out = []
    with PAIRS.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            old = {"date": r["가계부 날짜"], "store": r["가계부 가게"], "amount": int(r["가계부 금액"])}
            new = {"date": r["새 날짜"], "store": r["새 가게"], "amount": int(r["새 금액"])}
            out.append((r["번호"], score(new, old), r["정답"] == "중복", r["어떤 경우"]))
    return out


def table(pairs):
    dup = sum(1 for p in pairs if p[2])
    print(f"연습 묶음 {PAIRS} — {len(pairs)}쌍(중복 {dup} · 아님 {len(pairs) - dup})")
    head = ["threshold", "review 로 감", "false positive", "false negative"]
    print("  ".join(head))
    for t in (50, 60, 70, 80, 90):
        review = [p for p in pairs if p[1] > t]
        fp = sum(1 for p in review if not p[2])
        fn = sum(1 for p in pairs if p[2] and p[1] <= t)
        cells = [str(t), str(len(review)), str(fp), str(fn)]
        print("  ".join(rjust(c, width(h)) for c, h in zip(cells, head)))


def detail(pairs, t):
    print(f"threshold {t} — 점수가 {t} 을 넘으면 review 로, 넘지 않으면 다음 단계로")
    for name, s, is_dup, why in sorted(pairs, key=lambda p: -p[1]):
        went = "review" if s > t else "통과  "
        mark = "false positive" if s > t and not is_dup else "false negative" if s <= t and is_dup else ""
        print(f"{name}  {s:>3}  {went}  {'중복' if is_dup else '아님'}  {why}" + (f"  ← {mark}" if mark else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        table(load())
    elif len(args) == 2 and args[0] == "--at":
        detail(load(), int(args[1]))
    else:
        sys.exit("쓰는 법: uv run python threshold.py · uv run python threshold.py --at 70")

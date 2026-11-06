"""판매 글을 규칙으로 검사한다(rule-based check).

    uv run python check.py golden/01.md

exit code — 0: 규칙을 모두 지켰다 · 1: 하나라도 어겼다(이유를 찍는다)
"""
import re
import sys
from pathlib import Path

PRICE = "45,000원"           # item.md 에 적힌 가격
MUST = ["이어팁", "흠집"]     # item.md 의 상태에서 빠지면 안 되는 낱말


def check(text):
    reasons = []
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("# "):
        reasons.append("첫 줄이 '# ' 로 시작하는 제목이 아닙니다")
    if len(lines) > 10:
        reasons.append(f"빈 줄을 빼고 {len(lines)}줄입니다(10줄 이하)")
    price = [line for line in lines if line.startswith("가격:")]
    if not price:
        reasons.append("'가격:' 줄이 없습니다")
    elif PRICE not in price[0]:
        reasons.append(f"가격이 메모와 다릅니다 — {price[0]}")
    for word in MUST:
        if word not in text:
            reasons.append(f"상태 '{word}' 가 빠졌습니다")
    if re.search(r"(이어팁|흠집)[^.\n]{0,6}없", text):
        reasons.append("상태를 '없다' 로 뒤집었습니다")
    return reasons


if __name__ == "__main__":
    reasons = check(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for reason in reasons:
        print("거부 —", reason)
    if reasons:
        sys.exit(1)
    print("통과")

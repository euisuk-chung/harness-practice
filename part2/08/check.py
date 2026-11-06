"""환불 요청 문자를 규칙으로 검사한다.

    uv run python check.py draft.md

exit code — 0: 통과 · 1: 거부(이유를 찍는다)
"""
import sys
from pathlib import Path

MEMBER = "20417"       # memo.md 의 회원번호
AMOUNT = "135,000원"   # memo.md 의 환불 받을 금액
LIMIT = 100            # 공백을 포함한 글자 수 상한


def check(text):
    reasons = []
    if MEMBER not in text:
        reasons.append(f"회원번호 {MEMBER} 이 없습니다")
    if AMOUNT not in text:
        reasons.append(f"환불 금액 {AMOUNT} 이 없습니다")
    if len(text.strip()) > LIMIT:
        reasons.append(f"{len(text.strip())}자입니다({LIMIT}자 이하)")
    return reasons


if __name__ == "__main__":
    reasons = check(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for reason in reasons:
        print("거부 —", reason)
    if reasons:
        sys.exit(1)
    print("통과")

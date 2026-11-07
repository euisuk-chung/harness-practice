"""고른 안으로 plan.json 을 확정한다.

    uv run python choose.py 2      # plans/2.json 을 plan.json 으로

확정하기 전에 constraints.py 와 같은 검사를 그 안에 한 번 더 한다. 거부된 안은 확정하지 않는다(exit code 1).
확인 못 한 정보가 남은 안을 고르면, 그 목록을 plan.json 의 unknown 에 같이 적는다 — 내가 알고 고른 것이다.
"""
import json
import sys
from pathlib import Path

from constraints import check, load


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("쓰는 법: uv run python choose.py <번호>")
        sys.exit(1)
    n = sys.argv[1]
    f = Path("plans") / f"{n}.json"
    if not f.exists():
        print(f"없는 안입니다: {f}")
        sys.exit(1)
    plan = json.loads(f.read_text(encoding="utf-8"))
    trip, items = load(Path("."))
    reasons, unknown = check(plan, trip, items)
    if reasons:
        print(f"{n}안은 검사에서 거부되어 확정하지 않습니다.")
        for r in reasons:
            print(f"  {r}")
        sys.exit(1)
    plan["chosen"] = int(n)
    plan["unknown"] = unknown
    Path("plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"plan.json 에 {n}안을 확정했습니다 — {plan.get('title', '')}")
    for u in unknown:
        print(f"  알고 고른 것: {u}")


if __name__ == "__main__":
    main()

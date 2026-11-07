"""golden set 으로 검사를 잰다(eval).

    uv run python eval.py           # check.py 로 열 건을 판정하고 정답과 맞춰 본다
    uv run python eval.py --save    # 이번 판정을 baseline.json 에 저장한다
    uv run python eval.py --judge   # judge.md 로 Claude 가 판정한다(Claude 를 열 번 부른다)

baseline.json 이 있으면 저장해 둔 판정과 비교해, 전에 맞혔는데 이번에 틀린 건(regression)을 찍는다.
exit code — 0: regression 없음 · 1: regression 있음
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from check import check

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
BASELINE = HERE / "baseline.json"


def judge(text):
    """judge.md 와 메모·판매 글을 한 프롬프트로 보내 {"pass", "reason"} 을 받는다."""
    prompt = "\n\n".join([
        (HERE / "judge.md").read_text(encoding="utf-8"),
        "# 판매 메모\n" + (HERE / "item.md").read_text(encoding="utf-8"),
        "# 판매 글\n" + text,
    ])
    # 도구 없이(--tools ""), 정답 파일이 없는 빈 폴더에서 부른다
    with tempfile.TemporaryDirectory() as empty:
        done = subprocess.run(["claude", "-p", prompt, "--output-format", "json", "--tools", ""],
                              cwd=empty, capture_output=True, text=True, encoding="utf-8")
    try:
        result = json.loads(done.stdout)["result"]
        got = json.loads(re.search(r"\{.*\}", result, re.S).group())
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        got = None
    # 두 칸(pass · reason)만 있고 pass 는 true · false, reason 은 글이어야 판정으로 쓴다
    if (not isinstance(got, dict) or set(got) != {"pass", "reason"}
            or not isinstance(got["pass"], bool) or not isinstance(got["reason"], str)):
        return {"pass": None, "reason": "판정을 읽을 수 없습니다"}
    return got


def main():
    expected = json.loads((GOLDEN / "expected.json").read_text(encoding="utf-8"))
    use_judge = "--judge" in sys.argv
    verdicts, right = {}, 0
    for name, want in expected.items():
        text = (GOLDEN / name).read_text(encoding="utf-8")
        if use_judge:
            got = judge(text)
            ok, why = got["pass"], got["reason"]
        else:
            reasons = check(text)
            ok, why = not reasons, " / ".join(reasons)
        hit = ok == want["pass"]
        right += hit
        verdicts[name] = hit
        said = {True: "통과", False: "거부"}.get(ok, "실패")
        print(f"{name}  정답 {'통과' if want['pass'] else '거부'}  판정 {said}  "
              f"{'맞음' if hit else '틀림'}  ({want['kind']})  {why}")
    print(f"맞힌 개수: {right}/{len(expected)}")

    if use_judge:
        return
    if "--save" in sys.argv:
        BASELINE.write_text(json.dumps(verdicts, indent=2) + "\n", encoding="utf-8")
        print("baseline.json 에 저장했습니다")
        return
    if BASELINE.exists():
        before = json.loads(BASELINE.read_text(encoding="utf-8"))
        broken = [n for n in verdicts if before.get(n) and not verdicts[n]]
        fixed = [n for n in verdicts if before.get(n) is False and verdicts[n]]
        print("고쳐진 건:", ", ".join(fixed) or "없음")
        print("regression:", ", ".join(broken) or "없음")
        if broken:
            sys.exit(1)


main()

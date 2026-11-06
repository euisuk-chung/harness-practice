"""prompt.md 를 claude -p 로 한 번 보내고, 답의 result 가 schema.json 의 형식을 지켰는지 검증한다.

    uv run python run.py                              # Claude Code 를 한 번 부른다
    uv run python run.py fixtures/missing-when.json   # 저장해 둔 응답으로 검증만 한다

exit code — 0: 형식을 지켰다 · 1: 형식을 어겼거나 호출이 실패했다
"""
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).parent


def fail(reason):
    print("거부 —", reason)
    sys.exit(1)


def call_claude():
    prompt = (HERE / "prompt.md").read_text(encoding="utf-8")
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--allowedTools", "Read"]
    done = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        fail(f"claude -p 가 exit code {done.returncode} 로 끝났습니다")
    return done.stdout


def load(text, what):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail(f"{what} JSON 으로 읽을 수 없습니다")


def main():
    if len(sys.argv) > 1:
        outer = load(Path(sys.argv[1]).read_text(encoding="utf-8"), "바깥 응답을")
    else:
        outer = load(call_claude(), "바깥 응답을")
        (HERE / "response.json").write_text(
            json.dumps(outer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not isinstance(outer, dict) or not isinstance(outer.get("result"), str):
        fail("바깥 응답에 글로 된 result 칸이 없습니다")
    result = load(outer["result"], "result 를")

    schema = json.loads((HERE / "schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(result))
    if errors:
        for e in errors:
            where = "/".join(str(p) for p in e.path) or "(맨 위)"
            print(f"  {where}: {e.message}")
        fail(f"schema.json 과 다른 곳 {len(errors)}군데")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"통과 — 할 일 {len(result['todos'])}개")
    sys.exit(0)


main()

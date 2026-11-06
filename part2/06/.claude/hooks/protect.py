"""PreToolUse hook — sources/ 아래 파일을 쓰거나 고치려 하면 막는다.

Claude Code 는 Edit·Write 도구를 쓰기 직전에 이 스크립트를 부르고, 그 도구 호출을 JSON 으로 stdin 에 넣어 준다.
exit code — 0: 허용 · 2: 막음(이유는 stderr 에). 입력을 읽지 못하거나 어떤 예외가 나도 2 로 막는다(fail-closed).

    uv run python .claude/hooks/protect.py < fixtures/write-sources.json   # Claude 없이 직접 시험하기
"""
import json
import sys
from pathlib import Path


def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    data = json.loads(sys.stdin.read())
    cwd = Path(data["cwd"]).resolve()
    target = (cwd / data["tool_input"]["file_path"]).resolve()
    sources = cwd / "sources"
    if target == sources or sources in target.parents:
        block(f"막음 — sources/ 는 원문이라 고치지 않습니다: {target.relative_to(cwd)}")
    sys.exit(0)


try:
    main()
except Exception as e:
    block(f"막음 — hook 이 입력을 읽지 못했습니다: {type(e).__name__}")

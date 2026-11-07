"""PreToolUse hook — Edit · Write 를 research/ 안의 .json 파일에만 허용한다.

어느 subagent 가 어느 파일을 쓰는지(weather 가 research/weather.json 을 쓰는지)는 가리지 않는다 — 이름은 기록에만 쓴다.

Claude Code 는 Edit · Write 도구를 쓰기 직전에 이 스크립트를 부르고, 그 도구 호출을 JSON 으로 stdin 에 넣어 준다.
subagent 가 부른 도구에도 같은 hook 이 불리고, 그때는 JSON 에 subagent 의 이름(agent_type)이 함께 온다.
exit code — 0: 허용 · 2: 막음(이유는 stderr 에). 입력을 읽지 못하거나 어떤 예외가 나도 2 로 막는다(fail-closed).

불릴 때마다 hook-log.jsonl 에 한 줄을 남긴다 — 누가(subagent 이름, 본 세션이면 main) · 어느 도구 · 어느 파일 · 허용/막음.

    uv run python .claude/hooks/protect.py < fixtures/hook/write-weather.json   # Claude 없이 직접 시험하기
"""
import json
import re
import sys
from pathlib import Path

RESULT = re.compile(r"research/[a-z0-9-]+\.json")
seen = {"agent": "", "tool": "", "path": ""}


def record(decision):
    try:
        line = dict(seen, decision=decision)
        with open("hook-log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


def block(reason):
    record("block")
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    data = json.loads(sys.stdin.read())
    seen["agent"] = data.get("agent_type") or "main"
    seen["tool"] = data.get("tool_name", "")
    seen["path"] = data["tool_input"]["file_path"]
    cwd = Path(data["cwd"]).resolve()
    target = (cwd / data["tool_input"]["file_path"]).resolve()
    if not target.is_relative_to(cwd):
        block(f"막음 — 여행 폴더 밖에는 쓰지 않습니다: {seen['path']}")
    path = target.relative_to(cwd).as_posix()
    seen["path"] = path
    if not RESULT.fullmatch(path):
        block(f"막음 — 조사 결과는 research/<이름>.json 에만 씁니다: {path}")
    record("allow")      # 허용 — 아무것도 찍지 않고 exit code 0
    sys.exit(0)


try:
    main()
except Exception as e:
    block(f"막음 — hook 이 입력을 읽지 못했습니다: {type(e).__name__}")

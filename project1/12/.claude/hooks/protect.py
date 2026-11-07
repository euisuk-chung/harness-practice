"""PreToolUse hook — 수집 단계만 runs/<날짜>/sources/ 에 원문을 쓰게 한다.

Claude Code 는 Edit·Write 도구를 쓰기 직전에 이 스크립트를 부르고, 그 도구 호출을 JSON 으로 stdin 에 넣어 준다.
지금 단계 이름은 runner 가 넘기는 환경 변수 RUNNER_STEP 으로 본다.
- collect 단계: runs/<날짜>/sources/ 안의 파일만 쓸 수 있다
- 다른 단계, runner 없이 연 Claude: runs/ 아래를 쓰거나 고칠 수 없다 — 수집이 끝난 원문은 확정이다
exit code — 0: 허용 · 2: 막음(이유는 stderr 에). 입력을 읽지 못하거나 어떤 예외가 나도 2 로 막는다(fail-closed).

불릴 때마다 운영 기록에 한 줄을 남긴다. daily.py 가 환경 변수 RUN_LOG 로 그날의 runs/<날짜>/log.jsonl 을 알려 준다.
RUN_LOG 가 없으면(daily.py 없이 실행) 남기지 않는다. 남기다 실패해도 허용 · 막음 판단은 바뀌지 않는다.

    RUNNER_STEP=collect uv run python .claude/hooks/protect.py < fixtures/hook-write-source.json   # Claude 없이 직접 시험하기
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SOURCES = re.compile(r"runs/\d{4}-\d{2}-\d{2}/sources/[^/]+")
seen = {"tool": "", "path": ""}


def record(decision):
    """운영 기록에 hook 한 줄 — 언제 · 어느 단계 · 어느 도구 · 어느 파일 · 허용/막음."""
    log = os.environ.get("RUN_LOG")
    if not log:
        return
    try:
        line = {"t": "hook", "at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "step": os.environ.get("RUNNER_STEP", ""), "tool": seen["tool"],
                "path": seen["path"], "decision": decision}
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


def allow():
    record("allow")
    sys.exit(0)


def block(reason):
    record("block")
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    data = json.loads(sys.stdin.read())
    seen["tool"] = data.get("tool_name", "")
    cwd = Path(data["cwd"]).resolve()
    target = (cwd / data["tool_input"]["file_path"]).resolve()
    seen["path"] = data["tool_input"]["file_path"]
    path = target.relative_to(cwd).as_posix()       # 폴더 밖이면 여기서 예외 → 막음
    seen["path"] = path
    step = os.environ.get("RUNNER_STEP", "")
    if step == "collect":
        if not SOURCES.fullmatch(path):
            block(f"막음 — collect 단계는 runs/<날짜>/sources/ 에만 씁니다: {path}")
        allow()
    if path == "runs" or path.startswith("runs/"):
        block(f"막음 — 수집이 끝난 원문은 고치지 않습니다(지금 단계: {step or '없음'}): {path}")
    allow()


try:
    main()
except Exception as e:
    block(f"막음 — hook 이 입력을 읽지 못했습니다: {type(e).__name__}")

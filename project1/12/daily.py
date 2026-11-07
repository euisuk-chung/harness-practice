"""하루 한 번 실행 — run ID 를 정하고, 그날 이미 실행했는지 보고, runner 를 부르고, 운영 기록을 남긴다.

    uv run python daily.py                                  # 오늘 실행 — GitHub Actions 가 매일 아침 이것을 부른다
    uv run python daily.py --answer fixtures/empty.json     # Claude 대신 저장해 둔 응답으로 — 새 글 0건인 날

1. run ID 는 오늘 날짜(YYYY-MM-DD)다. 운영 기록은 runs/<run ID>/log.jsonl 에 한 줄씩 쌓는다
2. idempotency — origin 에 draft/<run ID> branch 가 있거나 그 branch 의 PR 이 있으면 그날은 이미 실행했다.
   건너뜀 한 줄만 남기고 exit code 0. 확인하지 못하면(인터넷 · gh 로그인) 실행하지 않고 exit code 1
3. runner.py 를 부른다. 환경 변수로 RUN_ID(승인 단계가 쓰는 날짜)와 RUN_LOG(hook 이 기록을 남길 파일)를 넘긴다
4. runner 가 끝나면 단계마다 한 줄(언제 · 몇 번째 · 결과 · exit code)과 끝 한 줄을 더한다
5. PR 을 연 날은 운영 기록을 draft/<run ID> branch 에 커밋해 push 한다. 그 밖의 날은 이 컴퓨터에만 남는다
6. steps/audit.py 로 빠진 기록이 없는지 보고, 운영 기록 전체를 화면에 찍는다 — GitHub Actions 의 실행 기록에 남는다
runner 는 고치지 않는다. 단계가 시작한 시각은 runner 가 찍는 「[단계] N번째 실행」 줄을 읽어 잰다.
exit code — 0: 건너뜀 · 끝 · PR 을 열었다 · 1: 그 밖 모두(사람이 볼 일 — GitHub Actions 는 실패로 표시하고 알린다)
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

STATE = Path("state.json")
EXIT = {"ok": 0, "reject": 1, "human": 3, "nothing": 4}      # run 단계의 결과 → 그 명령의 exit code
STARTED = re.compile(r"^\[(\w+)\] (\d+)번째 실행")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write(log, **line):
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")


def already_ran(run_id):
    """그날 이미 실행했는지 본다 — origin 의 draft/<run ID> branch, 그 branch 로 연 PR(닫히거나 합친 것까지)."""
    branch = f"draft/{run_id}"
    found = git("ls-remote", "--heads", "origin", branch)
    if found.returncode != 0:
        raise RuntimeError(f"git ls-remote — {found.stderr.strip()[-200:]}")
    if found.stdout.strip():
        return f"origin 에 {branch} branch 가 있습니다"
    found = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                            "--json", "url", "--jq", ".[].url"],
                           capture_output=True, text=True, encoding="utf-8")
    if found.returncode != 0:
        raise RuntimeError(f"gh pr list — {found.stderr.strip()[-200:]}")
    if found.stdout.strip():
        return f"{branch} 의 PR 이 있습니다: {found.stdout.split()[0]}"
    return ""


def finish(log, code):
    """빠진 기록이 없는지 보고, 운영 기록 전체를 찍는다."""
    audit = subprocess.run([sys.executable, "steps/audit.py", str(log)])
    print(f"운영 기록 — {log.relative_to(Path.cwd().resolve()).as_posix()}")
    print(log.read_text(encoding="utf-8"), end="")
    return 0 if code == 0 and audit.returncode == 0 else 1


def step_lines(graph_path, started):
    """state.json 의 history 가운데 이번에 실행한 시도만, 시작 시각 · exit code 를 붙여 돌려준다."""
    steps = yaml.safe_load(Path(graph_path).read_text(encoding="utf-8"))["steps"]
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    lines = []
    for h in state.get("history", []):
        key = (h["step"], h["attempt"])
        if key not in started:                    # 다른 날 · 다른 실행의 기록
            continue
        line = {"t": "step", "at": started[key], "step": h["step"], "attempt": h["attempt"],
                "result": h["result"]}
        if "run" in steps.get(h["step"], {}) and h["result"] in EXIT:
            line["exit"] = EXIT[h["result"]]
        if h["why"]:
            line["why"] = h["why"]
        lines.append(line)
    return state, lines


def main():
    sys.stdout.reconfigure(line_buffering=True)   # 점검 스크립트의 출력과 차례가 섞이지 않게
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", nargs="?", default="graph.yaml")
    ap.add_argument("--answer", help="runner 에 그대로 넘긴다 — Claude 를 부르지 않는다(fixture)")
    a = ap.parse_args()
    run_id = date.today().isoformat()
    log = Path("runs", run_id, "log.jsonl").resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    trigger = os.environ.get("GITHUB_EVENT_NAME", "local")
    print(f"run ID {run_id} · trigger {trigger}")

    try:                                          # ① idempotency — 그날 이미 실행했나
        why = already_ran(run_id)
    except (RuntimeError, OSError) as e:
        write(log, t="run", at=now(), run_id=run_id, trigger=trigger)
        write(log, t="end", at=now(), result="stopped", why=f"그날 실행했는지 확인하지 못했습니다 — {e}")
        print(f"멈춤 — 그날 실행했는지 확인하지 못했습니다: {e}")
        return finish(log, 1)
    if why:
        write(log, t="skip", at=now(), run_id=run_id, trigger=trigger, why=why)
        print(f"건너뜀 — {why}")
        return finish(log, 0)

    write(log, t="run", at=now(), run_id=run_id, trigger=trigger)
    env = dict(os.environ, RUN_ID=run_id, RUN_LOG=str(log), PYTHONUNBUFFERED="1")
    cmd = [sys.executable, "runner.py", a.graph] + (["--answer", a.answer] if a.answer else [])
    started = {}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8", env=env)
    for out in proc.stdout:                       # ② runner 의 출력을 그대로 보이며 단계 시작 시각을 잰다
        print(out, end="", flush=True)
        m = STARTED.match(out)
        if m:
            started[(m[1], int(m[2]))] = now()
    code = proc.wait()

    state, lines = step_lines(a.graph, started)
    last = (state.get("history") or [{}])[-1].get("why", "")
    opened = code == 3 and state.get("step") == "approve" and last.startswith("needs_approval")
    branch = f"draft/{run_id}"
    if opened:                                    # ③ PR 을 연 날 — 운영 기록은 draft branch 에 있다
        moved = git("switch", branch)
        if moved.returncode != 0:
            print(f"운영 기록을 {branch} 에 올리지 못했습니다 — {moved.stderr.strip()[-200:]}")
            opened = False
            code = 1
    for line in lines:
        write(log, **line)
    write(log, t="end", at=now(), runner_exit=code, status=state.get("status", ""))
    result = finish(log, 0 if code == 0 or opened else 1)
    if opened:
        for args in (("add", "--", log.relative_to(Path.cwd().resolve()).as_posix()),
                     ("commit", "-m", f"{run_id} 운영 기록"),
                     ("push", "origin", branch)):
            done = git(*args)
            if done.returncode != 0:
                print(f"운영 기록을 {branch} 에 올리지 못했습니다 — git {args[0]}: {done.stderr.strip()[-200:]}")
                result = 1
                break
        git("switch", "main")
    print(f"daily — exit code {result}")
    return result


if __name__ == "__main__":
    sys.exit(main())

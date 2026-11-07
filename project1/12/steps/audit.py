"""운영 기록 점검 — runs/<날짜>/log.jsonl 을 읽어, 있어야 할 기록이 빠지지 않았는지 본다.

    uv run python steps/audit.py runs/<날짜>/log.jsonl
    uv run python steps/audit.py fixtures/log/no-hook.jsonl     # hook 기록이 빠진 날 — exit code 1

한 파일에 실행이 여러 번 있으면 마지막 실행(run · skip 줄부터)만 본다.
- 건너뜀(skip) 줄로 시작하면 통과
- 줄이 JSON 이 아니거나, 시작(run) 줄 · 끝(end) 줄이 없으면 거부 — 실행이 중간에 끊겼다
- 세기(count)가 새 글이 있다고 했는데(결과 ok) 수집(collect) 단계의 hook 허용 줄이 하나도 없으면 거부.
  수집이 원문 파일을 썼다면 hook 이 불렸어야 한다 — hook 이 꺼졌거나 기록을 남기지 못했다(silent failure)
통과하면 운영 점검표(단계마다 몇 번 · 결과 · exit code, hook 허용 · 막음 수, runner 의 exit code)를 찍는다.
이 점검은 기록이 빠졌는지만 본다. 글이 맞는지, hook 이 막아야 할 것을 막았는지는 보지 않는다.
exit code — 0: 통과 · 1: 거부(이유를 찍는다)
"""
import json
import sys
from pathlib import Path


def last_run(path):
    lines = []
    for n, text in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not text.strip():
            continue
        try:
            line = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"{n}번째 줄이 JSON 이 아닙니다")
        if line.get("t") in ("run", "skip"):
            lines = []                            # 새 실행 — 앞 실행의 줄은 버린다
        lines.append(line)
    return lines


def main(path):
    try:
        lines = last_run(path)
    except (OSError, ValueError) as e:
        print(f"거부 — 운영 기록을 읽지 못했습니다: {e}")
        return 1
    if not lines or lines[0]["t"] not in ("run", "skip"):
        print("거부 — 시작 기록 없음: run 줄이 없습니다")
        return 1
    head = lines[0]
    print(f"운영 점검표 — run ID {head.get('run_id')} · trigger {head.get('trigger')}")
    if head["t"] == "skip":
        print(f"건너뜀 — {head.get('why')}")
        return 0
    end = [x for x in lines if x["t"] == "end"]
    if not end:
        print("거부 — 끝 기록 없음: run 줄 뒤에 end 줄이 없습니다. 실행이 중간에 끊겼습니다")
        return 1

    steps, hooks = {}, {"allow": 0, "block": 0}
    for x in lines:
        if x["t"] == "step":
            steps.setdefault(x["step"], []).append(x)
        elif x["t"] == "hook":
            hooks[x["decision"]] = hooks.get(x["decision"], 0) + 1
    for name, tries in steps.items():
        results = " → ".join(t["result"] for t in tries)
        codes = " → ".join(str(t["exit"]) for t in tries if "exit" in t)
        print(f"{name:<8} {len(tries)}번 · {results}" + (f" · exit {codes}" if codes else ""))
    print(f"{'hook':<8} 허용 {hooks['allow']} · 막음 {hooks['block']}")
    print(f"{'end':<8} runner exit code {end[-1].get('runner_exit', '-')} · {end[-1].get('why') or end[-1].get('status', '')}")

    found_new = any(t["result"] == "ok" for t in steps.get("count", []))
    collect_hook = any(x["t"] == "hook" and x.get("step") == "collect" and x.get("decision") == "allow"
                       for x in lines)
    if found_new and not collect_hook:
        print("거부 — hook 기록 없음: 새 글이 있었는데(count ok) collect 단계의 hook 허용 줄이 없습니다. "
              "hook 이 꺼졌을 수 있습니다(silent failure)")
        return 1
    print("점검 통과 — 있어야 할 기록이 모두 있습니다")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

# 실습 저장소

수업의 실습 폴더를 PART 별로 담은 저장소입니다. 받은 뒤에는 그 차시의 실습 폴더로 들어가 실행합니다.

| 폴더 | 하는 일 |
|---|---|
| `part2/05` | Claude Code 를 `claude -p` 로 한 번 부르고, 답이 `schema.json` 의 형식을 지켰는지 검증합니다. 지켰으면 exit code 0, 어겼으면 1 로 끝납니다. |
| `part2/06` | `sources/` 의 원문을 고치지 못하게 막는 PreToolUse hook(`.claude/hooks/protect.py`)과 permissions 설정 예시입니다. hook 은 막을 때 exit code 2 로 끝납니다. |

## 받기와 실행

```bash
git clone https://github.com/euisuk-chung/harness-practice.git
cd harness-practice/part2/05
uv sync
uv run python run.py fixtures/missing-when.json   # 저장해 둔 응답으로 검증만 — Claude 를 부르지 않습니다
uv run python run.py                              # Claude Code 를 한 번 부릅니다 — 로그인이 필요합니다
```

이미 받은 저장소는 맨 위 폴더에서 `git pull` 로 새 실습 폴더를 받습니다.

```bash
cd ~/harness-practice
git pull
cd part2/06
uv sync
uv run python .claude/hooks/protect.py < fixtures/write-sources.json   # hook 만 시험 — Claude 를 부르지 않습니다
```

실행에 필요한 것은 uv 와 Claude Code(구독 계정으로 로그인)입니다. `run.py` 가 만드는 `response.json` 과 `uv sync` 가 만드는 `.venv`·`uv.lock` 은 저장소에 올리지 않습니다.

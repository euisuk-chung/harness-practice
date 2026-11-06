# 실습 저장소

수업의 실습 폴더를 PART 별로 담은 저장소입니다. 받은 뒤에는 그 차시의 실습 폴더로 들어가 실행합니다.

| 폴더 | 하는 일 |
|---|---|
| `demo/minutes` | 회의록 자동화 시연입니다. 녹취록을 `inbox/` 에 넣으면 회의록과 검사 보고가 나옵니다. 그 폴더에서 `./start.sh --replay` 로 Claude 를 부르지 않고 다시 볼 수 있습니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `part2/05` | Claude Code 를 `claude -p` 로 한 번 부르고, 답이 `schema.json` 의 형식을 지켰는지 검증합니다. 지켰으면 exit code 0, 어겼으면 1 로 끝납니다. |
| `part2/06` | `sources/` 의 원문을 고치지 못하게 막는 PreToolUse hook(`.claude/hooks/protect.py`)과 permissions 설정 예시입니다. hook 은 막을 때 exit code 2 로 끝납니다. |
| `part2/07` | 중고 판매 글을 규칙으로 검사하는 `check.py` 와 Claude 가 판정하는 `judge.md`, 정답을 붙인 판매 글 열 건(`golden/`)으로 검사를 재는 `eval.py` 입니다. 검사를 고친 뒤 전에 맞히던 판정이 틀리면 exit code 1 로 끝납니다. |
| `part2/08` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 `runner.py` 와 환불 요청 문자를 검사하는 `check.py` 입니다. 거부되면 이유를 붙여 다시 쓰고, `max_attempts` 를 넘기거나 입력·권한이 막히면 `human_queue/` 에 남기고 exit code 3 으로 끝납니다. 단계가 exit code 4(할 일 없음)로 끝나면 남은 단계를 건너뛰고 exit code 0 으로 끝납니다. 멈췄다 다시 실행하면 `state.json` 에서 이어 갑니다. `--answer fixtures/…` 로 Claude 를 부르지 않고 시험할 수 있습니다. |
| `project1/09` | 프로젝트 1 블로그의 시작 저장소입니다. `project1` 아래 번호 폴더마다 그 차시 시작 상태 전체가 들어 있습니다. 이 폴더를 복사해 내 GitHub 계정의 새 저장소로 올리고 GitHub Pages 로 빈 블로그를 엽니다. `make_site.py` 가 `posts/` 의 글로 `docs/` 를 만들고, `examples/` 에 계획서 `PLAN.md`·graph 초안·`CLAUDE.md` 가 있습니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project1/10` | 블로그에 수집 · 작성 단계를 더한 상태입니다. `prompts/` 의 수집 · 작성 프롬프트, 수집 결과를 세는 `steps/count.py`, 수집 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 hook(`.claude/hooks/protect.py`), Claude 를 부르지 않고 시험하는 `fixtures/` 가 들어 있습니다. 이미 `~/my-blog` 가 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |

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

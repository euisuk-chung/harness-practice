# 실습 저장소

수업의 실습 폴더를 PART 별로 담은 저장소입니다. 받은 뒤에는 그 차시의 실습 폴더로 들어가 실행합니다.

| 폴더 | 하는 일 |
|---|---|
| `demo/minutes` | 회의록 자동화 시연입니다. 녹취록을 `inbox/` 에 넣으면 회의록과 검사 보고가 나옵니다. 그 폴더에서 `./start.sh --replay` 로 Claude 를 부르지 않고 다시 볼 수 있습니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `part1/03` | 업무를 구간으로 분해하고 구간마다 맡길지, 얼마나 크게 맡길지 적는 워크시트입니다. `worksheet.md` 는 빈 양식이고, `worksheet-blog.md` 는 프로젝트 1 블로그 업무로 채운 예시입니다. 실행할 코드는 없습니다. |
| `part1/04` | 업무의 판단 기준을 끌어내 기준 문서 `criteria.md` 한 장으로 적는 프롬프트 셋입니다. 인터뷰(`interview-prompt.md`), 기준 문서로 옮기기(`criteria-prompt.md`), 기준 문서만 보고 판단하기(`check-prompt.md`)를 차례로 Claude 대화 창에 붙여 넣습니다. 프로젝트 1 블로그로 만든 기준 문서 `criteria-blog.md`, 확인에 쓴 지난 사례 `check-cases-blog.md`, 그 대화를 고치지 않고 옮긴 기록 `blog-run-log.md` 가 함께 들어 있습니다. 실행할 코드는 없습니다. |
| `part2/05` | Claude Code 를 `claude -p` 로 한 번 부르고, 답이 `schema.json` 의 형식을 지켰는지 검증합니다. 지켰으면 exit code 0, 어겼으면 1 로 끝납니다. |
| `part2/06` | `sources/` 의 원문을 고치지 못하게 막는 PreToolUse hook(`.claude/hooks/protect.py`)과 permissions 설정 예시입니다. hook 은 막을 때 exit code 2 로 끝납니다. |
| `part2/07` | 중고 판매 글을 규칙으로 검사하는 `check.py` 와 Claude 가 판정하는 `judge.md`, 정답을 붙인 판매 글 열 건(`golden/`)으로 검사를 재는 `eval.py` 입니다. 검사를 고친 뒤 전에 맞히던 판정이 틀리면 exit code 1 로 끝납니다. |
| `part2/08` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 `runner.py` 와 환불 요청 문자를 검사하는 `check.py` 입니다. 거부되면 이유를 붙여 다시 쓰고, `max_attempts` 를 넘기거나 입력·권한이 막히면 `human_queue/` 에 남기고 exit code 3 으로 끝납니다. 단계가 exit code 4(할 일 없음)로 끝나면 남은 단계를 건너뛰고 exit code 0 으로 끝납니다. 멈췄다 다시 실행하면 `state.json` 의 멈춘 자리부터 다시 실행합니다. `--answer fixtures/…` 로 Claude 를 부르지 않고 시험할 수 있습니다. |
| `project1/09` | 프로젝트 1 블로그의 시작 저장소입니다. `project1` 아래 번호 폴더마다 그 차시 시작 상태 전체가 들어 있습니다. 이 폴더를 복사해 내 GitHub 계정의 새 저장소로 올리고 GitHub Pages 로 빈 블로그를 엽니다. `make_site.py` 가 `posts/` 의 글로 `docs/` 를 만들고, `examples/` 에 계획서 `PLAN.md`·graph 초안·`CLAUDE.md` 가 있습니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project1/10` | 블로그에 수집 · 작성 단계를 더한 상태입니다. `prompts/` 의 수집 · 작성 프롬프트, 수집 결과를 세는 `steps/count.py`, 수집 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 hook(`.claude/hooks/protect.py`), Claude 를 부르지 않고 시험하는 `fixtures/` 가 들어 있습니다. 이미 `~/my-blog` 가 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project1/11` | 블로그에 검사 · 승인 단계를 더한 상태입니다. 초안을 다섯 가지로 검사하는 `steps/check.py`, 통과한 초안으로 PR 을 여는 `steps/approve.py`, 작성 → 검사만 있는 연습 graph(`examples/graph-retry.yaml`), 검사마다 거부되는 초안이 든 `fixtures/check/` 가 들어 있습니다. 이미 `~/my-blog` 가 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project1/12` | 블로그를 매일 아침 저절로 실행하게 한 상태입니다. GitHub Actions workflow(`examples/daily.yml` — 매일 한국 시간 07:00 · 손으로 실행 · 한 번에 하나만), 그날 이미 실행했으면 건너뛰고 runner 를 불러 운영 기록 `runs/<날짜>/log.jsonl` 을 남기는 `daily.py`, 빠진 기록을 찾는 `steps/audit.py` 가 들어 있습니다. hook 은 불릴 때마다 운영 기록에 한 줄을 남깁니다. 이미 `~/my-blog` 가 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project2/13` | 프로젝트 2 가계부의 시작 상태입니다. 영수증을 `inbox/` 에 넣으면 폴더 trigger(`watch.py`)가 runner 를 실행하고, Claude 가 가계부 정리 skill(`examples/SKILL.md` — `.claude/skills/ledger-rules/SKILL.md` 로 복사)의 기준대로 영수증을 읽습니다. `ledger.py` 가 기록 전에 형식을 검사해 통과한 것만 Excel 가계부 `ledger.xlsx` 에 한 줄 더하고, 나머지는 이유와 함께 `review/` 로 보냅니다. 지어낸 연습 영수증 셋(`receipts/`)이 들어 있습니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project2/14` | 가계부에 같은 영수증이 두 번 적히지 않게 한 상태입니다. 기록할 때 영수증 파일의 content hash 를 가계부 「content hash」 칸에 같이 적고, graph 에 같은 파일을 알아보는 `seen` 단계와 날짜 · 가게 · 금액으로 중복 의심 점수를 매기는 `dup` 단계(`dedup.py`, threshold 70)가 더해졌습니다. 정답이 표시된 연습 묶음(`practice/pairs.csv`)으로 threshold 를 바꿔 보는 `threshold.py`, 연습용 카드 명세서(`statements/2026-10.csv`)와 가계부를 맞춰 일치 · 누락 · 중복을 찾는 `reconcile.py`, 같은 영수증을 다시 찍은 사진 `receipts/r01-again.png` 이 들어 있습니다. 이미 `~/my-ledger` 가 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project3/15` | 프로젝트 3 여행 계획의 시작 상태입니다. `trip.yaml` 에 도시 · 날짜 · 내 이동 한도를 적고, 본 세션이 날씨 · 문화 · 뉴스 · 명소 subagent 넷(`examples/agents/` — `.claude/agents/` 로 복사)을 차례로 부르면 넷이 각자 웹에서 조사해 `research/<이름>.json` 에 남깁니다. 확인하지 못한 값은 「모름」 으로 적습니다. 경로 hook(`.claude/hooks/protect.py`, 설정은 `examples/settings.json`)이 쓰기를 `research/<이름>.json` 으로 좁히고 누가 어느 파일을 썼는지 `hook-log.jsonl` 에 남깁니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `project3/16` | 여행 계획에 일정 짜기 · 검사 · 고르기를 더한 상태입니다. 일정 subagent(`examples/agents/planner.md` — `.claude/agents/` 로 복사)가 `research/*.json` 과 `trip.yaml` 을 읽어 일정 안 두세 개를 `plans/<번호>.json` 에 짜고, constraint check(`constraints.py`)가 날짜 · 운영 시간 · 하루 이동 한도 · 출처를 확인합니다. 거부되면 이유와 exit code 1, 거부는 없지만 확인 못 한 정보가 남으면 3 이고, 거부가 없으면 고를 칸 `choices.md` 를 씁니다. 고른 번호를 `choose.py <번호>` 로 넘기면 `plan.json` 으로 확정합니다. 경로 hook 은 planner 를 `plans/<번호>.json` 으로 좁힙니다. 가능한 일정 · 불가능한 일정 fixture(`fixtures/ok` · `fixtures/bad`)가 들어 있습니다. 이미 `~/my-trip` 이 있으면 더해지거나 바뀐 것만 복사합니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |

## 받기와 실행

```bash
git clone https://github.com/euisuk-chung/harness-practice.git
cd harness-practice/part2/05
uv sync
uv run python run.py fixtures/missing-when.json   # 저장해 둔 응답으로 검증만 — Claude 를 부르지 않습니다
uv run python run.py                              # Claude Code 를 한 번 부릅니다 — 로그인이 필요합니다
```

한 번 받으면 모든 차시의 실습 폴더가 함께 들어 있습니다. 다음 차시부터는 새로 받지 않고, 받아 둔 저장소에서 그 차시의 폴더로 들어갑니다.

```bash
cd ~/harness-practice/part2/06
uv sync
uv run python .claude/hooks/protect.py < fixtures/write-sources.json   # hook 만 시험 — Claude 를 부르지 않습니다
```

강사가 실습 파일을 고쳐 올린 것이 있으면 맨 위 폴더(`~/harness-practice`)에서 `git pull` 로 받습니다. 고친 것이 없으면 `Already up to date.` 한 줄이 찍힙니다.

실행에 필요한 것은 uv 와 Claude Code(구독 계정으로 로그인)입니다. `run.py` 가 만드는 `response.json` 과 `uv sync` 가 만드는 `.venv`·`uv.lock` 은 저장소에 올리지 않습니다.

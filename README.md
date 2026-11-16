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
| `projects/blog` | 프로젝트 1 블로그의 작업 폴더입니다. 시작 상태는 `reference/09` 와 같고, 9~12차시 내내 이 폴더 하나에서 이어 만듭니다. `make_site.py` 가 `posts/` 의 글로 저장소 맨 위 `docs/` 를 만듭니다. 자세한 것은 그 폴더의 `README.md` 에 있습니다. |
| `projects/ledger` | 프로젝트 2 가계부의 작업 폴더입니다. 시작 상태는 `reference/13` 과 같고, 13~14차시에 이 폴더에서 이어 만듭니다. 가계부 `ledger.xlsx` 와 내 영수증 · 카드 명세서는 `.gitignore` 가 가려 Git 에 올라가지 않습니다. |
| `projects/trip` | 프로젝트 3 여행 계획의 작업 폴더입니다. 시작 상태는 `reference/15` 와 같고, 15~16차시에 이 폴더에서 이어 만듭니다. |
| `reference/09` … `reference/12` | 블로그의 차시별 시작 상태입니다(보기만 하는 폴더). 10 은 수집 · 작성 단계와 hook, 11 은 검사 · 승인(PR) 단계, 12 는 매일 아침 실행하는 GitHub Actions workflow(`examples/daily.yml`) · `daily.py` · 운영 기록 점검 `steps/audit.py` 를 더합니다. |
| `reference/13` · `reference/14` | 가계부의 차시별 시작 상태입니다. 13 은 영수증을 `inbox/` 에 넣으면 skill 의 기준대로 읽어 형식 검사를 거쳐 `ledger.xlsx` 에 한 줄 더하고, 14 는 같은 영수증을 두 번 적지 않게 하는 `seen` · `dup` 단계와 카드 명세서 맞추기 `reconcile.py` 를 더합니다. |
| `reference/15` · `reference/16` | 여행 계획의 차시별 시작 상태입니다. 15 는 조사 subagent 넷과 경로 hook, 16 은 일정 subagent(planner) · constraint check `constraints.py` · 고르기 `choose.py` 를 더합니다. |
| `tools/advance.py` | 차시를 넘길 때 그 차시의 강사 파일을 작업 폴더로 가져옵니다. 내가 고친 파일은 덮어쓰지 않고, 강사도 바꾼 파일이면 차이를 보이고 아무것도 바꾸지 않은 채 멈춥니다(exit code 1). |
| `docs` | 블로그 페이지입니다. GitHub Pages 가 main 의 `/docs` 를 올립니다. `projects/blog` 의 `make_site.py` 만 이 폴더를 고칩니다. |

## 받기 — 내 GitHub 계정으로 fork

이 저장소를 내 GitHub 계정으로 fork 해 받습니다. 16차시까지 이 저장소 하나에서 실습하고, 블로그 · 가계부 · 여행 계획도 저장소 안의 `projects/` 에서 만듭니다 — 새 저장소를 만들거나 폴더를 밖으로 복사하지 않습니다.

```bash
cd ~
gh repo fork https://github.com/kr-harness-lab/harness-practice.git --clone
cd harness-practice
git remote -v                                       # origin = 내 fork, upstream = 강사 저장소
gh repo set-default <아이디>/harness-practice       # gh 가 강사 저장소가 아니라 내 저장소를 보게
```

gh 없이 받으려면 GitHub 화면에서 Fork 를 누른 뒤 `git clone https://github.com/<아이디>/harness-practice.git` 로 받고, `git remote add upstream https://github.com/kr-harness-lab/harness-practice.git` 을 실행합니다.
fork 한 저장소는 공개입니다. 내 가계부 · 영수증 · 개인 자료는 커밋하지 않습니다 — 프로젝트 폴더의 `.gitignore` 가 가계부와 영수증을 가리지만, 커밋하기 전에 `git status` 로 올라갈 파일을 확인합니다.

## 실행

```bash
cd ~/harness-practice/part2/05
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

프로젝트는 차시가 바뀌어도 같은 작업 폴더에서 이어 합니다. 차시를 넘길 때는 그 프로젝트 폴더에서 `tools/advance.py` 로 그 차시의 강사 파일을 가져옵니다.

```bash
cd ~/harness-practice/projects/blog
uv run python ../../tools/advance.py blog 10      # reference/10 에서 더해지거나 바뀐 파일만 — 내가 고친 파일은 그대로
```

## 강사가 고친 것 받기

강사가 실습 파일을 고쳐 올린 것이 있으면 맨 위 폴더에서 강사 저장소(upstream)의 main 을 합쳐 받고, 내 저장소에도 올립니다. 고친 것이 없으면 `Already up to date.` 한 줄이 찍힙니다.

```bash
cd ~/harness-practice
git pull --no-rebase --no-edit upstream main
git push
```

`reset --hard` 나 강사 main 으로 덮어쓰는 명령은 쓰지 않습니다 — 내 작업 폴더의 글 · 가계부 · 여행 계획이 지워집니다. 강사가 고친 차시 파일은 `reference/` 에 들어오고, 작업 폴더에는 `tools/advance.py` 가 가져옵니다.

실행에 필요한 것은 uv 와 Claude Code(구독 계정으로 로그인), GitHub CLI(`gh`)입니다. `run.py` 가 만드는 `response.json` 과 `uv sync` 가 만드는 `.venv`·`uv.lock` 은 저장소에 올리지 않습니다.

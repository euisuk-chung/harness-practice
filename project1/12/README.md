# project1 — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그를 매일 아침 저절로 실행하게 하는 상태입니다. GitHub Actions 의 workflow 가 매일 한국 시간 07:00 에 `daily.py` 를 부르고, `daily.py` 는 그날 이미 실행했는지 본 뒤 runner 로 수집 → 세기 → 작성 → 검사 → 승인을 실행합니다. 실행마다 무엇이 언제 어떻게 끝났는지 운영 기록 `runs/<날짜>/log.jsonl` 에 남깁니다. PR 을 읽고 합치는 일은 내가 GitHub 에서 합니다.
`project1` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지 `docs/` 를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `docs/` | GitHub Pages 가 올리는 폴더. `.nojekyll` 은 다른 변환 없이 그대로 올리라는 표시 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `daily.py` | 하루 한 번 실행 — run ID(오늘 날짜)를 정하고, origin 에 `draft/<날짜>` branch 나 그 PR 이 있으면 건너뛴다. 없으면 runner 를 부르고 운영 기록을 남긴 뒤 `steps/audit.py` 로 점검한다. PR 을 연 날은 운영 기록을 그 branch 에 커밋해 push 한다 |
| `examples/daily.yml` | GitHub Actions workflow. `.github/workflows/daily.yml` 로 복사한다 — 매일 UTC 22:00(한국 07:00) · 손으로 실행(`workflow_dispatch`) · 한 번에 하나만(`concurrency`) · secret `CLAUDE_CODE_OAUTH_TOKEN` |
| `examples/PLAN.md` | 과제 · 핵심 세 줄 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집(collect) → 세기(count) → 작성(write) → 검사(check) → 승인(approve) graph. 검사가 거부하면 이유를 붙여 작성을 다시, 승인 단계가 PR 을 열면 exit code 3 으로 멈춘다 |
| `examples/graph-retry.yaml` | 작성 → 검사만 있는 연습 graph. 다시 쓰기와 human queue 를 PR 없이 시험한다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |
| `examples/settings.json` | hook 을 거는 설정. `.claude/settings.json` 으로 복사한다 |
| `prompts/collect.md` | 수집 프롬프트 — 지난 24시간 · 세 회사 공식 사이트(OpenAI 는 RSS 피드) · 원문을 `runs/<날짜>/sources/` 에 · 답은 `sources.json` |
| `prompts/write.md` | 작성 프롬프트 — 숫자 · 인용은 원문 파일에 있는 것만 · 뉴스레터 형식 · 주장 목록 · 뺀 소식(제목 · 원문 · 이유) |
| `steps/check.py` | 검사 다섯 — 구조 · 출처와 기간 · 원문 대조(숫자 · 인용) · 형식 · 근거. 통과 0 · 거부 1(이유를 찍는다) |
| `steps/approve.py` | 초안의 글을 `posts/<날짜>.md` 로 쓰고 `docs/` 를 다시 만든 뒤, branch `draft/<날짜>` 를 push 하고 PR 을 연다. `needs_approval` 을 찍고 exit code 3 |
| `steps/audit.py` | 운영 기록 점검 — 끝 줄이 없거나, 새 글이 있었는데 collect 단계의 hook 기록이 없으면 거부(exit code 1). 통과하면 운영 점검표를 찍는다 |
| `steps/count.py` | `sources.json` 의 status 로 갈 곳을 정한다 — 새 글 있음 0(error 칸에 적힌 것이 있으면 함께 찍음) · 새 글 0건 4 · 수집 실패 1(수집을 다시). empty 인데 items · error 가 찬 결과, 모양이 틀린 결과, 원문 파일이 블로그 폴더 밖인 결과도 1 |
| `.claude/hooks/protect.py` | collect 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 PreToolUse hook. 막을 때 exit code 2. 불릴 때마다 운영 기록(환경 변수 `RUN_LOG`)에 허용 · 막음 한 줄을 남긴다 |
| `fixtures/` | Claude 를 부르지 않고 시험하는 입력 — 새 글 0건 · 수집 오류 · 일부 사이트만 확인한 수집 결과 · count 가 거부하는 수집 결과 셋(`empty-error` · `wrong-type` · `outside`) · hook 에 넣을 도구 호출 둘 · 틀린 인용 초안을 내는 작성 응답(`wrong-quote.json`) · 검사 단계에서 이어 가는 상태(`state-retry.json`) |
| `fixtures/log/` | 운영 기록 점검 시험용 — 실제 실행 기록(`good.jsonl`), 거기서 hook 줄을 뺀 기록(`no-hook.jsonl`), 끝 줄이 없는 기록(`cut.jsonl`), 건너뛴 날의 기록(`skip.jsonl`) |
| `fixtures/check/` | 검사 시험용 — 수집 결과와 원문 셋, 통과하는 초안 하나(`good.md`), 검사마다 거부되는 초안 다섯, 검사의 빈틈을 막았는지 보는 초안 넷(같은 소제목 두 번 · 빈 인용 · 부호가 다른 숫자는 거부, 약어 마침표 `abbrev.md` 는 통과). 원문 `s1.md` 는 실제로 가져온 글이고, 날짜만 시험용으로 바꿨다 |

## 내 저장소로 옮기기

```bash
cd ~
cp -r harness-practice/project1/12 my-blog
cd my-blog
cp examples/PLAN.md examples/graph.yaml examples/CLAUDE.md .
cp examples/settings.json .claude/settings.json
mkdir -p .github/workflows
cp examples/daily.yml .github/workflows/daily.yml
uv sync
uv run python make_site.py
```

`CLAUDE.md` 의 독자와 말투는 내 블로그에 맞게 고칩니다. 그다음 Git 저장소로 만들어 GitHub 에 올립니다.

```bash
git init -b main
git add .
git commit -m "블로그 시작"
gh repo create my-blog --public --source=. --push
```

GitHub 의 저장소 화면에서 Settings → Pages 로 가서, Build and deployment 의 Source 를 Deploy from a branch 로 두고 branch 는 `main`, 폴더는 `/docs` 로 골라 Save 를 누릅니다. 잠시 뒤 `https://<아이디>.github.io/my-blog/` 에 빈 블로그가 열립니다.

내 컴퓨터에서 먼저 보려면 `uv run python -m http.server 8001 --directory docs` 를 실행하고 브라우저로 `http://localhost:8001` 을 엽니다. 끝낼 때는 `Ctrl+C` 를 누릅니다.

## 앞 차시 폴더에서 이어 받기

이미 `~/my-blog` 가 있으면 이번에 더해지거나 바뀐 것만 복사하고, graph 를 제자리에 둡니다.

```bash
cd ~/harness-practice/project1/12
cp -r daily.py steps fixtures examples .claude README.md ~/my-blog/
cd ~/my-blog
mkdir -p .github/workflows
cp examples/daily.yml .github/workflows/daily.yml
```

번호 폴더에는 `.git` 도, 맨 위의 `CLAUDE.md` · `PLAN.md` · `graph.yaml` 도 없습니다. 그래서 `cp -r ~/harness-practice/project1/12/. ~/my-blog/` 처럼 폴더 안을 통째로 덮어써도 내 Git 기록과 고쳐 둔 `CLAUDE.md` 는 그대로 남습니다.
`cp -r harness-practice/project1/12 my-blog` 는 `my-blog` 가 이미 있으면 그 안에 `12` 폴더를 새로 만드니, 이미 있는 폴더에는 쓰지 않습니다.

## 실행

```bash
uv run python steps/audit.py fixtures/log/good.jsonl       # 실제 실행 기록 — 운영 점검표 · exit code 0
uv run python steps/audit.py fixtures/log/no-hook.jsonl    # 새 글이 있었는데 hook 기록이 없다 — 거부 · exit code 1
uv run python daily.py --answer fixtures/empty.json        # 새 글 0건인 날 — Claude 를 부르지 않는다 · exit code 0
uv run python daily.py                                     # 오늘 실행 — 수집 → 승인, PR 을 열면 exit code 0
uv run python daily.py                                     # 같은 날 한 번 더 — 건너뜀 한 줄만 남기고 exit code 0
```

`daily.py` 는 GitHub 저장소(`origin`)와 `gh` 로그인이 있어야 그날 이미 실행했는지 확인합니다. 확인하지 못하면 실행하지 않고 exit code 1 로 끝납니다.
새 글 0건인 날은 branch 도 PR 도 남지 않으니, 같은 날 다시 실행하면 수집부터 다시 합니다.
운영 기록 `runs/<날짜>/log.jsonl` 은 PR 을 연 날에는 `draft/<날짜>` branch 에 함께 올라가고, 그 밖의 날에는 실행한 컴퓨터에만 남습니다. GitHub Actions 에서 실행하면 기록 전체가 그 실행의 기록(Actions 화면)에 찍힙니다.

## GitHub 에서 매일 실행하기

1. `claude setup-token` 으로 내 구독 계정의 토큰을 만든다. 토큰은 화면에 한 번만 나오고 어디에도 저장되지 않는다
2. `gh secret set CLAUDE_CODE_OAUTH_TOKEN` 을 실행하고 토큰을 붙여 넣는다 — 저장소의 secret 으로 저장된다
3. 저장소 Settings → Actions → General → Workflow permissions 에서 「Allow GitHub Actions to create and approve pull requests」 를 켠다 — 켜지 않으면 workflow 가 PR 을 열지 못한다
4. `.github/workflows/daily.yml` 을 커밋해 push 한다. 이때부터 매일 UTC 22:00 에 실행된다
5. `gh workflow run daily.yml` 로 손으로 한 번 실행하고, `gh run list --workflow daily.yml` 로 결과를 본다

멈추려면 `gh workflow disable daily.yml`, 다시 켜려면 `gh workflow enable daily.yml` 을 실행합니다. 토큰은 Git 에 올리지 않습니다.

# projects/blog — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그의 검사 · 승인 단계를 더한 상태입니다. graph 는 수집 → 세기 → 작성 → 검사 → 승인까지 실행하고, 승인 단계가 PR 을 연 뒤 멈춥니다. PR 을 읽고 합치는 일은 내가 GitHub 에서 합니다.
작업은 저장소 안의 `projects/blog` 한 폴더에서 이어 합니다. `reference/09` … `reference/12` 는 차시마다의 시작 상태라 보기만 합니다. 차시를 넘길 때는 `tools/advance.py` 가 그 차시에 더해지거나 바뀐 강사 파일만 가져오고, 내가 고친 파일은 덮어쓰지 않습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지(저장소 맨 위 `docs/`)를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 요약 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집(collect) → 세기(count) → 작성(write) → 검사(check) → 승인(approve) graph. 검사가 거부하면 이유를 붙여 작성을 다시, 승인 단계가 PR 을 열면 exit code 3 으로 멈춘다 |
| `examples/graph-retry.yaml` | 작성 → 검사만 있는 연습 graph. 다시 쓰기와 human queue 를 PR 없이 시험한다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |
| `examples/settings.json` | hook 을 거는 설정. `.claude/settings.json` 으로 복사한다 |
| `prompts/collect.md` | 수집 프롬프트 — 지난 24시간 · 세 회사 공식 사이트(OpenAI 는 RSS 피드) · 원문을 `runs/<날짜>/sources/` 에 · 답은 `sources.json` |
| `prompts/write.md` | 작성 프롬프트 — 숫자 · 인용은 원문 파일에 있는 것만 · 뉴스레터 형식 · 주장 목록 · 뺀 소식(제목 · 원문 · 이유) |
| `steps/check.py` | 블로그 검사 — 구조 · 출처와 기간 · 원문 대조(숫자 · 인용) · 형식 · 근거. 통과 0 · 거부 1(이유를 찍는다) |
| `steps/approve.py` | 초안의 글을 `posts/<날짜>.md` 로 쓰고 맨 위 `docs/` 를 다시 만든 뒤, branch `blog/draft/<날짜>` 를 push 하고 내 저장소(`--repo <아이디>/harness-practice`)에 PR 을 연다. 커밋에는 블로그의 `posts/` · `runs/` 와 맨 위 `docs/` 만 넣는다. `needs_approval` 을 찍고 exit code 3 |
| `steps/count.py` | `sources.json` 의 status 로 갈 곳을 정한다 — 새 글 있음 0(error 칸에 적힌 것이 있으면 함께 찍음) · 새 글 0건 4 · 수집 실패 1(수집을 다시). empty 인데 items · error 가 찬 결과, 모양이 틀린 결과, 원문 파일이 블로그 폴더 밖인 결과도 1 |
| `.claude/hooks/protect.py` | collect 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 PreToolUse hook. 막을 때 exit code 2 |
| `fixtures/` | Claude 를 부르지 않고 시험하는 입력 — 새 글 0건 · 수집 오류 · 일부 사이트만 확인한 수집 결과 · count 가 거부하는 수집 결과 셋(`empty-error` · `wrong-type` · `outside`) · hook 에 넣을 도구 호출 둘 · 틀린 인용 초안을 내는 작성 응답(`wrong-quote.json`) · 검사 단계부터 다시 시작하는 상태(`state-retry.json`) |
| `fixtures/check/` | 검사 시험용 — 수집 결과와 원문 셋, 통과하는 초안 하나(`good.md`), 검사마다 거부되는 초안 다섯, 검사의 빈틈을 막았는지 보는 초안 넷(같은 소제목 두 번 · 빈 인용 · 부호가 다른 숫자는 거부, 약어 마침표 `abbrev.md` 는 통과). 원문 `s1.md` 는 실제로 가져온 글이고, 날짜만 시험용으로 바꿨다 |

## 이 차시 파일 가져오기

작업은 앞 차시와 같은 `projects/blog` 에서 이어 합니다. 이번 차시에 더해지거나 바뀐 강사 파일만 `reference/11` 에서 가져옵니다.

```bash
cd ~/harness-practice/projects/blog
uv run python ../../tools/advance.py blog 11
uv sync
```

`tools/advance.py` 는 파일마다 `+`(더함) · `~`(바꿈 — 내가 고치지 않은 강사 파일) · `=`(내가 고친 것 — 그대로 둠)를 찍습니다. 고치지 않은 `graph.yaml` · `.claude/settings.json` 은 이번 차시 판(`examples/`)으로 제자리에 놓으니, 따로 복사하지 않습니다.
내가 고친 파일을 강사도 바꿨으면 `!` 로 차이를 보이고, 아무 파일도 바꾸지 않은 채 exit code 1 로 멈춥니다. 그때는 `reference/11/` 의 강사 판을 보고 필요한 것을 내 파일에 옮겨 적은 뒤, 내 것을 두려면 `--keep <파일>` 을 붙여 다시 실행합니다.
앞 차시를 건너뛰었어도 같은 명령 하나로 그 사이 차시의 파일까지 가져옵니다. 가져온 것은 저장소 맨 위에서 `git add projects/blog` 로 커밋해 둡니다.

## 실행

```bash
uv run python steps/check.py fixtures/check/good.md fixtures/check/sources.json          # 블로그 검사 통과 — exit code 0
uv run python steps/check.py fixtures/check/wrong-quote.md fixtures/check/sources.json   # 틀린 인용 — 거부 이유를 찍고 exit code 1
cp fixtures/check/sources.json sources.json
uv run python runner.py examples/graph-retry.yaml --answer fixtures/wrong-quote.json     # 세 번 다시 써도 거부 — human queue · exit code 3
cp fixtures/check/wrong-quote.md draft.md
cp fixtures/state-retry.json state.json
uv run python runner.py examples/graph-retry.yaml                                        # 틀린 인용을 Claude 가 다시 쓴다 — Claude 를 한 번 이상 부릅니다
uv run python runner.py                                                                  # 수집 → 승인 — PR 을 열고 exit code 3
```

검사 fixture 는 `bad-structure` · `bad-source` · `wrong-quote` · `bad-format` · `bad-claim` 다섯이고, 하나마다 검사 하나가 거부합니다.
`dup-heading` · `empty-quote` · `wrong-sign` 은 같은 소제목 두 번 · 빈 인용 · 부호가 다른 숫자를 거부하는지, `abbrev` 는 「U.S.」 같은 약어에서 문장을 자르지 않고 통과하는지 봅니다.
승인 단계는 `projects/blog` 에서, main branch 에서, 내 저장소(`origin`)와 `gh` 로그인이 있어야 PR 을 엽니다. PR 은 늘 origin 의 저장소에 열고(fork 의 강사 저장소가 아니라), 다른 실습 폴더에서 고친 것은 커밋에 넣지 않습니다. 열지 못하면 이유를 찍고 같은 exit code 3 으로 멈춥니다.
PR 을 합치면 GitHub Pages 가 main 의 맨 위 `docs/` 를 올립니다. 합친 뒤에는 `git pull` 로 내 컴퓨터의 main 도 맞춥니다.
원문은 `runs/<날짜>/sources/` 에 남고, 그날의 수집 결과 `sources.json` · 초안 `draft.md` · PR 본문 `pr-body.md` 는 Git 에 올리지 않습니다.

# projects/blog — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그의 수집 · 작성 단계를 더한 상태입니다. graph 는 수집 → 세기 → 작성까지 실행하고, 초안이 준비되면 멈춥니다.
작업은 저장소 안의 `projects/blog` 한 폴더에서 이어 합니다. `reference/09` … `reference/12` 는 차시마다의 시작 상태라 보기만 합니다. 차시를 넘길 때는 `tools/advance.py` 가 그 차시에 더해지거나 바뀐 강사 파일만 가져오고, 내가 고친 파일은 덮어쓰지 않습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지(저장소 맨 위 `docs/`)를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 요약 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집(collect) → 세기(count) → 작성(write) graph. 초안 `draft.md` 가 준비되면 멈춘다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |
| `examples/settings.json` | hook 을 거는 설정. `.claude/settings.json` 으로 복사한다 |
| `prompts/collect.md` | 수집 프롬프트 — 지난 24시간 · 세 회사 공식 사이트(OpenAI 는 RSS 피드) · 원문을 `runs/<날짜>/sources/` 에 · 답은 `sources.json` |
| `prompts/write.md` | 작성 프롬프트 — 숫자 · 인용은 원문 파일에 있는 것만 · 뉴스레터 형식 · 주장 목록 · 뺀 소식(제목 · 원문 · 이유) |
| `steps/count.py` | `sources.json` 의 status 로 갈 곳을 정한다 — 새 글 있음 0(error 칸에 적힌 것이 있으면 함께 찍음) · 새 글 0건 4 · 수집 실패 1(수집을 다시). empty 인데 items · error 가 찬 결과, 모양이 틀린 결과, 원문 파일이 블로그 폴더 밖인 결과도 1 |
| `.claude/hooks/protect.py` | collect 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 PreToolUse hook. 막을 때 exit code 2 |
| `fixtures/` | Claude 를 부르지 않고 시험하는 입력 — 새 글 0건 · 수집 오류 · 일부 사이트만 확인한 수집 결과 · count 가 거부하는 수집 결과 셋(`empty-error` · `wrong-type` · `outside`) · hook 에 넣을 도구 호출 둘 |

## 이 차시 파일 가져오기

작업은 앞 차시와 같은 `projects/blog` 에서 이어 합니다. 이번 차시에 더해지거나 바뀐 강사 파일만 `reference/10` 에서 가져옵니다.

```bash
cd ~/harness-practice/projects/blog
uv run python ../../tools/advance.py blog 10
uv sync
```

`tools/advance.py` 는 파일마다 `+`(더함) · `~`(바꿈 — 내가 고치지 않은 강사 파일) · `=`(내가 고친 것 — 그대로 둠)를 찍습니다. 고치지 않은 `graph.yaml` · `.claude/settings.json` 은 이번 차시 판(`examples/`)으로 제자리에 놓으니, 따로 복사하지 않습니다.
내가 고친 파일을 강사도 바꿨으면 `!` 로 차이를 보이고, 아무 파일도 바꾸지 않은 채 exit code 1 로 멈춥니다. 그때는 `reference/10/` 의 강사 판을 보고 필요한 것을 내 파일에 옮겨 적은 뒤, 내 것을 두려면 `--keep <파일>` 을 붙여 다시 실행합니다.
앞 차시를 건너뛰었어도 같은 명령 하나로 그 사이 차시의 파일까지 가져옵니다. 가져온 것은 저장소 맨 위에서 `git add projects/blog` 로 커밋해 둡니다.

## 실행

```bash
uv run python runner.py                                         # 수집 → 세기 → 작성 — Claude 를 두 번 부릅니다
uv run python runner.py --answer fixtures/empty.json            # 새 글 0건 — count 가 exit code 4, 작성 없이 끝
uv run python runner.py --answer fixtures/collect-error.json    # 수집 오류 — 수집을 세 번 하고 human queue 에 남김
RUNNER_STEP=write uv run python .claude/hooks/protect.py < fixtures/hook-edit-source.json   # hook 만 시험 — exit code 2
uv run python steps/count.py fixtures/partial-sources.json       # 일부 사이트만 확인한 날 — 새 글이 있으니 0, error 칸을 함께 찍음
```

원문은 `runs/<날짜>/sources/` 에 남고, 그날의 수집 결과 `sources.json` 과 초안 `draft.md` 는 Git 에 올리지 않습니다.

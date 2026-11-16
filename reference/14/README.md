# projects/ledger — 같은 영수증을 두 번 적지 않는 가계부

프로젝트 2 가계부에 중복 방지를 더한 상태입니다. 영수증을 `inbox/` 에 넣으면 `watch.py` 가 runner 를 실행하는 것은 그대로이고, graph 가 네 단계가 됐습니다.

1. `seen` — 영수증 파일의 content hash(sha256)가 가계부의 「content hash」 칸에 있으면 같은 파일이 이미 기록된 것이라, 읽지 않고 끝냅니다(exit code 4).
2. `read` — Claude 가 ledger-rules skill 의 기준대로 영수증을 읽어 JSON 한 줄을 냅니다.
3. `dup` — 읽은 날짜 · 가게 · 금액을 가계부의 줄마다 견주어 중복 의심 점수(0~100)를 매기고, threshold(70)를 넘으면 `review/` 로 보냅니다(exit code 3).
4. `add` — 형식을 검사하고, 통과하면 content hash 와 함께 `ledger.xlsx` 에 한 줄 더합니다.

`watch.py` 는 가계부에 기록한 뒤에 영수증을 `done/` 으로 옮깁니다(기록 → 표시). 그 사이에 멈춰도 다시 실행하면 `seen` 이 같은 파일을 알아채므로 같은 줄이 두 번 생기지 않습니다.
작업은 저장소 안의 `projects/ledger` 한 폴더에서 이어 합니다. `reference/13` · `reference/14` 는 차시마다의 시작 상태라 보기만 합니다. 차시를 넘길 때는 `tools/advance.py` 가 그 차시에 더해지거나 바뀐 강사 파일만 가져오고, 내가 고친 파일은 덮어쓰지 않습니다.

| 파일 | 하는 일 |
|---|---|
| `dedup.py` | `seen` — 지금 영수증의 content hash 가 가계부에 있나 · `score entry.json --threshold 70` — 중복 의심 점수(날짜 40 · 금액 40 · 가게 20) · `hash <파일>` — content hash 보기 |
| `ledger.py` | 형식 검사와 기록. 기록할 때 7번째 「content hash」 칸에 content hash 를 적는다. 이 칸이 없는 가계부에 기록하면 머리에 칸을 더한다 |
| `watch.py` | 폴더 trigger. `done/` · `review/` 에 같은 이름이 있으면 `photo-2.png` 처럼 새 이름을 붙인다. `--stop-after-record` 는 시험용 — 기록한 뒤 `done/` 으로 옮기기 전에 멈춘다 |
| `examples/graph.yaml` | seen → read → dup → add graph. 맨 위로 복사한다. threshold 는 dup 단계의 `--threshold 70` |
| `threshold.py` | 정답이 표시된 연습 묶음 `practice/pairs.csv`(20쌍 — 중복 8 · 아님 12)로 threshold 50~90 의 review 로 가는 수 · false positive · false negative 를 센다. `--at 70` 은 쌍마다 |
| `reconcile.py` | 카드 명세서와 가계부를 날짜 · 금액으로 한 줄씩 맞춰 일치 · 누락 · 중복 · 가계부에만을 찾는다. 짝을 고를 수 없는 취소는 「판정 불가」 로 남긴다. 모두 맞으면 exit code 0, 사람이 볼 줄이 있으면 3, 명세서의 모양이 다르면 「명세서 N행 · 칸 · 값」 을 찍고 1 |
| `statements/2026-10.csv` | 연습용 10월 카드 명세서(승인 11줄 · 취소 1줄). 가맹점 이름은 지어낸 것이고 카드 번호는 없다 |
| `practice/ledger-2026-10.csv` | 연습용 10월 가계부 — 중복 한 줄과 금액을 잘못 읽은 줄이 섞여 있다 |
| `receipts/r01-again.png` | `r01.png` 와 같은 영수증을 다시 찍은 사진 — 내용은 같고 content hash 는 다르다 |
| `fixtures/answers/r01-again.json` | 다시 찍은 사진을 읽었을 때의 저장된 응답 |
| `practice/ledger-2026-10-fixed.csv` | 연습 가계부에서 찾은 줄을 고쳐 명세서와 모두 맞춘 가계부 |
| `fixtures/entry/other.json` | 중복이 아닌 기록 하나(시험용) |
| `fixtures/statement/cancel-alone.csv` | 연습 명세서에 짝이 되는 승인이 없는 취소(부분 취소) 한 줄을 더한 것 — `reconcile.py` 가 「판정 불가」 로 남기고 exit code 3(시험용) |

나머지(`runner.py` · `prompts/read.md` · `examples/SKILL.md` · `receipts/r01~r03.png` · 형식 검사 fixture)는 `reference/13` 과 같습니다.

## 이 차시 파일 가져오기

작업은 앞 차시와 같은 `projects/ledger` 에서 이어 합니다. 이번 차시에 더해지거나 바뀐 강사 파일만 `reference/14` 에서 가져옵니다.

```bash
cd ~/harness-practice/projects/ledger
uv run python ../../tools/advance.py ledger 14
uv sync
```

`tools/advance.py` 는 파일마다 `+`(더함) · `~`(바꿈 — 내가 고치지 않은 강사 파일) · `=`(내가 고친 것 — 그대로 둠)를 찍습니다. 고치지 않은 `graph.yaml` 은 이번 차시 판(`examples/graph.yaml`)으로 제자리에 놓습니다. 고쳐 둔 `.claude/skills/ledger-rules/SKILL.md` 와 가계부 `ledger.xlsx` 는 건드리지 않습니다.
내가 고친 파일을 강사도 바꿨으면 `!` 로 차이를 보이고, 아무 파일도 바꾸지 않은 채 exit code 1 로 멈춥니다. 그때는 `reference/14/` 의 강사 판을 보고 필요한 것을 내 파일에 옮겨 적은 뒤, 내 것을 두려면 `--keep <파일>` 을 붙여 다시 실행합니다.
앞 차시를 건너뛰었어도 같은 명령 하나로 그 사이 차시의 파일까지 가져옵니다. 가져온 것은 저장소 맨 위에서 `git add projects/ledger` 로 커밋해 둡니다.

`.claude/skills/ledger-rules/SKILL.md` 가 아직 없으면(앞 차시의 시작하기를 하지 않았으면) `mkdir -p .claude/skills/ledger-rules` 와 `cp examples/SKILL.md .claude/skills/ledger-rules/SKILL.md` 를 먼저 실행합니다.

## 실행

```bash
uv run python dedup.py hash receipts/r01.png                                   # content hash 보기
cp receipts/r01-again.png inbox/
uv run python watch.py inbox/ --once                                           # 다시 찍은 사진 — 중복 의심으로 review/
uv run python threshold.py                                                     # threshold 를 바꾸면
uv run python reconcile.py statements/2026-10.csv --ledger practice/ledger-2026-10.csv   # 연습 가계부와 명세서 맞추기
uv run python reconcile.py statements/2026-10.csv                              # 내 가계부 ledger.xlsx 와
```

Claude 를 부르지 않고 흐름만 보려면 `watch.py` 에 `--answers fixtures/answers` 를 붙입니다.

## 내 카드 명세서 넣기

카드사에서 받은 명세서는 `statements/2026-10.csv` 와 같은 모양의 CSV 로 바꿔 `statements/` 에 넣습니다.
이름은 연습 파일과 다르게(예: `statements/card-2026-11.csv`) 둡니다. 내 저장소는 공개 저장소의 fork 라서 Git 에 올린 것은 누구나 봅니다. `.gitignore` 가 연습 파일 밖의 명세서를 가립니다.

- UTF-8 로 저장합니다. Excel 에서는 「CSV UTF-8(쉼표로 분리)」 로 저장합니다.
- 첫 줄은 칸 이름 `이용일,가맹점,금액,구분` 입니다.
- 이용일은 `2026-10-03` 처럼 하이픈으로 나눈 날짜, 금액은 쉼표 없는 양의 정수, 구분은 `승인` 또는 `취소` 입니다.

모양이 다르면 `reconcile.py` 가 `명세서 4행 · 금액 · '1,000' — 쉼표 없는 양의 정수가 아닙니다` 처럼 몇 행의 어느 칸이 다른지 찍고 exit code 1 로 끝납니다.
취소는 같은 가맹점 · 같은 금액의 승인과 짝을 짓습니다. 그런 승인이 없거나(부분 취소 등) 둘 이상이면 고르지 않고 「판정 불가」 로 남기니, 명세서를 보고 직접 정합니다.

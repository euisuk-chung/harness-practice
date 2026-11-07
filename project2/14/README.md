# project2 — 같은 영수증을 두 번 적지 않는 가계부

프로젝트 2 가계부에 중복 방지를 더한 상태입니다. 영수증을 `inbox/` 에 넣으면 `watch.py` 가 runner 를 실행하는 것은 그대로이고, graph 가 네 단계가 됐습니다.

1. `seen` — 영수증 파일의 content hash(sha256)가 가계부의 「content hash」 칸에 있으면 같은 파일이 이미 기록된 것이라, 읽지 않고 끝냅니다(exit code 4).
2. `read` — Claude 가 ledger-rules skill 의 기준대로 영수증을 읽어 JSON 한 줄을 냅니다.
3. `dup` — 읽은 날짜 · 가게 · 금액을 가계부의 줄마다 견주어 중복 의심 점수(0~100)를 매기고, threshold(70)를 넘으면 `review/` 로 보냅니다(exit code 3).
4. `add` — 형식을 검사하고, 통과하면 content hash 와 함께 `ledger.xlsx` 에 한 줄 더합니다.

`watch.py` 는 가계부에 기록한 뒤에 영수증을 `done/` 으로 옮깁니다(기록 → 표시). 그 사이에 멈춰도 다시 실행하면 `seen` 이 같은 파일을 알아채므로 같은 줄이 두 번 생기지 않습니다.
`project2` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

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

나머지(`runner.py` · `prompts/read.md` · `examples/SKILL.md` · `receipts/r01~r03.png` · 형식 검사 fixture)는 `project2/13` 과 같습니다.

## 13 의 가계부에 더하기

```bash
cd ~/harness-practice/project2/14
cp dedup.py threshold.py reconcile.py ledger.py watch.py ~/my-ledger/
cp -r practice statements ~/my-ledger/
cp examples/graph.yaml ~/my-ledger/graph.yaml
cp receipts/r01-again.png ~/my-ledger/receipts/
cp fixtures/answers/r01-again.json ~/my-ledger/fixtures/answers/
```

`~/my-ledger` 가 없으면 폴더를 통째로 복사합니다.

```bash
cp -r ~/harness-practice/project2/14 ~/my-ledger
cd ~/my-ledger
mkdir -p .claude/skills/ledger-rules
cp examples/SKILL.md .claude/skills/ledger-rules/SKILL.md
cp examples/graph.yaml .
uv sync
```

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

- UTF-8 로 저장합니다. Excel 에서는 「CSV UTF-8(쉼표로 분리)」 로 저장합니다.
- 첫 줄은 칸 이름 `이용일,가맹점,금액,구분` 입니다.
- 이용일은 `2026-10-03` 처럼 하이픈으로 나눈 날짜, 금액은 쉼표 없는 양의 정수, 구분은 `승인` 또는 `취소` 입니다.

모양이 다르면 `reconcile.py` 가 `명세서 4행 · 금액 · '1,000' — 쉼표 없는 양의 정수가 아닙니다` 처럼 몇 행의 어느 칸이 다른지 찍고 exit code 1 로 끝납니다.
취소는 같은 가맹점 · 같은 금액의 승인과 짝을 짓습니다. 그런 승인이 없거나(부분 취소 등) 둘 이상이면 고르지 않고 「판정 불가」 로 남기니, 명세서를 보고 직접 정합니다.

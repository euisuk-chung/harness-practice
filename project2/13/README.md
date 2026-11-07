# project2 — 영수증을 넣으면 한 줄씩 쌓이는 가계부

프로젝트 2 가계부의 시작 상태입니다. 영수증 사진이나 파일을 `inbox/` 폴더에 넣으면, `watch.py` 가 새 파일을 찾아 runner 를 실행합니다. runner 는 Claude 에게 영수증을 읽게 하고(ledger-rules skill 의 기준대로), 기록하기 전에 `ledger.py` 로 형식을 검사합니다. 통과한 영수증만 Excel 가계부 `ledger.xlsx` 에 한 줄 더해지고, 나머지는 이유와 함께 `review/` 로 갑니다.
`project2` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `examples/SKILL.md` | 가계부 정리 skill — 칸 · 분류 표 · 판단 절차 · 내 규칙. `.claude/skills/ledger-rules/SKILL.md` 로 복사한다 |
| `examples/graph.yaml` | 읽기(read) → 형식 검사와 기록(add) graph. 맨 위로 복사한다 |
| `prompts/read.md` | 읽기 프롬프트 — `inbox/` 의 새 영수증을 skill 대로 JSON 한 줄로. 영수증 경로는 `current.txt` 에 있다 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner(프로젝트 1 과 같은 파일) |
| `ledger.py` | `add entry.json` — 빈 칸(공백뿐인 칸도) · 칸의 자료형 · 날짜 · 금액 · 분류 · 결제 수단을 검사하고 통과하면 `ledger.xlsx` 에 한 줄(exit code 0), 아니면 이유를 찍고 exit code 3. 분류 이름은 skill 의 분류 표에서 읽는다. `show` — 가계부에 적힌 줄 보기 |
| `watch.py` | 폴더 trigger — `inbox/` 를 2초마다 보고 새 파일마다 runner 를 실행한다. 끝나면 영수증을 `done/`(기록함) 또는 `review/`(이유는 `review/<이름>.txt`)로 옮긴다. 두 폴더에 같은 이름이 있으면 덮어쓰지 않고 `photo-2.png` 처럼 새 이름을 붙인다(가계부의 영수증 칸에도 새 이름). `--once` 는 지금 있는 파일만 처리하고 끝낸다 |
| `receipts/` | 연습 영수증 셋 — `r01.png` 정상 · `r02.png` 윗부분이 찢어져 상호가 없음 · `r03.png` 없는 날짜(9월 31일)가 적힌 간이영수증. 가게 이름 · 주소는 지어낸 것이다 |
| `inbox/` · `review/` | 영수증을 넣는 폴더 · 사람이 볼 영수증이 모이는 폴더 |
| `fixtures/entry/` | 형식 검사 시험용 JSON — 통과 하나(`good.json`), 빈 칸(`missing.json`), 없는 날짜(`bad-date.json`), 글자로 된 금액(`bad-amount.json`) |
| `fixtures/answers/` | Claude 대신 쓰는 저장된 응답 — 연습 영수증 셋을 읽었을 때의 답. `watch.py --answers` 로 쓴다 |

## 내 가계부 폴더 만들기

```bash
cd ~
cp -r harness-practice/project2/13 my-ledger
cd ~/my-ledger
mkdir -p .claude/skills/ledger-rules
cp examples/SKILL.md .claude/skills/ledger-rules/SKILL.md
cp examples/graph.yaml .
uv sync
```

`SKILL.md` 의 분류 표와 「내 규칙」은 내 가계부에 맞게 고칩니다. 분류 이름을 바꾸면 `ledger.py` 도 바뀐 표를 읽으니 다른 곳은 고치지 않습니다.

## 실행

```bash
uv run python ledger.py add fixtures/entry/good.json       # 형식 검사 통과 — 한 줄 기록 · exit code 0
uv run python ledger.py add fixtures/entry/bad-date.json   # 없는 날짜 — 기록하지 않음 · exit code 3
uv run python ledger.py show                               # 가계부 보기
rm ledger.xlsx                                             # 시험한 줄 지우기
uv run python watch.py inbox/                              # 폴더 trigger 켜기 — 끝낼 때는 Ctrl+C
```

폴더 trigger 를 켠 채로 다른 터미널에서 연습 영수증을 넣습니다.

```bash
cd ~/my-ledger
cp receipts/r01.png receipts/r02.png receipts/r03.png inbox/
```

Claude 를 부르지 않고 흐름만 보려면 `uv run python watch.py inbox/ --once --answers fixtures/answers` 를 실행합니다.

# project3 — 일정을 짜고, 검사하고, 내가 고르는 여행 계획

프로젝트 3 여행 계획의 일정을 짜는 상태입니다. 조사 subagent 넷이 남긴 `research/*.json` 과 `trip.yaml` 을 일정 subagent(planner)가 읽어 날짜별 일정 안을 두세 개 `plans/<번호>.json` 에 짭니다. `constraints.py` 가 안마다 날짜 · 운영 시간 · 하루 이동 한도 · 출처를 코드로 확인하고, 거부된 안은 이유와 함께 exit code 1 로 돌려보냅니다. 거부가 없으면 안마다의 판정을 고를 칸 `choices.md` 에 쓰고, 그중 하나를 골라 `choose.py <번호>` 로 `plan.json` 을 확정합니다.
`project3` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `trip.yaml` | 내 여행 — 도시 · 나라 · 첫날 · 마지막 날 · 하루 시작 · 끝 시각 · 내 이동 한도(하루 이동 시간 합계, 분). 내 여행으로 고친다 |
| `examples/agents/weather.md` · `culture.md` · `news.md` · `sights.md` | 조사 subagent 넷 — 각자 `research/<이름>.json` 에 결과를 남긴다 |
| `examples/agents/planner.md` | 일정 subagent — `research/*.json` 과 `trip.yaml` 을 읽어 `plans/<번호>.json` 에 일정 안을 짠다. 웹은 조사하지 않는다 |
| `constraints.py` | constraint check — 안마다 날짜 · 운영 시간 · 하루 이동 한도 · 출처를 확인한다. 모두 통과 exit code 0, 거부가 있으면 이유와 1, 거부는 없지만 확인 못 한 정보가 남았으면 3. 거부가 없으면 `choices.md` 를 쓴다 |
| `choose.py` | `uv run python choose.py <번호>` — 고른 안을 같은 검사로 한 번 더 확인하고 `plan.json` 으로 확정한다. 거부된 안은 확정하지 않는다(exit code 1) |
| `examples/settings.json` | 경로 hook 을 거는 설정 — `.claude/settings.json` 으로 복사한다 |
| `.claude/hooks/protect.py` | PreToolUse hook — 조사 subagent 는 `research/<이름>.json` 에만, planner 는 `plans/<번호>.json` 에만 쓰게 한다(허용 exit code 0, 막음 2). `plan.json` 은 어느 subagent 도 쓰지 못한다 |
| `fixtures/hook/` | Claude 없이 hook 을 시험하는 입력 — planner 의 일정 안 쓰기(`write-plan.json`) · planner 의 `plan.json` 쓰기(`write-final.json`)와 조사 결과 쓰기 · 막는 경우 넷 |
| `fixtures/ok/` · `fixtures/bad/` | Claude 없이 constraint check 를 시험하는 여행 폴더 — 가능한 일정 하나(`ok`)와 불가능한 일정 하나(`bad`) |
| `research/` · `plans/` | 조사 결과와 일정 안이 모이는 폴더 |

일정 안의 모양은 이렇습니다. 장소마다 `ref` 에 조사 결과 항목의 id 를 적고, `source` · `checked` 는 그 항목의 값을 그대로 옮깁니다.

```json
{"option": 1, "title": "",
 "days": [{"date": "YYYY-MM-DD",
           "stops": [{"ref": "sights-1", "name": "", "arrive": "09:30", "depart": "11:00", "stay_minutes": 90, "move_minutes": 30, "source": "", "checked": "확인"}]}]}
```

`move_minutes` 는 앞 장소(그날 첫 장소면 숙소)에서 그 장소까지의 이동 시간입니다. planner 가 짐작한 값이고, constraint check 는 그 합이 내 이동 한도를 넘는지만 봅니다.

## 내 여행 폴더에 더하기

앞 실습의 `~/my-trip` 이 있으면 더해지거나 바뀐 것만 복사합니다.

```bash
cd ~/harness-practice/project3/16
cp constraints.py choose.py pyproject.toml .gitignore ~/my-trip/
cp -r fixtures plans ~/my-trip/
cp .claude/hooks/protect.py ~/my-trip/.claude/hooks/
cp examples/agents/planner.md ~/my-trip/.claude/agents/
cd ~/my-trip
uv sync
```

`~/my-trip` 이 없으면 이 폴더를 통째로 복사하고, `project3/15/README.md` 대로 subagent 정의 · 설정을 복사한 뒤 조사부터 실행합니다.

```bash
cd ~
cp -r harness-practice/project3/16 my-trip
cd my-trip
mkdir -p .claude/agents
cp examples/agents/*.md .claude/agents/
cp examples/settings.json .claude/settings.json
uv sync
```

## 실행

```bash
uv run python .claude/hooks/protect.py < fixtures/hook/write-plan.json    # 허용 — exit code 0
uv run python .claude/hooks/protect.py < fixtures/hook/write-final.json   # 막음 — exit code 2
uv run python constraints.py fixtures/ok                                   # 가능한 일정 — exit code 0
uv run python constraints.py fixtures/bad                                  # 불가능한 일정 — 이유와 exit code 1
rm hook-log.jsonl                                                          # 시험한 기록 지우기
claude -p "uv run python constraints.py 를 실행하세요. exit code 가 1 이면 찍힌 내용을 그대로 planner subagent 에게 넘겨 일정 안을 짜게 하고, 다시 검사하세요. 짜기는 세 번까지입니다. exit code 가 0 이나 3 이면 멈추고 choices.md 를 보고 고르라고 알려 주세요. 일정은 직접 짜지 마세요." --allowedTools "Agent,Read,Write,Bash(uv run python constraints.py)"
uv run python constraints.py                                               # 내가 한 번 더 검사
cat choices.md                                                             # 고를 칸
uv run python choose.py 2                                                  # 고른 번호로 plan.json 확정
```

`claude -p` 는 Claude 를 부릅니다. 본 세션이 먼저 검사를 실행하고, 일정 안이 없거나 거부된 안이 있으면(exit code 1) 그 출력을 planner 에게 넘겨 짜게 한 뒤 다시 검사합니다. `trip.yaml` 의 조건을 바꾼 뒤 같은 명령을 다시 실행하면, 새 조건에서 거부된 안만 다시 짭니다. 일정 안과 검사 결과는 실행마다 다릅니다.

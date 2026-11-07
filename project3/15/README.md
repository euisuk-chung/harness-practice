# project3 — 조사를 subagent 넷에게 나눠 맡기는 여행 계획

프로젝트 3 여행 계획의 시작 상태입니다. `trip.yaml` 에 도시 · 날짜 · 내 이동 한도를 적고, Claude Code 의 본 세션이 날씨 · 문화 · 뉴스 · 명소 subagent 넷을 차례로 부르면, 넷이 각자 웹에서 조사한 결과를 `research/<이름>.json` 에 남깁니다. 경로 hook 이 쓰기를 `research/<이름>.json` 으로 좁히고, 불릴 때마다 누가 어느 파일을 썼는지 `hook-log.jsonl` 에 한 줄 남깁니다.
`project3` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `trip.yaml` | 내 여행 — 도시 · 나라 · 첫날 · 마지막 날 · 하루 시작 · 끝 시각 · 내 이동 한도(하루 이동 시간 합계, 분). 내 여행으로 고친다 |
| `examples/agents/weather.md` | 날씨 subagent — 여행 날짜의 예보, 없으면 그 달의 평년값 → `research/weather.json` |
| `examples/agents/culture.md` | 문화 subagent — 공휴일 · 축제 · 휴무 · 예절 → `research/culture.json` |
| `examples/agents/news.md` | 뉴스 subagent — 지난 30일의 교통 · 공사 · 요금 · 안전 소식 → `research/news.json` |
| `examples/agents/sights.md` | 명소 subagent — 대표 명소 다섯의 운영 시간 · 쉬는 날 → `research/sights.json` |
| `examples/settings.json` | 경로 hook 을 거는 설정 — `.claude/settings.json` 으로 복사한다 |
| `.claude/hooks/protect.py` | PreToolUse hook — Edit · Write 를 `research/<이름>.json` 에만 허용(exit code 0), 그 밖은 막는다(exit code 2). 어떤 예외도 막는다 |
| `fixtures/hook/` | Claude 없이 hook 을 시험하는 입력 — 결과 파일 쓰기(`write-weather.json`) · `trip.yaml` 고치기(`write-trip.json`) · 폴더 밖 쓰기(`write-outside.json`) · 깨진 입력(`broken.json`) |
| `research/` | subagent 넷의 결과 파일이 모이는 폴더 |

결과 파일의 모양은 넷이 같습니다.

```json
{"agent": "sights", "city": "", "checked_on": "YYYY-MM-DD",
 "items": [{"id": "sights-1", "name": "", "date": "YYYY-MM-DD", "hours": "", "info": "", "source": "", "checked": "확인"}]}
```

출처 페이지에서 확인하지 못한 값은 지어내지 않고 `"모름"` 으로 적고, `checked` 도 `"모름"` 으로 둡니다.

## 내 여행 폴더 만들기

```bash
cd ~
cp -r harness-practice/project3/15 my-trip
cd my-trip
mkdir -p .claude/agents
cp examples/agents/*.md .claude/agents/
cp examples/settings.json .claude/settings.json
uv sync
```

`trip.yaml` 의 도시 · 날짜 · 이동 한도를 내 여행으로 고칩니다.

## 실행

```bash
uv run python .claude/hooks/protect.py < fixtures/hook/write-weather.json   # 허용 — exit code 0
uv run python .claude/hooks/protect.py < fixtures/hook/write-trip.json      # 막음 — exit code 2
rm hook-log.jsonl                                                           # 시험한 기록 지우기
claude -p "weather · culture · news · sights subagent 를 차례로 불러 각자 결과 파일을 남기게 하세요. 직접 조사하지 마세요. 넷이 끝나면 research/ 의 결과 파일 넷을 읽고, 파일마다 항목 수와 「모름」 인 항목 수를 알려 주세요." --allowedTools "Agent,WebSearch,WebFetch,Write"
cat hook-log.jsonl                                                          # 누가 어느 파일을 썼나
```

마지막 `claude -p` 는 Claude 를 부르고, subagent 넷이 웹을 조사합니다. 넷이 끝날 때까지 화면에는 아무것도 찍히지 않고, 다른 터미널에서 `ls research` 를 치면 결과 파일이 하나씩 느는 것을 볼 수 있습니다. 결과는 실행마다 다릅니다.

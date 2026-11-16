# projects/blog — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그의 시작 상태입니다. 받아 둔 내 저장소(fork)에서 이 폴더를 그대로 쓰고, GitHub Pages 로 빈 블로그를 엽니다.
작업은 저장소 안의 `projects/blog` 한 폴더에서 이어 합니다. `reference/09` … `reference/12` 는 차시마다의 시작 상태라 보기만 합니다. 차시를 넘길 때는 `tools/advance.py` 가 그 차시에 더해지거나 바뀐 강사 파일만 가져오고, 내가 고친 파일은 덮어쓰지 않습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지(저장소 맨 위 `docs/`)를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 요약 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집 → 작성 → 검사 → 승인 graph 초안. 단계 파일이 아직 없어 실행하지 않는다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |

## 시작하기

받아 둔 저장소의 `projects/blog` 가 블로그의 작업 폴더입니다. 새 저장소를 만들거나 폴더를 복사하지 않습니다.

```bash
cd ~/harness-practice/projects/blog
cp examples/PLAN.md examples/graph.yaml examples/CLAUDE.md .
uv sync
uv run python make_site.py
```

`make_site.py` 는 `../../docs/index.html 을 만들었습니다 — 글 0편` 을 찍습니다. 블로그 페이지는 이 폴더가 아니라 저장소 맨 위 `docs/` 에 만들어집니다 — GitHub Pages 가 branch 에서 올릴 수 있는 폴더는 맨 위(`/`)와 `/docs` 뿐입니다. `docs/.nojekyll` 은 다른 변환 없이 그대로 올리라는 표시입니다.
`CLAUDE.md` 의 독자와 말투는 내 블로그에 맞게 고칩니다. 그다음 고친 것을 내 저장소에 올립니다.

```bash
cd ~/harness-practice
git add projects/blog
git commit -m "블로그 시작"
git push
```

GitHub 의 내 저장소 화면에서 Settings → Pages 로 가서, Build and deployment 의 Source 를 Deploy from a branch 로 두고 branch 는 `main`, 폴더는 `/docs` 로 골라 Save 를 누릅니다. 잠시 뒤 `https://<아이디>.github.io/harness-practice/` 에 빈 블로그가 열립니다.

내 컴퓨터에서 먼저 보려면 `projects/blog` 에서 `uv run python -m http.server 8001 --directory ../../docs` 를 실행하고 브라우저로 `http://localhost:8001` 을 엽니다. 끝낼 때는 `Ctrl+C` 를 누릅니다.

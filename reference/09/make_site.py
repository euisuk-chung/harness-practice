"""posts/ 의 글로 블로그 페이지(저장소 맨 위 docs/)를 만든다.

    uv run python make_site.py          # projects/blog 에서

posts/ 의 YYYY-MM-DD.md 하나가 글 한 편이다. 글마다 docs/YYYY-MM-DD.html 을 만들고,
docs/index.html 에 최근 글부터 목록을 적는다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다.
posts/ 에서 지운 글의 docs/YYYY-MM-DD.html 은 지운다(index.html · .nojekyll 은 둔다).
docs/ 는 이 폴더가 아니라 저장소 맨 위에 있다 — GitHub Pages 가 branch 에서 올릴 수 있는 폴더는 / 와 /docs 뿐이다.
GitHub Pages 는 main 브랜치의 /docs 폴더를 그대로 올린다(docs/.nojekyll — 다른 변환 없이 그대로).
posts/ 와 docs/ 는 어디서 실행해도 이 파일의 자리로 정한다. reference/ 의 사본에서 실행하면 아무것도 쓰지 않고 멈춘다
(그 사본의 posts/ 로 저장소 맨 위 docs/ 를 다시 만들면 올린 글의 페이지가 지워진다).
"""
import html
import os
import sys
from pathlib import Path

import markdown

TITLE = "내 블로그 — AI 기업 소식"
HERE = Path(__file__).resolve().parent              # projects/blog
POSTS = HERE / "posts"
DOCS = HERE.parents[1] / "docs"                      # 저장소 맨 위 docs/

PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ max-width: 42rem; margin: 3rem auto; padding: 0 1rem; font-family: system-ui, sans-serif; line-height: 1.7; color: #222; }}
header a {{ color: inherit; text-decoration: none; }}
a {{ color: #0b57d0; }}
li {{ margin: .4rem 0; }}
</style>
</head>
<body>
<header><h1><a href="./">{site}</a></h1></header>
{body}
</body>
</html>
"""


def page(title, body):
    return PAGE.format(title=html.escape(title), site=html.escape(TITLE), body=body)


def main():
    if HERE.parent.name != "projects":
        sys.exit(f"make_site.py 는 projects/blog 에서 실행합니다 — 여기는 {HERE.parent.name}/{HERE.name} 입니다(reference/ 는 보기만 하는 폴더)")
    DOCS.mkdir(exist_ok=True)
    posts = sorted(POSTS.glob("*.md"), reverse=True) if POSTS.exists() else []
    items = []
    for post in posts:
        text = post.read_text(encoding="utf-8")
        head = text.strip().splitlines()[0].lstrip("# ").strip() if text.strip() else post.stem
        (DOCS / f"{post.stem}.html").write_text(page(head, markdown.markdown(text)), encoding="utf-8")
        items.append(f'<li>{post.stem} · <a href="{post.stem}.html">{html.escape(head)}</a></li>')
    for old in DOCS.glob("*.html"):                # 원본 글이 없는 페이지는 지운다
        if old.stem != "index" and not (POSTS / f"{old.stem}.md").exists():
            old.unlink()
    body = "<ul>\n" + "\n".join(items) + "\n</ul>" if items else "<p>아직 올라온 글이 없습니다.</p>"
    (DOCS / "index.html").write_text(page(TITLE, body), encoding="utf-8")
    print(f"{os.path.relpath(DOCS / 'index.html')} 을 만들었습니다 — 글 {len(posts)}편")


if __name__ == "__main__":
    main()

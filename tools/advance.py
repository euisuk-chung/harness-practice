"""차시를 넘길 때 — 강사가 그 차시에 더하거나 바꾼 파일을 내 작업 폴더(projects/<프로젝트>)로 가져온다.

    uv run python tools/advance.py blog 10                      # 저장소 맨 위에서 — reference/10 을 projects/blog 로
    uv run python tools/advance.py blog 10 --dry-run            # 무엇을 가져올지 보기만
    uv run python tools/advance.py blog 11 --keep graph.yaml    # 충돌 난 파일은 내 것을 두고 나머지를 가져오기

프로젝트와 차시: blog 09~12 · ledger 13~14 · trip 15~16. reference/<차시>/ 의 파일마다 projects/<프로젝트>/ 의 같은 파일을 본다.
- 내 폴더에 없으면 더한다(+). 이미 같으면 그대로 둔다
- 강사가 실은 판 그대로면(내가 고치지 않았으면) 새 판으로 바꾼다(~)
- 내가 고친 파일이면 그대로 둔다(=). 단 지금 차시 뒤로 강사 판도 바뀌었으면 충돌(!) — 무엇이 다른지 보이고,
  아무 파일도 바꾸지 않은 채 exit code 1 로 멈춘다. 덮어쓰지 않는다
「강사가 실은 판」은 이 저장소의 git 기록에 있는 reference/*/<같은 경로> 의 모든 판과 지금 reference/ 의 파일이다.
examples/ 의 graph.yaml · settings.json · agents/*.md 처럼 제자리에 놓아 쓰는 파일(PLACE)은 같은 규칙으로 제자리에 놓는다.
내 폴더에만 있는 파일(글 · 가계부 · 조사 결과 · 고쳐 둔 CLAUDE.md · SKILL.md …)은 건드리지 않는다. 지우는 파일은 없다.
exit code — 0: 가져옴(가져올 것이 없었음) · 1: 충돌 · 잘못된 인자 · 지난 차시로 돌아가기. 1 이면 아무 파일도 바꾸지 않았다.

보장하지 않는 것 — 내가 고친 내용과 강사의 새 판을 합쳐 주지 않는다(충돌이면 멈출 뿐). 내 판이 강사의 어느 판과 글자 하나까지
같으면 「고치지 않았다」로 본다. git 기록이 없는 사본에서는 지금 reference/ 의 판만 강사 판으로 안다(그 밖은 충돌로 멈춘다).
"""
import argparse
import difflib
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # 저장소 맨 위
SESSIONS = {"blog": ["09", "10", "11", "12"], "ledger": ["13", "14"], "trip": ["15", "16"]}
# 강사 파일(reference 안의 경로) → 내 폴더에서 놓이는 자리. / 로 끝나면 그 폴더 안의 파일 모두
PLACE = {"blog": {"examples/graph.yaml": "graph.yaml", "examples/settings.json": ".claude/settings.json"},
         "ledger": {"examples/graph.yaml": "graph.yaml"},
         "trip": {"examples/settings.json": ".claude/settings.json", "examples/agents/": ".claude/agents/"}}
SKIP = {".venv", "__pycache__"}


def blob(data):
    """git 이 파일 내용에 매기는 이름(blob id)."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def files(folder):
    return {p.relative_to(folder).as_posix(): p for p in sorted(folder.rglob("*"))
            if p.is_file() and not SKIP & set(p.relative_to(folder).parts)}


def planned(project, ref):
    """reference 한 차시의 (내 폴더 경로 → 강사 파일). 제자리에 놓는 파일은 원래 자리와 놓을 자리 둘 다."""
    out = {}
    for rel, path in files(ref).items():
        out[rel] = path
        for src, dst in PLACE[project].items():
            if rel == src or (src.endswith("/") and rel.startswith(src)):
                out[dst + rel[len(src):] if src.endswith("/") else dst] = path
    return out


def known_versions(project):
    """경로마다 강사가 실은 판의 blob id — git 기록의 reference/*/<경로> 와 지금 reference/ 의 파일."""
    known = {}
    for session in SESSIONS[project]:
        for rel, path in planned(project, ROOT / "reference" / session).items():
            known.setdefault(rel, set()).add(blob(path.read_bytes()))
    log = subprocess.run(["git", "log", "--no-renames", "--raw", "--no-abbrev", "--format=", "--",
                          *[f"reference/{s}" for s in SESSIONS[project]]],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    for line in log.stdout.splitlines() if log.returncode == 0 else []:
        meta, _, path = line.partition("\t")
        sha, parts = meta.split()[3], path.split("/", 2)
        if len(parts) == 3 and set(sha) != {"0"}:
            rel = parts[2]
            known.setdefault(rel, set()).add(sha)
            for src, dst in PLACE[project].items():
                if rel == src or (src.endswith("/") and rel.startswith(src)):
                    known.setdefault(dst + rel[len(src):] if src.endswith("/") else dst, set()).add(sha)
    return known


def current(project, work):
    """내 폴더가 몇 차시까지 왔나 — 그 차시에 처음 생긴 강사 파일이 하나라도 있으면 그 차시까지 왔다."""
    sessions, now = SESSIONS[project], SESSIONS[project][0]
    for before, session in zip(sessions, sessions[1:]):
        added = set(files(ROOT / "reference" / session)) - set(files(ROOT / "reference" / before))
        if any((work / rel).exists() for rel in added):
            now = session
    return now


def diff(mine, theirs, a, b):
    try:
        lines = difflib.unified_diff(mine.decode("utf-8").splitlines(), theirs.decode("utf-8").splitlines(),
                                     a, b, lineterm="", n=1)
    except UnicodeDecodeError:
        return ["  (글이 아닌 파일 — 차이를 찍지 않습니다)"]
    lines = list(lines)
    return lines[:40] + ([f"  … {len(lines) - 40}줄 더"] if len(lines) > 40 else [])


def main():
    ap = argparse.ArgumentParser(description="강사의 다음 차시 파일을 내 작업 폴더로 가져온다 — 내가 고친 파일은 덮어쓰지 않는다")
    ap.add_argument("project", choices=SESSIONS)
    ap.add_argument("session")
    ap.add_argument("--keep", action="append", default=[], help="충돌 난 파일을 내 것으로 둔다(내 폴더 안의 경로)")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 가져올지 보이기만 하고 바꾸지 않는다")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    if a.session not in SESSIONS[a.project]:
        print(f"{a.project} 의 차시는 {' · '.join(SESSIONS[a.project])} 입니다: {a.session}")
        return 1
    work, ref = ROOT / "projects" / a.project, ROOT / "reference" / a.session
    now = current(a.project, work)
    if int(a.session) < int(now):
        print(f"projects/{a.project} 는 이미 {now}차시까지 왔습니다 — 지난 차시({a.session})로 되돌리지 않습니다")
        return 1
    base = planned(a.project, ROOT / "reference" / now)
    known = known_versions(a.project)
    print(f"{a.project}: {now}차시 → {a.session}차시 (reference/{a.session} → projects/{a.project})")
    add, change, kept, conflict = [], [], [], []
    for rel, src in sorted(planned(a.project, ref).items()):
        theirs, dst = src.read_bytes(), work / rel
        mine = dst.read_bytes() if dst.exists() else None
        if mine == theirs:
            continue
        if mine is None:
            add.append((rel, src))
        elif {blob(mine), blob(mine.replace(b"\r\n", b"\n"))} & known.get(rel, set()):
            change.append((rel, src))                 # 강사 판 그대로 — 고치지 않았다
        elif rel in a.keep or (rel in base and base[rel].read_bytes() == theirs):
            kept.append(rel)                          # 내가 고쳤고, 강사 판은 그 뒤로 바뀌지 않았다(또는 --keep)
        else:
            conflict.append((rel, src, mine, theirs))
    for rel, src, mine, theirs in conflict:
        print(f"! {rel} — 내가 고친 파일인데 강사 판도 바뀌었습니다")
        print("\n".join(diff(mine, theirs, f"내 것 projects/{a.project}/{rel}", f"강사 {src.relative_to(ROOT).as_posix()}")))
    if conflict:
        print(f"충돌 {len(conflict)}건 — 아무 파일도 바꾸지 않았습니다. 강사 판을 보고 필요한 것을 내 파일에 옮겨 적은 뒤,")
        print(f"내 것을 두려면 다시 실행할 때 {' '.join('--keep ' + c[0] for c in conflict)} 를 붙입니다.")
        return 1
    for rel, src in add + change:
        print(f"{'+' if (rel, src) in add else '~'} {rel}")
        if not a.dry_run:
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, work / rel)
            shutil.copymode(src, work / rel)
    for rel in kept:
        print(f"= {rel} (내가 고친 것 — 그대로 둠)")
    print(f"더함 {len(add)} · 바꿈 {len(change)} · 그대로 둠 {len(kept)}" + (" — --dry-run 이라 바꾸지 않았습니다" if a.dry_run else ""))
    if any(rel == "pyproject.toml" for rel, _ in change + add) and not a.dry_run:
        print(f"pyproject.toml 이 바뀌었습니다 — projects/{a.project} 에서 uv sync 를 실행합니다")
    return 0


if __name__ == "__main__":
    sys.exit(main())

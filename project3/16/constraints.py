"""constraint check — 일정 안(plans/*.json)이 지켜야 할 조건을 하나씩 코드로 확인한다.

조건은 넷이다: 날짜 · 운영 시간 · 하루 이동 한도 · 출처. 기준은 trip.yaml 과 research/*.json 이다.
exit code — 0: 모든 안이 통과 · 1: 거부된 안이 있음(이유를 찍는다) · 3: 거부는 없지만 확인 못 한 정보가 남은 안이 있음(사람 차례).
거부가 없으면 안마다의 판정을 choices.md(고를 칸)에 쓴다. 확인 못 한 정보는 통과시키지 않고 그 칸에 적는다.

    uv run python constraints.py                 # 내 여행 폴더의 plans/*.json 을 검사
    uv run python constraints.py fixtures/ok     # 다른 폴더(그 안의 trip.yaml · research/ · plans/)를 검사
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

HOURS = re.compile(r"(\d{1,2}):(\d{2})\s*[-~–]\s*(\d{1,2}):(\d{2})")   # 운영 시간 글에서 첫 「시각-시각」 만 읽는다


def minutes(hhmm):
    h, m = str(hhmm).split(":")
    return int(h) * 60 + int(m)


def check(plan, trip, items):
    """안 하나를 검사해 (거부 이유 목록, 확인 못 한 것 목록)을 돌려준다."""
    reasons, unknown = [], []
    start, end = date.fromisoformat(str(trip["start"])), date.fromisoformat(str(trip["end"]))
    for day in plan["days"]:
        d = day["date"]
        # 날짜 — 여행 기간 안인가
        if not start <= date.fromisoformat(d) <= end:
            reasons.append(f"{d}: 여행 기간({start} ~ {end}) 밖의 날짜입니다")
        clock = minutes(trip["day_start"])          # 숙소를 나서는 시각
        moved = 0
        for s in day["stops"]:
            name, item = s.get("name", s.get("ref")), items.get(s.get("ref"))
            # 출처 — 조사 결과에 있는 항목이고, 출처 · 확인 여부를 그대로 옮겼는가
            if item is None:
                reasons.append(f"{d} {name}: 조사 결과에 없는 장소입니다(ref {s.get('ref')})")
                continue
            if s.get("source") != item["source"] or s.get("checked") != item["checked"]:
                reasons.append(f"{d} {name}: 출처 · 확인 여부가 조사 결과와 다릅니다")
            if item["checked"] != "확인" or item["source"] == "모름":
                unknown.append(f"{d} {name}: 출처에서 확인하지 못한 정보입니다")
            # 날짜 — 그날에만 있는 항목인가
            if item["date"] != "기간 전체" and item["date"] != d:
                reasons.append(f"{d} {name}: {item['date']} 에만 있는 항목입니다")
            # 운영 시간 — 도착 · 출발이 하루 시작 · 끝과 운영 시간 안에 드는가
            arrive, depart = minutes(s["arrive"]), minutes(s["depart"])
            if arrive < clock + s["move_minutes"]:
                reasons.append(f"{d} {name}: 앞 장소에서 {s['move_minutes']}분 이동하면 {s['arrive']} 에 닿지 못합니다")
            if depart - arrive != s["stay_minutes"]:
                reasons.append(f"{d} {name}: 머무는 시간 {s['stay_minutes']}분이 도착 · 출발과 맞지 않습니다")
            if depart > minutes(trip["day_end"]):
                reasons.append(f"{d} {name}: 하루 끝({trip['day_end']}) 뒤에 떠납니다")
            hours = HOURS.search(item["hours"])
            if hours is None:
                unknown.append(f"{d} {name}: 운영 시간을 모릅니다(「{item['hours']}」)")
            else:
                opens, closes = int(hours[1]) * 60 + int(hours[2]), int(hours[3]) * 60 + int(hours[4])
                if arrive < opens or depart > closes:
                    reasons.append(f"{d} {name}: 운영 시간({hours[0]}) 밖입니다({s['arrive']}-{s['depart']})")
            clock = depart
            moved += s["move_minutes"]
        # 하루 이동 한도 — 그날 이동 시간의 합
        if moved > trip["move_limit_minutes"]:
            reasons.append(f"{d}: 이동 {moved}분이 내 이동 한도 {trip['move_limit_minutes']}분을 넘습니다")
    return reasons, unknown


def load(folder):
    trip = yaml.safe_load((folder / "trip.yaml").read_text(encoding="utf-8"))
    items = {}
    for f in sorted((folder / "research").glob("*.json")):
        for item in json.loads(f.read_text(encoding="utf-8"))["items"]:
            items[item["id"]] = item
    return trip, items


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    trip, items = load(folder)
    files = sorted((folder / "plans").glob("*.json"), key=lambda f: int(f.stem))
    if not files:
        print(f"검사할 일정 안이 없습니다: {folder / 'plans'}")
        sys.exit(1)                                 # 일정 안이 없어도 1 — 짜게 한다
    results = []
    for f in files:
        try:
            plan = json.loads(f.read_text(encoding="utf-8"))
            reasons, unknown = check(plan, trip, items)
        except (KeyError, TypeError, ValueError) as e:
            plan, reasons, unknown = {"title": ""}, [f"일정 파일을 읽지 못했습니다({type(e).__name__}: {e})"], []
        verdict = "거부" if reasons else "고를 칸" if unknown else "통과"
        print(f"{f.stem}안 {verdict} — {plan.get('title', '')}")
        for r in reasons + unknown:
            print(f"  {r}")
        results.append((f.stem, plan, verdict, unknown))
    if any(v == "거부" for _, _, v, _ in results):
        (folder / "choices.md").unlink(missing_ok=True)   # 지난 고를 칸은 지운다
        sys.exit(1)                                 # 거부 — 이유를 넘겨 다시 짠다
    write_choices(folder / "choices.md", results)
    print(f"고를 칸: {folder / 'choices.md'} — 번호를 골라 uv run python choose.py <번호>")
    sys.exit(3 if any(unknown for *_, unknown in results) else 0)


def write_choices(path, results):
    lines = ["# 고를 칸", "", "번호를 골라 `uv run python choose.py <번호>` 로 확정합니다.", ""]
    for n, plan, verdict, unknown in results:
        lines += [f"## {n}안 — {plan.get('title', '')} ({verdict})", ""]
        for day in plan["days"]:
            route = " → ".join(f"{s['name']} {s['arrive']}-{s['depart']}" for s in day["stops"])
            lines.append(f"- {day['date']}: {route} (이동 {sum(s['move_minutes'] for s in day['stops'])}분)")
        lines += [f"- 확인 못 한 것: {u}" for u in unknown] + [""]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

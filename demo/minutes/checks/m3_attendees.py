"""M3 참석자 실재 — 참석자 이름이 녹취나 참석자 명단에 나오나, 빠진 사람이 없나.

명단(녹취록 머리의 `참석:` 줄)이 있으면 말하지 않은 참석자도 안다 — 명단의 이름도 모두 참석자에 들어가야 한다.
명단이 없으면 녹취에 이름이 없는 참석자(말 없는 참석자)는 이 검사가 알 수 없다 — 사람이 채운다.

녹음을 받아 적은 녹취록(capture/)은 누가 말했는지 모른다 — 화자가 모두 `미확인` 이다.
`미확인` 은 사람 이름이 아니라서 참석자에 넣으면 거부하고, 「참석자에서 빠졌다」 로도 걸지 않는다.
그때 참석자는 명단으로만 확인되므로 사람이 볼 메모를 남긴다.
"""

UNKNOWN = "미확인"


def check(draft: dict, speakers: list[str], roster: list[str] | None = None) -> list[str]:
    roster = roster or []
    att = draft.get("attendees", [])
    named = [s for s in speakers if s != UNKNOWN]
    known = set(named) | set(roster)
    probs = [f"attendee '{a}' is not a person — speaker unknown" for a in att if a == UNKNOWN]
    probs += [f"attendee '{a}' not in transcript" + (" or roster" if roster else "") for a in att
              if a != UNKNOWN and a not in known]
    probs += [f"speaker '{s}' missing from attendees" for s in named if s not in att]
    probs += [f"roster member '{r}' missing from attendees" for r in roster if r not in att]
    return probs


def notes(draft: dict, speakers: list[str], roster: list[str] | None = None) -> list[str]:
    """거부는 아니지만 사람이 볼 것 — 명단에 없는데 말한 사람(명단이 덜 적혔을 수 있다), 누가 말했는지 모르는 녹취."""
    out = []
    if UNKNOWN in speakers:
        out.append("speakers are unknown (recorded transcript) — attendees checked against the roster only"
                   if roster else "speakers are unknown and there is no roster — attendees cannot be checked")
    if roster:
        out += [f"speaker '{s}' is not on the roster" for s in speakers if s != UNKNOWN and s not in roster]
    return out

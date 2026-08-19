#!/usr/bin/env python3
"""A Vadkelet liga élő adata a nyílt Draft API-ból -> league.json

league/{id}/details      -> résztvevők, valódi nevek
league/{id}/element-status -> AKTUÁLIS birtoklás (csere/waiver után is helyes)
draft/{id}/choices       -> a draft tényleges sorrendje (kör + pick)
"""
import json, pathlib, subprocess, sys

LEAGUE = 20944
HERE = pathlib.Path(__file__).parent
API = "https://draft.premierleague.com/api"

def get(path):
    r = subprocess.run(["curl", "-s", f"{API}/{path}"], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {path}")
    try: return json.loads(r.stdout)
    except json.JSONDecodeError: sys.exit(f"nem JSON: {path} -> {r.stdout[:200]!r}")

det = get(f"league/{LEAGUE}/details")
stat = get(f"league/{LEAGUE}/element-status")
cho = get(f"draft/{LEAGUE}/choices")["choices"]

entries = {e["entry_id"]: {
    "league_entry": e["id"], "entry_id": e["entry_id"], "team": e["entry_name"],
    "name": f'{e["player_first_name"]} {e["player_last_name"]}'.strip(),
    "first": e["player_first_name"], "initials": e["short_name"],
} for e in det["league_entries"]}

owned = {}
for s in stat["element_status"]:
    if s["owner"]:
        owned.setdefault(s["owner"], []).append(s["element"])

picks = {}          # element -> (index, round, pick, owner_at_draft)
for c in cho:
    picks[c["element"]] = {"index": c["index"], "round": c["round"],
                           "pick": c["pick"], "drafted_by": c["entry"]}

order = []          # a draft menete
for c in sorted(cho, key=lambda c: c["index"]):
    order.append({"index": c["index"], "round": c["round"], "pick": c["pick"],
                  "element": c["element"], "entry": c["entry"],
                  "auto": c["was_auto"], "seconds": c["seconds_to_pick"]})

out = {
    "league": {"id": LEAGUE, "name": det["league"]["name"],
               "draft_dt": det["league"]["draft_dt"], "status": det["league"]["draft_status"],
               "size": len(entries), "rounds": max(c["round"] for c in cho)},
    "entries": list(entries.values()),
    "owned": {str(k): v for k, v in owned.items()},
    "picks": {str(k): v for k, v in picks.items()},
    "order": order,
}
(HERE / "league.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{out['league']['name']} · {out['league']['size']} csapat · {out['league']['rounds']} kör · {len(cho)} pick")
for e in entries.values():
    n = len(owned.get(e["entry_id"], []))
    auto = sum(1 for c in cho if c["entry"] == e["entry_id"] and c["was_auto"])
    print(f"  {e['initials']:<3} {e['name']:<20} {e['team']:<16} {n:>2} játékos, {auto} auto-pick")
print(f"\nBirtokolt összesen: {sum(len(v) for v in owned.values())} / draftolt: {len(cho)}")

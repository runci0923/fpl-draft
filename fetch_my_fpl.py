#!/usr/bin/env python3
"""A sima (nem draft) FPL csapat lehúzása: my_fpl.json.

A picks-végpont csak LEZÁRT fordulóra ad választ (deadline előtt 404), ezért
minden lejátszott fordulóra elmentjük a tényleges 15-öt, a kapitányt és a
kispad-sorrendet — így a napló „Játékosaim" része nem képernyőképről, hanem
az API-ból jön. A transfer-lista és a fordulónkénti pont/hely is ide kerül.
"""
import json, pathlib, sys, urllib.error, urllib.request

HERE = pathlib.Path(__file__).parent
ENTRY = int(sys.argv[1]) if len(sys.argv) > 1 else 117238
API = "https://fantasy.premierleague.com/api"

def get(path):
    try:
        with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

bs = get("bootstrap-static/")
TEAM = {t["id"]: t["short_name"] for t in bs["teams"]}
PT = {p["id"]: p["singular_name_short"] for p in bs["element_types"]}
EL = {e["id"]: e for e in bs["elements"]}
def pl(i):
    e = EL[i]
    return {"id": i, "n": e["web_name"], "club": TEAM[e["team"]],
            "pos": PT[e["element_type"]], "price": e["now_cost"] / 10,
            "own": float(e["selected_by_percent"])}

entry = get(f"entry/{ENTRY}/")
hist = get(f"entry/{ENTRY}/history/")
tr = get(f"entry/{ENTRY}/transfers/") or []

# hol áll a szezon: csak a lezárt fordulókra van picks
finished = [e["id"] for e in bs["events"] if e["finished"]]
current = next((e["id"] for e in bs["events"] if e["is_current"]), 0)
gws = {}
for gw in sorted(set(finished + ([current] if current else []))):
    p = get(f"entry/{ENTRY}/event/{gw}/picks/")
    if not p: continue
    picks = p["picks"]
    gws[str(gw)] = {
        "chip": p.get("active_chip"),
        "points": p["entry_history"]["points"],
        "bench_points": p["entry_history"]["points_on_bench"],
        "rank": p["entry_history"]["rank"],
        "overall_rank": p["entry_history"]["overall_rank"],
        "transfers": p["entry_history"]["event_transfers"],
        "transfer_cost": p["entry_history"]["event_transfers_cost"],
        "bank": p["entry_history"]["bank"] / 10,
        "value": p["entry_history"]["value"] / 10,
        "auto_subs": [{"in": s["element_in"], "out": s["element_out"]}
                      for s in p.get("automatic_subs", [])],
        "xi": [dict(pl(x["element"]), slot=x["position"],
                    cap=x["is_captain"], vice=x["is_vice_captain"],
                    mult=x["multiplier"]) for x in picks if x["position"] <= 11],
        "bench": [dict(pl(x["element"]), slot=x["position"],
                       cap=x["is_captain"], vice=x["is_vice_captain"])
                  for x in picks if x["position"] > 11],
    }

out = {
    "_doc": ["A sima FPL csapat az API-ból (fetch_my_fpl.py).",
             "A picks csak LEZÁRT fordulóra elérhető, ezért gws csak azokat tartalmazza."],
    "entry": ENTRY,
    "team_name": entry["name"],
    "manager": f'{entry["player_first_name"]} {entry["player_last_name"]}'.strip(),
    "total_points": entry["summary_overall_points"],
    "overall_rank": entry["summary_overall_rank"],
    "current_event": entry["current_event"],
    "chips_used": hist.get("chips", []),
    "history": hist.get("current", []),
    "transfers": [{"gw": t["event"], "in": pl(t["element_in"]),
                   "out": pl(t["element_out"]),
                   "in_cost": t["element_in_cost"] / 10,
                   "out_cost": t["element_out_cost"] / 10, "time": t["time"]}
                  for t in tr],
    "gws": gws,
}
(HERE / "my_fpl.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f'my_fpl.json — {out["team_name"]} ({out["manager"]}), {out["total_points"]} pt, '
      f'{out["overall_rank"]:,} hely · lezárt fordulók: {", ".join(gws) or "nincs"} · '
      f'{len(out["transfers"])} transfer'.replace(",", " "))

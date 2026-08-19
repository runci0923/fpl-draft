#!/usr/bin/env python3
"""Valós kezdő XI és pontok a deadline után -> actuals.json

`entry/{id}/event/{gw}` a deadline ELŐTT "No pick history"-t ad, utána a tényleges
felállást és a játékosonkénti pontot. Ez a fájl mondja meg, ki KEZDETT valójában —
szemben azzal, akit a projekció szerint kezdeni kellett volna.
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
LEAGUE = 20944
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

def api(path):
    r = subprocess.run(["curl", "-s", "-A", UA, f"https://draft.premierleague.com/api/{path}"],
                       capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {path}")
    try: return json.loads(r.stdout)
    except json.JSONDecodeError: return None

game = api("game")
det = api(f"league/{LEAGUE}/details")
entries = [e["entry_id"] for e in det["league_entries"]]
live_cache = {}

out = {"updated_for": game["current_event"], "next_event": game["next_event"], "gw": {}}
done = [m["event"] for m in det["matches"] if m["started"]]
gws = sorted(set(done)) or ([game["current_event"]] if game["current_event"] else [])

for gw in gws:
    live = live_cache.get(gw) or api(f"event/{gw}/live")
    live_cache[gw] = live
    pts = {}
    if live and "elements" in live:
        for eid, v in live["elements"].items():
            pts[int(eid)] = v.get("stats", {}).get("total_points")
    per = {}
    for ent in entries:
        d = api(f"entry/{ent}/event/{gw}")
        if not isinstance(d, dict) or "picks" not in d:
            continue                      # deadline előtt: "No pick history"
        per[str(ent)] = {
            "xi": [p["element"] for p in d["picks"] if p["position"] <= 11],
            "bench": [p["element"] for p in d["picks"] if p["position"] > 11],
            "points": {str(p["element"]): pts.get(p["element"]) for p in d["picks"]},
        }
    if per: out["gw"][str(gw)] = per

(HERE / "actuals.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")
if out["gw"]:
    for gw, per in out["gw"].items():
        print(f"GW{gw}: {len(per)}/{len(entries)} csapat valós felállása letöltve")
else:
    print(f"Még nincs valós felállás — a deadline előtt az API "
          f'"No pick history"-t ad. Következő forduló: GW{game["next_event"]}.')

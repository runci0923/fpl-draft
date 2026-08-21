#!/usr/bin/env python3
"""Projektált vs. valós H2H -> h2h.json  (a forduló-oldal adatforrása)

Projektált meccspontszám = a becslés szerinti LEGJOBB legális kezdő XI összege.
(Deadline előtt a valós XI nem kérhető le, és a racionális manager amúgy is ezt állítaná.)
Deadline után az actuals.json adja, ki KEZDETT valójában és mennyit hozott.
"""
import datetime as dt
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
LEAGUE = 20944
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

# FPL Draft felállás-szabály: 11 fő, pontosan 1 GK, DEF 3-5, MID 2-5, FWD 1-3
FORMATIONS = [(d, m, f) for d in range(3, 6) for m in range(2, 6) for f in range(1, 4)
              if d + m + f == 10]

def api(p):
    r = subprocess.run(["curl", "-s", "-A", UA, f"https://draft.premierleague.com/api/{p}"],
                       capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {p}")
    return json.loads(r.stdout)

def best_xi(squad, pts):
    """(xi_ids, összpont) — a legjobb legális felállás a becslés szerint."""
    byp = {p: sorted((i for i, q in squad if q == p), key=lambda i: -pts.get(i, 0.0))
           for p in ("GKP", "DEF", "MID", "FWD")}
    if not byp["GKP"]: return [], 0.0
    gk = byp["GKP"][0]
    best, bestsum = None, -1.0
    for d, m, f in FORMATIONS:
        if len(byp["DEF"]) < d or len(byp["MID"]) < m or len(byp["FWD"]) < f: continue
        pick = byp["DEF"][:d] + byp["MID"][:m] + byp["FWD"][:f]
        tot = sum(pts.get(i, 0.0) for i in pick) + pts.get(gk, 0.0)
        if tot > bestsum: best, bestsum = [gk] + pick, tot
    return (best or []), round(bestsum if best else 0.0, 2)

# --- legfrissebb snapshot a TARTALOM taken_at-je szerint (a fájlnév-rendezés vegyes
#     időzónánál hibázik: 18:03 UTC későbbi, mint 19:55 CEST)
# a proj_private/ tartalmazza a fizetős forrásokat is; ha van, azt használjuk
# a legfrissebb MINDKÉT mappából: a proj_private/ csak akkor tartalmaz többet, ha van
# olyan forrás, amit nem publikálunk — különben elavult snapshotot választanánk
cands = list((HERE / "proj").glob("*.json")) + list((HERE / "proj_private").glob("*.json"))
if not cands: sys.exit("Nincs projekció-snapshot — futtasd a fetch_projections.py-t")
def when(p):
    ts = json.loads(p.read_text(encoding="utf-8"))["taken_at"].replace("Z", "+00:00")
    x = dt.datetime.fromisoformat(ts)
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
snapf = sorted(cands, key=when)[-1]
snap = json.loads(snapf.read_text(encoding="utf-8"))

data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
P = data["players"]
det = api(f"league/{LEAGUE}/details")
LE2ENT = {e["id"]: e["entry_id"] for e in det["league_entries"]}
bs = api("bootstrap-static")
CLUB = {t["id"]: t["short_name"] for t in bs["teams"]}
# a Draft bootstrapban a fixtures fordulónként kulcsolt DICT, nem lista
FIX = {}                       # gw -> csapat_id -> (ellenfél rövidítés, H/A)
for gwk, lst in bs["fixtures"].items():
    for x in lst:
        gwn = x.get("event") or int(gwk)
        FIX.setdefault(gwn, {})[x["team_h"]] = (CLUB[x["team_a"]], "H")
        FIX[gwn][x["team_a"]] = (CLUB[x["team_h"]], "A")
TEAM = {x["id"]: x["team"] for x in bs["elements"]}
NAME = {x["id"]: x["web_name"] for x in bs["elements"]}

squads = {m["entry"]: [(s["id"], P[str(s["id"])]["p"]) for s in m["squad"]]
          for m in data["managers"]}

act = {}
ap = HERE / "actuals.json"
if ap.exists(): act = json.loads(ap.read_text(encoding="utf-8")).get("gw", {})

rounds = {}
for mt in det["matches"]:
    rounds.setdefault(mt["event"], []).append({
        "home": LE2ENT[mt["league_entry_1"]], "away": LE2ENT[mt["league_entry_2"]],
        "actual": ([mt["league_entry_1_points"], mt["league_entry_2_points"]]
                   if mt["finished"] else None),
        "finished": mt["finished"], "started": mt["started"]})

def card(i, pts, gw, real_pts=None):
    opp = FIX.get(gw, {}).get(TEAM[i])
    return {"id": i, "n": NAME[i], "c": CLUB[TEAM[i]], "p": P[str(i)]["p"],
            "proj": round(pts.get(i, 0.0), 2),
            "opp": (f"{opp[0]} ({opp[1]})" if opp else None),
            "act": real_pts}

out = {"league": data["league"], "snapshot": snapf.name, "taken_at": snap["taken_at"],
       "sources": snap["sources"], "next_event": None, "rounds": {}}
game = api("game")
out["next_event"] = game["next_event"]
out["current_event"] = game["current_event"]

for gw in range(snap["gw_from"], snap["gw_to"] + 1):
    if gw not in rounds: continue
    per_src = {}
    for src, tbl in snap["data"].items():
        pts = {int(d): v[str(gw)]["pts"] for d, v in tbl.items() if v.get(str(gw))}
        if not pts: continue
        A = act.get(str(gw), {})
        teams = {}
        for ent, sq in squads.items():
            xi, tot = best_xi(sq, pts)
            real = A.get(str(ent))
            rp = {int(k): v for k, v in (real or {}).get("points", {}).items()}
            teams[ent] = {
                "proj": tot,
                "xi": [card(i, pts, gw, rp.get(i)) for i in xi],
                "bench": [card(i, pts, gw, rp.get(i)) for i, _ in sq if i not in set(xi)],
                "real_xi": (real or {}).get("xi"),
                "real_total": (sum(v for v in (rp.get(i) for i in (real or {}).get("xi", []))
                                   if v is not None) if real else None),
            }
        per_src[src] = {"teams": teams, "matches": [
            {"home": m["home"], "away": m["away"],
             "proj": [teams[m["home"]]["proj"], teams[m["away"]]["proj"]],
             "proj_result": ("H" if teams[m["home"]]["proj"] > teams[m["away"]]["proj"]
                             else "A" if teams[m["away"]]["proj"] > teams[m["home"]]["proj"] else "D"),
             "actual": m["actual"], "finished": m["finished"], "started": m["started"]}
            for m in rounds[gw]]}
    out["rounds"][str(gw)] = per_src

(HERE / "h2h.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                               encoding="utf-8")

gw = out["next_event"] or out["current_event"] or snap["gw_from"]
per = out["rounds"].get(str(gw), {})
src = next(iter(per), None)
r = per.get(src) if src else None
print(f"Snapshot: {snapf.name}   GW{gw}   forrás: {snap['sources'][src]['label'] if src else '—'}"
      f"   valós felállás: {'megvan' if str(gw) in act else 'még nincs (deadline előtt)'}")
if r:
    ENT = {m["entry"]: m["first"] for m in data["managers"]}
    for m in r["matches"]:
        h, a = ENT[m["home"]], ENT[m["away"]]
        mark = "→" if m["proj_result"] == "H" else "←" if m["proj_result"] == "A" else "="
        print(f"   {h:>10} {m['proj'][0]:>6} {mark} {m['proj'][1]:<6} {a}")

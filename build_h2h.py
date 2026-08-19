#!/usr/bin/env python3
"""Projektált vs. valós H2H eredmények a Vadkelet ligában.

Projektált meccspontszám = a becslés szerinti LEGJOBB legális kezdő XI összege.
(Deadline előtt a valós XI nem kérhető le, és a racionális manager amúgy is ezt állítaná.)
Valós pontszám = a liga `matches` végpontjából, ha a forduló lezárult.

Kimenet: h2h.json — fordulónként, forrásonként: projektált eredmény + valós + szerencse-mérleg.
"""
import datetime as dt
import json, pathlib, subprocess, sys
from itertools import combinations

HERE = pathlib.Path(__file__).parent
LEAGUE = 20944
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

# FPL Draft felállás-szabály: 11 fő, pontosan 1 GK, DEF 3-5, MID 2-5, FWD 1-3
FORMATIONS = [(d, m, f) for d in range(3, 6) for m in range(2, 6) for f in range(1, 4)
              if d + m + f == 10]

def curl(u):
    r = subprocess.run(["curl", "-s", "-A", UA, u], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {u}")
    return json.loads(r.stdout)

def best_xi(squad, pts):
    """A legjobb legális XI és összpontja. squad: [(id,pos)], pts: id -> becslés."""
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

# A legfrissebb snapshot a TARTALOM taken_at-je szerint, nem fájlnév szerint:
# a fájlnév-rendezés vegyes időzónánál (helyi gép vs. UTC runner) hibázik.
cands = list((HERE / "proj").glob("*.json"))
if not cands: sys.exit("Nincs projekció-snapshot — futtasd a fetch_projections.py-t")
def when(p):
    ts = json.loads(p.read_text(encoding="utf-8"))["taken_at"].replace("Z", "+00:00")
    d = dt.datetime.fromisoformat(ts)
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
snaps = sorted(cands, key=when)
snap = json.loads(snaps[-1].read_text(encoding="utf-8"))
print(f"Snapshot: {snaps[-1].name}  (készült {snap['taken_at']}, GW{snap['gw_from']}–{snap['gw_to']})\n")

data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
P = data["players"]
det = curl(f"https://draft.premierleague.com/api/league/{LEAGUE}/details")
LE2ENT = {e["id"]: e["entry_id"] for e in det["league_entries"]}
ENT = {m["entry"]: m for m in data["managers"]}
squads = {m["entry"]: [(s["id"], P[str(s["id"])]["p"]) for s in m["squad"]] for m in data["managers"]}
bs = curl("https://draft.premierleague.com/api/bootstrap-static")
NAME = {x["id"]: x["web_name"] for x in bs["elements"]}

rounds = {}
for mt in det["matches"]:
    gw = mt["event"]
    e1, e2 = LE2ENT[mt["league_entry_1"]], LE2ENT[mt["league_entry_2"]]
    rounds.setdefault(gw, []).append({
        "home": e1, "away": e2,
        "actual": ([mt["league_entry_1_points"], mt["league_entry_2_points"]]
                   if mt["finished"] else None),
        "finished": mt["finished"], "started": mt["started"]})

out = {"league": data["league"], "snapshot": snaps[-1].name, "taken_at": snap["taken_at"],
       "sources": snap["sources"], "rounds": {}}

for gw in range(snap["gw_from"], snap["gw_to"] + 1):
    if gw not in rounds: continue
    per_src = {}
    for src, tbl in snap["data"].items():
        pts = {}
        for did, per in tbl.items():
            v = per.get(str(gw))
            if v: pts[int(did)] = v["pts"]
        if not pts: continue
        xis = {}
        for ent, sq in squads.items():
            xi, tot = best_xi(sq, pts)
            xis[ent] = {"xi": xi, "proj": tot,
                        "names": [NAME[i] for i in xi]}
        per_src[src] = {
            "teams": xis,
            "matches": [{"home": m["home"], "away": m["away"],
                         "proj": [xis[m["home"]]["proj"], xis[m["away"]]["proj"]],
                         "proj_result": ("H" if xis[m["home"]]["proj"] > xis[m["away"]]["proj"]
                                         else "A" if xis[m["away"]]["proj"] > xis[m["home"]]["proj"] else "D"),
                         "actual": m["actual"], "finished": m["finished"]}
                        for m in rounds[gw]]}
    out["rounds"][str(gw)] = per_src

(HERE / "h2h.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

src = "fplform"
gw = snap["gw_from"]
r = out["rounds"][str(gw)][src]
print(f"GW{gw} projektált H2H (FPL Form szerint):")
for m in r["matches"]:
    h, a = ENT[m["home"]], ENT[m["away"]]
    ph, pa = m["proj"]
    mark = "→" if m["proj_result"] == "H" else "←" if m["proj_result"] == "A" else "="
    print(f"   {h['first']:>10} {ph:>6} {mark} {pa:<6} {a['first']}")
print(f"\nProjektált kezdő XI-k (FPL Form, GW{gw}):")
for ent, t in sorted(r["teams"].items(), key=lambda kv: -kv[1]["proj"]):
    print(f"   {ENT[int(ent)]['first']:<10} {t['proj']:>6}   {', '.join(t['names'])}")
fin = sum(1 for g in out["rounds"].values() for mm in g.get(src, {}).get("matches", []) if mm["finished"])
print(f"\nLezárt meccs a horizonton: {fin} — a szerencse-mérleg a fordulók lejátszása után áll össze.")

#!/usr/bin/env python3
"""SIMA (nem draft) FPL keret-optimalizálás GW1-3-ra, forrásonként. -> squads_test.json

Exakt MILP (pulp + CBC). Fontos: a cél a KEZDŐ XI összpontja fordulónként, nem a 15-é —
az FPL is csak a kezdőt számolja. Kapitány is benne van (duplázás), fordulónként szabadon.

Megkötések: 15 fő · 2 GK / 5 DEF / 5 MID / 3 FWD · max 3 játékos klubonként · <= 100.0m
Felállás fordulónként: 11 fő, pontosan 1 GK, DEF 3-5, MID 2-5, FWD 1-3.

Változatok: szabad · Haaland+Bruno · csak Haaland (Bruno tiltva) · csak Bruno (Haaland tiltva)
"""
import json, pathlib, subprocess, sys
import pulp

HERE = pathlib.Path(__file__).parent
BUDGET = 1000          # tized-millióban (100.0m)
GWS = 3
NEED = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
XI_MIN = {"GKP": 1, "DEF": 3, "MID": 2, "FWD": 1}
XI_MAX = {"GKP": 1, "DEF": 5, "MID": 5, "FWD": 3}

snaps = sorted((HERE / "proj_private").glob("*.json")) or sorted((HERE / "proj").glob("*.json"))
if not snaps: sys.exit("nincs projekció-snapshot")
S = json.loads(snaps[-1].read_text(encoding="utf-8"))
gw0 = S["gw_from"]
gws = [str(g) for g in range(gw0, gw0 + GWS)]

idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
D2M = {int(k): v for k, v in idmap["draft_to_main"].items()}
mn = json.loads(subprocess.run(["curl", "-s", "https://fantasy.premierleague.com/api/bootstrap-static/"],
                               capture_output=True).stdout)
TEAM = {t["id"]: t["short_name"] for t in mn["teams"]}
PT = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
MAIN = {x["id"]: {"cost": x["now_cost"], "club": TEAM[x["team"]], "pos": PT[x["element_type"]],
                  "web": x["web_name"], "status": x["status"]} for x in mn["elements"]}

def load(src):
    """draft_id -> {gw: pts} + ár/klub/pozíció a fő FPL API-ból"""
    out = {}
    for d, per in S["data"].get(src, {}).items():
        d = int(d)
        m = D2M.get(d)
        if m is None or m not in MAIN: continue
        info = MAIN[m]
        if info["status"] in ("u",):            # kilépett játékos nem választható
            continue
        pts = [per[g]["pts"] for g in gws if g in per]
        if len(pts) != GWS: continue
        out[d] = {"pts": pts, **info}
    return out

def solve(pool, force=(), ban=(), label=""):
    ids = list(pool)
    prob = pulp.LpProblem("fpl", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x{i}", cat="Binary") for i in ids}
    y = {(i, g): pulp.LpVariable(f"y{i}_{g}", cat="Binary") for i in ids for g in range(GWS)}
    c = {(i, g): pulp.LpVariable(f"c{i}_{g}", cat="Binary") for i in ids for g in range(GWS)}

    prob += pulp.lpSum(pool[i]["pts"][g] * (y[(i, g)] + c[(i, g)]) for i in ids for g in range(GWS))

    prob += pulp.lpSum(x[i] for i in ids) == 15
    for p, n in NEED.items():
        prob += pulp.lpSum(x[i] for i in ids if pool[i]["pos"] == p) == n
    clubs = {pool[i]["club"] for i in ids}
    for cl in clubs:
        prob += pulp.lpSum(x[i] for i in ids if pool[i]["club"] == cl) <= 3
    prob += pulp.lpSum(pool[i]["cost"] * x[i] for i in ids) <= BUDGET

    for g in range(GWS):
        prob += pulp.lpSum(y[(i, g)] for i in ids) == 11
        prob += pulp.lpSum(c[(i, g)] for i in ids) == 1
        for p in NEED:
            grp = [i for i in ids if pool[i]["pos"] == p]
            prob += pulp.lpSum(y[(i, g)] for i in grp) >= XI_MIN[p]
            prob += pulp.lpSum(y[(i, g)] for i in grp) <= XI_MAX[p]
        for i in ids:
            prob += y[(i, g)] <= x[i]
            prob += c[(i, g)] <= y[(i, g)]

    for i in force:
        if i in x: prob += x[i] == 1
        else: return None
    for i in ban:
        if i in x: prob += x[i] == 0

    st = prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[st] != "Optimal": return None

    squad = [i for i in ids if x[i].value() > .5]
    per_gw = []
    for g in range(GWS):
        xi = [i for i in squad if y[(i, g)].value() > .5]
        cap = next((i for i in squad if c[(i, g)].value() > .5), None)
        per_gw.append({"gw": gw0 + g, "xi": xi, "captain": cap,
                       "pts": round(sum(pool[i]["pts"][g] for i in xi)
                                    + (pool[cap]["pts"][g] if cap else 0), 2)})
    return {"label": label,
            "cost": round(sum(pool[i]["cost"] for i in squad) / 10, 1),
            "total": round(sum(r["pts"] for r in per_gw), 2),
            "squad": [{"id": i, "web": pool[i]["web"], "club": pool[i]["club"],
                       "pos": pool[i]["pos"], "cost": pool[i]["cost"] / 10,
                       "pts": [round(v, 2) for v in pool[i]["pts"]]} for i in squad],
            "rounds": per_gw}

# Haaland / B.Fernandes draft-id megkeresése
NAMES = {"Haaland": None, "B.Fernandes": None}
for d, m in D2M.items():
    w = MAIN.get(m, {}).get("web")
    if w in NAMES: NAMES[w] = d
HAA, BRU = NAMES["Haaland"], NAMES["B.Fernandes"]
if not HAA or not BRU: sys.exit(f"nem találom: {NAMES}")

VARIANTS = [("free", "Szabad", (), ()),
            ("both", "Haaland + Bruno", (HAA, BRU), ()),
            ("haaland", "Csak Haaland", (HAA,), (BRU,)),
            ("bruno", "Csak Bruno", (BRU,), (HAA,))]

out = {"gw_from": gw0, "gws": GWS, "budget": BUDGET / 10, "taken_at": S["taken_at"],
       "sources": {}, "variants": [{"key": k, "label": l} for k, l, _, _ in VARIANTS]}
for src in S["data"]:
    pool = load(src)
    res = {}
    print(f"\n=== {S['sources'][src]['label']}  ({len(pool)} választható játékos)")
    for key, label, force, ban in VARIANTS:
        r = solve(pool, force, ban, label)
        res[key] = r
        if not r: print(f"  {label:<18} nincs megoldás"); continue
        print(f"  {label:<18} {r['total']:>6.1f} pt   £{r['cost']:>5.1f}m")
    out["sources"][src] = {"label": S["sources"][src]["label"], "pool": len(pool), "variants": res}

(HERE / "squads_test.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                       encoding="utf-8")
print(f"\nsquads_test.json kiírva")

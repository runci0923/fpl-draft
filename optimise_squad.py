#!/usr/bin/env python3
"""SIMA (nem draft) FPL keret-optimalizálás GW1-3-ra, forrásonként. -> squads_test.json

Exakt MILP (pulp + CBC). A cél a KEZDŐ XI összpontja fordulónként — DE GW1-ben
BENCH BOOST van, ott mind a 15 játékos pontja számít. Kapitány minden fordulóban duplázik.

A „csak zöld" változat a cheatsheet/gw1_fran.json „green" (Great Option) minősítésű
játékosaira szorít — kivéve a kapust, mert a kapus-táblát nem ismerjük (a tulaj engedélyével).

Megkötések: 15 fő · 2 GK / 5 DEF / 5 MID / 3 FWD · max 3 játékos klubonként · <= 100.0m
Felállás fordulónként: 11 fő, pontosan 1 GK, DEF 3-5, MID 2-5, FWD 1-3.

Változatok: szabad · Haaland+Bruno · csak Haaland (Bruno tiltva) · csak Bruno (Haaland tiltva)
"""
import json, pathlib, subprocess, sys
import pulp

HERE = pathlib.Path(__file__).parent
BUDGET = 1000          # tized-millióban (100.0m)
BBOOST_GW = 0          # 0-alapú index: az ELSŐ vizsgált fordulóban van a bench boost
GWS = 3
NEED = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
XI_MIN = {"GKP": 1, "DEF": 3, "MID": 2, "FWD": 1}
XI_MAX = {"GKP": 1, "DEF": 5, "MID": 5, "FWD": 3}

def _newest(*dirs):
    import datetime as _dt
    c = [p for d in dirs for p in (HERE / d).glob("*.json")]
    if not c: return None
    def w(p):
        t = json.loads(p.read_text(encoding="utf-8"))["taken_at"].replace("Z", "+00:00")
        x = _dt.datetime.fromisoformat(t)
        return x if x.tzinfo else x.replace(tzinfo=_dt.timezone.utc)
    return sorted(c, key=w)[-1]
snaps = [_newest("proj", "proj_private")]
if not snaps[0]: sys.exit("nincs projekció-snapshot")
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

    # GW1 (bench boost): a KERET minden tagja pontot hoz -> x, nem y.
    # A többi fordulóban csak a kezdő XI (y). A kapitány mindig duplázik (c).
    prob += pulp.lpSum(
        pool[i]["pts"][g] * ((x[i] if g == BBOOST_GW else y[(i, g)]) + c[(i, g)])
        for i in ids for g in range(GWS))

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
        scoring = squad if g == BBOOST_GW else xi
        per_gw.append({"gw": gw0 + g, "xi": xi, "captain": cap,
                       "bboost": g == BBOOST_GW,
                       "pts": round(sum(pool[i]["pts"][g] for i in scoring)
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

# a „mag" változathoz: Haaland + Bruno + João Pedro + Calvert-Lewin
CORE_NAMES = ["Haaland", "B.Fernandes", "João Pedro", "Calvert-Lewin"]
CORE = []
for w in CORE_NAMES:
    hit = [d for d, m in D2M.items() if MAIN.get(m, {}).get("web") == w]
    if len(hit) != 1: sys.exit(f"nem egyértelmű: {w} -> {len(hit)}")
    CORE.append(hit[0])
print("Mag-négyes: " + ", ".join(
    f'{MAIN[D2M[i]]["web"]} ({MAIN[D2M[i]]["pos"]} £{MAIN[D2M[i]]["cost"]/10:.1f}m)' for i in CORE)
    + f'  = £{sum(MAIN[D2M[i]]["cost"] for i in CORE)/10:.1f}m')

# --- „csak zöld": a cheat sheet Great Option minősítése
cs = HERE / "cheatsheet" / "gw1_fran.json"
GREEN = set()
if cs.exists():
    import unicodedata
    def nz(t):
        t = (t or "").lower()
        for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i")]: t = t.replace(a, b)
        t = "".join(ch for ch in unicodedata.normalize("NFKD", t) if not unicodedata.combining(ch))
        return "".join(ch for ch in t if ch.isalnum())
    rows = [r for r in json.loads(cs.read_text(encoding="utf-8"))["players"] if r["rate"] == "green"]
    by = {}
    for m, info in MAIN.items():
        by.setdefault((nz(info["web"]), info["club"], info["pos"]), []).append(m)
    miss = []
    for r in rows:
        hit = by.get((nz(r["n"]), r["club"], r["pos"]))
        if hit and len(hit) == 1: GREEN.add(hit[0])
        else: miss.append(f'{r["n"]} ({r["club"]}/{r["pos"]})')
    print(f"Zöld (Great Option) lista: {len(GREEN)}/{len(rows)} párosítva"
          + (f", kimaradt: {', '.join(miss)}" if miss else ""))

VARIANTS = [("free", "Szabad", (), (), False),
            ("both", "Haaland + Bruno", (HAA, BRU), (), False),
            ("haaland", "Csak Haaland", (HAA,), (BRU,), False),
            ("bruno", "Csak Bruno", (BRU,), (HAA,), False),
            ("green", "Csak zöldek", (), (), True),
            ("green_core", "Zöldek + a mag-négyes", tuple(CORE), (), True)]

out = {"gw_from": gw0, "gws": GWS, "budget": BUDGET / 10, "taken_at": S["taken_at"],
       "bboost_gw": gw0 + BBOOST_GW,
       "sources": {}, "variants": [{"key": k, "label": l, "green": gr}
                                   for k, l, _, _, gr in VARIANTS]}
for src in S["data"]:
    pool = load(src)
    res = {}
    print(f"\n=== {S['sources'][src]['label']}  ({len(pool)} választható játékos)")
    for key, label, force, ban, green_only in VARIANTS:
        sub = pool
        if green_only:
            if not GREEN:
                res[key] = None; print(f"  {label:<18} nincs zöld-lista"); continue
            # a kapus szabad (nincs kapus-tábla), a többi pozíció csak zöld
            sub = {i: v for i, v in pool.items()
                   if v["pos"] == "GKP" or D2M[i] in GREEN}
        r = solve(sub, force, ban, label)
        res[key] = r
        if not r: print(f"  {label:<18} nincs megoldás"); continue
        extra = f"   (készlet {len(sub)})" if green_only else ""
        print(f"  {label:<18} {r['total']:>6.1f} pt   £{r['cost']:>5.1f}m{extra}")
    out["sources"][src] = {"label": S["sources"][src]["label"], "pool": len(pool), "variants": res}

(HERE / "squads_test.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                       encoding="utf-8")
print(f"\nsquads_test.json kiírva")

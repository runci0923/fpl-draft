#!/usr/bin/env python3
"""FPL napló: heti jegyzet + watchlist, önmagát publikáló artifactként.

Miért külön lap: a `secret.html`-t a generátor minden futásnál újraírja, tehát
oda beírt jegyzet elveszne. Ez a lap viszont a saját állapotát a HTML-jébe
mentve publikálja újra magát (artifact capability), így a jegyzet ott marad,
és a következő generálás előtt visszaolvasható:

    Artifact action=read <url>  ->  a <script id="st"> tartalma  ->  journal_state.json
    python3 render_journal.py --state journal_state.json

A keret az API-ból jön (my_fpl.json), a becslések a proj-snapshotból.
"""
import argparse, datetime as _dt, json, pathlib, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=str(HERE / "naplo.html"))
ap.add_argument("--state", default=str(HERE / "journal_state.json"),
                help="a lapról visszaolvasott állapot; ha nincs, üresen indul")
A = ap.parse_args()

# ---------- adat ----------
MY = json.loads((HERE / "my_fpl.json").read_text(encoding="utf-8"))

def _newest(*dirs):
    c = [p for d in dirs for p in (HERE / d).glob("*.json")]
    if not c: return None
    def w(p):
        t = json.loads(p.read_text(encoding="utf-8"))["taken_at"].replace("Z", "+00:00")
        x = _dt.datetime.fromisoformat(t)
        return x if x.tzinfo else x.replace(tzinfo=_dt.timezone.utc)
    return sorted(c, key=w)[-1]

snap = _newest("proj", "proj_private")
if not snap: raise SystemExit("nincs projekció-snapshot")
S = json.loads(snap.read_text(encoding="utf-8"))

mn = json.loads((HERE / "fpl_bootstrap_cache.json").read_text(encoding="utf-8")) \
     if (HERE / "fpl_bootstrap_cache.json").exists() else None
if mn is None:
    import urllib.request
    mn = json.loads(urllib.request.urlopen(
        "https://fantasy.premierleague.com/api/bootstrap-static/", timeout=30).read())
TEAM = {t["id"]: t["short_name"] for t in mn["teams"]}
PT = {p["id"]: p["singular_name_short"] for p in mn["element_types"]}

# ellenfél fordulónként (fő FPL fixtures)
import urllib.request
FIX = json.loads(urllib.request.urlopen(
    "https://fantasy.premierleague.com/api/fixtures/", timeout=30).read())
OPP = {}
for f in FIX:
    if f["event"] is None: continue
    g = str(f["event"])
    OPP.setdefault(f["team_h"], {})[g] = (TEAM[f["team_a"]].upper(), 1)
    OPP.setdefault(f["team_a"], {})[g] = (TEAM[f["team_h"]].lower(), 0)

GW_FROM, GW_TO = S["gw_from"], S["gw_to"]
GWS = list(range(GW_FROM, GW_TO + 1))
SRCS = [{"slug": k, "label": v["label"], "note": v.get("note", "")}
        for k, v in S["sources"].items() if k in S["data"]]
ORDER = [s for s in SRCS if s["slug"] == "ffhub"] + [s for s in SRCS if s["slug"] != "ffhub"]

# A snapshot DRAFT element_id-vel van kulcsolva (fetch_projections.py: tbl[draft_id]),
# a bootstrap viszont MAIN id-t ad. 24 id más játékost jelöl a két térben — leképezés
# nélkül Tzolis (main 557) a draft-557-es Penders nulláit kapná.
idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
M2D = {int(k): v for k, v in idmap["main_to_draft"].items()}

pool = []
for e in mn["elements"]:
    did = M2D.get(e["id"])
    if did is None: continue
    eid = str(did)
    per = {}
    for s in ORDER:
        d = S["data"][s["slug"]].get(eid)
        if d: per[s["slug"]] = {g: round(v["pts"], 2) for g, v in d.items() if v.get("pts") is not None}
    if not per: continue
    pool.append({
        "id": e["id"], "n": e["web_name"], "club": TEAM[e["team"]],
        "pos": PT[e["element_type"]], "price": e["now_cost"] / 10,
        "own": float(e["selected_by_percent"]), "st": e["status"],
        "news": (e.get("news") or "")[:120],
        "fx": {g: list(v) for g, v in (OPP.get(e["team"]) or {}).items()
               if GW_FROM <= int(g) <= GW_TO},
        "p": per,
    })
POOL_IDS = {p["id"] for p in pool}
# az id-csapda őrszeme: a 24 eltérő id egyikén se legyen csendes nulla
_probe = {p["n"]: p for p in pool if p["n"] in ("Tzolis", "Haaland", "B.Fernandes")}
for _n, _p in _probe.items():
    _v = [v for src in _p["p"].values() for v in src.values()]
    if _v and max(_v) == 0:
        raise SystemExit(f"{_n} minden becslése 0 — az id-leképezés elromlott")
print("  id-ellenőrzés: " + " · ".join(
    f'{n}={max(v for src in x["p"].values() for v in src.values()):.1f}'
    for n, x in _probe.items()))

# a saját keret fordulónként (lezárt fordulókra tényleges)
squads = {}
for gw, d in MY["gws"].items():
    squads[gw] = {
        "chip": d["chip"], "points": d["points"], "bench_points": d["bench_points"],
        "rank": d["overall_rank"], "transfers": d["transfers"],
        "cost": d["transfer_cost"], "bank": d["bank"], "value": d["value"],
        "xi": [{"id": x["id"], "cap": x["cap"], "vice": x["vice"]} for x in d["xi"]],
        "bench": [{"id": x["id"]} for x in d["bench"]],
    }
LAST_SQUAD = max(squads, key=int) if squads else None

# a cheat sheet minősítése — kontextus a watchlisthez
CS = {}
for f in sorted((HERE / "cheatsheet").glob("gw*_fran.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    for r in d["players"]:
        if r.get("eid"): CS[r["eid"]] = {"rate": r["rate"], "gw": d.get("gw")}

DATA = {
    "team": MY["team_name"], "manager": MY["manager"],
    "total": MY["total_points"], "rank": MY["overall_rank"],
    "current": MY["current_event"], "chips": MY["chips_used"],
    "history": MY["history"], "apitransfers": MY["transfers"],
    "gws": GWS, "gw_from": GW_FROM, "gw_to": GW_TO,
    "taken_at": S["taken_at"], "srcs": ORDER,
    "squads": squads, "last_squad": LAST_SQUAD,
    "pool": pool, "cs": CS,
}

state = {"v": 1, "updated": None, "rounds": {}}
sp = pathlib.Path(A.state)
if sp.exists():
    try:
        loaded = json.loads(sp.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and "rounds" in loaded: state = loaded
        else: print(f"  {sp.name}: nem napló-állapot, kihagyva")
    except json.JSONDecodeError as e:
        raise SystemExit(f"{sp.name} nem olvasható JSON: {e}")

def j(o):
    """JSON <script>-be: a < jelet escape-eljük, hogy a blokk ne záruljon le."""
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

CSS = (HERE / "journal.css").read_text(encoding="utf-8")
APP = (HERE / "journal.js").read_text(encoding="utf-8")

HTML = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,200..800&family=DM+Mono:wght@400;500&display=swap">
<title>FPL napló</title>
<style id="css">__CSS__</style>
<script id="pool" type="application/json">__DATA__</script>
<script id="st" type="application/json">__STATE__</script>
<div id="root"></div>
<script id="app">__APP__</script>
"""
out = (HTML.replace("__CSS__", CSS).replace("__DATA__", j(DATA))
           .replace("__STATE__", j(state)).replace("__APP__", APP))
p = pathlib.Path(A.out)
p.write_text(out, encoding="utf-8")
print(f'{p}: {len(out.encode()):,} bájt · {len(pool)} játékos · forduló {GW_FROM}–{GW_TO} · '
      f'keret: {", ".join(sorted(squads, key=int)) or "nincs"} · '
      f'jegyzet: {len(state["rounds"])} forduló'.replace(",", " "))

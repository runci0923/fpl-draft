#!/usr/bin/env python3
"""Fordulónkénti projekciós pontok több forrásból, DRAFT element_id-ra kötve.

Snapshot-elvű: minden futás külön fájlba megy időbélyeggel (proj/YYYY-MM-DDTHH-MM_<gw>.json).
A deadline előtti utolsó snapshot lesz a kanonikus — ez az, amit egy manager látott dönteni.

Források:
  fplform   — fplform.com POST-export. Fordulónkénti xFPL + kezdés-valószínűség. Ingyenes.
  official  — a fő FPL API `ep_next` mezője. Ingyenes, de szezon előtt lapos placeholder.

Használat:  fetch_projections.py [--gw N] [--horizon 5]
"""
import argparse, csv, io, json, pathlib, subprocess, sys, datetime as dt

HERE = pathlib.Path(__file__).parent
OUT = HERE / "proj"; OUT.mkdir(exist_ok=True)              # publikus források (verziókövetve)
PRIV = HERE / "proj_private"; PRIV.mkdir(exist_ok=True)    # fizetős források is (git-ignorálva)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

def curl(args):
    r = subprocess.run(["curl", "-s", "-A", UA, *args], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {args[-1]}")
    return r.stdout

ap = argparse.ArgumentParser()
ap.add_argument("--gw", type=int, help="melyik fordulótól (alap: a következő)")
ap.add_argument("--horizon", type=int, default=5, help="hány fordulóra előre")
a = ap.parse_args()

idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
MAIN2DRAFT = {int(k): v for k, v in idmap["main_to_draft"].items()}

game = json.loads(curl(["https://draft.premierleague.com/api/game"]))
gw = a.gw or game["next_event"] or 1
last = min(38, gw + a.horizon - 1)
# UTC MINDENHOL: a gép CEST, a CI-runner UTC — naiv időbélyeggel a fájlnév-rendezés
# a régebbi snapshotot hinné frissebbnek.
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")

sources, notes = {}, {}

# ---------------------------------------------------------------- FPL Form
raw = curl(["-X", "POST", "-d", f"firstgw={gw}&lastgw={last}&all=1",
            "https://fplform.com/export-fpl-form-data"]).decode("utf-8", "replace")
rows = list(csv.DictReader(io.StringIO(raw)))
if not rows or "ID" not in rows[0]:
    sys.exit("fplform: váratlan válasz — megváltozhatott az űrlap")
ff, ff_skip = {}, 0
for r in rows:
    d = MAIN2DRAFT.get(int(r["ID"]))
    if d is None: ff_skip += 1; continue
    per = {}
    for g in range(gw, last + 1):
        n = g - gw + 1
        if f"{n}_with_prob" in r and r[f"{n}_with_prob"]:
            per[str(g)] = {"pts": round(float(r[f"{n}_with_prob"]), 3),
                           "raw": round(float(r[f"{n}_pts_no_prob"]), 3),
                           "start_prob": round(float(r[f"{n}_prob"]), 3)}
    ff[str(d)] = per
sources["fplform"] = ff
notes["fplform"] = {"label": "FPL Form", "url": "https://fplform.com/fpl-predicted-points",
                    "players": len(ff), "skipped": ff_skip,
                    "note": "xFPL kezdés-valószínűséggel súlyozva; `raw` a súlyozás nélküli"}

# ------------------------------------------------------- Fantasy Football Hub (PRO)
# FIZETŐS ADAT: a tulaj PRO-előfizetéséből, Chrome-mal lehúzva (public-api…/league/players,
# `after` kurzoros lapozás, bearer a /auth/access-token-ből). A gyűjtés NEM automatizálható,
# mert bejelentkezés kell hozzá -> a repóban egy pillanatkép él a ffhub/ mappában.
# `private: True` -> a publikus build KIHAGYJA. Nem adjuk tovább, amit ő fizet.
ffh = HERE / "ffhub" / "ffhub_raw.json"
if ffh.exists():
    raw = json.loads(ffh.read_text(encoding="utf-8"))
    hub, skip = {}, 0
    for p in raw["players"]:
        d = MAIN2DRAFT.get(p["fpl"])
        if d is None: skip += 1; continue
        per = {}
        for g in p["gw"]:
            if g["pts"] is None or not (gw <= g["g"] <= last): continue
            per[str(g["g"])] = {"pts": round(g["pts"], 3),
                                "mins": g["min"], "likelihood": g["lk"],
                                "goals": round(g["gls"] or 0, 3),
                                "assists": round(g["ast"] or 0, 3)}
        if per: hub[str(d)] = per
    sources["ffhub"] = hub
    notes["ffhub"] = {"label": "Fantasy Football Hub", "url": "https://www.fantasyfootballhub.co.uk/predictions",
                      "players": len(hub), "skipped": skip, "private": False,
                      "snapshot": raw["taken_at"],
                      "note": "PRO-előfizetés saját modellje; fordulónkénti pont, várható perc, "
                              "gól- és gólpassz-becslés. Fizetős adat — a tulaj döntése alapján "
                              "MEHET a nyílt oldalra (2026-08-19)"}
else:
    print("  (ffhub/ffhub_raw.json nincs meg — FPL Hub forrás kihagyva)")

# ----------------------------------------------------------------- Solio
# Bejelentkezés-köteles, canvas-rácsból olvasva -> kézi pillanatkép a solio/ mappában.
sol = HERE / "solio" / "solio.json"
if sol.exists():
    raw = json.loads(sol.read_text(encoding="utf-8"))
    tbl = {}
    for p in raw["players"]:
        per = {}
        for i, v in enumerate(p["gw"]):
            g = raw["gw_from"] + i
            if v is not None and gw <= g <= last: per[str(g)] = {"pts": round(v, 3)}
        if per: tbl[str(p["draft_id"])] = per
    sources["solio"] = tbl
    notes["solio"] = {"label": "Solio", "url": "https://fpl.solioanalytics.com/",
                      "players": len(tbl), "private": True,
                      "note": "fordulónkénti becslés; bejelentkezés-köteles, "
                              "canvas-rácsból olvasva -> kézi pillanatkép. " + raw["coverage_note"]}
else:
    print("  (solio/solio.json nincs meg — Solio forrás kihagyva)")

def write(path, srcs):
    payload = {"taken_at": now.isoformat().replace("+00:00", "Z"),
               "gw_from": gw, "gw_to": last, "deadline_gw": game["next_event"],
               "sources": {k: notes[k] for k in srcs}, "data": {k: sources[k] for k in srcs}}
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# private=True forrás nem kerül a verziókövetett proj/-ba (most: csak a Solio).
# Az FPL Hub a tulaj döntése szerint publikus -> hogy a CI-újraépítés se veszítse el,
# a committolt snapshotban is benne kell lennie.
pubsrc = [k for k in sources if not notes[k].get("private")]
privsrc = list(sources)
f = OUT / f"{stamp}_gw{gw}.json"
write(f, pubsrc)
if len(privsrc) > len(pubsrc):
    write(PRIV / f"{stamp}_gw{gw}.json", privsrc)

# --- nyesés: fordulónként a 3 legfrissebb marad a munkakönyvtárban.
# Nem veszik el semmi: a git-történet a törölt snapshotokat is megőrzi
# (`git log --diff-filter=D --name-only -- proj/`). A deadline előtti utolsó
# mindig benne van, mert a forduló váltásakor új gw-csoport indul.
KEEP = 3
pruned = 0
for d in (OUT, PRIV):
    groups = {}
    for p in d.glob("*_gw*.json"):
        groups.setdefault(p.name.split("_gw")[-1], []).append(p)
    for _, ps in groups.items():
        for p in sorted(ps)[:-KEEP]:
            p.unlink(); pruned += 1

print(f"Snapshot: {f.name}   GW{gw}–{last}" + (f"   (nyesve {pruned} régi)" if pruned else ""))
for k, n in notes.items():
    print(f"  {n['label']:<24} {n['players']:>3} játékos" +
          (f", {n['skipped']} kihagyva" if n.get("skipped") else "") + f"   — {n['note']}")
draft_bs = json.loads(curl(["https://draft.premierleague.com/api/bootstrap-static"]))
NAME = {x["id"]: x["web_name"] for x in draft_bs["elements"]}
print(f"\nGW{gw} legmagasabb projekció (FPL Form):")
best = sorted(ff.items(), key=lambda kv: -(kv[1].get(str(gw), {}).get("pts") or 0))[:8]
for did, per in best:
    p = per[str(gw)]
    print(f"   {NAME[int(did)]:<16} {p['pts']:>5}  (nyers {p['raw']}, kezdés {int(p['start_prob']*100)}%)")

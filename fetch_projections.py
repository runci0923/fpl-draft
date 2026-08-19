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
OUT = HERE / "proj"; OUT.mkdir(exist_ok=True)
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
stamp = dt.datetime.now().replace(microsecond=0).isoformat().replace(":", "-")

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

# ---------------------------------------------------------------- FPL official ep_next
mn = json.loads(curl(["https://fantasy.premierleague.com/api/bootstrap-static/"]))
off, flat = {}, {}
for e in mn["elements"]:
    d = MAIN2DRAFT.get(e["id"])
    if d is None or e.get("ep_next") in (None, ""): continue
    v = float(e["ep_next"])
    off[str(d)] = {str(gw): {"pts": v}}
    flat[v] = flat.get(v, 0) + 1
top = sorted(flat.items(), key=lambda kv: -kv[1])[:3]
sources["official"] = off
notes["official"] = {"label": "FPL hivatalos (ep_next)",
                     "url": "https://fantasy.premierleague.com/api/bootstrap-static/",
                     "players": len(off), "only_gw": gw,
                     "note": "csak a KÖVETKEZŐ fordulóra ad értéket; szezon előtt lapos "
                             f"(a leggyakoribb értékek: {', '.join(f'{v}={n}x' for v, n in top)})"}

payload = {"taken_at": dt.datetime.now().replace(microsecond=0).isoformat(),
           "gw_from": gw, "gw_to": last, "deadline_gw": game["next_event"],
           "sources": notes, "data": sources}
f = OUT / f"{stamp}_gw{gw}.json"
f.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

print(f"Snapshot: {f.name}   GW{gw}–{last}")
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

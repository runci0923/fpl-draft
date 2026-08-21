#!/usr/bin/env python3
"""rosters.json — olvashatóan diffelhető keret-napló.

A draftban folyamatos a waiver/trade. Publikus tranzakció-végpont NINCS (404), de az
`element-status` mindig az AKTUÁLIS birtoklást adja. Ezt szépen formázva commitolva
a git-történet lesz az átigazolás-napló:  `git log -p rosters.json`

Csak keresztnév és játékosnév kerül bele — nyílt repóba mehet.
"""
import json, pathlib, subprocess, sys, datetime as dt

HERE = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

def api(u):
    r = subprocess.run(["curl", "-s", "-A", UA, u], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {u}")
    return json.loads(r.stdout)

d = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
P = d["players"]
bs = api("https://draft.premierleague.com/api/bootstrap-static")
NAME = {x["id"]: x["web_name"] for x in bs["elements"]}
CLUB = {t["id"]: t["short_name"] for t in bs["teams"]}
INFO = {x["id"]: (x["web_name"], CLUB[x["team"]],
                  {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}[x["element_type"]])
        for x in bs["elements"]}

POS = ["GKP", "DEF", "MID", "FWD"]
out = {"_doc": "Aktuális keretek. A git-történet ennek a fájlnak a diffje = átigazolás-napló.",
       "taken_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
                     .isoformat().replace("+00:00", "Z"),
       "rosters": {}}
for m in sorted(d["managers"], key=lambda m: m.get("slot", 999)):
    byp = {p: [] for p in POS}
    for s in sorted(m["squad"], key=lambda s: (s["pick"] is None, s["pick"] or 0)):
        n, c, p = INFO[s["id"]]
        # waiverrel szerzett játékosnak nincs pickje — ez a diffben rögtön látszik
        how = f"pick {s['pick']}" if s.get("pick") else "waiver"
        byp[p].append(f"{n} ({c}) · {how}")
    out["rosters"][m["first"]] = byp

(HERE / "rosters.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                   encoding="utf-8")
n = sum(len(v) for r in out["rosters"].values() for v in r.values())
print(f"rosters.json: {len(out['rosters'])} keret, {n} játékos — soronként egy, diffelhető")

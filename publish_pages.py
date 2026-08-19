#!/usr/bin/env python3
"""Publikus GitHub Pages build: keresztnevek, csapatnevek nélkül.

A privát artifact a teljes nevekkel megy tovább (index.html, git-ignorálva);
ez a szkript külön `docs/` mappába dolgozik, azt szolgálja ki a Pages.

A szivárgás-ellenőrzés listáját FUTÁSIDŐBEN a privát data.json-ból származtatjuk,
hogy egyetlen családnév vagy csapatnév se kerüljön magába a szkriptbe sem.
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
SITE = HERE / "docs"; SITE.mkdir(exist_ok=True)

d = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

# amit tilos kiengedni: családnevek + csapatnevek + a liga neve
forbidden = set()
for m in d["managers"]:
    forbidden.update(t for t in m["name"].split() if t != m["first"])
    if m.get("team"): forbidden.add(m["team"])
forbidden.add(d["league"]["name"])
forbidden = {x for x in forbidden if len(x) > 2}

for m in d["managers"]:
    m["name"] = m["first"]      # csak keresztnév
    m["team"] = ""              # csapatnév nem kerül nyílt webre
d["league"] = {**d["league"], "name": "Draft-liga"}

h2h = json.loads((HERE / "h2h.json").read_text(encoding="utf-8"))
h2h["league"] = {**h2h["league"], "name": "Draft-liga"}
# Melyik forrás mehet a NYÍLT webre. A tulaj döntése (2026-08-19): mindkettő.
# Mindkettő előfizetéses termék adata -> az ő előfizetői szerződései a felelősség;
# egy név kivételével visszavehető.
PUBLIC_SOURCES = {"ffhub", "solio"}
private = {k for k in h2h.get("sources", {}) if k not in PUBLIC_SOURCES}
for k in private:
    h2h["sources"].pop(k, None)
    for r in h2h.get("rounds", {}).values(): r.pop(k, None)
if private: print(f"  privát forrás kizárva a publikus buildből: {', '.join(sorted(private))}")
(SITE / "h2h.public.json").write_text(json.dumps(h2h, ensure_ascii=False, separators=(",", ":")),
                                      encoding="utf-8")

pub = SITE / "data.public.json"
pub.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
# a landing a FORDULÓ-oldal (azt nézi hetente), a draft-elemzés a draft.html
subprocess.run([sys.executable, str(HERE / "render.py"),
                "--data", str(pub), "--out", str(SITE / "draft.html"),
                "--title", "FPL Draft Scorecard", "--gw-href", "index.html"], check=True)
subprocess.run([sys.executable, str(HERE / "render_gw.py"),
                "--data", str(pub), "--h2h", str(SITE / "h2h.public.json"),
                "--out", str(SITE / "index.html"),
                "--title", "FPL Draft — a forduló", "--draft-href", "draft.html"], check=True)
(SITE / ".nojekyll").write_text("", encoding="utf-8")

for page in ("index.html", "draft.html"):
    html = (SITE / page).read_text(encoding="utf-8")
    leak = sorted(x for x in forbidden if x in html)
    if leak:
        sys.exit(f"HIBA: azonosító adat maradt a(z) docs/{page}-ben ({len(leak)} db)")
    print(f"docs/{page} kész ({len(html)} bájt) — tiszta")
print(f"{len(forbidden)} tiltott kifejezés ellenőrizve mindkét lapon")

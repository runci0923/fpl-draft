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

pub = SITE / "data.public.json"
pub.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
subprocess.run([sys.executable, str(HERE / "render.py"),
                "--data", str(pub), "--out", str(SITE / "index.html"),
                "--title", "FPL Draft Scorecard"], check=True)
(SITE / ".nojekyll").write_text("", encoding="utf-8")

html = (SITE / "index.html").read_text(encoding="utf-8")
leak = sorted(x for x in forbidden if x in html)
if leak:
    sys.exit(f"HIBA: azonosító adat maradt a publikus buildben ({len(leak)} db)")
print(f"docs/index.html kész ({len(html)} bájt) — {len(forbidden)} tiltott kifejezés ellenőrizve, egy sem szivárgott")

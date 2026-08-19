#!/usr/bin/env python3
"""solio/raw.txt -> solio/solio.json  (fordulónkénti becslés, GW1-5)

A Solio rácsa CANVASRA rajzol (Glide Data Grid), az adat pedig helyi IndexedDB-ben ül
(Rocicorp Zero). A tárolót nem olvassuk; ehelyett a rács akadálymentességi tükör-tábláját
olvassuk ki — az CSAK akkor jön létre, ha az akadálymentességi fa aktív, és CSAK valódi
görgetésre frissül (programozott scrollTop és szintetikus wheel nem hat rá).
Ezért a gyűjtés kézi lépés, mint az FPL Hubnál.
"""
import csv, json, pathlib, subprocess, unicodedata

HERE = pathlib.Path(__file__).parent
rows = []
for line in (HERE / "solio" / "raw.txt").read_text(encoding="utf-8").splitlines():
    p = line.strip().split("|")
    if len(p) != 7: continue
    rows.append({"n": p[0], "price": float(p[1]),
                 "gw": [None if x == "" else float(x) for x in p[2:]]})

def norm(s):
    s = (s or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i")]: s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())

pool = list(csv.DictReader((HERE / "sources" / "_players.csv").open(encoding="utf-8")))
# ár a draft bootstrapból: a névütközéseket ez oldja fel (a Solio ad árat)
bs = json.loads(subprocess.run(["curl","-s","https://draft.premierleague.com/api/bootstrap-static"],
                               capture_output=True).stdout)
PRICE = {x["id"]: None for x in bs["elements"]}
for x in bs["elements"]:
    # a Draft játékban nincs ár; a fő FPL-ből jön -> idmap-en át
    pass
idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
D2M = {int(k): v for k, v in idmap["draft_to_main"].items()}
mn = json.loads(subprocess.run(["curl","-s","https://fantasy.premierleague.com/api/bootstrap-static/"],
                               capture_output=True).stdout)
MPRICE = {x["id"]: x["now_cost"]/10 for x in mn["elements"]}
PRICE = {d: MPRICE.get(m) for d, m in D2M.items()}
drafted = set()
dj = HERE / "data.json"
if dj.exists():
    dd = json.loads(dj.read_text(encoding="utf-8"))
    drafted = {s["id"] for m in dd["managers"] for s in m["squad"]}
# a Solio a web_name-et használja, ár nélkül nem mindig egyedi -> ár is szűr
out, miss, ambi = [], [], []
for r in rows:
    n = norm(r["n"])
    cand = [p for p in pool if norm(p["web_name"]) == n]
    if len(cand) > 1:
        # 1) ár egyezés (a Solio ad árat), 2) ha még mindig több: a draftolt nyer
        byprice = [p for p in cand
                   if PRICE.get(int(p["element_id"])) is not None
                   and abs(PRICE[int(p["element_id"])] - r["price"]) < 0.05]
        if len(byprice) == 1:
            cand = byprice
        else:
            base = byprice or cand
            pref = [p for p in base if int(p["element_id"]) in drafted]
            if len(pref) == 1:
                cand = pref
            else:
                # utolsó döntő: a hivatalos draft_rank (az ismertebb játékos előrébb van)
                cand = sorted(base, key=lambda p: int(p["official_draft_rank"]))[:1]
                ambi.append(f'{r["n"]}(£{r["price"]}) -> {cand[0]["web_name"]} '
                            f'{cand[0]["club"]} {cand[0]["pos"]} dr={cand[0]["official_draft_rank"]}')
    if len(cand) == 1:
        out.append({"draft_id": int(cand[0]["element_id"]), "web": cand[0]["web_name"],
                    "club": cand[0]["club"], "pos": cand[0]["pos"],
                    "price": r["price"], "gw": r["gw"]})
    else:
        miss.append(r["n"])

res = {"source": "fpl.solioanalytics.com — Projections",
       "note": "fordulónkénti becslés (GW1-5), teljes lebegőpontos pontossággal; "
               "canvas-rács akadálymentességi tükréből olvasva",
       "gw_from": 1, "horizon": 5, "coverage_note":
       f"{len(out)} játékos: a lista a legjobbtól ~1,3-es átlagig lefedve, "
       "a 90 draftolt mind benne. A lista alja (sub-1,3 átlag) nincs begyűjtve.",
       "players": out}
(HERE / "solio" / "solio.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")),
                                           encoding="utf-8")
print(f"{len(rows)} sor · {len(out)} párosítva · {len(miss)} kimaradt · {len(ambi)} névütközés")
if miss: print("  kimaradt:", ", ".join(miss[:14]))
if ambi: print("  ár sem oldotta fel:", ", ".join(ambi[:10]))

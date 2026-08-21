#!/usr/bin/env python3
"""sources/*.csv + league.json (+ squads.json a GW1 kezdő XI-hez) -> data.json

A pontozás a lapon (JS) fut, hogy forrást váltani újraszámolás nélkül lehessen.
Itt: összefűzés, konszenzus, forrás-egyezés, és a képernyőképek ellenőrzése az API ellen.
"""
import csv, json, pathlib, re, statistics, unicodedata

HERE = pathlib.Path(__file__).parent
SRC = HERE / "sources"

SOURCES = [
    ("consensus",    "Konszenzus",        "az öt forrás rangátlaga, újrarangsorolva",
     None),
    ("draftsociety", "The Draft Society", "Top 200, kézi szakértői sorrend, pozíciós szűkösséggel",
     "https://www.thedraftsociety.com/fpl-draft-rankings"),
    ("draftfantasy", "DraftFantasy",      "Top 240, szezon-xP és VORP („Edge”) alapján gépiesen",
     "https://www.draftfantasy.com/fpl/draft-cheat-sheet"),
    ("official",     "FPL hivatalos",     "mind az 595 játékos, a Draft-app saját sorrendje",
     "https://draft.premierleague.com/draft"),
    ("onefpl",       "OneFPL",            "Top 100, szerkesztői lista draft-indoklással",
     "https://onefpl.com/blog/fpl-draft-rankings-top-100-2026-27"),
    ("rotowire",     "RotoWire",          "Top 400+, napi frissítésű szezonrangsor",
     "https://www.rotowire.com/soccer/article/fantasy-premier-league-fpl-rankings-top-400-for-2026-27-season-124261"),
]
AB = {"draftsociety":"DS", "draftfantasy":"DF", "official":"FPL", "onefpl":"1FPL", "rotowire":"RW"}

# ------------------------------------------------------------------ rangsorok
players = {}
for r in csv.DictReader((SRC / "_players.csv").open(encoding="utf-8")):
    players[int(r["element_id"])] = {"id": int(r["element_id"]), "name": r["web_name"],
                                     "club": r["club"], "pos": r["pos"], "ranks": {}}
sizes = {}
real = [s for s, _, _, _ in SOURCES if s != "consensus"]
for slug in real:
    rows = list(csv.DictReader((SRC / f"{slug}.csv").open(encoding="utf-8")))
    sizes[slug] = len(rows)
    for r in rows:
        players[int(r["element_id"])]["ranks"][slug] = int(r["rank"])

scored = list(players.values())
for p in scored:
    got = [p["ranks"][s] for s in real if s in p["ranks"]]
    p["cover"], p["mean"] = len(got), round(statistics.fmean(got), 2)
    p["spread"] = (max(got) - min(got)) if len(got) > 1 else None
scored.sort(key=lambda p: (p["mean"], -p["cover"], p["ranks"]["official"]))
for i, p in enumerate(scored, 1):
    p["ranks"]["consensus"] = i
sizes["consensus"] = len(scored)

def spearman(xs, ys):
    n = len(xs)
    if n < 3: return None
    def rk(v):
        order = sorted(range(n), key=lambda i: v[i]); out = [0.0] * n; i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]: j += 1
            for k in range(i, j + 1): out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out
    rx, ry = rk(xs), rk(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** .5
    return round(num / den, 3) if den else None

agree = {}
for i, a in enumerate(real):
    for b in real[i + 1:]:
        common = [(p["ranks"][a], p["ranks"][b]) for p in scored if a in p["ranks"] and b in p["ranks"]]
        agree[f"{a}|{b}"] = {"rho": spearman([x for x, _ in common], [y for _, y in common]),
                             "n": len(common)}

# ------------------------------------------------------------------- a liga
lg = json.loads((HERE / "league.json").read_text(encoding="utf-8"))
owned = {int(k): v for k, v in lg["owned"].items()}
picks = {int(k): v for k, v in lg["picks"].items()}
ENT = {e["entry_id"]: e for e in lg["entries"]}

# --- GW1 kezdő XI a képernyőképekből (a deadline előtt az API nem adja: "No pick history")
def norm(s):
    s = (s or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i")]: s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())

shots = json.loads((HERE / "squads.json").read_text(encoding="utf-8"))
SHOT_TO_ENTRY = {"Attila": 106153, "Dominik": 106154, "David": 106155,
                 "Dani": 106156, "Norci": 106157, "Krisz": 106158}
xi, shot_ids, mismatch = {}, {}, []
for m in shots["managers"]:
    ent = SHOT_TO_ENTRY[m["name"]]
    ids = set()
    for pk in m["squad"]:
        n = norm(pk["n"])
        hit = [p for p in players.values() if p["club"] == pk["club"] and p["pos"] == pk["pos"]
               and (norm(p["name"]) == n or norm(p["name"]).endswith(n) or n.endswith(norm(p["name"])))]
        if len(hit) != 1:
            mismatch.append(f"{m['name']}: {pk['n']} ({len(hit)} találat)"); continue
        ids.add(hit[0]["id"]); xi[hit[0]["id"]] = pk["start"]
    shot_ids[ent] = ids
if mismatch: raise SystemExit("Feloldatlan képernyőkép-név: " + "; ".join(mismatch))

print("Képernyőkép vs. API keret-ellenőrzés:")
ok = True
for ent, ids in shot_ids.items():
    api = set(owned[ent])
    d1, d2 = ids - api, api - ids
    tag = "egyezik" if not (d1 or d2) else (
        f"KÜLÖNBSÉG  csak képen: {[players[i]['name'] for i in d1]}  csak API-n: {[players[i]['name'] for i in d2]}")
    ok &= not (d1 or d2)
    print(f"  {ENT[ent]['initials']} {ENT[ent]['name']:<20} {tag}")
print(f"  -> {'mind a 6 keret egyezik' if ok else 'eltérés van, az API az irány'}\n")

# A draft-slot a TÉNYLEGES draft-sorrendből jön, nem a jelenlegi keretből:
# waiver/csere után a keret első tagjának már nem feltétlenül van pickje.
slot = {}
for o in lg["order"]:
    slot.setdefault(o["entry"], o["index"])

managers = []
for ent, ids in owned.items():
    e = ENT[ent]
    sq = []
    for i in ids:
        pk = picks.get(i)          # waiverrel szerzett játékosnak NINCS pickje
        sq.append({"id": i, "start": xi.get(i, False),
                   "pick": pk["index"] if pk else None,
                   "round": pk["round"] if pk else None,
                   "via": "draft" if pk else "waiver"})
    sq.sort(key=lambda s: (s["pick"] is None, s["pick"] or 0))
    managers.append({
        "entry": ent, "name": e["name"], "first": e["first"], "team": e["team"],
        "initials": e["initials"], "slot": slot.get(ent, 999),
        "squad": sq,
    })
managers.sort(key=lambda m: m["slot"])

waivers = [(m["first"], [q["id"] for q in m["squad"] if q["via"] == "waiver"])
           for m in managers]
waivers = [(n, v) for n, v in waivers if v]
if waivers:
    print("Draft utáni szerzés (nincs pickjük):")
    for n, v in waivers:
        print(f"  {n}: " + ", ".join(players[i]["name"] for i in v))
    print()

# --- a tulaj saját vonal-értékelése (a lapon alapértékként jelenik meg)
mr = json.loads((HERE / "my_rating.json").read_text(encoding="utf-8"))
INIT = {e["initials"]: e["entry_id"] for e in lg["entries"]}
if [INIT[x] for x in mr["order"]] != [m["entry"] for m in sorted(managers, key=lambda m: m["squad"][0]["pick"])]:
    raise SystemExit("A my_rating.json 'order' nem a draft-sorrend — a számjegyek elcsúsznának")
my_rating = {f'{ent}|{pos}': v for pos, d in mr["ratings"].items() for ent, v in d.items()}
print(f"Saját értékelés betöltve ({mr['date']}, {len(my_rating)}/24 vonal):")
for pos in ("GKP", "DEF", "MID", "FWD"):
    print(f"  {pos}  " + "  ".join(f"{ENT[INIT[i]]['first']}:{mr['ratings'][pos][str(INIT[i])]}"
                                   for i in mr["order"]))
tot = {i: sum(mr["ratings"][p][str(INIT[i])] for p in mr["ratings"]) for i in mr["order"]}
print("  összesen: " + "  ".join(f"{ENT[INIT[i]]['first']}={tot[i]}"
                                 for i in sorted(tot, key=lambda x: -tot[x])) + "\n")

used = set(owned_id for v in owned.values() for owned_id in v)

# --- fedés: a 90 draftolt közül hányat rangsorol egyáltalán a forrás
cover = {s: sum(1 for i in used if s in players[i]["ranks"]) for s, _, _, _ in SOURCES}

data = {
    "league": lg["league"],
    "sources": [{"slug": s, "label": l, "note": n, "size": sizes[s], "ab": AB.get(s, "KONS"),
                 "covers": cover[s], "of": len(used), "url": u}
                for s, l, n, u in SOURCES],
    "managers": managers,
    "players": {str(p["id"]): {"n": p["name"], "c": p["club"], "p": p["pos"], "r": p["ranks"],
                               "cv": p["cover"], "m": p["mean"], "sp": p["spread"],
                               "pk": picks.get(p["id"], {}).get("index"),
                               "rd": picks.get(p["id"], {}).get("round")}
                for p in scored
                if p["id"] in used or min(p["ranks"].values()) <= 300},
    "agreement": agree,
    "my_rating": my_rating,
    "order": lg["order"],
}
(HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

print("Források (készlet / a 90 draftoltból fedve):")
for s, l, _, _ in SOURCES:
    print(f"  {AB.get(s,'KONS'):>4} {l:<20} {sizes[s]:>4} játékos   fedés {cover[s]:>2}/90"
          + ("   ← a többi büntetőpontot kap" if cover[s] < 80 else ""))
print(f"Lapra kerül: {len(data['players'])} játékos\n")
print(f"{'Manager':<20} {'1. pick':>7}   " + "  ".join(f"{AB.get(s,'KONS'):>5}" for s, _, _, _ in SOURCES))
for m in managers:
    line = []
    for s, _, _, _ in SOURCES:
        line.append(f"{sum(players[q['id']]['ranks'].get(s, sizes[s] + 1) for q in m['squad']):>5}")
    print(f"{m['name']:<20} {m['slot']:>7}   " + "  ".join(line))

# CSAK a draftolt játékosokra értelmes: a waiverrel szerzettnek nincs pick-sorszáma
print("\nLegnagyobb lopások (pick-sorszám mínusz konszenzus-rang):")
sur = sorted(((players[i]["ranks"]["consensus"], picks[i]["index"], i)
              for i in used if i in picks),
             key=lambda t: -(t[1] - t[0]))
for r, pk, i in sur[:6]:
    who = next(m["name"] for m in managers if any(q["id"] == i for q in m["squad"]))
    print(f"  {players[i]['name']:<16} kons #{r:<4} pick {pk:<3} = +{pk - r:<4} {who}")
print("Legnagyobb túlnyúlások:")
for r, pk, i in sur[-6:][::-1]:
    who = next(m["name"] for m in managers if any(q["id"] == i for q in m["squad"]))
    print(f"  {players[i]['name']:<16} kons #{r:<4} pick {pk:<3} = {pk - r:<5} {who}")

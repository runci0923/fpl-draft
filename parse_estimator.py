#!/usr/bin/env python3
"""estimator/raw.txt -> estimator/estimator.json  (5 fordulós xPts-összeg)

Az fplestimator xPts-e KLIENS OLDALON számolódik: nincs szerveren kész becslés
(a Supabase-ben a players/fixtures/events anon-olvasható, de a player_gameweek_stats
és a player_xpts_snapshot RLS-zárt, a get_xpts_snapshots_range RPC pedig üres).
Ezért a /best-picks tábláját olvassuk ki, ami 5 fordulós ÖSSZEGET ad, nem per-fordulót.
"""
import json, pathlib, re, unicodedata

HERE = pathlib.Path(__file__).parent
raw = (HERE / "estimator" / "raw.txt").read_text(encoding="utf-8")

STATUS = re.compile(r"(Injured|Doubtful|Suspended|Unavailable)$")

def clean_name(n):
    n = STATUS.sub("", n).strip()
    # a lap két változatban rendereli a nevet (mobil+desktop) -> duplikálódik
    for _ in range(3):
        L = len(n)
        if L % 2 == 0 and n[:L//2] == n[L//2:]:
            n = n[:L//2]; continue
        # a "RRogersRogers" alak: az utolsó fél ismétlődik elöl is
        m = re.match(r"^(.+?)\1$", n)
        if m: n = m.group(1); continue
        break
    # "RRogers" -> "Rogers" (duplázott kezdőbetű)
    if len(n) > 2 and n[0] == n[1] and n[1].isupper(): n = n[1:]
    return n.strip()

rows = []
for tok in raw.replace("\n", "~").split("~"):
    tok = tok.strip()
    if not tok: continue
    p = tok.split("|")
    if len(p) != 6: continue
    rows.append({"rank": int(p[0]), "n": clean_name(p[1]), "club": p[2],
                 "pos": p[3], "xpts5": float(p[4]), "price": float(p[5])})

CLUB = {"Man City":"MCI","Man Utd":"MUN","Nott'm Forest":"NFO","Spurs":"TOT","Newcastle":"NEW",
        "Brighton":"BHA","Crystal Palace":"CRY","Aston Villa":"AVL","Bournemouth":"BOU",
        "Brentford":"BRE","Chelsea":"CHE","Arsenal":"ARS","Liverpool":"LIV","Everton":"EVE",
        "Fulham":"FUL","Leeds":"LEE","Sunderland":"SUN","Coventry City":"COV","Hull City":"HUL",
        "Ipswich Town":"IPS","Hull":"HUL","Ipswich":"IPS"}

def norm(s):
    s = (s or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i")]: s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())

players = json.loads((HERE / "sources" / "_players.csv").read_text(encoding="utf-8")) \
    if False else None
import csv
pool = list(csv.DictReader((HERE / "sources" / "_players.csv").open(encoding="utf-8")))
out, miss = [], []
for r in rows:
    club = CLUB.get(r["club"])
    n = norm(r["n"])
    cand = [p for p in pool if p["club"] == club and p["pos"] == r["pos"]
            and (norm(p["web_name"]) == n or norm(p["web_name"]).endswith(n)
                 or n.endswith(norm(p["web_name"])) or norm(p["second_name"]) == n)]
    if len(cand) == 1:
        out.append({**r, "draft_id": int(cand[0]["element_id"]), "web": cand[0]["web_name"]})
    else:
        miss.append(f'{r["rank"]}. {r["n"]} ({r["club"]}/{r["pos"]}) -> {len(cand)}')

res = {"source": "fplestimator.com /best-picks",
       "note": "5 fordulós xPts-ÖSSZEG (GW1-5), nem per-forduló — a lap kliens oldalon számolja",
       "horizon": 5, "players": out}
(HERE / "estimator" / "estimator.json").write_text(
    json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"{len(rows)} sor beolvasva, {len(out)} párosítva, {len(miss)} kimaradt")
for m in miss[:12]: print("   ", m)

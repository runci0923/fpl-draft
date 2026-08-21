#!/usr/bin/env python3
"""Öt draft-rangsor letöltése és FPL element_id-ra kötése.

Kimenet: sources/<slug>.csv  (element_id, rank, name, club, pos)
         sources/_players.csv (FPL játékos-törzs)
"""
import csv, difflib, html, json, pathlib, re, subprocess, sys, unicodedata

HERE = pathlib.Path(__file__).parent
OUT = HERE / "sources"; OUT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
BS = "https://draft.premierleague.com/api/bootstrap-static"

def get(url, binary=False):
    r = subprocess.run(["curl", "-sL", "-A", UA, url], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {url}")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")

def norm(s):
    s = (s or "").lower().strip()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ð","d"),("þ","th"),
                 ("ı","i"),("i̇","i"),("ħ","h"),("ŋ","n"),("œ","oe")]:
        s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())

def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

# ---------------------------------------------------------------- FPL törzs
bs = json.loads(get(BS))
SHORT = {t["id"]: t["short_name"] for t in bs["teams"]}
NAME  = {t["id"]: t["name"] for t in bs["teams"]}
PT = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}

CLUB = {}                              # normalizált klubnév/rövidítés -> short_name
for t in bs["teams"]:
    for alias in (t["short_name"], t["name"]):
        CLUB[norm(alias)] = t["short_name"]
CLUB.update({norm(k): v for k, v in {
    "man city": "MCI", "man utd": "MUN", "man united": "MUN", "manchester utd": "MUN",
    "nottm forest": "NFO", "nott'm forest": "NFO", "forest": "NFO", "spurs": "TOT",
    "tottenham": "TOT", "wolves": "WOL", "newcastle": "NEW", "brighton": "BHA",
    "west ham": "WHU", "leeds": "LEE", "leicester": "LEI", "palace": "CRY",
    "crystal palace": "CRY", "bournemouth": "BOU", "sunderland": "SUN",
    "coventry": "COV", "ipswich": "IPS", "hull": "HUL", "villa": "AVL",
    "aston villa": "AVL", "brentford": "BRE", "everton": "EVE", "fulham": "FUL",
    "chelsea": "CHE", "arsenal": "ARS", "liverpool": "LIV",
}.items()})

POSMAP = {"gk": "GKP", "gkp": "GKP", "g": "GKP", "goalkeeper": "GKP",
          "d": "DEF", "def": "DEF", "defender": "DEF",
          "m": "MID", "mid": "MID", "midfielder": "MID",
          "f": "FWD", "fw": "FWD", "fwd": "FWD", "forward": "FWD"}

players = []
for x in bs["elements"]:
    players.append({
        "id": x["id"], "web": x["web_name"], "first": x["first_name"], "second": x["second_name"],
        "club": SHORT[x["team"]], "pos": PT[x["element_type"]], "draft_rank": x["draft_rank"],
        "n_web": norm(x["web_name"]), "n_second": norm(x["second_name"]),
        "n_full": norm(x["first_name"] + x["second_name"]),
        "n_last": norm(x["second_name"].split()[-1]) if x["second_name"] else "",
    })
with (OUT / "_players.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["element_id","web_name","first_name","second_name","club","pos","official_draft_rank"])
    for p in players:
        w.writerow([p["id"], p["web"], p["first"], p["second"], p["club"], p["pos"], p["draft_rank"]])
print(f"FPL törzs: {len(players)} játékos")

STATUS = re.compile(r"\s+(Doubtful|Injured|Suspended|Unavailable|Out|Ineligible)$", re.I)

def variants(name):
    """A forrás-névből előálló alakok, a legszűkebbtől a legszélesebbig."""
    name = STATUS.sub("", name).strip()
    toks = [t for t in re.split(r"[\s.]+", name) if t]
    out = [norm(name)]                                  # teljes egybeírva
    if len(toks) > 1:
        out.append(norm(toks[-1]))                      # családnév
        out.append(norm(toks[0][0] + toks[-1]))         # B.Fernandes alak
        out.append(norm(" ".join(toks[1:])))            # keresztnév nélkül
    return [v for i, v in enumerate(out) if v and v not in out[:i]]

def match(name, club=None, pos=None):
    """Egyediség elve: klub+pozíció szűkítés, majd névalak-lépcső (Vikingo-szabály)."""
    club = CLUB.get(norm(club or ""))
    pos = POSMAP.get(norm(pos or ""))
    vs = variants(name)
    for use_club, use_pos in ((1,1),(1,0),(0,1),(0,0)):
        pool = [p for p in players
                if (not use_club or not club or p["club"] == club)
                and (not use_pos or not pos or p["pos"] == pos)]
        for v in vs:
            for key in ("n_web", "n_second", "n_last", "n_full"):
                hit = [p for p in pool if p[key] == v]
                if len(hit) == 1: return hit[0]
        for v in vs:
            hit = [p for p in pool if p["n_full"].endswith(v) or p["n_full"].startswith(v)]
            if len(hit) == 1: return hit[0]
    # utolsó lépcső: elírás-tűrő családnév, CSAK klub+pozíción belül
    if club and pos:
        pool = [p for p in players if p["club"] == club and p["pos"] == pos]
        near = difflib.get_close_matches(vs[-1], [p["n_last"] or p["n_web"] for p in pool], 1, 0.86)
        if near:
            hit = [p for p in pool if (p["n_last"] or p["n_web"]) == near[0]]
            if len(hit) == 1: return hit[0]
    return None

def write(slug, label, recs):
    """recs: (rank, name, club, pos)"""
    rows, miss = [], []
    for rank, name, club, pos in recs:
        p = match(name, club, pos)
        (rows.append([p["id"], rank, p["web"], p["club"], p["pos"]]) if p
         else miss.append(f"{rank}. {name} ({club}/{pos})"))
    with (OUT / f"{slug}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["element_id","rank","web_name","club","pos"]); w.writerows(rows)
    print(f"  {label:<24} {len(rows):>4} párosítva, {len(miss):>2} kimaradt" +
          (("  → " + "; ".join(miss[:6])) if miss else ""))
    return miss

def table_rows(h, pick=0):
    tbls = re.findall(r"<table.*?</table>", h, re.S)
    if not tbls: return []
    t = sorted(tbls, key=len)[-1] if pick == "big" else tbls[pick]
    out = []
    for r in re.findall(r"<tr.*?</tr>", t, re.S):
        out.append([strip_tags(c) for c in re.findall(r"<t[hd].*?</t[hd]>", r, re.S)])
    return out

def guarded(label, fn):
    """Egy forrás hibája NE döntse el az egész futást — a többi rangsor akkor is kell."""
    try:
        fn()
    except SystemExit as e:
        print(f"  {label:<24} KIMARAD: {e}")
    except Exception as e:
        print(f"  {label:<24} KIMARAD: {type(e).__name__}: {e}")

print("Rangsorok:")

# 1) Hivatalos FPL draft_rank (mind az 595)
write("official", "FPL official draft_rank",
      [(p["draft_rank"], p["web"], p["club"], p["pos"])
       for p in sorted(players, key=lambda p: p["draft_rank"])])

# 2) The Draft Society Top 200 (Google Sheet CSV)
def _ds():
    ds = list(csv.DictReader(get(
        "https://docs.google.com/spreadsheets/d/1xeZKNo9Z9WdcW1PlJiePTnGKM5ZCTxIRSCDUsHNnPDI/export?format=csv"
    ).splitlines()))
    got = [(int(r["Rank"]), r["Player"], r["Team"], r["Position"]) for r in ds if r.get("Rank")]
    if len(got) < 100: raise RuntimeError(f"csak {len(got)} sor")
    write("draftsociety", "The Draft Society 200", got)
guarded("The Draft Society 200", _ds)

# 3) OneFPL Top 100
def _onefpl():
    rows = table_rows(get("https://onefpl.com/blog/fpl-draft-rankings-top-100-2026-27"), "big")
    got = [(int(r[0]), r[1], r[2], r[3]) for r in rows if len(r) >= 4 and r[0].isdigit()]
    if len(got) < 50: raise RuntimeError(f"csak {len(got)} sor — megváltozott az oldal?")
    write("onefpl", "OneFPL 100", got)
guarded("OneFPL 100", _onefpl)

# 4) RotoWire Top 400
def _roto():
    rows = table_rows(get("https://www.rotowire.com/soccer/article/"
                          "fantasy-premier-league-fpl-rankings-top-400-for-2026-27-season-124261"), "big")
    got = [(int(r[0]), r[5], r[6], r[7]) for r in rows if len(r) >= 8 and r[0].isdigit()]
    if len(got) < 200: raise RuntimeError(f"csak {len(got)} sor — megváltozott az oldal?")
    write("rotowire", "RotoWire 400", got)
guarded("RotoWire 400", _roto)

# 5) DraftFantasy cheat sheet (VORP/Edge) — "Haaland MCI · FWD 1" formátum
def _dfan():
    rows = table_rows(get("https://www.draftfantasy.com/fpl/draft-cheat-sheet"), "big")
    recs = []
    for r in rows:
        if len(r) < 3 or not r[0].isdigit(): continue
        m = re.match(r"^(.*?)\s+([A-Z]{3})\s*·\s*(GKP|DEF|MID|FWD)", STATUS.sub("", r[2]))
        if m: recs.append((int(r[0]), m.group(1).strip(), m.group(2), m.group(3)))
    if len(recs) < 120: raise RuntimeError(f"csak {len(recs)} sor — megváltozott az oldal?")
    write("draftfantasy", "DraftFantasy cheat sheet", recs)
guarded("DraftFantasy cheat sheet", _dfan)

#!/usr/bin/env python3
"""A cheat sheet sorait a fő FPL element-listához kötjük.

Miért: a képernyőképről a nevek úgy kerülnek le, ahogy ott állnak („A. Silva",
„Odegaard", „Gross"), az API viszont „Silva", „Ødegaard", „Groß" néven ismeri őket.
Ha a fájlok más néven tartják ugyanazt a játékost, a fordulók közti összehasonlítás
és a csapat-optimalizáló párosítása is elromlik. Ezért minden sorhoz beírjuk a fő FPL
element-id-t (eid) és az API kanonikus nevét (n), a képernyőn látott formát pedig
sheet_n-ben megőrizzük. Idempotens: újrafuttatva nem változtat.
"""
import json, pathlib, re, sys, unicodedata, urllib.request

HERE = pathlib.Path(__file__).parent

def nz(t):
    t = (t or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i"),("ğ","g")]:
        t = t.replace(a, b)
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return "".join(c for c in t if c.isalnum())

def base(t):
    """kezdőbetű-előtag nélkül: 'M.Sangaré' / 'A. Silva' -> 'sangare' / 'silva'"""
    return nz(re.sub(r"^\s*[A-Za-z]\s*[.\s]\s*", "", (t or "").strip()))

mn = json.loads(urllib.request.urlopen(
    "https://fantasy.premierleague.com/api/bootstrap-static/", timeout=30).read())
TEAM = {t["id"]: t["short_name"] for t in mn["teams"]}
PT = {p["id"]: p["singular_name_short"] for p in mn["element_types"]}
ELS = [{"id": e["id"], "web": e["web_name"], "sur": e["second_name"],
        "club": TEAM[e["team"]], "pos": PT[e["element_type"]]} for e in mn["elements"]]

IDX, IDX_NOCLUB = {}, {}
for e in ELS:
    for k in {(nz(e["web"]), e["club"], e["pos"]), (base(e["web"]), e["club"], e["pos"]),
              (base(e["sur"]), e["club"], e["pos"])}:
        IDX.setdefault(k, set()).add(e["id"])
    for k in {(nz(e["web"]), e["pos"]), (base(e["web"]), e["pos"]), (base(e["sur"]), e["pos"])}:
        IDX_NOCLUB.setdefault(k, set()).add(e["id"])
BY_ID = {e["id"]: e for e in ELS}

def resolve(row):
    names = (row.get("sheet_n") or row["n"], row["n"])
    for name in names:
        for k in ((nz(name), row["club"], row["pos"]), (base(name), row["club"], row["pos"])):
            hit = IDX.get(k)
            if hit and len(hit) == 1:
                return next(iter(hit)), None
    # klub nélküli tartalék: a régi lapon a játékos még a KORÁBBI klubjánál állt
    for name in names:
        for k in ((nz(name), row["pos"]), (base(name), row["pos"])):
            hit = IDX_NOCLUB.get(k)
            if hit and len(hit) == 1:
                eid = next(iter(hit))
                return eid, f'{row["n"]}: {row["club"]} → {BY_ID[eid]["club"]} (klubváltás)'
    return None, None

def main(paths):
    rc = 0
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        miss, changed, moved = [], 0, []
        for row in d["players"]:
            eid, note = resolve(row)
            if note: moved.append(note)
            if not eid:
                miss.append(f'{row["n"]} ({row["club"]}/{row["pos"]})'); continue
            api = BY_ID[eid]["web"]
            if row.get("sheet_n") is None and row["n"] != api:
                row["sheet_n"] = row["n"]          # a képernyőn látott forma megmarad
            if row.get("eid") != eid or row["n"] != api: changed += 1
            row["eid"], row["n"] = eid, api
        # az eid/sheet_n a név mellé kerüljön, ne a sor végére
        order = ["pos", "price", "n", "sheet_n", "eid", "club", "rate", "tag", "trend",
                 "fx", "npxg", "npxg_xag", "xa", "ga", "cbit", "saves90"]
        d["players"] = [{k: r[k] for k in order if k in r} for r in d["players"]]
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{p.name}: {len(d['players'])} sor, {changed} módosult"
              + (f", NEM PÁROSÍTHATÓ: {', '.join(miss)}" if miss else ", mind párosítva")
              + (f"\n  a lap rögzítése óta klubot váltott: {'; '.join(moved)}" if moved else ""))
        if miss: rc = 1
    return rc

if __name__ == "__main__":
    fs = [pathlib.Path(a) for a in sys.argv[1:]] or \
         sorted((HERE / "cheatsheet").glob("gw*_fran.json"))
    sys.exit(main(fs))

#!/usr/bin/env python3
"""Draft element_id  <->  fő FPL element_id leképezés.

A két API az id-k végén SZÉTCSÚSZIK (554-től 24 id más játékost jelöl).
Minden külső projekció a FŐ FPL id-t használja, a ligánk a DRAFT id-t.
Enélkül a projekció rossz játékosra kerül.
"""
import json, pathlib, subprocess, sys, unicodedata

HERE = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"

def get(url):
    r = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {url}")
    return json.loads(r.stdout)

def norm(s):
    s = (s or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i"),("ð","d"),("þ","th")]:
        s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())

dr = get("https://draft.premierleague.com/api/bootstrap-static")
mn = get("https://fantasy.premierleague.com/api/bootstrap-static/")

def index(bs):
    teams = {t["id"]: t["short_name"] for t in bs["teams"]}
    out = []
    for x in bs["elements"]:
        out.append({"id": x["id"], "web": x["web_name"], "club": teams[x["team"]],
                    "pos": x["element_type"],
                    "key": (norm(x["web_name"]), teams[x["team"]], x["element_type"]),
                    "key2": (norm(x["first_name"] + x["second_name"]), teams[x["team"]], x["element_type"])})
    return out

D, M = index(dr), index(mn)
by_key = {}
for m in M: by_key.setdefault(m["key"], []).append(m)
by_key2 = {}
for m in M: by_key2.setdefault(m["key2"], []).append(m)

d2m, unmatched = {}, []
for d in D:
    hit = by_key.get(d["key"]) or by_key2.get(d["key2"])
    if hit and len(hit) == 1:
        d2m[d["id"]] = hit[0]["id"]
    else:
        unmatched.append(d)

# ellenőrzés: bijekció-e
rev = {}
for k, v in d2m.items(): rev.setdefault(v, []).append(k)
dupes = {v: ks for v, ks in rev.items() if len(ks) > 1}

out = {"draft_to_main": {str(k): v for k, v in sorted(d2m.items())},
       "main_to_draft": {str(v): k for k, v in sorted(d2m.items())},
       "unmatched_draft_ids": [d["id"] for d in unmatched],
       "counts": {"draft": len(D), "main": len(M), "mapped": len(d2m)}}
(HERE / "idmap.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

shifted = [k for k, v in d2m.items() if k != v]
print(f"Draft {len(D)} · fő FPL {len(M)} · leképezve {len(d2m)}")
print(f"Eltérő id: {len(shifted)} db  ->  {sorted(shifted)[:6]}{' …' if len(shifted) > 6 else ''}")
print(f"Kétszer használt fő id: {len(dupes)}   Párosítatlan: {len(unmatched)}")
for d in unmatched: print(f"   nem párosult: draft {d['id']} {d['web']} {d['club']}")
DN = {d["id"]: d for d in D}; MN = {m["id"]: m for m in M}
for k in sorted(shifted)[:5]:
    print(f"   pl. {DN[k]['web']:<14} draft {k} -> fő {d2m[k]}  "
          f"(fő {k} ott: {MN[k]['web']})")

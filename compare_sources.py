#!/usr/bin/env python3
"""Becslés-összevetés: FPL Form vs FPL Hub vs fplestimator, közös 5 fordulós ablakon.

Csak az fplestimator ad ELEVE 5 fordulós összeget; a másik kettőnél összegzünk.
Kimenet: compare.json (a titkos lap harmadik nézete) + konzol-összefoglaló.
"""
import json, pathlib, statistics

HERE = pathlib.Path(__file__).parent
H = 5   # fordulós ablak

snap = sorted((HERE / "proj_private").glob("*.json")) or sorted((HERE / "proj").glob("*.json"))
if not snap: raise SystemExit("nincs projekció-snapshot")
S = json.loads(snap[-1].read_text(encoding="utf-8"))
gw0 = S["gw_from"]
gws = [str(g) for g in range(gw0, gw0 + H)]

data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
P = data["players"]
owner = {}
for m in data["managers"]:
    for s in m["squad"]: owner[s["id"]] = m["first"]

def summed(src):
    out = {}
    for did, per in S["data"].get(src, {}).items():
        vals = [per[g]["pts"] for g in gws if g in per]
        if len(vals) == H: out[int(did)] = round(sum(vals), 2)
    return out

srcs = {k: summed(k) for k in S["data"]}
LABEL = {k: S["sources"][k]["label"] for k in S["data"]}

# per-FORDULÓ összevetés is lehetséges, mert mindkét forrás fordulónkénti
def per_gw(src, g):
    return {int(d): per[str(g)]["pts"] for d, per in S["data"].get(src, {}).items()
            if per.get(str(g))}

common = set.intersection(*(set(v) for v in srcs.values()))
def spearman(xs, ys):
    n = len(xs)
    def rk(v):
        o = sorted(range(n), key=lambda i: v[i]); out=[0.0]*n; i=0
        while i < n:
            j=i
            while j+1 < n and v[o[j+1]] == v[o[i]]: j+=1
            for k in range(i,j+1): out[o[k]] = (i+j)/2+1
            i=j+1
        return out
    rx, ry = rk(xs), rk(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den = (sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**.5
    return round(num/den, 3) if den else None

keys = list(srcs)
agree = {}
for i,a in enumerate(keys):
    for b in keys[i+1:]:
        ids = sorted(set(srcs[a]) & set(srcs[b]))
        xs = [srcs[a][i2] for i2 in ids]; ys = [srcs[b][i2] for i2 in ids]
        agree[f"{a}|{b}"] = {"rho": spearman(xs,ys), "n": len(ids),
                             "mean_a": round(statistics.fmean(xs),2),
                             "mean_b": round(statistics.fmean(ys),2)}

rows = []
for did in common:
    p = P.get(str(did))
    if not p: continue
    vals = {k: srcs[k][did] for k in keys}
    v = list(vals.values())
    rows.append({"id": did, "n": p["n"], "club": p["c"], "pos": p["p"],
                 "vals": vals, "spread": round(max(v)-min(v), 2),
                 "mean": round(statistics.fmean(v), 2),
                 "owner": owner.get(did)})
# --- a nézeteltérés KÉT fajtája
# (1) kezdő-vita: legalább egy forrás ~0-t ad (nem játszik), egy másik sokat
# (2) érték-vita: mindegyik forrás kezdőnek tartja, mégis eltérnek a szinten
THRESH = 2.0
for r in rows:
    v = list(r["vals"].values())
    r["kind"] = "rotation" if min(v) < THRESH <= max(v) else "value"
rows.sort(key=lambda r: -r["spread"])

# FFHub várható perc: ez magyarázza a nullákat
mins = {}
for did, per in S["data"].get("ffhub", {}).items():
    g = per.get(str(gw0))
    if g and g.get("mins") is not None: mins[int(did)] = g["mins"]
for r in rows: r["ffhub_mins"] = mins.get(r["id"])

starters = [r for r in rows if r["kind"] == "value"]
def rho_on(a, b, subset):
    ids=[r["id"] for r in subset]
    xs=[srcs[a][i] for i in ids]; ys=[srcs[b][i] for i in ids]
    return spearman(xs, ys)
agree_starters = {}
for i,a in enumerate(keys):
    for b in keys[i+1:]:
        agree_starters[f"{a}|{b}"] = {"rho": rho_on(a,b,starters), "n": len(starters)}

# fordulónkénti egyezés: itt derül ki, hogy a különbség a szinten vagy a sorrenden van
by_gw = {}
for g in range(gw0, gw0 + H):
    tabs = {k: per_gw(k, g) for k in keys}
    ent = {}
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            ids = sorted(set(tabs[a]) & set(tabs[b]))
            if len(ids) < 3: continue
            xs = [tabs[a][i2] for i2 in ids]; ys = [tabs[b][i2] for i2 in ids]
            ent[f"{a}|{b}"] = {"rho": spearman(xs, ys), "n": len(ids),
                               "mean_a": round(statistics.fmean(xs), 2),
                               "mean_b": round(statistics.fmean(ys), 2)}
    by_gw[str(g)] = ent

out = {"horizon": H, "gw_from": gw0, "labels": LABEL, "agreement": agree,
       "agreement_starters": agree_starters, "by_gw": by_gw,
       "estimator_note": None,
       "taken_at": S["taken_at"], "rows": rows}
(HERE / "compare.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")

print(f"Közös játékos mind a {len(keys)} forráson: {len(common)}   (GW{gw0}–{gw0+H-1} összeg)\n")
print("Átlagos becsült pont 5 fordulóra:")
for k in keys:
    v = [srcs[k][i] for i in common]
    print(f"  {LABEL[k]:<14} átlag {statistics.fmean(v):>5.2f}   "
          f"medián {statistics.median(v):>5.2f}   max {max(v):>5.1f}")
print("\nFordulónkénti egyezés (Spearman-rho):")
for g, ent in by_gw.items():
    for k, v in ent.items():
        a, b = k.split("|")
        print(f"  GW{g}: {LABEL[a]} vs {LABEL[b]}  rho {v['rho']:>6}  n={v['n']}   "
              f"átlag {v['mean_a']} vs {v['mean_b']}")

print("\nEgyezés az 5 fordulós összegen:")
for k,v in sorted(agree.items(), key=lambda kv: -(kv[1]['rho'] or 0)):
    a,b = k.split("|")
    print(f"  {LABEL[a]:<14} vs {LABEL[b]:<14} rho {v['rho']:>6}   n={v['n']}")
rot = [r for r in rows if r["kind"] == "rotation"]
print(f"\nAz eltérések természete: {len(rot)} kezdő-vita, {len(starters)} érték-vita")
print(f"\nEgyezés CSAK azokon, akit mind a {len(keys)} forrás kezdőnek tart:")
for k,v in sorted(agree_starters.items(), key=lambda kv: -(kv[1]['rho'] or 0)):
    a,b = k.split("|")
    print(f"  {LABEL[a]:<14} vs {LABEL[b]:<14} rho {v['rho']:>6}   n={v['n']}")

hdr = f"  {'játékos':<15} {'':4} " + "  ".join(f"{LABEL[k]:>12}" for k in keys)
print("\n1) KEZDŐ-VITA — valaki szerint nem is játszik (FPL Hub várható perce zárójelben):")
print(hdr + "   szórás  kinél")
for r in rot[:8]:
    mm = f" ({r['ffhub_mins']}')" if r.get("ffhub_mins") is not None else ""
    print(f"  {r['n']:<15} {r['pos']:<4} " + "  ".join(f"{r['vals'][k]:>12.1f}" for k in keys) +
          f"   {r['spread']:>6.1f}  {r['owner'] or 'szabad'}{mm}")
print("\n2) ÉRTÉK-VITA — mind a 3 kezdőnek tartja, mégis eltérnek:")
print(hdr + "   szórás  kinél")
for r in starters[:10]:
    print(f"  {r['n']:<15} {r['pos']:<4} " + "  ".join(f"{r['vals'][k]:>12.1f}" for k in keys) +
          f"   {r['spread']:>6.1f}  {r['owner'] or 'szabad'}")

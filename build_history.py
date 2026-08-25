#!/usr/bin/env python3
"""locked/gw*.json + deadlines.json -> history.json  (a „Fordulók" nézet adata)

Egy helyen: mit tippeltek a források a TÉNYLEGES felállásra, és mi lett a valóság.
A forrás-pontosság csak lezárult fordulókból számol; amíg nincs ilyen, üresen marad.
"""
import datetime as dt
import json, pathlib, statistics

HERE = pathlib.Path(__file__).parent
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
dl = json.loads((HERE / "deadlines.json").read_text(encoding="utf-8"))
ENT = {m["entry"]: {"first": m["first"], "ini": m["initials"]} for m in data["managers"]}
P = data["players"]

FORM = [(a, b, c) for a in range(3, 6) for b in range(2, 6) for c in range(1, 4) if a + b + c == 10]

def best_xi_pts(squad_ids, pts):
    """A lehető legjobb legális XI pontja — ehhez mérjük a tényleges felállítást."""
    byp = {}
    for i in squad_ids: byp.setdefault(P.get(str(i), {}).get("p"), []).append(i)
    for k in byp: byp[k].sort(key=lambda i: -pts.get(i, 0))
    if not byp.get("GKP"): return None
    gk = pts.get(byp["GKP"][0], 0)
    best = None
    for a, bb, c in FORM:
        if len(byp.get("DEF", [])) < a or len(byp.get("MID", [])) < bb or len(byp.get("FWD", [])) < c:
            continue
        v = gk + sum(pts.get(i, 0) for i in byp["DEF"][:a] + byp["MID"][:bb] + byp["FWD"][:c])
        best = v if best is None else max(best, v)
    return best

SQUAD = {m["entry"]: [s["id"] for s in m["squad"]] for m in data["managers"]}
snapdirs = [HERE / "proj", HERE / "proj_private"]

rounds, srcs = [], {}
for f in sorted((HERE / "locked").glob("gw*.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    gw = r["gw"]
    teams = {}
    for ent, lu in r["lineups"].items():
        t = {"xi": [], "bench": [], "tip": {}, "real": None}
        for grp in ("xi", "bench"):
            for i in lu[grp]:
                p = P.get(str(i)) or {}
                t[grp].append({"id": i, "n": p.get("n", str(i)),
                               "c": p.get("c"), "p": p.get("p")})
        for src, tv in (r.get("tips") or {}).items():
            srcs[src] = tv["label"]
            t["tip"][src] = tv["teams"].get(ent)
        if r.get("actual"):
            a = r["actual"]["teams"].get(ent)
            if a:
                t["real"] = {"xi": a["xi"], "bench": a["bench"], "players": a["players"]}
        teams[ent] = t
    # felállítás-hatékonyság: mennyit hagyott az asztalon a KIÁLLÍTÁSSAL
    eff = {}
    snapf = None
    for dd in snapdirs:
        p = dd / (r.get("snapshot") or "")
        if r.get("snapshot") and p.exists(): snapf = p; break
    if snapf:
        sn = json.loads(snapf.read_text(encoding="utf-8"))
        for src, tbl in sn["data"].items():
            pts = {int(k): (v.get(str(gw), {}) or {}).get("pts", 0) for k, v in tbl.items()}
            per = {}
            for ent, lu in r["lineups"].items():
                act = round(sum(pts.get(i, 0) for i in lu["xi"]), 2)
                bst = best_xi_pts(SQUAD.get(int(ent), []), pts)
                per[ent] = {"actual": act, "best": round(bst, 2) if bst else None,
                            "left": round(bst - act, 2) if bst else None}
            eff[src] = per

    rounds.append({"gw": gw, "deadline": r["deadline"], "snapshot_at": r.get("snapshot_at"),
                   "efficiency": eff,
                   "has_tip": bool(r.get("tips")), "has_real": bool(r.get("actual")),
                   "provisional": bool((r.get("actual") or {}).get("provisional")),
                   "matches": r.get("matches", []), "teams": teams})

# --- forrás-pontosság: |tipp - valós| a kezdő XI-re, csak lezárult fordulókból
acc = {}
for src, label in srcs.items():
    errs, n = [], 0
    for rd in rounds:
        if not rd["has_real"]: continue
        for ent, t in rd["teams"].items():
            tip = (t["tip"] or {}).get(src)
            if not tip or not t["real"]: continue
            errs.append(abs(tip["xi"] - t["real"]["xi"])); n += 1
    acc[src] = {"label": label, "n": n,
                "mae": round(statistics.fmean(errs), 2) if errs else None}

# --- szerencse-mérleg: valós mínusz tipp (pozitív = szerencsés / túlteljesített)
luck = {}
for src in srcs:
    per = {}
    for ent in ENT:
        d = [rd["teams"][str(ent)]["real"]["xi"] - rd["teams"][str(ent)]["tip"][src]["xi"]
             for rd in rounds if rd["has_real"] and str(ent) in rd["teams"]
             and rd["teams"][str(ent)]["real"] and (rd["teams"][str(ent)]["tip"] or {}).get(src)]
        if d: per[str(ent)] = {"sum": round(sum(d), 1), "n": len(d)}
    luck[src] = per

out = {"built_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
                     .isoformat().replace("+00:00", "Z"),
       "managers": ENT, "sources": srcs, "rounds": rounds,
       "accuracy": acc, "luck": luck,
       "upcoming": [e for e in dl["events"]
                    if e["deadline"] and e["deadline"] > dt.datetime.now(dt.timezone.utc)
                       .isoformat().replace("+00:00", "Z")][:6],
       "lock_after_minutes": dl["lock_after_minutes"]}
(HERE / "history.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")
print(f"history.json · lezárt forduló: {len(rounds)} · tippelt: "
      f"{sum(1 for r in rounds if r['has_tip'])} · valós ponttal: "
      f"{sum(1 for r in rounds if r['has_real'])}")
if acc:
    print("Forrás-pontosság (átlagos eltérés a kezdő XI-re):")
    for s, v in sorted(acc.items(), key=lambda kv: (kv[1]["mae"] is None, kv[1]["mae"])):
        print(f"  {v['label']:<24} MAE {v['mae']}  (n={v['n']})")
else:
    print("Pontosság: még nincs lezárult forduló — a GW1 után lesz első adat.")
print(f"Következő deadline: GW{out['upcoming'][0]['gw']} {out['upcoming'][0]['deadline']}"
      if out["upcoming"] else "Nincs hátralévő forduló.")

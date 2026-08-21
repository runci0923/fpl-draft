#!/usr/bin/env python3
"""Forduló-lezárás: a tipp és a valóság összepárosítása. -> locked/gw{N}.json

Miért így: a projekciót a deadline ELŐTT kell elkapni, különben nem tipp. A felállást
viszont csak a deadline UTÁN adja ki az API (`entry/{id}/event/{gw}` előtte 404). Ez a
szkript a kettőt köti össze, és IDEMPOTENS: óránként futhat, mindig azt teszi hozzá,
ami még hiányzik.

Három szakasz fordulónként:
  1. deadline előtt        -> nincs teendő
  2. deadline után         -> TIPP LEZÁRÁSA: valós felállás + a deadline előtti utolsó
                              projekció-pillanatkép -> „ezt tippeltük erre a felállásra"
  3. a forduló véget ért   -> VALÓS PONTOK beírása ugyanabba a fájlba

A projekciót NEM tudja lehúzni: az FPL Hub és a Solio bejelentkezést kér. Ha a deadline
előtt nincs friss pillanatkép, a szkript ezt kiírja és a tipp-részt kihagyja — a valós
felállás és a pontok akkor is rögzülnek.
"""
import datetime as dt
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
OUT = HERE / "locked"; OUT.mkdir(exist_ok=True)
LEAGUE = 20944

def api(p):
    r = subprocess.run(["curl", "-s", f"https://draft.premierleague.com/api/{p}"],
                       capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {p}")
    try: return json.loads(r.stdout)
    except json.JSONDecodeError: return None

def parse(t):
    if not t: return None
    x = dt.datetime.fromisoformat(t.replace("Z", "+00:00"))
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)

now = dt.datetime.now(dt.timezone.utc)
dl = json.loads((HERE / "deadlines.json").read_text(encoding="utf-8"))
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
P = data["players"]
ENT = {m["entry"]: m for m in data["managers"]}

det = api(f"league/{LEAGUE}/details")
LE2ENT = {e["id"]: e["entry_id"] for e in det["league_entries"]}
matches = {}
for m in det["matches"]:
    matches.setdefault(m["event"], []).append(
        {"home": LE2ENT[m["league_entry_1"]], "away": LE2ENT[m["league_entry_2"]],
         "home_pts": m["league_entry_1_points"], "away_pts": m["league_entry_2_points"],
         "finished": m["finished"], "started": m["started"]})

# minden projekció-pillanatkép, időbélyeggel — ebből választunk deadline előttit
snaps = []
for d in ("proj", "proj_private"):
    for p in (HERE / d).glob("*.json"):
        s = json.loads(p.read_text(encoding="utf-8"))
        snaps.append({"file": p.name, "at": parse(s["taken_at"]), "snap": s})
snaps.sort(key=lambda x: x["at"])

def canonical(gw, deadline):
    """A deadline előtti UTOLSÓ pillanatkép, ami tartalmazza ezt a fordulót."""
    ok = [s for s in snaps if s["at"] < deadline
          and s["snap"]["gw_from"] <= gw <= s["snap"]["gw_to"]]
    return ok[-1] if ok else None

changed, notes = [], []
for e in dl["events"]:
    gw, deadline = e["gw"], parse(e["deadline"])
    if not deadline or now < deadline: continue          # 1. szakasz
    f = OUT / f"gw{gw:02d}.json"
    rec = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    # --- 2. szakasz: tipp + valós felállás lezárása
    if rec is None or not rec.get("locked"):
        lineups, missing = {}, []
        for ent in ENT:
            d = api(f"entry/{ent}/event/{gw}")
            if isinstance(d, dict) and d.get("picks"):
                lineups[str(ent)] = {
                    "xi": [p["element"] for p in d["picks"] if p["position"] <= 11],
                    "bench": [p["element"] for p in d["picks"] if p["position"] > 11]}
            else:
                missing.append(ENT[ent]["first"])
        if missing:
            notes.append(f"GW{gw}: a felállás még nem kérhető le ({', '.join(missing)}) — kihagyva")
            continue

        can = canonical(gw, deadline)
        tips = {}
        if can:
            snap = can["snap"]
            for src, tbl in snap["data"].items():
                per = {}
                for ent, lu in lineups.items():
                    pts = lambda ids: round(sum(
                        (tbl.get(str(i), {}).get(str(gw), {}) or {}).get("pts", 0) for i in ids), 2)
                    per[ent] = {"xi": pts(lu["xi"]), "bench": pts(lu["bench"])}
                tips[src] = {"label": snap["sources"][src]["label"], "teams": per}
        else:
            notes.append(f"GW{gw}: NINCS deadline előtti projekció-pillanatkép — a tipp kimarad")

        rec = {"gw": gw, "deadline": e["deadline"], "locked": True,
               "locked_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
               "snapshot": can["file"] if can else None,
               "snapshot_at": can["at"].isoformat().replace("+00:00", "Z") if can else None,
               "lineups": lineups, "tips": tips,
               "matches": matches.get(gw, []), "actual": None}
        changed.append(f"GW{gw} tipp+felállás lezárva"
                       + (f" ({len(tips)} forrás)" if tips else " (tipp nélkül)"))

    # --- 3. szakasz: valós pontok, ha a forduló véget ért
    ms = matches.get(gw, [])
    if ms and all(m["finished"] for m in ms) and not rec.get("actual"):
        live = api(f"event/{gw}/live") or {}
        pts = {int(k): (v.get("stats", {}) or {}).get("total_points")
               for k, v in (live.get("elements") or {}).items()}
        per = {}
        for ent, lu in rec["lineups"].items():
            g = lambda ids: sum(pts.get(i) or 0 for i in ids)
            per[ent] = {"xi": g(lu["xi"]), "bench": g(lu["bench"]),
                        "players": {str(i): pts.get(i) for i in lu["xi"] + lu["bench"]}}
        rec["actual"] = {"teams": per, "matches": ms}
        changed.append(f"GW{gw} valós pontok beírva")

    rec["matches"] = matches.get(gw, [])
    f.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

locked = sorted(OUT.glob("gw*.json"))
print(f"Lezárt fordulók: {len(locked)}" + (f" ({', '.join(p.stem for p in locked)})" if locked else ""))
for c in changed: print("  +", c)
for n in notes: print("  !", n)
if not changed and not notes: print("  nincs teendő")

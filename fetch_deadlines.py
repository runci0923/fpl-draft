#!/usr/bin/env python3
"""Fordulók deadline-jai -> deadlines.json

A `bootstrap-static.events.data` mind a 38 fordulóra adja a `deadline_time`-ot, plusz
a draft-specifikus `waivers_time` és `trades_time` mezőket.

Minek: a lezárás (lock_gw.py) ebből tudja, hogy egy forduló deadline-ja elmúlt-e, és
hogy melyik projekció-pillanatkép számít KANONIKUS tippnek (a deadline előtti utolsó).
"""
import datetime as dt
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
LOCK_AFTER_MIN = 30      # a deadline után ennyivel már látszanak a felállások

def api(p):
    r = subprocess.run(["curl", "-s", f"https://draft.premierleague.com/api/{p}"],
                       capture_output=True)
    if r.returncode: sys.exit(f"curl hiba: {p}")
    return json.loads(r.stdout)

bs = api("bootstrap-static")
ev = bs["events"]
rows = ev["data"] if isinstance(ev["data"], list) else list(ev["data"].values())

def iso(t): return t.replace("+00:00", "Z") if t else None
def parse(t):
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None

out = {"fetched_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
                       .isoformat().replace("+00:00", "Z"),
       "current": ev.get("current"), "next": ev.get("next"),
       "lock_after_minutes": LOCK_AFTER_MIN,
       "events": []}
for r in rows:
    d = parse(r.get("deadline_time"))
    out["events"].append({
        "gw": r["id"], "name": r.get("name"),
        "deadline": iso(r.get("deadline_time")),
        "lock_at": iso((d + dt.timedelta(minutes=LOCK_AFTER_MIN)).isoformat()) if d else None,
        "waivers": iso(r.get("waivers_time")), "trades": iso(r.get("trades_time")),
        "finished": bool(r.get("finished")),
        "avg_score": r.get("average_entry_score"),
    })
(HERE / "deadlines.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8")

now = dt.datetime.now(dt.timezone.utc)
fut = [e for e in out["events"] if e["deadline"] and parse(e["deadline"]) > now]
past = [e for e in out["events"] if e["deadline"] and parse(e["deadline"]) <= now]
print(f"{len(out['events'])} forduló · lezárult deadline: {len(past)} · hátralévő: {len(fut)}")
print(f"aktuális: {out['current']}  következő: {out['next']}  (lezárás a deadline után {LOCK_AFTER_MIN} perccel)\n")
for e in fut[:19]:
    d = parse(e["deadline"])
    h = (d - now).total_seconds() / 3600
    print(f"  GW{e['gw']:<3} {d:%Y-%m-%d %H:%M} UTC   {h:>7.1f} óra   "
          f"lezárás {parse(e['lock_at']):%m-%d %H:%M}"
          + (f"   waiver {parse(e['waivers']):%m-%d %H:%M}" if e["waivers"] else ""))

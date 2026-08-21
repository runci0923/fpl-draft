#!/usr/bin/env python3
"""Kapu: van-e egyáltalán teendő? -> kiírja a GITHUB_OUTPUT-ba (work=true|false)

Miért: a projekció lehúzása kézi (bejelentkezés kell), tehát a gépnek csak akkor van
dolga, ha
  (a) elmúlt egy deadline és az a forduló még nincs lezárva, vagy
  (b) egy lezárt forduló összes meccse véget ért, de a valós pontok még nincsenek beírva,
  (c) vagy kézzel indítottuk (FORCE=1).

Így a futások nagy része azonnal, munka nélkül zárul — nincs zaj és nincs hibázási felület.
"""
import datetime as dt
import json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
LEAGUE = 20944
FORCE = os.environ.get("FORCE") == "1"

def api(p):
    r = subprocess.run(["curl", "-s", f"https://draft.premierleague.com/api/{p}"],
                       capture_output=True)
    try: return json.loads(r.stdout)
    except Exception: return None

def parse(t):
    if not t: return None
    x = dt.datetime.fromisoformat(t.replace("Z", "+00:00"))
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)

reasons = []
if FORCE:
    reasons.append("kézi indítás")
else:
    now = dt.datetime.now(dt.timezone.utc)
    bs = api("bootstrap-static") or {}
    ev = (bs.get("events") or {}).get("data") or []
    rows = ev if isinstance(ev, list) else list(ev.values())
    det = api(f"league/{LEAGUE}/details") or {}
    by_gw = {}
    for m in det.get("matches", []):
        by_gw.setdefault(m["event"], []).append(m)

    for e in rows:
        gw, d = e["id"], parse(e.get("deadline_time"))
        if not d or now < d: continue
        f = HERE / "locked" / f"gw{gw:02d}.json"
        if not f.exists():
            reasons.append(f"GW{gw}: elmúlt a deadline, még nincs lezárva")
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        ms = by_gw.get(gw, [])
        if ms and all(m["finished"] for m in ms) and not rec.get("actual"):
            reasons.append(f"GW{gw}: véget ért, a valós pontok még nincsenek beírva")

work = bool(reasons)
out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a") as fh:
        fh.write(f"work={'true' if work else 'false'}\n")
        fh.write(f"reason={'; '.join(reasons) if reasons else 'nincs teendő'}\n")
print(("TEENDŐ: " + "; ".join(reasons)) if work else "Nincs teendő — a futás munka nélkül zárul.")

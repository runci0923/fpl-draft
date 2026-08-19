#!/usr/bin/env python3
"""Titkos oldal: fordulónkénti becsült pontok, draft- és fantasy-nézetben.

NEM megy nyílt webre: az FPL Hub fizetős adatára épül, és a draft-nézet
szándékosan megmutatja, kinél van kicsi és ki a szabad (ez versenyelőny).
"""
import argparse, json, pathlib, subprocess, sys, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import theme

HERE = pathlib.Path(__file__).parent

def norm(x):
    x = (x or "").lower()
    for a, b in [("ø","o"),("æ","ae"),("đ","d"),("ł","l"),("ß","ss"),("ı","i")]: x = x.replace(a, b)
    x = "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c))
    return "".join(c for c in x if c.isalnum())
ap = argparse.ArgumentParser()
ap.add_argument("--out", default=str(HERE / "secret.html"))
ap.add_argument("--fpl-entry", type=int, default=117238, help="a saját (nem draft) FPL csapat")
A = ap.parse_args()

snaps = sorted((HERE / "proj_private").glob("*.json")) or sorted((HERE / "proj").glob("*.json"))
if not snaps: raise SystemExit("nincs projekció-snapshot")
SNAP = json.loads(snaps[-1].read_text(encoding="utf-8"))
hub = json.loads((HERE / "ffhub" / "ffhub_raw.json").read_text(encoding="utf-8"))

cs_path = HERE / "cheatsheet" / "gw1_fran.json"
CS = json.loads(cs_path.read_text(encoding="utf-8")) if cs_path.exists() else None
sq_path = HERE / "squads_test.json"
SQ = json.loads(sq_path.read_text(encoding="utf-8")) if sq_path.exists() else None
cmp_path = HERE / "compare.json"
CMP = json.loads(cmp_path.read_text(encoding="utf-8")) if cmp_path.exists() else None
idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
M2D = {int(k): v for k, v in idmap["main_to_draft"].items()}
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

ME_DRAFT = 106153                        # Attila draft-entryje
owner, mine_draft = {}, set()
for m in data["managers"]:
    for s in m["squad"]:
        owner[s["id"]] = {"first": m["first"], "ini": m["initials"], "me": m["entry"] == ME_DRAFT}
        if m["entry"] == ME_DRAFT: mine_draft.add(s["id"])

# a sima FPL keret deadline előtt 404 — ha megjön az API-ból, kiemeljük
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
fpl_squad, fpl_note = [], ""
for gw in range(1, 39):
    r = subprocess.run(["curl", "-s", "-A", UA,
                        f"https://fantasy.premierleague.com/api/entry/{A.fpl_entry}/event/{gw}/picks/"],
                       capture_output=True)
    try: j = json.loads(r.stdout)
    except json.JSONDecodeError: break
    if isinstance(j, dict) and j.get("picks"):
        fpl_squad = [p["element"] for p in j["picks"]]
    else:
        break
if not fpl_squad:
    fpl_note = ("A sima FPL keret a deadline előtt nem kérhető le (a picks-végpont 404-et ad), "
                "ezért a fantasy-nézetben most nincs kijelölve a te csapatod. GW1 után magától megjelenik.")

# forrásonkénti per-fordulós becslés a snapshotból
SRC = {}
for slug, note in SNAP["sources"].items():
    SRC[slug] = {"label": note["label"], "note": note.get("note", ""),
                 "url": note.get("url"), "per_gw": True,
                 "players": note.get("players"), "data": SNAP["data"][slug]}
ORDER = [k for k in ("ffhub", "solio") if k in SRC] + [k for k in SRC if k not in ("ffhub", "solio")]

players = []
for p in hub["players"]:
    d = M2D.get(p["fpl"])
    if d is None: continue
    o = owner.get(d)
    players.append({
        "fpl": p["fpl"], "draft": d, "n": p["n"], "club": p["club"],
        "pos": {"GK": "GKP"}.get(p["pos"], p["pos"]),
        "price": p["price"], "own": p["own"], "cop": p["cop"], "status": p["status"],
        "pps": round(p["pps"], 2) if p["pps"] else None,
        "gw": {str(g["g"]): {"pts": round(g["pts"], 2), "min": g["min"],
                             "opp": g["opp"], "h": g["h"]}
               for g in p["gw"] if g["pts"] is not None},
        "owner": (o["first"] if o else None), "ini": (o["ini"] if o else None),
        "mine_draft": d in mine_draft, "mine_fpl": p["fpl"] in set(fpl_squad),
    })
gws = sorted({int(k) for p in players for k in p["gw"]})

# --- a sima FPL keret képernyőképről (a picks-végpont a deadline előtt 404)
MYSQ = HERE / "my_fpl_squad.json"
manual_meta = None
if MYSQ.exists() and not fpl_squad:
    mj = json.loads(MYSQ.read_text(encoding="utf-8"))
    manual_meta = {"gw": mj["gw"], "chip": mj.get("chip"), "date": mj["date"],
                   "captain": mj.get("captain"), "formation": mj.get("formation"),
                   "xi": [], "bench": []}
    unresolved = []
    for grp in ("xi", "bench"):
        for e in mj[grp]:
            n = norm(e["n"])
            hit = [p for p in players if p["club"] == e["club"] and p["pos"] == e["pos"]
                   and (norm(p["n"]) == n or norm(p["n"]).endswith(n) or n.endswith(norm(p["n"])))]
            if len(hit) == 1:
                hit[0]["mine_fpl"] = True
                hit[0]["fpl_bench"] = (grp == "bench")
                manual_meta[grp].append(hit[0]["draft"])
            else:
                unresolved.append(f'{e["n"]} ({e["club"]}/{e["pos"]}) -> {len(hit)}')
    if unresolved:
        raise SystemExit("my_fpl_squad.json feloldatlan: " + "; ".join(unresolved))
    fpl_note = (f'A sima FPL kereted képernyőképről ({mj["date"]}), mert a picks-végpont a '
                f'deadline előtt 404-et ad. Chip: {mj.get("chip","-")} — bench boostnál '
                f'mind a 15 játékos pontja számít, ezért a kispadosok is meg vannak jelölve.')

PAY = json.dumps({"taken_at": SNAP["taken_at"], "gws": gws, "players": players, "cmp": CMP,
                  "sq": SQ, "cs": CS,
                  "src": {k: {kk: vv for kk, vv in SRC[k].items() if kk != "data"} for k in ORDER},
                  "srcdata": {k: SRC[k]["data"] for k in ORDER}, "order": ORDER,
                  "fpl_note": fpl_note, "fpl_squad_size": len(fpl_squad),
                  "fpl_manual": manual_meta,
                  "managers": [{"first": m["first"], "ini": m["initials"],
                                "me": m["entry"] == ME_DRAFT} for m in data["managers"]]},
                 ensure_ascii=False, separators=(",", ":"))

TPL = r"""<title>Titkos becslés-tábla</title>__HEAD__
.wrap{max-width:1300px;margin:0 auto;padding:clamp(26px,4.5vw,52px) var(--gutter) 90px}
h1{font-weight:600;font-size:clamp(30px,5vw,50px);line-height:1.03;letter-spacing:-.022em;margin:0 0 12px}
h2{font-size:clamp(18px,2.2vw,23px);font-weight:600;margin:0}
.kicker{font-family:var(--mono);font-size:11.5px;letter-spacing:.15em;text-transform:uppercase;color:var(--coral);margin:0 0 12px}
.lede{max-width:66ch;font-size:clamp(14.5px,1.35vw,17px);color:var(--dim);margin:0}
.lede b{color:var(--fg);font-weight:500}
.nav{display:flex;gap:4px;margin:24px 0 0;border-bottom:1px solid var(--rule);justify-content:flex-end}
.nav .spacer{flex:1 1 auto}
.nav a{padding:10px 17px;color:var(--dim);text-decoration:none;font-size:15px;font-weight:500;
  border-bottom:2px solid transparent;margin-bottom:-1px}
.nav a:hover{color:var(--fg)}
.nav a[aria-current="page"]{color:var(--fg);border-bottom-color:var(--coral)}
.warn{margin:18px 0 0;padding:11px 14px;border-radius:var(--r-sm);border:1px solid var(--coral);
  font-family:var(--mono);font-size:11px;line-height:1.65;color:var(--fg);
  background:color-mix(in oklab,var(--coral) 12%,transparent)}
.ctl{display:flex;flex-wrap:wrap;gap:9px 14px;align-items:center;margin-top:20px;padding:13px 15px;
  background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);box-shadow:var(--sh-sm)}
.ctl .lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.grp{display:flex;gap:6px;flex-wrap:wrap}
.b{padding:5px 11px;border-radius:999px;border:1.5px solid var(--rule);background:transparent;
  color:var(--dim);cursor:pointer;font-family:var(--mono);font-size:11px;letter-spacing:.04em}
.b:hover{border-color:var(--fg);color:var(--fg)}
.b[aria-pressed="true"]{background:var(--fg);border-color:var(--fg);color:var(--bg)}
.tabs{display:flex;gap:2px;margin-top:18px;border-bottom:1px solid var(--rule)}
.tab{padding:9px 16px;border:0;background:transparent;color:var(--dim);cursor:pointer;
  font-family:var(--display);font-size:15px;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px}
.tab[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--coral)}
.cols{display:grid;gap:16px;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:22px}
@media (max-width:1000px){.cols{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:600px){.cols{grid-template-columns:1fr}}
.col{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);
  box-shadow:var(--sh-sm);overflow:hidden}
.col > h3{margin:0;padding:11px 13px;font-size:14px;font-weight:600;background:var(--surface-2);
  border-bottom:1px solid var(--rule);display:flex;justify-content:space-between;align-items:baseline}
.col > h3 span{font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;color:var(--dim)}
ol.list{list-style:none;margin:0;padding:0}
ol.list li{display:grid;grid-template-columns:20px 1fr auto;gap:7px;align-items:center;
  padding:6px 11px;border-bottom:1px solid color-mix(in oklab,var(--rule) 45%,transparent);font-size:13px}
ol.list li:last-child{border-bottom:0}
ol.list li.me{background:color-mix(in oklab,var(--coral) 11%,transparent);
  box-shadow:inset 3px 0 0 var(--coral)}
ol.list li.free .nm{font-weight:600}
.ix{font-family:var(--mono);font-size:9.5px;color:var(--dim);text-align:right}
.nm{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nm em{font-style:normal;font-family:var(--mono);font-size:8.5px;color:var(--dim);margin-left:4px}
.rt{text-align:right;white-space:nowrap}
.rt .p{font-family:var(--mono);font-size:13px;font-weight:500;font-variant-numeric:tabular-nums}
.rt .x{display:block;font-family:var(--mono);font-size:8.5px;color:var(--dim)}
.ow{display:inline-block;font-family:var(--mono);font-size:8px;letter-spacing:.05em;padding:1px 5px;
  border-radius:999px;background:var(--dim);color:var(--bg);margin-left:5px}
.ow.free{background:transparent;border:1px dashed var(--coral);color:var(--coral)}
.ow.me{background:var(--coral);color:#fff}
[hidden]{display:none !important}
.tw{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r-md);background:var(--surface);
  box-shadow:var(--sh-sm);margin-top:16px}
table{width:100%;border-collapse:collapse}
thead th{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--dim);font-weight:400;text-align:right;padding:11px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}
tbody td{padding:9px 10px;border-bottom:1px solid var(--rule);font-size:13px;text-align:right;
  white-space:nowrap;font-variant-numeric:tabular-nums}
tbody tr:last-child td{border-bottom:0}
th.l,td.l{text-align:left}
td.nm2{font-weight:500;font-size:14px}
tr.hi{background:var(--surface-2)}
.dimc{color:var(--dim)}
.hot{color:var(--coral);font-weight:500}
.sechd{margin:26px 0 0;font-size:16px;font-weight:600}
.sechd + p{margin:3px 0 0;font-family:var(--mono);font-size:11px;color:var(--dim);line-height:1.6}
.cstbl td.rt2{text-align:right}
.rate{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:7px;vertical-align:middle}
.rate.green{background:#22c55e}.rate.yellow{background:#facc15}
.rate.orange{background:#f97316}.rate.red{background:#ef4444}
.fxc{display:inline-block;min-width:42px;text-align:center;font-family:var(--mono);font-size:10px;
  padding:1px 5px;border-radius:3px;margin-right:3px}
.fxc.home{background:color-mix(in oklab,var(--fg) 14%,transparent);font-weight:600}
.fxc.away{color:var(--dim)}
.cslegend{display:flex;flex-wrap:wrap;gap:8px 16px;margin:14px 0 0;font-family:var(--mono);
  font-size:11px;color:var(--dim);align-items:center}
.sqbar{display:flex;flex-wrap:wrap;gap:9px 14px;align-items:center;margin:18px 0 0;padding:12px 15px;
  background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);box-shadow:var(--sh-sm)}
.sqgrid{display:grid;gap:16px;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:18px}
@media (max-width:1000px){.sqgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:600px){.sqgrid{grid-template-columns:1fr}}
.sqhead{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:baseline;margin-top:20px}
.sqhead .big{font-size:30px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.sqhead .lbl2{font-family:var(--mono);font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--dim)}
.rnd{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.rnd span{font-family:var(--mono);font-size:11px;padding:4px 10px;border-radius:999px;
  border:1px solid var(--rule);color:var(--dim)}
.rnd span b{color:var(--fg);font-weight:500}
.bench2{opacity:.55}
.note{margin-top:clamp(32px,5vw,54px);padding-top:18px;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:11px;line-height:1.75;color:var(--dim);max-width:84ch}
.note b{color:var(--fg);font-weight:500}
:focus-visible{outline:2px solid var(--coral);outline-offset:2px}
</style>

<div class="wrap">
  <p class="kicker">csak neked &middot; ne oszd meg</p>
  <h1>Becslés-tábla</h1>
  <p class="lede">Az FPL Hub PRO-modellje fordulónként, minden játékosra. A <b>draft-nézetben</b>
  ott van, kinél van — így kiugranak a <b>szabad</b> játékosok, akik sok pontot hoznának.
  A <b>fantasy-nézet</b> a sima csapatodhoz ad árat és tulajdonlást.</p>

  <nav class="nav">
    <span class="spacer"></span>
    <a href="gw.html">A forduló</a>
    <a href="index.html">Draft</a>
    <a href="#" aria-current="page">Titkos</a>
  </nav>

  <p class="warn">Fizetős adat (FPL Hub PRO). Ez a lap <b>nincs</b> a publikus oldalon, és a
  GitHub-repóba sem kerül be — se a becslések, se ez a fájl.</p>

  <div class="tabs" role="tablist">
    <button class="tab" role="tab" id="t-draft" aria-selected="true">Draft-nézet</button>
    <button class="tab" role="tab" id="t-fpl" aria-selected="false">Fantasy-nézet</button>
    <button class="tab" role="tab" id="t-cs" aria-selected="false">GW1 cheat sheet</button>
    <button class="tab" role="tab" id="t-sq" aria-selected="false">Csapat-teszt</button>
    <button class="tab" role="tab" id="t-cmp" aria-selected="false">Becslés-különbségek</button>
  </div>

  <div class="ctl">
    <span class="lbl">becslés</span><span class="grp" id="srcs"></span>
    <span class="lbl">forduló</span><span class="grp" id="gws"></span>
    <span class="lbl">mutasd</span><span class="grp" id="filt"></span>
    <span class="lbl">rendezés</span><span class="grp" id="sort"></span>
  </div>

  <p class="warn" id="fplnote" hidden></p>
  <div class="cols" id="cols"></div>
  <div id="csview" hidden></div>
  <div id="sqview" hidden></div>
  <div id="cmpview" hidden></div>
  <p class="note" id="foot"></p>
</div>

<script id="p" type="application/json">__PAY__</script>
<script>
const D = JSON.parse(document.getElementById('p').textContent);
const POS = [['GKP','Kapus'],['DEF','Védelem'],['MID','Középpálya'],['FWD','Támadók']];
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let view = 'draft', gw = String(D.gws[0]), filt = 'all', sortBy = 'pts';
let src = D.order[0];
const SUM = 'sum';
const S = () => D.src[src];
const row = p => (D.srcdata[src] || {})[String(p.draft ?? p.id ?? '')] || null;

const val = p => {
  const r = D.srcdata[src] ? D.srcdata[src][String(p.draft)] : null;
  if (!r) return null;
  if (!S().per_gw) return r.sum5 ?? null;                 // csak 5 fordulós összeg
  if (gw === SUM) {
    const v = Object.values(r).map(x => x.pts).filter(x => x != null);
    return v.length ? v.reduce((a, b) => a + b, 0) : null;
  }
  return r[gw] ? r[gw].pts : null;
};
// a várható perc és a fixtúra az FPL Hub adatából jön (csak ő ad ilyet)
const mins = p => (gw !== SUM && p.gw[gw]) ? p.gw[gw].min : null;
const fx = p => (gw !== SUM && p.gw[gw]) ? `${p.gw[gw].opp}${p.gw[gw].h ? '(H)' : '(A)'}` : null;

function render() {
  document.getElementById('srcs').innerHTML = D.order.map(k =>
    `<button class="b" data-src="${k}" aria-pressed="${k === src}">${esc(D.src[k].label)}</button>`).join('');
  const perGw = S().per_gw;
  document.getElementById('gws').innerHTML = perGw ?
    (D.gws.map(g => `<button class="b" data-g="${g}" aria-pressed="${String(g) === gw}">${g}.</button>`).join('')
     + `<button class="b" data-g="${SUM}" aria-pressed="${gw === SUM}">összeg</button>`)
    : `<span class="none">5 fordulós összeg (ez a forrás nem ad fordulónkénti bontást)</span>`;
  document.getElementById('filt').innerHTML =
    [['all','mind'],['free','csak szabad'],['mine','csak az enyém']].map(([k, l]) =>
      `<button class="b" data-f="${k}" aria-pressed="${filt === k}">${l}</button>`).join('');
  document.getElementById('sort').innerHTML =
    [['pts','pont'],['ppm','pont/ár']].map(([k, l]) =>
      `<button class="b" data-s="${k}" aria-pressed="${sortBy === k}">${l}</button>`).join('');

  const nf = document.getElementById('fplnote');
  if (view === 'fpl' && D.fpl_note) { nf.hidden = false; nf.textContent = D.fpl_note; }
  else nf.hidden = true;

  const isMine = p => view === 'draft' ? p.mine_draft : p.mine_fpl;
  document.getElementById('cols').innerHTML = POS.map(([k, label]) => {
    let list = D.players.filter(p => p.pos === k && val(p) !== null);
    if (filt === 'free') list = list.filter(p => !p.owner);
    if (filt === 'mine') list = list.filter(isMine);
    list.sort((a, b) => sortBy === 'ppm'
      ? (val(b) / b.price) - (val(a) / a.price)
      : val(b) - val(a));
    const free = list.filter(p => !p.owner).length;
    return `<div class="col"><h3>${label}<span>${list.length} db${
      view === 'draft' ? ` · ${free} szabad` : ''}</span></h3>
      <ol class="list">` + list.slice(0, 40).map((p, i) => {
        const v = val(p), m = mins(p), f = fx(p);
        const ownChip = view === 'draft'
          ? (p.owner ? `<span class="ow${p.mine_draft ? ' me' : ''}">${esc(p.ini)}</span>`
                     : `<span class="ow free">szabad</span>`)
          : `<span class="ow">${p.own.toFixed(0)}%</span>`;
        return `<li class="${isMine(p) ? 'me' : ''} ${!p.owner ? 'free' : ''}">
          <span class="ix">${i + 1}</span>
          <span class="nm">${esc(p.n)}<em>${esc(p.club)}${f ? ' · ' + esc(f) : ''}</em>${ownChip}</span>
          <span class="rt"><span class="p">${v.toFixed(1)}</span>
            <span class="x">${view === 'draft'
              ? (m !== null ? m + "'" : '')
              : '£' + p.price.toFixed(1)}</span></span>
        </li>`;
      }).join('') + `</ol></div>`;
  }).join('');

  document.getElementById('foot').innerHTML =
    `<b>Aktív becslés.</b> ${esc(S().label)} — ${esc(S().note)}
     (${S().players} játékos). Snapshot: ${esc(D.taken_at.replace('T',' ').replace('Z',' UTC'))}.<br>
     <b>Perc és fixtúra.</b> A kártyák alatti perc és az ellenfél az FPL Hub adatából jön —
     a többi forrás nem ad várható játékpercet.<br>
     <b>Draft-nézet.</b> A monogram a birtokos, a szaggatott „szabad" azt jelenti, hogy senki
     keretében sincs — ezek a waiver-célpontok. A sajátjaid coral csíkkal.<br>
     <b>Fantasy-nézet.</b> Ár és a mezőny tulajdonlási aránya, a sima FPL csapatodhoz.<br>
     <b>Miért titkos.</b> Egyrészt fizetős adat, amit nem adunk tovább. Másrészt a szabad
     játékosok listája versenyelőny a ligában — ezért nincs a publikus oldalon.`;
}

let csPos = 'ALL', csOnlyGreen = false;
function renderCs() {
  const C = D.cs, box = document.getElementById('csview');
  if (!C) { box.innerHTML = '<p class="note">Nincs cheat sheet adat.</p>'; return; }
  const RATE = {green: 'Great Option', yellow: 'Good Option',
                orange: 'Differential', red: 'Avoid'};
  let rows = C.players.filter(p => (csPos === 'ALL' || p.pos === csPos)
                                && (!csOnlyGreen || p.rate === 'green'));
  rows.sort((a, b) => a.pos.localeCompare(b.pos) || a.price - b.price
                      || ['green','yellow','orange','red'].indexOf(a.rate)
                       - ['green','yellow','orange','red'].indexOf(b.rate));
  const fx = p => (p.fx || []).map(f =>
    `<span class="fxc ${f === f.toUpperCase() ? 'home' : 'away'}">${esc(f)}</span>`).join('');
  const num = v => v === undefined || v === null ? '–' : v.toFixed(2);
  box.innerHTML = `
    <div class="sqbar">
      <span class="lbl">pozíció</span><span class="grp">${
        [['ALL','mind'],['DEF','védő'],['MID','közép'],['FWD','csatár']].map(([k,l]) =>
        `<button class="b" data-cspos="${k}" aria-pressed="${csPos===k}">${l}</button>`).join('')}</span>
      <span class="lbl">szűrés</span><span class="grp">
        <button class="b" data-csgreen="1" aria-pressed="${csOnlyGreen}">csak zöldek</button></span>
    </div>
    <p class="note" style="margin-top:12px;border:0;padding:0">
      <b>${esc(C.source)}</b>, rögzítve ${esc(C.date)}. A statisztikák a 25/26-os szezon
      per 90 perces értékei. A fixtúra vastagon = hazai. ${esc(C.missing[0])}.</p>
    <div class="cslegend">${Object.entries(RATE).map(([k, v]) =>
      `<span><span class="rate ${k}"></span>${esc(v)}</span>`).join('')}
      <span>▲▼ = a forrás trend-jelzése · „new" = új a listán</span></div>
    <div class="tw cstbl"><table>
      <thead><tr><th class="l">Játékos</th><th>Poz</th><th>Ár</th><th class="l">GW1–3</th>
        <th>npxG</th><th>xA / G+A</th><th>CBIT</th></tr></thead><tbody>` +
    rows.map(p => `<tr>
      <td class="l nm2"><span class="rate ${p.rate}" title="${esc(RATE[p.rate])}"></span>${esc(p.n)}
        <span class="dimc" style="font-family:var(--mono);font-size:9px">${esc(p.club)}</span>
        ${p.trend ? `<span class="dimc">${p.trend === 'up' ? '▲' : '▼'}</span>` : ''}
        ${p.tag ? `<span class="ow">${esc(p.tag)}</span>` : ''}</td>
      <td class="dimc">${p.pos}</td><td>£${p.price.toFixed(1)}</td>
      <td class="l">${fx(p)}</td>
      <td>${num(p.npxg !== undefined ? p.npxg : p.npxg_xag)}</td>
      <td>${p.xa !== undefined ? num(p.xa) + ' / ' : ''}${num(p.ga)}</td>
      <td class="dimc">${num(p.cbit)}</td></tr>`).join('') +
    `</tbody></table></div>
    <p class="note" style="margin-top:10px;border:0;padding:0">${rows.length} sor.
     A „Csapat-teszt" fülön a <b>Csak zöldek</b> változat pontosan ezekre a zöldekre szorít —
     a kapus kivételével, mert a kapus-tábláról nincs kép.</p>`;
}

let sqSrc = null, sqVar = 'free';
function renderSq() {
  const Q = D.sq, box = document.getElementById('sqview');
  if (!Q) { box.innerHTML = '<p class="note">Nincs csapat-teszt adat (optimise_squad.py).</p>'; return; }
  const keys = Object.keys(Q.sources);
  if (!sqSrc || !keys.includes(sqSrc)) sqSrc = keys[0];
  const S0 = Q.sources[sqSrc], R = S0.variants[sqVar];
  const gwLabels = Array.from({length: Q.gws}, (_, i) => Q.gw_from + i);

  // összehasonlító tábla: minden forrás x minden változat
  const cmpTbl = `<div class="tw"><table>
    <thead><tr><th class="l">Változat</th>${keys.map(k =>
      `<th>${esc(Q.sources[k].label)}</th>`).join('')}<th>Különbség</th></tr></thead><tbody>` +
    Q.variants.map(v => {
      const vals = keys.map(k => Q.sources[k].variants[v.key]);
      const best = Math.max(...keys.map(k => Q.sources[k].variants.free?.total || 0));
      return `<tr class="${v.key === sqVar ? 'hi' : ''}">
        <td class="l nm2">${esc(v.label)}</td>` +
        vals.map(r2 => `<td>${r2 ? r2.total.toFixed(1) : '–'}</td>`).join('') +
        `<td class="dimc">${vals.every(Boolean)
          ? (vals[0].total - vals[1].total >= 0 ? '+' : '') + (vals[0].total - vals[1].total).toFixed(1)
          : '–'}</td></tr>`;
    }).join('') + '</tbody></table></div>';

  const cols = [['GKP','Kapus'],['DEF','Védelem'],['MID','Középpálya'],['FWD','Támadók']]
    .map(([p, label]) => {
      const g = R.squad.filter(x => x.pos === p).sort((a, b) =>
        (b.pts.reduce((s2,v)=>s2+v,0)) - (a.pts.reduce((s2,v)=>s2+v,0)));
      const startsAll = new Set(R.rounds.flatMap(rd => rd.xi));
      return `<div class="col"><h3>${label}<span>${g.length}</span></h3><ol class="list">` +
        g.map((x, i) => `<li class="${startsAll.has(x.id) ? '' : 'bench2'}">
          <span class="ix">${i + 1}</span>
          <span class="nm">${esc(x.web)}<em>${esc(x.club)} · £${x.cost.toFixed(1)}m</em></span>
          <span class="rt"><span class="p">${x.pts.reduce((s2,v)=>s2+v,0).toFixed(1)}</span>
            <span class="x">${x.pts.map(v => v.toFixed(1)).join(' / ')}</span></span></li>`).join('') +
        '</ol></div>';
    }).join('');

  const capName = id => (R.squad.find(x => x.id === id) || {}).web || '?';
  box.innerHTML = `
    <div class="sqbar">
      <span class="lbl">becslés</span><span class="grp">${keys.map(k =>
        `<button class="b" data-sqsrc="${k}" aria-pressed="${k === sqSrc}">${esc(Q.sources[k].label)}</button>`).join('')}</span>
      <span class="lbl">változat</span><span class="grp">${Q.variants.map(v =>
        `<button class="b" data-sqvar="${v.key}" aria-pressed="${v.key === sqVar}">${esc(v.label)}</button>`).join('')}</span>
    </div>
    <p class="note" style="margin-top:12px;border:0;padding:0">
      Exakt MILP: 15 fő · 2-5-5-3 · max 3 játékos klubonként · £${Q.budget.toFixed(1)}m.
      A cél a <b>kezdő XI</b> összpontja GW${gwLabels[0]}–${gwLabels[gwLabels.length-1]}-ra,
      DE GW${Q.bboost_gw}-ben <b style="color:var(--coral)">bench boost</b> van, ott
      <b>mind a 15</b> pontja számít. Kapitány minden fordulóban duplázik.
      Halványan a keretben lévő, de egyszer sem kezdő játékos. Választható készlet: ${S0.pool} fő.</p>
    <div class="sqhead">
      <span><span class="lbl2">összes projektált pont</span><br><span class="big">${R.total.toFixed(1)}</span></span>
      <span><span class="lbl2">keret értéke</span><br><span class="big">£${R.cost.toFixed(1)}m</span></span>
    </div>
    <div class="rnd">${R.rounds.map(rd =>
      `<span>GW${rd.gw}: <b>${rd.pts.toFixed(1)}</b> · C: <b>${esc(capName(rd.captain))}</b>${
        rd.bboost ? ' · <b style="color:var(--coral)">bench boost</b>' : ''}</span>`).join('')}</div>
    <div class="sqgrid">${cols}</div>
    <h3 class="sechd">Minden változat, mindkét becsléssel</h3>
    <p>a „Különbség" a két forrás közti eltérés ugyanarra a változatra</p>
    ${cmpTbl}`;
}

function renderCmp() {
  const C = D.cmp, box = document.getElementById('cmpview');
  if (!C) { box.innerHTML = '<p class="note">Nincs összevetés-adat (futtasd a compare_sources.py-t).</p>'; return; }
  const K = Object.keys(C.labels);
  const L = k => esc(C.labels[k]);
  const rhoTbl = (obj, cap) => `<div class="tw"><table>
    <thead><tr><th class="l">${cap}</th>${K.map(k=>`<th>${L(k)}</th>`).join('')}</tr></thead><tbody>` +
    K.map(a=>`<tr><td class="l nm2">${L(a)}</td>` + K.map(b=>{
      if (a===b) return '<td class="dimc">·</td>';
      const v = obj[a+'|'+b] || obj[b+'|'+a];
      return `<td class="${v && v.rho>=0.7?'hot':'dimc'}">${v&&v.rho!=null?v.rho.toFixed(2):'–'}</td>`;
    }).join('') + '</tr>').join('') + '</tbody></table></div>';

  const rot = C.rows.filter(r=>r.kind==='rotation');
  const val = C.rows.filter(r=>r.kind==='value');
  const list = (arr, n) => `<div class="tw"><table>
    <thead><tr><th class="l">Játékos</th><th>Poz</th>${K.map(k=>`<th>${L(k)}</th>`).join('')}
      <th>Szórás</th><th>FPL Hub perc</th><th class="l">Kinél van</th></tr></thead><tbody>` +
    arr.slice(0,n).map(r=>`<tr><td class="l nm2">${esc(r.n)} <span class="dimc" style="font-family:var(--mono);font-size:9px">${esc(r.club)}</span></td>
      <td class="dimc">${r.pos}</td>` +
      K.map(k=>`<td>${r.vals[k].toFixed(1)}</td>`).join('') +
      `<td class="hot">${r.spread.toFixed(1)}</td>
       <td class="dimc">${r.ffhub_mins!=null?r.ffhub_mins+"'":'–'}</td>
       <td class="l">${r.owner?esc(r.owner):'<span class="ow free">szabad</span>'}</td></tr>`).join('') +
    '</tbody></table></div>';

  box.innerHTML = `
    <h3 class="sechd">Mennyire értenek egyet</h3>
    <p>Spearman-rho a GW${C.gw_from}–${C.gw_from+C.horizon-1} összegen. 1,0 = azonos sorrend.</p>
    ${rhoTbl(C.agreement, 'mindenkin')}
    <p style="margin-top:9px">Csak azokon, akit <b style="color:var(--fg)">mindegyik forrás kezdőnek tart</b> —
    ez mutatja a valódi érték-egyezést, a kezdő-kérdés nélkül.</p>
    ${rhoTbl(C.agreement_starters, 'csak kezdőkön')}

    <h3 class="sechd">1. Kezdő-vita — valaki szerint nem is játszik</h3>
    <p>${rot.length} ilyen eset. Az FPL Hub várható perce megmutatja, miért ad nullát.</p>
    ${list(rot, 14)}

    <h3 class="sechd">2. Érték-vita — mind kezdőnek tartja, mégis eltérnek</h3>
    <p>${val.length} ilyen eset. Itt a modellek a játékos szintjéről vitáznak, nem a szerepéről.</p>
    ${list(val, 16)}`;
}

document.addEventListener('click', ev => {
  const b = ev.target.closest('.b');
  if (b && (b.dataset.cspos || b.dataset.csgreen)) {
    if (b.dataset.cspos) csPos = b.dataset.cspos;
    if (b.dataset.csgreen) csOnlyGreen = !csOnlyGreen;
    renderCs(); return;
  }
  if (b && (b.dataset.sqsrc || b.dataset.sqvar)) {
    if (b.dataset.sqsrc) sqSrc = b.dataset.sqsrc;
    if (b.dataset.sqvar) sqVar = b.dataset.sqvar;
    renderSq(); return;
  }
  if (b) { if (b.dataset.src) src = b.dataset.src;
           if (b.dataset.g !== undefined) gw = b.dataset.g;
           if (b.dataset.f) filt = b.dataset.f;
           if (b.dataset.s) sortBy = b.dataset.s; render(); return; }
  const t = ev.target.closest('[role="tab"]');
  if (t) {
    view = t.id === 't-fpl' ? 'fpl' : t.id === 't-cmp' ? 'cmp'
         : t.id === 't-sq' ? 'sq' : t.id === 't-cs' ? 'cs' : 'draft';
    document.querySelectorAll('[role="tab"]').forEach(x => x.setAttribute('aria-selected', x === t));
    const isCmp = view === 'cmp', isSq = view === 'sq', isCs = view === 'cs';
    document.getElementById('cmpview').hidden = !isCmp;
    document.getElementById('sqview').hidden = !isSq;
    document.getElementById('csview').hidden = !isCs;
    document.getElementById('cols').hidden = isCmp || isSq || isCs;
    document.querySelector('.ctl').hidden = isCmp || isSq || isCs;
    if (isCmp) renderCmp(); else if (isSq) renderSq();
    else if (isCs) renderCs(); else render();
  }
});
render();
</script>
"""

out = pathlib.Path(A.out)
out.write_text(TPL.replace("__HEAD__", theme.HEAD).replace("__PAY__", PAY), encoding="utf-8")
print(f"{out.name}: {out.stat().st_size} bájt · {len(players)} játékos · fordulók {gws[0]}–{gws[-1]}")
if fpl_note: print("  megjegyzés:", fpl_note)

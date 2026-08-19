#!/usr/bin/env python3
"""Titkos oldal: fordulónkénti becsült pontok, draft- és fantasy-nézetben.

NEM megy nyílt webre: az FPL Hub fizetős adatára épül, és a draft-nézet
szándékosan megmutatja, kinél van kicsi és ki a szabad (ez versenyelőny).
"""
import argparse, json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import theme

HERE = pathlib.Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--out", default=str(HERE / "secret.html"))
ap.add_argument("--fpl-entry", type=int, default=117238, help="a saját (nem draft) FPL csapat")
A = ap.parse_args()

hub = json.loads((HERE / "ffhub" / "ffhub_raw.json").read_text(encoding="utf-8"))
idmap = json.loads((HERE / "idmap.json").read_text(encoding="utf-8"))
M2D = {int(k): v for k, v in idmap["main_to_draft"].items()}
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

ME_DRAFT = 106153                        # Attila draft-entryje
owner, mine_draft = {}, set()
for m in data["managers"]:
    for s in m["squad"]:
        owner[s["id"]] = {"first": m["first"], "ini": m["initials"], "me": m["entry"] == ME_DRAFT}
        if m["entry"] == ME_DRAFT: mine_draft.add(s["id"])

# a sima FPL keret deadline előtt 404 — ha megjön, kiemeljük
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

PAY = json.dumps({"taken_at": hub["taken_at"], "gws": gws, "players": players,
                  "fpl_note": fpl_note, "fpl_squad_size": len(fpl_squad),
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
  </div>

  <div class="ctl">
    <span class="lbl">forduló</span><span class="grp" id="gws"></span>
    <span class="lbl">mutasd</span><span class="grp" id="filt"></span>
    <span class="lbl">rendezés</span><span class="grp" id="sort"></span>
  </div>

  <p class="warn" id="fplnote" hidden></p>
  <div class="cols" id="cols"></div>
  <p class="note" id="foot"></p>
</div>

<script id="p" type="application/json">__PAY__</script>
<script>
const D = JSON.parse(document.getElementById('p').textContent);
const POS = [['GKP','Kapus'],['DEF','Védelem'],['MID','Középpálya'],['FWD','Támadók']];
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let view = 'draft', gw = String(D.gws[0]), filt = 'all', sortBy = 'pts';
const SUM = 'sum';

const val = p => {
  if (gw === SUM) return Object.values(p.gw).reduce((a, v) => a + v.pts, 0);
  return p.gw[gw] ? p.gw[gw].pts : null;
};
const mins = p => (gw !== SUM && p.gw[gw]) ? p.gw[gw].min : null;
const fx = p => (gw !== SUM && p.gw[gw]) ? `${p.gw[gw].opp}${p.gw[gw].h ? '(H)' : '(A)'}` : null;

function render() {
  document.getElementById('gws').innerHTML =
    D.gws.map(g => `<button class="b" data-g="${g}" aria-pressed="${String(g) === gw}">${g}.</button>`).join('')
    + `<button class="b" data-g="${SUM}" aria-pressed="${gw === SUM}">${D.gws.length} forduló</button>`;
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
    `<b>Forrás.</b> Fantasy Football Hub PRO-modell, lehúzva ${esc(D.taken_at.replace('T',' ').replace('Z',' UTC'))}.
     Fordulónkénti pont és várható játékperc; a gyűjtés bejelentkezést kér, ezért kézi lépés.<br>
     <b>Draft-nézet.</b> A monogram a birtokos, a szaggatott „szabad" azt jelenti, hogy senki
     keretében sincs — ezek a waiver-célpontok. A sajátjaid coral csíkkal.<br>
     <b>Fantasy-nézet.</b> Ár és a mezőny tulajdonlási aránya, a sima FPL csapatodhoz.<br>
     <b>Miért titkos.</b> Egyrészt fizetős adat, amit nem adunk tovább. Másrészt a szabad
     játékosok listája versenyelőny a ligában — ezért nincs a publikus oldalon.`;
}

document.addEventListener('click', ev => {
  const b = ev.target.closest('.b');
  if (b) { if (b.dataset.g !== undefined) gw = b.dataset.g;
           if (b.dataset.f) filt = b.dataset.f;
           if (b.dataset.s) sortBy = b.dataset.s; render(); return; }
  const t = ev.target.closest('[role="tab"]');
  if (t) { view = t.id === 't-fpl' ? 'fpl' : 'draft';
           document.querySelectorAll('[role="tab"]').forEach(x =>
             x.setAttribute('aria-selected', x === t)); render(); }
});
render();
</script>
"""

out = pathlib.Path(A.out)
out.write_text(TPL.replace("__HEAD__", theme.HEAD).replace("__PAY__", PAY), encoding="utf-8")
print(f"{out.name}: {out.stat().st_size} bájt · {len(players)} játékos · fordulók {gws[0]}–{gws[-1]}")
if fpl_note: print("  megjegyzés:", fpl_note)

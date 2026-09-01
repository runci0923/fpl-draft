#!/usr/bin/env python3
"""h2h.json -> a forduló-oldal (pályakép, párosítások, tipp)"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import theme

HERE = pathlib.Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--h2h", default=str(HERE / "h2h.json"))
ap.add_argument("--history", default=str(HERE / "history.json"))
ap.add_argument("--data", default=str(HERE / "data.json"))
ap.add_argument("--out", default=str(HERE / "gw.html"))
ap.add_argument("--title", default="Vadkelet — a forduló")
ap.add_argument("--draft-href", default="index.html")
A = ap.parse_args()

H2H = pathlib.Path(A.h2h).read_text(encoding="utf-8")
_hp = pathlib.Path(A.history)
HIST = _hp.read_text(encoding="utf-8") if _hp.exists() else "null"
D = json.loads(pathlib.Path(A.data).read_text(encoding="utf-8"))
MGRS = json.dumps([{"entry": m["entry"], "first": m["first"], "initials": m["initials"],
                    "team": m.get("team", ""), "slot": m.get("slot", 999)} for m in D["managers"]],
                  ensure_ascii=False, separators=(",", ":"))

TPL = r"""<title>__TITLE__</title>__HEAD__
.wrap{max-width:1500px;margin:0 auto;padding:clamp(26px,4.5vw,56px) var(--gutter) 90px}
h1{font-weight:600;font-size:clamp(30px,5vw,52px);line-height:1.03;letter-spacing:-.022em;margin:0 0 12px}
h2{font-size:clamp(18px,2.2vw,24px);font-weight:600;letter-spacing:-.01em;margin:0}
.kicker{font-family:var(--mono);font-size:11.5px;letter-spacing:.15em;text-transform:uppercase;color:var(--coral);margin:0 0 12px}
.lede{max-width:66ch;font-size:clamp(14.5px,1.35vw,17px);color:var(--dim);margin:0}
.lede b{color:var(--fg);font-weight:500}

/* --- oldalnavigáció --- */
.nav{display:flex;gap:4px;margin:24px 0 0;border-bottom:1px solid var(--rule);
  justify-content:flex-end}
.nav .spacer{flex:1 1 auto}
.nav a{padding:10px 17px;color:var(--dim);text-decoration:none;font-size:15px;font-weight:500;
  border-bottom:2px solid transparent;margin-bottom:-1px}
.nav a:hover{color:var(--fg)}
.nav a[aria-current="page"]{color:var(--fg);border-bottom-color:var(--coral)}

/* --- fejléc-csík --- */
.bar{display:flex;flex-wrap:wrap;gap:11px 16px;align-items:center;margin-top:22px;padding:13px 16px;
  background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);box-shadow:var(--sh-sm)}
.bar .lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.bar .v{font-family:var(--mono);font-size:12px}
.bar .v b{font-weight:500}
.pills{display:flex;gap:7px;flex-wrap:wrap;margin-left:auto}
.pill{padding:5px 12px;border-radius:999px;border:1.5px solid var(--rule);background:transparent;
  color:var(--fg);cursor:pointer;font-family:var(--display);font-size:13.5px;font-weight:500}
.pill[aria-pressed="true"]{background:var(--fg);border-color:var(--fg);color:var(--bg)}
.state{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;
  padding:2px 8px;border-radius:999px;border:1px solid var(--coral);color:var(--coral)}

/* --- párosítás --- */
.tie{margin-top:26px;background:var(--surface);border:1px solid var(--rule);
  border-radius:var(--r-lg);box-shadow:var(--sh-md);overflow:hidden}
.tie-h{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center;
  padding:15px 18px;border-bottom:1px solid var(--rule);background:var(--surface-2)}
.side{min-width:0}
.side.r{text-align:right}
.side .who{font-size:19px;font-weight:600;letter-spacing:-.01em}
.side .sub{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}
.vs{text-align:center}
.vs .sc{font-size:26px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums;white-space:nowrap}
.vs .sc .mid{color:var(--dim);font-weight:400;margin:0 6px}
.vs .tip{font-family:var(--mono);font-size:10px;letter-spacing:.05em;color:var(--coral);margin-top:2px}
.vs .tip.draw{color:var(--dim)}
.win{color:var(--coral)}

.pitches{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule)}
@media (max-width:880px){.pitches{grid-template-columns:1fr}}

/* --- pálya --- */
.pitch{background:var(--surface);padding:16px 14px 12px;position:relative}
.turf{position:relative;border-radius:var(--r-md);padding:14px 10px 10px;
  background:
    linear-gradient(var(--turf-a),var(--turf-a)),
    repeating-linear-gradient(180deg,var(--turf-b) 0 34px,transparent 34px 68px);
  border:1px solid var(--turf-line);display:flex;flex-direction:column;gap:11px}
.turf::before{content:"";position:absolute;left:8%;right:8%;top:50%;height:1px;background:var(--turf-line)}
.turf::after{content:"";position:absolute;left:50%;top:50%;width:74px;height:74px;margin:-37px 0 0 -37px;
  border:1px solid var(--turf-line);border-radius:50%}
:root{--turf-a:#E7EEE2;--turf-b:#DDE7D7;--turf-line:#B7C6AE}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --turf-a:#212A38;--turf-b:#252F3E;--turf-line:#46536A}}
:root[data-theme="dark"]{--turf-a:#212A38;--turf-b:#252F3E;--turf-line:#46536A}
.row{display:flex;justify-content:center;gap:7px;flex-wrap:wrap;position:relative;z-index:1}
.pl{width:96px;background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-sm);
  padding:5px 4px;text-align:center;box-shadow:var(--sh-sm)}
.pl .n,.pl .fx,.pl .pt{display:block}
.pl .n{font-size:11.5px;font-weight:600;line-height:1.15;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pl .fx{font-family:var(--mono);font-size:8px;letter-spacing:.03em;color:var(--dim);margin-top:1px}
.pl .pt{font-family:var(--mono);font-size:13px;font-weight:500;margin-top:2px;font-variant-numeric:tabular-nums}
.pl.top .pt{color:var(--coral)}
.pl .real{display:block;font-family:var(--mono);font-size:9px;color:var(--dim)}
.pl.out{border-style:dashed;opacity:.62}
.pl .mark{position:absolute;margin:-13px 0 0 62px;font-family:var(--mono);font-size:8px;
  background:var(--coral);color:#fff;border-radius:999px;padding:0 4px}
.plabel{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--dim);text-align:center;margin-bottom:-6px}
.bench{margin-top:12px;padding-top:11px;border-top:1px dashed var(--rule)}
.bench .plabel{text-align:left;margin-bottom:7px}
.bench .row{justify-content:flex-start;align-items:flex-start}
.bgrp{display:flex;gap:7px}
.bgrp.gk{padding-right:13px;margin-right:6px;border-right:1px solid var(--rule);position:relative}
.bgrp.gk::after{content:"kapus";position:absolute;right:13px;bottom:-15px;font-family:var(--mono);
  font-size:7.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.tot{display:flex;justify-content:space-between;align-items:baseline;margin-top:11px;
  font-family:var(--mono);font-size:11px;color:var(--dim)}
.tot b{font-family:var(--display);font-size:21px;font-weight:600;color:var(--fg);
  font-variant-numeric:tabular-nums}
.dlstrip{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.dlstrip span{font-family:var(--mono);font-size:11px;padding:5px 11px;border-radius:999px;
  border:1px solid var(--rule);color:var(--dim)}
.dlstrip span b{color:var(--fg);font-weight:500}
.dlstrip span.nx{border-color:var(--coral);color:var(--coral)}
.dlstrip span.nx b{color:var(--coral)}
.gwb{font-family:var(--mono);font-size:11.5px;padding:5px 12px;border-radius:999px;
  border:1.5px solid var(--rule);background:transparent;color:var(--dim);cursor:pointer}
.gwb:hover{border-color:var(--fg);color:var(--fg)}
.gwb[aria-pressed="true"]{background:var(--fg);border-color:var(--fg);color:var(--bg)}
.gwb.done{border-style:solid}
.gwb.fut{border-style:dashed}
.hit{color:var(--coral);font-weight:500}
.miss{color:var(--dim)}
.prov{font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;
  border:1px solid var(--coral);color:var(--coral);border-radius:999px;padding:1px 7px;margin-left:8px}
.htbl{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r-md);
  background:var(--surface);box-shadow:var(--sh-sm);margin-top:16px}
.htbl table{width:100%;border-collapse:collapse;min-width:640px}
.htbl th{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--dim);font-weight:400;text-align:right;padding:11px 10px;border-bottom:1px solid var(--rule)}
.htbl th.l,.htbl td.l{text-align:left}
.htbl td{padding:10px;border-bottom:1px solid var(--rule);font-size:13.5px;text-align:right;
  font-variant-numeric:tabular-nums;white-space:nowrap}
.htbl tr:last-child td{border-bottom:0}
.htbl td.nm3{font-weight:500;font-size:14.5px}
.d-pos{color:var(--coral)}
.empty2{padding:22px;border:1px dashed var(--rule);border-radius:var(--r-md);
  font-family:var(--mono);font-size:11.5px;line-height:1.75;color:var(--dim)}
.empty2 b{color:var(--fg);font-weight:500}
.note{margin-top:clamp(34px,5vw,58px);padding-top:18px;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:11px;line-height:1.75;color:var(--dim);max-width:84ch}
.note b{color:var(--fg);font-weight:500}
.empty{padding:26px;text-align:center;font-family:var(--mono);font-size:12px;color:var(--dim)}
:focus-visible{outline:2px solid var(--coral);outline-offset:2px}
</style>

<div class="wrap">
  <p class="kicker" id="kick"></p>
  <h1 id="h1">A forduló</h1>
  <p class="lede" id="lede"></p>

  <nav class="nav">
    <span class="spacer"></span>
    <a href="#" aria-current="page">A forduló</a>
    <a href="__DRAFT_HREF__">Draft</a>
  </nav>

  <div class="bar">
    <span><span class="lbl">forduló</span> <span class="v" id="bgw"></span></span>
    <span><span class="lbl">becslés kelte</span> <span class="v" id="bsnap"></span></span>
    <span id="bstate"></span>
    <span class="pills" id="pills" role="group" aria-label="Projekciós forrás"></span>
  </div>

  <div class="dlstrip" id="gwpick"></div>
  <div class="dlstrip" id="dls"></div>

  <div id="ties"></div>

  <div class="sec">
    <div class="sec-h"><h2>Fordulók</h2>
      <p>lezárt fordulóknál a tipp és a végeredmény &middot; a jövőnél a becslés</p></div>
    <div id="histview"></div>
  </div>

  <p class="note" id="foot"></p>
</div>

<script id="h2h" type="application/json">__H2H__</script>
<script id="histdata" type="application/json">__HIST__</script>
<script id="mgrs" type="application/json">__MGRS__</script>
<script>
const H = JSON.parse(document.getElementById('h2h').textContent);
const M = JSON.parse(document.getElementById('mgrs').textContent);
const NAME = Object.fromEntries(M.map(m => [m.entry, m]));
let GW = String(H.next_event || H.current_event || Object.keys(H.rounds)[0]);
const HI0 = JSON.parse(document.getElementById('histdata').textContent || 'null');
const LOCKED = Object.fromEntries(((HI0 && HI0.rounds) || []).map(r => [String(r.gw), r]));
const ALLGW = [...new Set([...Object.keys(H.rounds || {}), ...Object.keys(LOCKED)])]
  .map(Number).sort((a, b) => a - b);
// alap: a legfrissebb LEZÁRT forduló, ha van; különben a következő
if (Object.keys(LOCKED).length) GW = String(Math.max(...Object.keys(LOCKED).map(Number)));
const SRCS = Object.entries(H.sources).map(([slug, s]) => ({slug, ...s}));
// alapértelmezés: FPL Hub (a tulaj választása), különben az első elérhető
let active = ['ffhub','fplform'].find(k => SRCS.some(s => s.slug === k)) || (SRCS[0] || {}).slug;

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ROWS = [['GKP','Kapus'],['DEF','Védelem'],['MID','Középpálya'],['FWD','Támadók']];

function playerCard(p, opts = {}) {
  const started = opts.realXi ? opts.realXi.includes(p.id) : null;
  const cls = ['pl'];
  if (opts.top) cls.push('top');
  if (started === false && opts.inXi) cls.push('out');
  return `<span class="${cls.join(' ')}">
    ${started === true && !opts.inXi ? '<span class="mark">kezdett</span>' : ''}
    <span class="n">${esc(p.n)}</span>
    <span class="fx">${esc(p.c)}${p.opp ? ' · ' + esc(p.opp) : ''}</span>
    <span class="pt">${p.proj.toFixed(1)}${p.act !== null && p.act !== undefined
      ? `<span class="real">valós ${p.act}</span>` : ''}</span>
  </span>`;
}

function lockedPitch(ent, t, srcKey) {
  const rows = ROWS.map(([k]) => {
    const g = t.xi.filter(p => p.p === k);
    if (!g.length) return '';
    return `<div class="row">${g.map(p => `<span class="pl">
      <span class="n">${esc(p.n)}</span>
      <span class="fx">${esc(p.c || '')} · ${p.p}</span>
      <span class="pt">${p.real !== null && p.real !== undefined
        ? p.real + `<span class="real">tipp ${(p.tip[srcKey] ?? 0).toFixed(1)}</span>`
        : (p.tip[srcKey] ?? 0).toFixed(1)}</span></span>`).join('')}</div>`;
  }).join('');
  const bGk = t.bench.filter(p => p.p === 'GKP'), bOut = t.bench.filter(p => p.p !== 'GKP');
  const card = p => `<span class="pl"><span class="n">${esc(p.n)}</span>
    <span class="fx">${esc(p.c || '')} · ${p.p}</span>
    <span class="pt">${p.real !== null && p.real !== undefined
      ? p.real + `<span class="real">tipp ${(p.tip[srcKey] ?? 0).toFixed(1)}</span>`
      : (p.tip[srcKey] ?? 0).toFixed(1)}</span></span>`;
  const shown = t.real ? t.real.xi : (t.tip[srcKey] || {}).xi;
  return `<div class="pitch">
    <div class="turf">${rows}</div>
    <div class="bench"><div class="plabel">Kispad</div><div class="row">
      <span class="bgrp gk">${bGk.map(card).join('')}</span>
      <span class="bgrp">${bOut.map(card).join('')}</span></div></div>
    <div class="tot"><span>${t.real ? 'valós / tipp' : 'tipp'}</span>
      <b>${t.real ? t.real.xi + ' / ' + ((t.tip[srcKey] || {}).xi ?? 0).toFixed(1)
                  : (((t.tip[srcKey] || {}).xi) ?? 0).toFixed(1)}</b></div>
  </div>`;
}

function pitch(ent, t, realMode) {
  const best = Math.max(...t.xi.map(p => p.proj));
  const rows = ROWS.map(([k, label]) => {
    const g = t.xi.filter(p => p.p === k);
    if (!g.length) return '';
    return `<div class="row">${g.map(p => playerCard(p,
      {top: p.proj === best, inXi: true, realXi: realMode ? t.real_xi : null})).join('')}</div>`;
  }).join('');
  // a kispadon a kapus MINDIG első és külön csoportban áll
  const bGk = t.bench.filter(p => p.p === 'GKP');
  const bOut = t.bench.filter(p => p.p !== 'GKP')
    .sort((a, b) => b.proj - a.proj);
  const opt = {inXi: false, realXi: realMode ? t.real_xi : null};
  const bench = `<span class="bgrp gk">${bGk.map(p => playerCard(p, opt)).join('')}</span>` +
                `<span class="bgrp">${bOut.map(p => playerCard(p, opt)).join('')}</span>`;
  const shown = realMode && t.real_total !== null && t.real_total !== undefined;
  return `<div class="pitch">
    <div class="turf">${rows}</div>
    <div class="bench"><div class="plabel">Kispad</div><div class="row">${bench}</div></div>
    <div class="tot"><span>${shown ? 'valós / projektált' : 'projektált összesen'}</span>
      <b>${shown ? t.real_total + ' / ' + t.proj.toFixed(1) : t.proj.toFixed(1)}</b></div>
  </div>`;
}

function renderPick() {
  document.getElementById('gwpick').innerHTML = ALLGW.map(g => {
    const l = LOCKED[String(g)];
    const tag = l ? (l.has_real ? 'eredmény' : 'lezárva') : 'becslés';
    return `<button class="gwb ${l ? 'done' : 'fut'}" data-hgw="${g}"
      aria-pressed="${String(g) === GW}">GW${g} · ${tag}</button>`;
  }).join('');
}

function render() {
  renderPick();
  const lock = LOCKED[GW];
  if (lock) return renderLocked(lock);
  const r = (H.rounds[GW] || {})[active];
  document.getElementById('kick').textContent =
    `${H.league.name} · ${H.league.size} csapat · FPL Draft ${'2026/27'}`;
  document.getElementById('h1').textContent = `${GW}. forduló`;
  document.getElementById('lede').innerHTML = `<b>Még hátralévő forduló:</b> mindenki kerete a
    pályán, a <b>projektált pont szerinti legjobb legális felállásban</b> — vagyis kiket
    <i>kellene</i> játszatni. Egymás mellett a párosítás két csapata, és hogy ebből ki nyerne.`;
  document.getElementById('bgw').innerHTML = `<b>${GW}.</b>`;
  document.getElementById('bsnap').innerHTML = `<b>${esc(H.taken_at.replace('T',' ').replace('Z',' UTC'))}</b>`;
  const anyReal = r && Object.values(r.teams).some(t => t.real_xi);
  document.getElementById('bstate').innerHTML = anyReal
    ? '<span class="state">tényleges felállás</span>'
    : '<span class="state">deadline előtt · projektált</span>';
  document.getElementById('pills').innerHTML = SRCS.map(s =>
    `<button class="pill" data-s="${s.slug}" aria-pressed="${s.slug === active}">${esc(s.label)}</button>`).join('');

  if (!r) { document.getElementById('ties').innerHTML =
    `<p class="empty">Ehhez a fordulóhoz még nincs becslés ezen a forráson.</p>`; return; }

  document.getElementById('ties').innerHTML = r.matches.map(m => {
    const h = NAME[m.home], a = NAME[m.away];
    const th = r.teams[m.home], ta = r.teams[m.away];
    const useReal = anyReal && th.real_total !== null && ta.real_total !== null;
    const sh = useReal ? th.real_total : th.proj, sa = useReal ? ta.real_total : ta.proj;
    const diff = Math.abs(sh - sa);
    const tip = sh > sa ? `${esc(h.first)} nyer, ${diff.toFixed(1)} ponttal`
              : sa > sh ? `${esc(a.first)} nyer, ${diff.toFixed(1)} ponttal` : 'döntetlen';
    const fmt = v => useReal ? v : v.toFixed(1);
    return `<section class="tie">
      <header class="tie-h">
        <span class="side"><span class="who ${sh > sa ? 'win' : ''}">${esc(h.first)}</span>
          <span class="sub">${esc(h.initials)}${h.team ? ' · ' + esc(h.team) : ''}</span></span>
        <span class="vs">
          <span class="sc"><span class="${sh > sa ? 'win' : ''}">${fmt(sh)}</span>
            <span class="mid">–</span><span class="${sa > sh ? 'win' : ''}">${fmt(sa)}</span></span>
          <span class="tip${sh === sa ? ' draw' : ''}">${useReal ? '' : 'tipp: '}${tip}</span>
        </span>
        <span class="side r"><span class="who ${sa > sh ? 'win' : ''}">${esc(a.first)}</span>
          <span class="sub">${esc(a.initials)}${a.team ? ' · ' + esc(a.team) : ''}</span></span>
      </header>
      <div class="pitches">${pitch(m.home, th, anyReal)}${pitch(m.away, ta, anyReal)}</div>
    </section>`;
  }).join('');

  const s = SRCS.find(x => x.slug === active) || {};
  document.getElementById('foot').innerHTML =
    `<b>Becslés.</b> ${esc(s.label || '')} — ${esc(s.note || '')}. A pályán a becslés szerinti
     legjobb legális felállás (11 fő, 1 kapus, 3–5 védő, 2–5 középpályás, 1–3 csatár);
     a kiemelt szám a keret legjobb becsült játékosa. A fixtúra a játékos klubjának
     ellenfele ebben a fordulóban.<br>
     <b>Snapshot.</b> Minden gyűjtés külön fájl UTC-időbélyeggel; a deadline előtti utolsó
     a kanonikus — az az információ, amiből dönteni lehetett.<br>
     <b>Deadline után.</b> A lap a tényleges felállásra vált: szaggatott kerettel jelöli, akit
     a becslés kezdett volna, de a padon maradt, és „kezdett" jelöléssel azt, aki a
     kispadról bekerült. Így látszik, mennyit ért a döntés.<br>
     <b>Igazolások.</b> A keretet minden futás az élő birtoklásból veszi, tehát a waiver és
     a csere magától átjön. A változások a <code>rosters.json</code> git-történetében
     olvashatók: <code>git log -p rosters.json</code>.`;
}

function renderLocked(lock) {
  const avail = SRCS.filter(s => LOCKED[GW] && Object.keys(lock.teams).length
    && Object.values(lock.teams)[0].tip && Object.values(lock.teams)[0].tip[s.slug]);
  const use = avail.some(s => s.slug === active) ? active : (avail[0] || {}).slug;
  document.getElementById('kick').textContent =
    `${H.league.name} · ${H.league.size} csapat · FPL Draft 2026/27`;
  document.getElementById('h1').textContent = `${GW}. forduló`;
  document.getElementById('lede').innerHTML = lock.has_real
    ? `<b>Lezárt forduló:</b> a pályán a <b>tényleges</b> felállás, a nagy szám a
       <b>valós pont</b>, alatta a deadline előtti <b>tipp</b>. Így egymás mellett látszik,
       mit mondott a becslés és mi lett belőle.`
    : `<b>Lezárt forduló:</b> a pályán a <b>tényleges</b> felállás és a deadline előtti
       <b>tipp</b>. A valós pontok még nincsenek meg.`;
  document.getElementById('bgw').innerHTML = `<b>${GW}.</b>`;
  document.getElementById('bsnap').innerHTML =
    `<b>${esc((lock.snapshot_at || '').replace('T', ' ').replace(':00Z', ' UTC'))}</b>`;
  document.getElementById('bstate').innerHTML = lock.has_real
    ? `<span class="state">${lock.provisional ? 'ideiglenes eredmény' : 'végleges eredmény'}</span>`
    : '<span class="state">lezárva · eredményre vár</span>';
  document.getElementById('pills').innerHTML = avail.map(s =>
    `<button class="pill" data-s="${s.slug}" aria-pressed="${s.slug === use}">${esc(s.label)}</button>`).join('');

  const nmOf = e => (HI0 && HI0.managers[e] ? HI0.managers[e].first : (NAME[e] || {}).first || e);
  document.getElementById('ties').innerHTML = (lock.matches || []).map(m => {
    const th = lock.teams[m.home], ta = lock.teams[m.away];
    const useReal = !!(th.real && ta.real);
    const sh = useReal ? th.real.xi : (th.tip[use] || {}).xi;
    const sa = useReal ? ta.real.xi : (ta.tip[use] || {}).xi;
    const diff = Math.abs(sh - sa);
    const txt = sh > sa ? `${esc(nmOf(m.home))} nyer, ${diff.toFixed(1)} ponttal`
              : sa > sh ? `${esc(nmOf(m.away))} nyer, ${diff.toFixed(1)} ponttal` : 'döntetlen';
    const fmt = v => useReal ? v : v.toFixed(1);
    return `<section class="tie">
      <header class="tie-h">
        <span class="side"><span class="who ${sh > sa ? 'win' : ''}">${esc(nmOf(m.home))}</span>
          <span class="sub">tényleges felállás</span></span>
        <span class="vs"><span class="sc"><span class="${sh > sa ? 'win' : ''}">${fmt(sh)}</span>
          <span class="mid">–</span><span class="${sa > sh ? 'win' : ''}">${fmt(sa)}</span></span>
          <span class="tip${sh === sa ? ' draw' : ''}">${useReal ? '' : 'tipp: '}${txt}</span></span>
        <span class="side r"><span class="who ${sa > sh ? 'win' : ''}">${esc(nmOf(m.away))}</span>
          <span class="sub">tényleges felállás</span></span>
      </header>
      <div class="pitches">${lockedPitch(m.home, th, use)}${lockedPitch(m.away, ta, use)}</div>
    </section>`;
  }).join('');

  const s0 = SRCS.find(x => x.slug === use) || {};
  document.getElementById('foot').innerHTML =
    `<b>Ez egy lezárt forduló.</b> A pályán a <b>tényleges</b> felállás áll — az, amit valóban
     kiállítottak. A kártyán a nagy szám a ${lock.has_real ? 'VALÓS pont, alatta a tipp'
     : 'tipp (a valós pontok még nincsenek meg)'}. A tipp a
     ${esc((lock.snapshot_at || '').replace('T', ' ').replace(':00Z', ' UTC'))}-i,
     tehát a deadline előtti utolsó becslésből (${esc(s0.label || '')}).<br>
     <b>Miért nem módosítható.</b> A tipp csak akkor tipp, ha a deadline előtt rögzítettük.
     Utólag nem írjuk át — ez a mérés lényege.`;
  renderHist();
}

/* ---------- deadline-csík + tipp/valóság ---------- */
const HI = JSON.parse(document.getElementById('histdata').textContent || 'null');

let hgw = null;   // a lenti szekció a fenti választót követi

function gwCatalog() {
  const locked = {}, proj = {};
  for (const r of (HI && HI.rounds) || []) locked[r.gw] = r;
  for (const k of Object.keys(H.rounds || {})) proj[+k] = true;
  const all = [...new Set([...Object.keys(locked).map(Number), ...Object.keys(proj).map(Number)])]
    .sort((a, b) => a - b);
  return {locked, proj, all};
}

function renderHist() {
  const strip = document.getElementById('dls');
  if (HI && HI.upcoming && HI.upcoming.length) {
    const fmt = t => t.replace('T', ' ').replace(':00Z', ' UTC');
    strip.innerHTML = HI.upcoming.slice(0, 4).map((e, i) =>
      `<span class="${i === 0 ? 'nx' : ''}">GW${e.gw} deadline: <b>${esc(fmt(e.deadline))}</b>${
        i === 0 && HI.lock_after_minutes ? ` · lezárás +${HI.lock_after_minutes} perc` : ''}</span>`).join('');
  } else strip.innerHTML = '';

  const {locked, proj, all} = gwCatalog();
  const box = document.getElementById('histview');
  if (!all.length) { box.innerHTML = ''; return; }
  hgw = +GW;

  const nm = e => (HI && HI.managers[e] ? HI.managers[e].first : (NAME[e] || {}).first || e);
  const rd = locked[hgw];

  // --- JÖVŐ: csak becslés van
  if (!rd) {
    const per = H.rounds[String(hgw)] || {};
    const ks = Object.keys(per);
    if (!ks.length) { box.innerHTML = '<p class="empty2">Erre a fordulóra nincs adat.</p>'; return; }
    box.innerHTML = `<p class="empty2" style="border:0;padding:0;margin:10px 0 0">
      GW${hgw} még nem volt — itt a <b>becslés</b> áll, a keretből kihozható legjobb legális
      XI-re. A tipp majd a deadline után a <b>tényleges</b> felállásra rögzül.</p>
      <div class="htbl"><table><thead><tr><th class="l">Párosítás</th>` +
      ks.map(k => `<th>${esc(H.sources[k].label)}</th>`).join('') + `</tr></thead><tbody>` +
      (per[ks[0]].matches || []).map(m => `<tr>
        <td class="l nm3">${esc(nm(m.home))} – ${esc(nm(m.away))}</td>` +
        ks.map(k => {
          const mm = per[k].matches.find(x => x.home === m.home && x.away === m.away);
          if (!mm) return '<td class="dimc">–</td>';
          const w = mm.proj[0] > mm.proj[1] ? nm(m.home) : nm(m.away);
          return `<td class="dimc">${mm.proj[0].toFixed(1)} – ${mm.proj[1].toFixed(1)}
                  <span style="display:block;font-size:10px">${esc(w)}</span></td>`;
        }).join('') + '</tr>').join('') + '</tbody></table></div>';
    return;
  }

  // --- LEZÁRT forduló
  const SR = Object.keys(HI.sources);
  const prov = rd.has_real && (rd.provisional === true);
  let html = `<p class="empty2" style="border:0;padding:0;margin:10px 0 0">
    A tipp a <b>${esc((rd.snapshot_at || '').replace('T', ' ').replace(':00Z', ' UTC'))}</b>-i
    becslésből, a <b>tényleges</b> felállásra — vagyis arra a csapatra, amit valóban kiállítottak.
    ${rd.has_real ? '' : 'A valós pontok még nincsenek meg.'}
    ${prov ? '<span class="prov">ideiglenes — a bónusz még nincs lezárva</span>' : ''}</p>`;

  html += `<div class="htbl"><table><thead><tr><th class="l">Párosítás</th>` +
    SR.map(k => `<th>${esc(HI.sources[k])}</th>`).join('') +
    `<th>Végeredmény</th></tr></thead><tbody>`;
  for (const m of rd.matches) {
    const th = rd.teams[m.home], ta = rd.teams[m.away];
    const realW = th.real && ta.real ? (th.real.xi > ta.real.xi ? m.home : m.away) : null;
    html += `<tr><td class="l nm3">${esc(nm(m.home))} – ${esc(nm(m.away))}</td>` +
      SR.map(k => {
        const a = (th.tip || {})[k], b = (ta.tip || {})[k];
        if (!a || !b) return '<td class="dimc">–</td>';
        const w = a.xi > b.xi ? m.home : m.away;
        const cls = realW === null ? 'dimc' : (w === realW ? 'hit' : 'miss');
        return `<td class="${cls}">${a.xi.toFixed(1)} – ${b.xi.toFixed(1)}
                <span style="display:block;font-size:10px">${esc(nm(w))}${
                  realW === null ? '' : (w === realW ? ' ✓' : ' ✗')}</span></td>`;
      }).join('') +
      `<td>${th.real && ta.real
        ? `<b>${th.real.xi} – ${ta.real.xi}</b><span style="display:block;font-size:10px" class="dimc">${esc(nm(realW))}</span>`
        : '<span class="dimc">–</span>'}</td></tr>`;
  }
  html += '</tbody></table></div>';

  // managerenkénti eltérés
  if (rd.has_real) {
    html += `<h3 style="margin:20px 0 0;font-size:16px">Managerenként</h3>
      <div class="htbl"><table><thead><tr><th class="l">Manager</th>` +
      SR.map(k => `<th>${esc(HI.sources[k])}</th>`).join('') +
      `<th>Valós</th><th>Eltérés</th></tr></thead><tbody>` +
      Object.entries(rd.teams).map(([e, t]) => ({e, t}))
        .filter(x => x.t.real)
        .sort((a, b) => b.t.real.xi - a.t.real.xi)
        .map(({e, t}) => {
          const d = t.real.xi - ((t.tip || {})[SR[0]] || {}).xi;
          return `<tr><td class="l nm3">${esc(nm(e))}</td>` +
            SR.map(k => `<td class="dimc">${(t.tip || {})[k] ? t.tip[k].xi.toFixed(1) : '–'}</td>`).join('') +
            `<td><b>${t.real.xi}</b></td>
             <td class="${Math.abs(d) > 10 ? 'hit' : 'dimc'}">${d >= 0 ? '+' : ''}${d.toFixed(1)}</td></tr>`;
        }).join('') + '</tbody></table></div>';
  }

  // felállítás-hatékonyság
  if (rd.efficiency && Object.keys(rd.efficiency).length) {
    const k0 = Object.keys(rd.efficiency)[0];
    html += `<h3 style="margin:20px 0 0;font-size:16px">Felállítás-hatékonyság</h3>
      <p class="empty2" style="border:0;padding:0;margin:4px 0 0">Mennyit hagyott az asztalon
      a <b>kiállítással</b>: a tényleges XI becsült pontja a keretből kihozható legjobbhoz mérve
      (${esc(HI.sources[k0])}).</p>
      <div class="htbl"><table><thead><tr><th class="l">Manager</th><th>Tényleges</th>
      <th>Legjobb</th><th>Elhagyott</th></tr></thead><tbody>` +
      Object.entries(rd.efficiency[k0]).map(([e, v]) => ({e, ...v}))
        .sort((a, b) => (a.left ?? 99) - (b.left ?? 99))
        .map(v => `<tr><td class="l nm3">${esc(nm(v.e))}</td>
          <td class="dimc">${v.actual.toFixed(1)}</td>
          <td class="dimc">${v.best === null ? '–' : v.best.toFixed(1)}</td>
          <td class="${v.left > 3 ? 'hit' : 'dimc'}">${v.left === null ? '–' : v.left.toFixed(1)}</td>
        </tr>`).join('') + '</tbody></table></div>';
  }

  // utólagos felállítás-hatékonyság: a VALÓS pontokkal
  if (rd.hindsight && Object.keys(rd.hindsight).length) {
    html += `<h3 style="margin:20px 0 0;font-size:16px">Mennyi maradt a padon — utólag</h3>
      <p class="empty2" style="border:0;padding:0;margin:4px 0 0">Ugyanez a <b>tényleges</b>
      pontokkal: a kiállított XI hozama, és amennyit az AKKORI 15-ből ki lehetett volna hozni.
      Ez már nem döntés-minőség, hanem tiszta utólagos mérleg — a becslés nem játszik bele.</p>
      <div class="htbl"><table><thead><tr><th class="l">Manager</th><th>Kiállt</th>
      <th>Legjobb XI</th><th>A padon maradt</th></tr></thead><tbody>` +
      Object.entries(rd.hindsight).map(([e, v]) => ({e, ...v}))
        .sort((a, b) => b.left - a.left)
        .map(v => `<tr><td class="l nm3">${esc(nm(v.e))}</td>
          <td class="dimc">${v.actual}</td><td class="dimc">${v.best.toFixed(0)}</td>
          <td class="${v.left > 5 ? 'hit' : 'dimc'}">${v.left.toFixed(0)}</td>
        </tr>`).join('') + '</tbody></table></div>';
  }

  // forrás-pontosság (összesített)
  if (HI.accuracy && Object.values(HI.accuracy).some(a => a.mae !== null)) {
    const n = Math.max(...Object.values(HI.accuracy).map(a => a.n || 0));
    html += `<h3 style="margin:20px 0 0;font-size:16px">Melyik becslés talál jobban — összesítve</h3>
      <p class="empty2" style="border:0;padding:0;margin:4px 0 0">Átlagos eltérés a kezdő XI-re,
      minden lezárt fordulóból. ${n < 30 ? '<b>Vigyázat:</b> ' + n + ' mérésből ez még zaj — '
      + '5-6 forduló után lesz értelme.' : ''}</p>
      <div class="htbl"><table><thead><tr><th class="l">Forrás</th><th>Átlagos eltérés</th>
      <th>Minta</th></tr></thead><tbody>` +
      Object.entries(HI.accuracy).sort((a, b) => (a[1].mae ?? 99) - (b[1].mae ?? 99))
        .map(([k, v]) => `<tr><td class="l nm3">${esc(v.label)}</td>
          <td>${v.mae === null ? '–' : v.mae.toFixed(2)}</td>
          <td class="dimc">${v.n}</td></tr>`).join('') + '</tbody></table></div>';
  }
  box.innerHTML = html;
}

document.addEventListener('click', ev => {
  const b = ev.target.closest('.gwb');
  if (b) { GW = String(+b.dataset.hgw); render(); }
});

document.getElementById('pills').addEventListener('click', ev => {
  const b = ev.target.closest('.pill'); if (!b) return;
  active = b.dataset.s; render();
});
render();
if (!LOCKED[GW]) renderHist();
</script>
"""

out = pathlib.Path(A.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(TPL.replace("__TITLE__", A.title).replace("__HEAD__", theme.HEAD)
                  .replace("__DRAFT_HREF__", A.draft_href)
                  .replace("__H2H__", H2H).replace("__HIST__", HIST)
                  .replace("__MGRS__", MGRS), encoding="utf-8")
print(f"{out}: {out.stat().st_size} bájt")

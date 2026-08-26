/* FPL napló — a lap a saját állapotát publikálja vissza magába.
   Elv: minden szerkesztés azonnal a localStorage-be megy (semmi ne veszhessen el),
   a felhőbe viszont csak explicit Mentéssel — mert a publish újratölti a nézetet. */
'use strict';
const D = JSON.parse(document.getElementById('pool').textContent);
const LS = 'fplnaplo:v1';

function loadState() {
  const emb = JSON.parse(document.getElementById('st').textContent);
  let loc = null;
  try { loc = JSON.parse(localStorage.getItem(LS) || 'null'); } catch (e) { loc = null; }
  // a lokális példány csak akkor nyer, ha frissebb a publikáltnál
  if (loc && loc.rounds && (!emb.updated || (loc.updated || '') > emb.updated)) {
    return {s: loc, local: true};
  }
  return {s: emb, local: false};
}
const _l = loadState();
let S = _l.s, unsaved = _l.local;
if (!S.rounds) S.rounds = {};

const esc = t => String(t == null ? '' : t)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');
const P = {}; D.pool.forEach(p => P[p.id] = p);
const RATES = ['green', 'yellow', 'orange', 'red'];
const POSL = {GKP: 'kapus', DEF: 'védő', MID: 'közép', FWD: 'csatár'};
const art = n => (n === 1 || n === 5) ? 'az' : 'a';   // az 1. / az 5. forduló, a 2. forduló

/* ---------- állapot-segédek ---------- */
const stamp = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');
function round(gw) {
  const k = String(gw);
  if (!S.rounds[k]) S.rounds[k] = {};
  return S.rounds[k];
}
function touch() {
  S.updated = stamp(); unsaved = true;
  try { localStorage.setItem(LS, JSON.stringify(S)); } catch (e) {}
  renderStatus();
}
/* a watchlist előre öröklődik: ha ehhez a fordulóhoz még nincs, az előző hozza */
function watchSrc(gw) {
  const k = String(gw);
  if (S.rounds[k] && S.rounds[k].watch) return {list: S.rounds[k].watch, from: null};
  const prev = Object.keys(S.rounds).map(Number).filter(g => g < gw && S.rounds[String(g)].watch)
    .sort((a, b) => b - a)[0];
  if (prev !== undefined) return {list: S.rounds[String(prev)].watch, from: prev};
  return {list: [], from: null};
}
function watchOwn(gw) {                       // első szerkesztéskor másolatot készít
  const r = round(gw);
  if (!r.watch) r.watch = watchSrc(gw).list.map(w => ({...w}));
  return r.watch;
}

/* ---------- keret ---------- */
function squadOf(gw) {
  const k = String(gw);
  if (D.squads[k]) return {sq: D.squads[k], gw: gw, real: true};
  const prev = Object.keys(D.squads).map(Number).filter(g => g < gw).sort((a, b) => b - a)[0];
  if (prev === undefined) return {sq: null, gw: null, real: false};
  return {sq: D.squads[String(prev)], gw: prev, real: false};
}

/* ---------- becslés ---------- */
let src = (D.srcs[0] || {}).slug, GW = null, win = 3;
let fPos = 'ALL', fQ = '', fSort = 'proj', fDir = -1, fFree = false;

function winGws(from) {
  return D.gws.filter(g => g >= from && g < from + win);
}
function proj(id, from, n) {
  const p = P[id]; if (!p || !p.p[src]) return null;
  const gs = winGws(from), v = gs.map(g => p.p[src][String(g)]).filter(x => x != null);
  return v.length ? (n ? v.reduce((a, b) => a + b, 0) / v.length : v.reduce((a, b) => a + b, 0)) : null;
}
const fx1 = (id, gw) => {
  const f = (P[id] || {}).fx || {}, v = f[String(gw)];
  return v ? v[0] : '–';
};

/* ---------- kirajzolás ---------- */
function shell() {
  const upcoming = D.gws.filter(g => !D.squads[String(g)]);
  const dflt = upcoming.length ? upcoming[0] : D.gws[D.gws.length - 1];
  if (GW === null) GW = dflt;
  document.getElementById('root').innerHTML = `
  <div class="wrap">
    <p class="kicker">csak neked · a heti naplód</p>
    <h1>FPL napló</h1>
    <div class="sub">
      <span><b>${esc(D.team)}</b> · ${esc(D.manager)}</span>
      <span>összpont <b>${D.total}</b></span>
      <span>helyezés <b>${D.rank ? D.rank.toLocaleString('hu-HU') : '–'}</b></span>
      <span>becslés <b>${esc(D.taken_at.replace('T', ' ').replace('Z', ' UTC'))}</b></span>
    </div>
    <nav class="nav"><span class="spacer"></span>
      <a href="gw.html">A forduló</a><a href="index.html">Draft</a>
      <a href="secret.html">Becslés-tábla</a><a href="#" aria-current="page">Napló</a></nav>
    ${unsaved ? `<p class="warnbox">Van <b>nem mentett</b> változás ebben a böngészőben.
      A lap alján a <b>Mentés</b> teszi fel a felhőbe.</p>` : ''}
    <div class="rail" id="rail"></div>
    <div class="bar">
      <span class="lbl">becslés</span><span class="grp" id="srcs"></span>
      <span class="lbl">hány forduló</span><span class="grp" id="wins"></span>
    </div>
    <div id="pitch"></div>
    <div class="grid">
      <div id="left"></div>
      <div id="right"></div>
    </div>
    <div id="watch"></div>
    <div id="picker"></div>
    <p class="note" id="foot"></p>
  </div>
  <div class="save">
    <span class="st" id="stat"></span>
    <button class="btn ghost" id="copy">JSON a vágólapra</button>
    <button class="btn" id="dosave">Mentés</button>
  </div>`;
  renderRail(); renderBar(); renderAll();
}
function hasNotes(g) {
  const r = S.rounds[String(g)];
  return !!(r && (
    (r.pre && Object.values(r.pre).some(v => v && (typeof v !== 'object' || v.length))) ||
    (r.post && (r.post.note || r.post.plan ||
      (r.post.players && Object.keys(r.post.players).length))) ||
    (r.watch && r.watch.length)));
}
function renderRail() {
  const has = hasNotes;
  document.getElementById('rail').innerHTML = D.gws.map(g =>
    `<button class="gwb" data-gw="${g}" aria-pressed="${g === GW}">${g}. forduló${
      D.squads[String(g)] ? '' : ' <span class="lbl">terv</span>'}${
      has(g) ? '<span class="dot"></span>' : ''}</button>`).join('');
}
function renderBar() {
  document.getElementById('srcs').innerHTML = D.srcs.map(s =>
    `<button class="b" data-src="${s.slug}" aria-pressed="${s.slug === src}">${esc(s.label)}</button>`).join('');
  document.getElementById('wins').innerHTML = [1, 3, 5].map(n =>
    `<button class="b" data-win="${n}" aria-pressed="${n === win}">${n}</button>`).join('');
}
function renderAll() { renderPitch(); renderJournal(); renderSquad(); renderWatch(); renderPick(); renderStatus(); }


/* --- focipálya: kik vannak meg éppen --- */
/* a szám-cella színe a SAJÁT pozíción belüli percentilis, nem fix küszöb:
   egy védőnél az 5 pont kiváló, egy csatárnál gyenge */
function bands(gw) {
  const out = {};
  ['GKP', 'DEF', 'MID', 'FWD'].forEach(ps => {
    const v = D.pool.filter(p => p.pos === ps && p.st === 'a')
      .map(p => (p.p[src] || {})[String(gw)]).filter(x => x != null).sort((a, b) => a - b);
    out[ps] = v.length ? {hi: v[Math.floor(v.length * .88)], mid: v[Math.floor(v.length * .62)]}
                       : {hi: 99, mid: 99};
  });
  return out;
}
function pcard(e, opts) {
  const p = P[e.id]; if (!p) return '';
  const gs = winGws(GW), B = opts.bands, cs = D.cs[e.id];
  const cells = gs.map(g => {
    const v = (p.p[src] || {})[String(g)], b = B[g][p.pos];
    const cl = v == null ? '' : v >= b.hi ? 'hi' : v >= b.mid ? 'mid' : 'lo';
    const fx = ((p.fx || {})[String(g)] || ['–'])[0];
    return `<span class="g1 ${cl}"><b>${v == null ? '–' : v.toFixed(1)}</b><em>${esc(fx)}</em></span>`;
  }).join('');
  return `<div class="pc${p.st !== 'a' ? ' out' : ''}"${p.st !== 'a' && p.news
      ? ` title="${esc(p.news)}"` : ''}>
    <span class="pcn">${esc(p.n)}${e.cap ? ' <span class="tag c">C</span>'
      : e.vice ? ' <span class="tag">VC</span>' : ''}${
      cs ? ` <span class="rate ${cs.rate}" title="FPL Fran GW${cs.gw}: ${cs.rate}"></span>` : ''}</span>
    <span class="pcm">${esc(p.club)} · £${p.price.toFixed(1)}m</span>
    <span class="pcg">${cells}</span>
  </div>`;
}
function renderPitch() {
  const {sq, gw, real} = squadOf(GW), box = document.getElementById('pitch');
  if (!sq) { box.innerHTML = ''; return; }
  const gs = winGws(GW), B = {};
  gs.forEach(g => B[g] = bands(g));
  const bandsFor = {}; gs.forEach(g => bandsFor[g] = B[g]);
  const opts = {bands: bandsFor};
  const byPos = ps => sq.xi.filter(e => (P[e.id] || {}).pos === ps);
  const rows = ['GKP', 'DEF', 'MID', 'FWD'].map(ps => {
    const g = byPos(ps);
    return g.length ? `<div class="prow">${g.map(e => pcard(e, opts)).join('')}</div>` : '';
  }).join('');
  const form = ['DEF', 'MID', 'FWD'].map(ps => byPos(ps).length).join('-');
  const bench = [...sq.bench].sort((a, b) =>
    ((P[a.id] || {}).pos === 'GKP' ? 0 : 1) - ((P[b.id] || {}).pos === 'GKP' ? 0 : 1));
  const sum = sq.xi.reduce((t, e) => t + (proj(e.id, GW, false) || 0), 0);
  box.innerHTML = `<div class="card pitchcard">
    <h2>A keretem <span class="m">${real ? `${GW}. forduló · tényleges`
      : `${art(gw)} ${gw}. fordulóból · ${art(GW)} ${GW}. még nincs lezárva`} · ${form}
      · kezdő XI becslés <b>${sum.toFixed(1)}</b> pont
      (GW${gs[0]}${gs.length > 1 ? '–' + gs[gs.length - 1] : ''})</span></h2>
    <div class="pitch">${rows}</div>
    <div class="bench"><div class="bh">kispad</div>
      <div class="prow">${bench.map((e, i) =>
        (i === 0 && (P[e.id] || {}).pos === 'GKP' ? '<span class="gkslot">' : '') +
        pcard(e, opts) + (i === 0 && (P[e.id] || {}).pos === 'GKP' ? '</span>' : '')).join('')}</div>
    </div>
  </div>`;
}

/* --- bal oldal: a jegyzet --- */
function renderJournal() {
  const r = round(GW), pre = r.pre || (r.pre = {}), post = r.post || (r.post = {});
  if (!pre.transfers) pre.transfers = [];
  const apiTr = D.apitransfers.filter(t => t.gw === GW);
  const h = D.history.find(x => x.event === GW);
  document.getElementById('left').innerHTML = `
  <div class="card">
    <h2>Előtte <span class="m">${GW}. forduló · amit tervezek</span></h2>
    <div class="pad">
      <label class="fld"><span>gondolatok a fordulóról</span>
        <textarea data-f="pre.note" rows="4" placeholder="Mit várok, mi a helyzet, mi aggaszt…">${esc(pre.note)}</textarea></label>
      <div class="fld"><span>transzferek${apiTr.length ? ` · az API szerint ${apiTr.length} volt` : ''}</span>
        <div class="trs" id="trs">${(pre.transfers.length ? pre.transfers : []).map((t, i) => `
          <div class="tr">
            <input type="text" data-f="tr.out.${i}" value="${esc(t.out)}" placeholder="kifelé">
            <span class="ar">→</span>
            <input type="text" data-f="tr.in.${i}" value="${esc(t.in)}" placeholder="befelé">
            <button class="x" data-deltr="${i}" title="sor törlése">×</button>
          </div>
          <input type="text" data-f="tr.why.${i}" value="${esc(t.why)}" placeholder="miért">`).join('')}
          <button class="add" id="addtr">+ transzfer</button>
        </div>
        ${apiTr.length ? `<p class="empty" style="padding:6px 0 0">Megtörtént: ${apiTr.map(t =>
          `${esc(t.out.n)} → ${esc(t.in.n)}`).join(' · ')}</p>` : ''}
      </div>
      <div class="row2">
        <label class="fld"><span>kapitány</span>
          <input type="text" data-f="pre.captain" value="${esc(pre.captain)}" placeholder="ki és miért"></label>
        <label class="fld"><span>szabad transzfer</span>
          <input type="text" data-f="pre.ft" value="${esc(pre.ft)}" placeholder="pl. 2FT volt"></label>
      </div>
      <label class="fld"><span>kispad-sorrend</span>
        <input type="text" data-f="pre.bench" value="${esc(pre.bench)}" placeholder="mire számítok a padon"></label>
      <label class="fld"><span>középtávú stratégia</span>
        <textarea data-f="pre.strategy" rows="3" placeholder="Chipek, meddig áll a keret, mit tartalékolok…">${esc(pre.strategy)}</textarea></label>
    </div>
  </div>
  <div class="card" style="margin-top:16px">
    <h2>Utána <span class="m">${h ? `${h.points} pont · ${h.overall_rank.toLocaleString('hu-HU')}. hely`
      : 'a forduló még nincs lezárva'}</span></h2>
    <div class="pad">
      <label class="fld"><span>mit gondolok, mi történt</span>
        <textarea data-f="post.note" rows="4" placeholder="Milyen forduló volt, bejöttek-e a döntések…">${esc(post.note)}</textarea></label>
      <label class="fld"><span>tervezés a következő fordulóig</span>
        <textarea data-f="post.plan" rows="3" placeholder="Kit adnék el, mit figyelek, mire várok…">${esc(post.plan)}</textarea></label>
    </div>
  </div>`;
}

/* --- jobb oldal: a keret jelzőlámpákkal --- */
function renderSquad() {
  const {sq, gw, real} = squadOf(GW), box = document.getElementById('right');
  if (!sq) { box.innerHTML = `<div class="card"><h2>Játékosaim</h2>
    <p class="empty">Még nincs lezárt forduló, tehát az API nem ad keretet.</p></div>`; return; }
  const r = round(GW), post = r.post || (r.post = {});
  if (!post.players) post.players = {};
  const wl = new Set(watchSrc(GW).list.map(w => w.id));
  const line = (e, bench) => {
    const p = P[e.id] || {n: '?', club: '?', pos: '?', price: 0, own: 0};
    const rt = post.players[e.id] || {};
    const pj = proj(e.id, GW, false), cs = D.cs[e.id];
    return `<div class="pl">
      <span class="lights">${RATES.map(v =>
        `<button class="li" data-v="${v}" data-pid="${e.id}" aria-pressed="${rt.r === v}"
          title="${v}"></button>`).join('')}</span>
      <span class="pn">
        <span class="nm">${esc(p.n)}
          ${e.cap ? '<span class="tag c">C</span>' : e.vice ? '<span class="tag">VC</span>' : ''}
          ${cs ? `<span class="rate ${cs.rate}" title="FPL Fran GW${cs.gw}: ${cs.rate}"></span>` : ''}
          ${wl.has(e.id) ? '<span class="tag w">watch</span>' : ''}</span>
        <span class="meta">${esc(p.club)} · ${esc(p.pos)} · £${p.price.toFixed(1)}m · ${p.own}%
          ${p.st !== 'a' && p.news ? ` · <span class="inj">${esc(p.news)}</span>` : ''}</span>
        <input type="text" data-f="rate.${e.id}" value="${esc(rt.c)}" placeholder="megjegyzés">
      </span>
      <span class="pts"><span class="big">${pj == null ? '–' : pj.toFixed(1)}</span>
        <span class="x2">${esc(fx1(e.id, GW))}</span></span>
    </div>`;
  };
  box.innerHTML = `<div class="card">
    <h2>Játékosaim <span class="m">${real ? `${GW}. forduló tényleges kerete`
      : `${art(gw)} ${gw}. forduló kerete — ${art(GW)} ${GW}. még nincs lezárva`}${
      sq.chip ? ' · ' + esc(sq.chip) : ''}</span></h2>
    <div class="sq">
      <div class="sqh"><span>kezdő</span>
        <span style="margin-left:auto;text-transform:none;letter-spacing:0">
          <span class="rate green"></span> jó · <span class="rate yellow"></span> elmegy ·
          <span class="rate orange"></span> gyenge · <span class="rate red"></span> kuka</span>
        <span>${win > 1 ? `becslés GW${winGws(GW)[0]}–${winGws(GW)[winGws(GW).length-1]}`
        : `becslés GW${GW}`}</span></div>
      ${sq.xi.map(e => line(e, false)).join('')}
      <div class="sqh">kispad</div>
      ${sq.bench.map(e => line(e, true)).join('')}
    </div>
  </div>
  <div class="card" style="margin-top:16px">
    <h2>Mit cserélne a becslés <span class="m">${esc((D.srcs.find(s => s.slug === src) || {}).label)}
      · bank £${sq.bank.toFixed(1)}m</span></h2>
    <div class="sugg" id="sugg"></div>
  </div>`;
  renderSugg(sq);
}

/* --- transzfer-javaslat: azonos pozíció, belefér a bankba, max 3 klub --- */
function renderSugg(sq) {
  const own = [...sq.xi, ...sq.bench].map(e => e.id);
  const ownSet = new Set(own);
  const clubs = {};
  own.forEach(i => { const c = (P[i] || {}).club; if (c) clubs[c] = (clubs[c] || 0) + 1; });
  const out = [];
  own.forEach(i => {
    const me = P[i]; if (!me) return;
    const mine = proj(i, GW, false); if (mine == null) return;
    const budget = me.price + sq.bank;
    const cand = D.pool.filter(c => c.pos === me.pos && !ownSet.has(c.id)
      && c.price <= budget + 1e-9 && c.st === 'a'
      && ((clubs[c.club] || 0) - (c.club === me.club ? 1 : 0)) < 3)
      .map(c => ({c, v: proj(c.id, GW, false)}))
      .filter(x => x.v != null && x.v > mine)
      .sort((a, b) => b.v - a.v)[0];
    if (cand) out.push({out: me, in: cand.c, gain: cand.v - mine, mine});
  });
  out.sort((a, b) => b.gain - a.gain);
  const box = document.getElementById('sugg');
  if (!out.length) { box.innerHTML = `<p class="empty">Ezen a becslésen és ezzel a bankkal nincs
    olyan azonos pozíciós csere, ami többet hozna.</p>`; return; }
  const gs = winGws(GW);
  box.innerHTML = out.slice(0, 6).map(o => `<div class="sg">
      <span>${esc(o.out.n)} <span class="p2">${esc(o.out.club)} £${o.out.price.toFixed(1)}m ·
        ${o.mine.toFixed(1)}</span></span>
      <span class="ar">→</span>
      <span>${esc(o.in.n)} <span class="p2">${esc(o.in.club)} £${o.in.price.toFixed(1)}m ·
        ${(o.mine + o.gain).toFixed(1)}</span></span>
      <span class="gain">+${o.gain.toFixed(1)}</span>
    </div>`).join('') +
    `<p class="empty">GW${gs[0]}${gs.length > 1 ? '–' + gs[gs.length - 1] : ''} összpontra, a
     saját árából + a bankból. A klubonkénti hármas korlátot figyeli; a keret-szabályt (2-5-5-3)
     nem sérti, mert azonos pozícióban cserél. Nem javasol pontlevonásos lépést.</p>`;
}

/* --- watchlist --- */
function renderWatch() {
  const w = watchSrc(GW), box = document.getElementById('watch');
  const gs = winGws(GW);
  box.innerHTML = `<div class="card" style="margin-top:16px">
    <h2>Akik nincsenek bent, de tetszenek
      <span class="m">${GW}. forduló${w.from ? ` · ${art(w.from)} ${w.from}. fordulóról öröklődött`
        : ''} · ${w.list.length} játékos</span></h2>
    ${w.list.length ? `<div class="wl">${w.list.map((x, i) => {
      const p = P[x.id] || {n: '?', club: '?', pos: '?', price: 0, own: 0};
      const pj = proj(x.id, GW, false), cs = D.cs[x.id];
      return `<div class="wr">
        <span class="pn"><span class="nm">${esc(p.n)}
            <span class="tag">${esc(POSL[p.pos] || p.pos)}</span>
            ${cs ? `<span class="rate ${cs.rate}" title="FPL Fran GW${cs.gw}"></span>` : ''}</span>
          <span class="meta">${esc(p.club)} · £${p.price.toFixed(1)}m · ${p.own}% ·
            becslés ${pj == null ? '–' : pj.toFixed(1)} (GW${gs[0]}${gs.length > 1 ? '–' + gs[gs.length-1] : ''})
            ${p.st !== 'a' && p.news ? ` · <span class="inj">${esc(p.news)}</span>` : ''}</span>
          <input type="text" data-f="why.${x.id}" value="${esc(x.why)}" placeholder="miért figyelem"></span>
        <button class="x" data-delw="${x.id}" title="le a listáról">×</button>
      </div>`; }).join('')}</div>`
    : `<p class="empty">Még üres. Lentebb keresd meg a játékost és a + gombbal tedd fel.</p>`}
  </div>`;
}

/* --- kereső + kiválasztó --- */
function renderPick() {
  const {sq} = squadOf(GW);
  const ownSet = new Set(sq ? [...sq.xi, ...sq.bench].map(e => e.id) : []);
  const wl = new Set(watchSrc(GW).list.map(x => x.id));
  const gs = winGws(GW);
  let rows = D.pool.filter(p => (fPos === 'ALL' || p.pos === fPos)
    && (!fQ || (p.n + ' ' + p.club).toLowerCase().includes(fQ))
    && (!fFree || !ownSet.has(p.id)));
  const key = p => fSort === 'proj' ? (proj(p.id, GW, false) ?? -1)
    : fSort === 'ppm' ? ((proj(p.id, GW, false) ?? 0) / p.price)
    : fSort === 'price' ? p.price : fSort === 'own' ? p.own : p.n;
  rows.sort((a, b) => {
    const x = key(a), y = key(b);
    return (typeof x === 'string' ? x.localeCompare(y, 'hu') : x - y) * fDir;
  });
  const shown = rows.slice(0, 120);
  const th = (k, l, cls) => `<th class="${cls || ''}" data-sort="${k}"
    ${fSort === k ? `aria-sort="${fDir < 0 ? 'descending' : 'ascending'}"` : ''}>${l}</th>`;
  document.getElementById('picker').innerHTML = `<div class="card" style="margin-top:16px">
    <h2>Játékos-kereső <span class="m">${rows.length} találat${
      shown.length < rows.length ? `, az első ${shown.length} látszik` : ''}</span></h2>
    <div class="bar" style="margin:0;border:0;border-radius:0;box-shadow:none;
      border-bottom:1px solid var(--rule)">
      <input type="text" id="q" value="${esc(fQ)}" placeholder="név vagy klub…"
        style="max-width:230px" autocomplete="off">
      <span class="grp">${[['ALL', 'mind'], ['GKP', 'kapus'], ['DEF', 'védő'],
        ['MID', 'közép'], ['FWD', 'csatár']].map(([k, l]) =>
        `<button class="b" data-pos="${k}" aria-pressed="${fPos === k}">${l}</button>`).join('')}</span>
      <span class="grp"><button class="b" data-free="1" aria-pressed="${fFree}">akik nincsenek nálam</button></span>
    </div>
    <div class="tw pick"><table>
      <thead><tr>${th('n', 'Játékos', 'l')}<th>Poz</th>${th('price', 'Ár')}${th('own', 'Mezőny')}
        ${th('proj', `GW${gs[0]}${gs.length > 1 ? '–' + gs[gs.length - 1] : ''}`)}
        ${th('ppm', 'Pont/£')}<th class="l">Fixtúra</th><th>Fran</th><th></th></tr></thead>
      <tbody>${shown.map(p => {
        const pj = proj(p.id, GW, false), cs = D.cs[p.id];
        return `<tr class="${ownSet.has(p.id) ? 'mine' : ''}">
          <td class="l">${esc(p.n)}${ownSet.has(p.id) ? ' <span class="tag c">nálam</span>' : ''}
            ${p.st !== 'a' ? ' <span class="inj">!</span>' : ''}</td>
          <td class="dimc">${esc(p.pos)}</td>
          <td>£${p.price.toFixed(1)}</td><td>${p.own.toFixed(1)}%</td>
          <td><b>${pj == null ? '–' : pj.toFixed(1)}</b></td>
          <td>${pj == null ? '–' : (pj / p.price).toFixed(2)}</td>
          <td class="l">${gs.map(g => esc(fx1(p.id, g))).join(' ')}</td>
          <td>${cs ? `<span class="rate ${cs.rate}" title="GW${cs.gw}"></span>` : '<span class="dimc">–</span>'}</td>
          <td><button class="plus" data-add="${p.id}" aria-pressed="${wl.has(p.id)}"
            title="${wl.has(p.id) ? 'le a watchlistről' : 'fel a watchlistre'}">${wl.has(p.id) ? '−' : '+'}</button></td>
        </tr>`; }).join('')}</tbody>
    </table></div>
  </div>`;
  document.getElementById('foot').innerHTML = `
    <b>Hogyan mentődik.</b> Minden beírás azonnal a böngésző tárolójába kerül, tehát nem
    veszhet el. A <b>Mentés</b> a teljes naplót visszapublikálja ebbe az artifactba — utána a
    lap újratölt, és onnantól bárhonnan ez a mentett állapot jön.<br>
    <b>Watchlist.</b> Fordulónként áll, és előre öröklődik: ha ehhez a fordulóhoz még nem
    nyúltál hozzá, az előző hetit látod. Amint hozzáadsz vagy leveszel valakit, ez a forduló
    saját listát kap, a korábbi hetek érintetlenek maradnak.<br>
    <b>Keret.</b> Az API-ból jön (<code>fetch_my_fpl.py</code>), lezárt fordulóra a tényleges
    felállás, kapitánnyal és kispaddal. A még le nem játszott fordulónál az utolsó ismert keret
    látszik, mert a picks-végpont a deadline előtt 404-et ad.<br>
    <b>Fran-oszlop.</b> A cheat sheet minősítése (zöld = Great Option), ha az a játékos rajta van.`;
}

function renderStatus() {
  const el = document.getElementById('stat');
  const n = Object.keys(S.rounds).filter(g => hasNotes(+g)).length;
  el.className = 'st' + (unsaved ? ' dirty' : '');
  el.innerHTML = unsaved
    ? `<b>nem mentett változás</b> · ${n} forduló jegyzete · utolsó szerkesztés ${esc(S.updated || '')}`
    : `<b>mentve</b>${S.updated ? ' · ' + esc(S.updated) : ' · még üres'} · ${n} forduló jegyzete`;
  const b = document.getElementById('dosave');
  if (b) b.disabled = !unsaved;
}

/* ---------- a lap újraépítése önmagából ---------- */
function pageHtml(state) {
  const css = document.getElementById('css').textContent;
  const pool = document.getElementById('pool').textContent;
  const app = document.getElementById('app').textContent;
  const st = JSON.stringify(state).replace(/</g, '\\u003c');
  const S1 = '<' + 'script', S2 = '<' + '/script>';
  return `<!doctype html>
<html lang="hu"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FPL napló</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,200..800&family=DM+Mono:wght@400;500&display=swap">
<style id="css">${css}</style></head><body>
${S1} id="pool" type="application/json">${pool}${S2}
${S1} id="st" type="application/json">${st}${S2}
<div id="root"></div>
${S1} id="app">${app}${S2}
</body></html>`;
}

let API = null;
if (window.claude && window.claude.use) {
  window.claude.use('artifact').then(a => { API = a; renderStatus(); }).catch(() => {});
}
async function save() {
  const btn = document.getElementById('dosave');
  if (!API) {
    alert('A mentés csak a publikált artifactban működik (itt nincs artifact-jog).\n'
      + 'A munkád a böngésző tárolójában megvan — a „JSON a vágólapra" gombbal ki tudod menteni.');
    return;
  }
  btn.disabled = true; btn.textContent = 'mentés…';
  try { sessionStorage.setItem(LS, JSON.stringify(S)); } catch (e) {}
  try {
    await API.publish(pageHtml(S));
    unsaved = false;
    try { localStorage.setItem(LS, JSON.stringify(S)); } catch (e) {}
    btn.textContent = 'mentve';
  } catch (e) {
    const c = (e && e.code) || 'upstream_error';
    btn.disabled = false; btn.textContent = 'Mentés';
    if (c === 'conflict') return;                       // a nézet magától újratölt
    if (c === 'not_writer' || c === 'not_granted' || c === 'not_declared') {
      btn.style.display = 'none';
      alert('Ez a nézet csak olvasható, ide nem tud menteni. A jegyzet a böngésző tárolójában megvan.');
    } else if (c === 'too_large') {
      alert('A lap túl nagy a mentéshez. Szólj, és karcsúsítom az adatot.');
    } else {
      alert('A mentés nem sikerült (' + c + '). Próbáld újra; a munkád nem veszett el.');
    }
  }
}

/* ---------- események ---------- */
document.addEventListener('click', ev => {
  const t = ev.target.closest('button');
  if (!t) return;
  if (t.dataset.gw) { GW = +t.dataset.gw; renderRail(); renderAll(); return; }
  if (t.dataset.src) { src = t.dataset.src; renderBar(); renderAll(); return; }
  if (t.dataset.win) { win = +t.dataset.win; renderBar(); renderAll(); return; }
  if (t.dataset.pos) { fPos = t.dataset.pos; renderPick(); return; }
  if (t.dataset.free) { fFree = !fFree; renderPick(); return; }
  if (t.dataset.sort) { return; }
  if (t.dataset.v && t.dataset.pid) {
    const r = round(GW); r.post = r.post || {}; r.post.players = r.post.players || {};
    const cur = r.post.players[t.dataset.pid] || {};
    cur.r = cur.r === t.dataset.v ? null : t.dataset.v;
    r.post.players[t.dataset.pid] = cur;
    touch(); renderSquad(); renderRail(); return;
  }
  if (t.dataset.add) {
    const id = +t.dataset.add, w = watchOwn(GW), i = w.findIndex(x => x.id === id);
    if (i >= 0) w.splice(i, 1); else w.push({id: id, why: ''});
    touch(); renderWatch(); renderPick(); renderSquad(); renderRail(); return;
  }
  if (t.dataset.delw) {
    const w = watchOwn(GW), i = w.findIndex(x => x.id === +t.dataset.delw);
    if (i >= 0) w.splice(i, 1);
    touch(); renderWatch(); renderPick(); renderSquad(); return;
  }
  if (t.dataset.deltr) {
    round(GW).pre.transfers.splice(+t.dataset.deltr, 1);
    touch(); renderJournal(); return;
  }
  if (t.id === 'addtr') {
    const r = round(GW); r.pre = r.pre || {}; r.pre.transfers = r.pre.transfers || [];
    r.pre.transfers.push({out: '', in: '', why: ''});
    touch(); renderJournal(); return;
  }
  if (t.id === 'dosave') { save(); return; }
  if (t.id === 'copy') {
    navigator.clipboard.writeText(JSON.stringify(S, null, 1)).then(() => {
      t.textContent = 'a vágólapon';
      setTimeout(() => t.textContent = 'JSON a vágólapra', 1600);
    }, () => alert('A vágólap nem elérhető ebben a nézetben.'));
  }
});
/* fejléc-kattintás = rendezés (a th nem button) */
document.addEventListener('click', ev => {
  const th = ev.target.closest('th[data-sort]');
  if (!th) return;
  const k = th.dataset.sort;
  if (fSort === k) fDir = -fDir; else { fSort = k; fDir = k === 'n' ? 1 : -1; }
  renderPick();
});
/* szövegmezők: NEM rajzolunk újra, csak az állapotot írjuk (különben elszáll a fókusz) */
document.addEventListener('input', ev => {
  const el = ev.target, f = el.dataset && el.dataset.f;
  if (el.id === 'q') { fQ = el.value.trim().toLowerCase(); renderPick();
    const q = document.getElementById('q'); if (q) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
    return; }
  if (!f) return;
  const r = round(GW), v = el.value;
  if (f.startsWith('pre.')) { r.pre = r.pre || {}; r.pre[f.slice(4)] = v; }
  else if (f.startsWith('post.')) { r.post = r.post || {}; r.post[f.slice(5)] = v; }
  else if (f.startsWith('tr.')) {
    const [, key, i] = f.split('.');
    r.pre.transfers[+i][key] = v;
  } else if (f.startsWith('rate.')) {
    r.post = r.post || {}; r.post.players = r.post.players || {};
    const id = f.slice(5), cur = r.post.players[id] || {};
    cur.c = v; r.post.players[id] = cur;
  } else if (f.startsWith('why.')) {
    const id = +f.slice(4), w = watchOwn(GW), x = w.find(y => y.id === id);
    if (x) x.why = v;
  }
  touch();
});
window.addEventListener('beforeunload', e => {
  if (unsaved) { e.preventDefault(); e.returnValue = ''; }
});
/* publish után a nézet újratölt — a mentés előtti állapot innen jön vissza */
try {
  const ss = JSON.parse(sessionStorage.getItem(LS) || 'null');
  if (ss && ss.updated && (!S.updated || ss.updated > S.updated)) { S = ss; unsaved = true; }
  sessionStorage.removeItem(LS);
} catch (e) {}
shell();

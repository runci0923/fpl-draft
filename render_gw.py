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
  <p class="lede">Mindenki kerete a pályán, a <b>projektált pont szerinti legjobb legális
  felállásban</b> — vagyis kiket <i>kellene</i> játszatni. Egymás mellett a párosítás két
  csapata, és hogy ebből ki nyerne. Deadline után a lap a <b>tényleges</b> felállásra vált.</p>

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

  <div class="dlstrip" id="dls"></div>

  <div id="ties"></div>

  <div class="sec">
    <div class="sec-h"><h2>Tipp és valóság</h2>
      <p>a deadline előtti utolsó becslés a TÉNYLEGES felállásra, majd a valós pontok</p></div>
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
const GW = String(H.next_event || H.current_event || Object.keys(H.rounds)[0]);
const SRCS = Object.entries(H.sources).map(([slug, s]) => ({slug, ...s}))
  .filter(s => (H.rounds[GW] || {})[s.slug]);
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

function render() {
  const r = (H.rounds[GW] || {})[active];
  document.getElementById('kick').textContent =
    `${H.league.name} · ${H.league.size} csapat · FPL Draft ${'2026/27'}`;
  document.getElementById('h1').textContent = `${GW}. forduló`;
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

/* ---------- deadline-csík + tipp/valóság ---------- */
const HI = JSON.parse(document.getElementById('histdata').textContent || 'null');

function renderHist() {
  const strip = document.getElementById('dls');
  if (HI && HI.upcoming && HI.upcoming.length) {
    const fmt = t => t.replace('T', ' ').replace(':00Z', ' UTC');
    strip.innerHTML = HI.upcoming.slice(0, 5).map((e, i) =>
      `<span class="${i === 0 ? 'nx' : ''}">GW${e.gw} deadline: <b>${esc(fmt(e.deadline))}</b>${
        i === 0 ? ` · lezárás +${HI.lock_after_minutes} perc` : ''}</span>`).join('');
  } else strip.innerHTML = '';

  const box = document.getElementById('histview');
  if (!HI) { box.innerHTML = ''; return; }
  const done = (HI.rounds || []).filter(r => r.has_tip || r.has_real);
  if (!done.length) {
    box.innerHTML = `<p class="empty2">Még nincs lezárt forduló.
      A rendszer a deadline után <b>${HI.lock_after_minutes} perccel</b> lezárja a fordulót:
      lehúzza a <b>tényleges felállásokat</b> (előtte az API nem adja ki), és hozzájuk párosítja
      a <b>deadline előtti utolsó becslést</b> — így a tipp arra a csapatra szól, amit valóban
      kiállítottak. Amikor a forduló véget ér, ugyanabba a rekordba bekerülnek a <b>valós
      pontok</b>, és innentől itt látszik a kettő egymás mellett, forrásonként.</p>`;
    return;
  }
  const SR = Object.keys(HI.sources);
  const nm = e => (HI.managers[e] || {}).first || e;
  let html = '';

  if (Object.values(HI.accuracy || {}).some(a => a.mae !== null)) {
    html += `<h3 style="margin:18px 0 0;font-size:16px">Melyik becslés talál jobban</h3>
      <div class="htbl"><table><thead><tr><th class="l">Forrás</th>
      <th>Átlagos eltérés</th><th>Mintaszám</th></tr></thead><tbody>` +
      Object.entries(HI.accuracy).sort((a, b) => (a[1].mae ?? 99) - (b[1].mae ?? 99))
        .map(([k, v]) => `<tr><td class="l nm3">${esc(v.label)}</td>
          <td>${v.mae === null ? '–' : v.mae.toFixed(2)}</td>
          <td class="dimc">${v.n}</td></tr>`).join('') + '</tbody></table></div>';
  }

  for (const rd of done.slice().reverse()) {
    html += `<h3 style="margin:22px 0 0;font-size:16px">GW${rd.gw}${
      rd.has_real ? '' : ' — még tart'}</h3>
      <div class="htbl"><table><thead><tr><th class="l">Párosítás</th>` +
      SR.map(k => `<th>${esc(HI.sources[k])}</th>`).join('') +
      `<th>Valós</th><th class="l">Eltérés</th></tr></thead><tbody>`;
    for (const m of rd.matches) {
      const th = rd.teams[m.home], ta = rd.teams[m.away];
      const cell = k => {
        const a = (th.tip || {})[k], b = (ta.tip || {})[k];
        return a && b ? `${a.xi.toFixed(1)} – ${b.xi.toFixed(1)}` : '–';
      };
      const real = th.real && ta.real ? `${th.real.xi} – ${ta.real.xi}` : '–';
      let diff = '–';
      if (th.real && ta.real && SR.length) {
        const k = SR[0], a = (th.tip || {})[k], b = (ta.tip || {})[k];
        if (a && b) {
          const dh = th.real.xi - a.xi, da = ta.real.xi - b.xi;
          diff = `${nm(m.home)} ${dh >= 0 ? '+' : ''}${dh.toFixed(1)} · ` +
                 `${nm(m.away)} ${da >= 0 ? '+' : ''}${da.toFixed(1)}`;
        }
      }
      html += `<tr><td class="l nm3">${esc(nm(m.home))} – ${esc(nm(m.away))}</td>` +
        SR.map(k => `<td class="dimc">${cell(k)}</td>`).join('') +
        `<td class="${th.real ? 'd-pos' : 'dimc'}">${real}</td>
         <td class="l dimc">${esc(diff)}</td></tr>`;
    }
    html += '</tbody></table></div>';
  }
  box.innerHTML = html;
}

document.getElementById('pills').addEventListener('click', ev => {
  const b = ev.target.closest('.pill'); if (!b) return;
  active = b.dataset.s; render();
});
render();
renderHist();
</script>
"""

out = pathlib.Path(A.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(TPL.replace("__TITLE__", A.title).replace("__HEAD__", theme.HEAD)
                  .replace("__DRAFT_HREF__", A.draft_href)
                  .replace("__H2H__", H2H).replace("__HIST__", HIST)
                  .replace("__MGRS__", MGRS), encoding="utf-8")
print(f"{out}: {out.stat().st_size} bájt")

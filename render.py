#!/usr/bin/env python3
"""data.json -> index.html  (Vikingo Design System tokenek, kliens-oldali pontozás)"""
import argparse, json, pathlib

HERE = pathlib.Path(__file__).parent
ap = argparse.ArgumentParser()
ap.add_argument("--data", default=str(HERE / "data.json"))
ap.add_argument("--out", default=str(HERE / "index.html"))
ap.add_argument("--title", default="Vadkelet Draft Scorecard")
A = ap.parse_args()
DATA = pathlib.Path(A.data).read_text(encoding="utf-8")

TPL = r"""<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,200..800&family=DM+Mono:wght@400;500&display=swap">
<style>
:root{
  --coral:#FF544D; --coral-d:#E83D36;
  --ink:#3E2E45; --paper:#F3EEEB; --sand:#DCD0C3; --mauve:#7A687F;
  --bg:var(--paper); --fg:var(--ink); --dim:var(--mauve);
  --surface:#FFFFFF; --surface-2:#F6EFE8; --rule:var(--sand); --raised:#EFE7E1;
  --r-sm:8px; --r-md:12px; --r-lg:16px;
  --sh-sm:0 1px 2px rgba(42,32,54,.08); --sh-md:0 4px 16px rgba(42,32,54,.10);
  --gutter:clamp(20px,5.5vw,80px);
  --display:"Clash Display","Bricolage Grotesque",system-ui,sans-serif;
  --mono:"DM Mono",ui-monospace,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#25273E; --fg:#F3EEEB; --dim:#A99BAE;
  --surface:#2E3049; --surface-2:#343657; --rule:#454869; --raised:#3B3D5C;
  --sh-sm:0 1px 2px rgba(0,0,0,.30); --sh-md:0 4px 16px rgba(0,0,0,.34);
}}
:root[data-theme="dark"]{
  --bg:#25273E; --fg:#F3EEEB; --dim:#A99BAE;
  --surface:#2E3049; --surface-2:#343657; --rule:#454869; --raised:#3B3D5C;
  --sh-sm:0 1px 2px rgba(0,0,0,.30); --sh-md:0 4px 16px rgba(0,0,0,.34);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--display);
  font-optical-sizing:auto;-webkit-font-smoothing:antialiased;line-height:1.45}
.mono{font-family:var(--mono)}
.num,.score,b,td,th{font-variant-numeric:tabular-nums}
.wrap{max-width:1360px;margin:0 auto;padding:clamp(30px,5.5vw,64px) var(--gutter) 96px}
h1{font-weight:600;font-size:clamp(32px,5.8vw,58px);line-height:1.02;letter-spacing:-.022em;margin:0 0 14px;text-wrap:balance}
h2{font-size:clamp(19px,2.3vw,25px);font-weight:600;letter-spacing:-.01em;margin:0}
.kicker{font-family:var(--mono);font-size:11.5px;letter-spacing:.15em;text-transform:uppercase;color:var(--coral);margin:0 0 13px}
.lede{max-width:64ch;font-size:clamp(15px,1.4vw,17.5px);color:var(--dim);margin:0}
.lede b{color:var(--fg);font-weight:500}
.sec{margin-top:clamp(40px,6vw,76px)}
.sec-h{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;padding-bottom:11px;border-bottom:1px solid var(--rule);margin-bottom:22px}
.sec-h p{margin:0;font-family:var(--mono);font-size:11.5px;color:var(--dim)}

/* ---------- forrásválasztó ---------- */
.picker{margin-top:30px;padding:18px 20px;background:var(--surface);border:1px solid var(--rule);
  border-radius:var(--r-lg);box-shadow:var(--sh-sm)}
.picker > h2{font-size:12px;font-weight:500;letter-spacing:.11em;text-transform:uppercase;color:var(--dim);margin-bottom:12px}
.pills{display:flex;flex-wrap:wrap;gap:8px}
.pill{display:inline-flex;align-items:center;gap:7px;padding:7px 14px;border-radius:999px;
  border:1.5px solid var(--rule);background:transparent;color:var(--fg);cursor:pointer;
  font-family:var(--display);font-size:14px;font-weight:500;line-height:1.2}
.pill:hover{border-color:var(--fg)}
.pill[aria-pressed="true"]{background:var(--fg);border-color:var(--fg);color:var(--bg)}
.pill .n{font-family:var(--mono);font-size:10.5px;opacity:.65}
.pill .st{font-size:12px;color:var(--coral)}
.pill[aria-pressed="true"] .st{color:var(--bg)}
.picker-note{margin:13px 0 0;font-family:var(--mono);font-size:11.5px;color:var(--dim);line-height:1.65}
.picker-note b{color:var(--fg);font-weight:500}
.starbtn{margin-top:12px;padding:6px 12px;border-radius:999px;border:1.5px solid var(--coral);
  background:transparent;color:var(--coral);cursor:pointer;font-family:var(--mono);font-size:11px;letter-spacing:.05em}
.starbtn[aria-pressed="true"]{background:var(--coral);color:#fff}

/* ---------- nézet-váltó ---------- */
.tabs{display:flex;gap:2px;margin-top:26px;border-bottom:1px solid var(--rule)}
.tab{padding:10px 18px;border:0;background:transparent;color:var(--dim);cursor:pointer;
  font-family:var(--display);font-size:15px;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px}
.tab[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--coral)}
.tab:hover{color:var(--fg)}
[hidden]{display:none !important}

/* ---------- chipek ---------- */
.chip{flex:0 0 auto;min-width:38px;padding:2px 7px;border-radius:999px;font-family:var(--mono);
  font-size:11.5px;text-align:center;border:1.5px solid transparent}
.chip.t1{background:var(--coral);color:#fff;border-color:var(--coral)}
.chip.t2{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.chip.t3{color:var(--fg);border-color:var(--fg)}
.chip.t4{color:var(--dim);border-color:var(--dim)}
.chip.nr{color:var(--dim);border:1.5px dashed var(--rule)}
.legend{display:flex;flex-wrap:wrap;gap:7px 15px;margin:18px 0 0;padding:0;list-style:none;
  font-family:var(--mono);font-size:11px;letter-spacing:.03em;color:var(--dim)}
.legend li{display:flex;align-items:center;gap:6px}
.sw{width:24px;height:15px;border-radius:999px;border:1.5px solid var(--rule)}
.sw.t1{background:var(--coral);border-color:var(--coral)}
.sw.t2{background:var(--fg);border-color:var(--fg)}
.sw.t3{border-color:var(--fg)}
.sw.t4{border-color:var(--dim)}
.sw.nr{border-style:dashed}
.place{font-family:var(--mono);font-size:11px;padding:1px 6px;border-radius:var(--r-sm);
  background:var(--raised);color:var(--dim)}
.place.p1{background:var(--coral);color:#fff}

/* ---------- táblák ---------- */
.tw{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--sh-sm)}
table{width:100%;border-collapse:collapse}
thead th{font-family:var(--mono);font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--dim);
  font-weight:400;text-align:right;padding:13px 11px;border-bottom:1px solid var(--rule);white-space:nowrap;
  position:sticky;top:0;background:var(--surface);z-index:1}
tbody td{padding:11px;border-bottom:1px solid var(--rule);font-size:13.5px;text-align:right;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
th.l,td.l{text-align:left}
td.strong{font-weight:500;font-size:16px}
td.nm{font-size:14.5px;font-weight:500}
.hi{background:var(--surface-2)}
.dimc{color:var(--dim)}
.best{color:var(--coral)}
.tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--dim);border:1px solid var(--rule);border-radius:var(--r-sm);padding:1px 5px}

/* ---------- csapatkártyák ---------- */
.grid{display:grid;gap:22px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-lg) var(--r-lg) 0 0;
  box-shadow:var(--sh-md);display:flex;flex-direction:column;overflow:hidden}
.card-h{display:flex;align-items:center;gap:12px;padding:17px 19px 15px;border-bottom:1px solid var(--rule)}
.badge{flex:0 0 auto;width:38px;height:38px;border-radius:999px;background:var(--fg);color:var(--bg);
  display:grid;place-items:center;font-family:var(--mono);font-size:11.5px;letter-spacing:.03em}
.card-id{flex:1 1 auto;min-width:0}
.card-id h3{margin:0;font-size:20px;font-weight:600;letter-spacing:-.01em}
.sub{margin:1px 0 0;font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--dim)}
.card-score{display:flex;align-items:baseline;gap:5px}
.score{font-size:31px;font-weight:600;letter-spacing:-.03em;line-height:1}
.score-l{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--rule);background:var(--surface-2)}
.kpis > div{padding:10px 6px;text-align:center;border-right:1px solid var(--rule)}
.kpis > div:last-child{border-right:0}
.k{display:block;font-family:var(--mono);font-size:9px;letter-spacing:.07em;text-transform:uppercase;color:var(--dim)}
.kpis b{font-size:15.5px;font-weight:500}
.line{padding:13px 19px;border-bottom:1px solid var(--rule)}
.line-h{display:flex;align-items:baseline;gap:8px;margin-bottom:8px}
.line-h h4{margin:0;font-size:11.5px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;flex:1 1 auto}
.line-avg{font-family:var(--mono);font-size:12.5px}
.picks{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:5px}
.picks li{display:flex;align-items:center;gap:8px;font-size:14px}
.pname{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pclub{font-family:var(--mono);font-size:9.5px;letter-spacing:.05em;color:var(--dim)}
.bench{font-family:var(--mono);font-size:8.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--dim);
  border:1px solid var(--rule);border-radius:var(--r-sm);padding:0 4px}
.card-f{display:flex;flex-wrap:wrap;gap:3px 16px;padding:12px 19px;font-family:var(--mono);font-size:10.5px;color:var(--dim)}
.card-f b{color:var(--fg);font-weight:500}
.zz{height:9px;background:var(--surface);
  -webkit-mask:conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) 50%/32px 100%;
  mask:conic-gradient(from -45deg at bottom,#0000,#000 1deg 89deg,#0000 90deg) 50%/32px 100%}

/* ---------- vonalak ---------- */
.lgrid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(225px,1fr))}
.lcard{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);padding:17px;box-shadow:var(--sh-sm)}
.lcard h3{margin:0;font-size:16.5px;font-weight:600}
.lsub{margin:2px 0 13px;font-family:var(--mono);font-size:10.5px;letter-spacing:.04em;color:var(--coral)}
.lrank{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.lrank li{display:flex;align-items:center;gap:8px;font-size:14px}
.ln{flex:1 1 auto}
.lv{font-family:var(--mono);font-size:12px;color:var(--dim)}

/* ---------- egyezés-mátrix ---------- */
.mx{overflow-x:auto}
.mx table{min-width:520px}
.mxc{font-family:var(--mono);font-size:12.5px;text-align:center;padding:12px 8px}
.mxc span{display:inline-block;min-width:52px;padding:3px 8px;border-radius:var(--r-sm)}
.filters{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px;align-items:center}
.fbtn{padding:5px 12px;border-radius:999px;border:1.5px solid var(--rule);background:transparent;color:var(--dim);
  cursor:pointer;font-family:var(--mono);font-size:11px;letter-spacing:.05em}
.fbtn[aria-pressed="true"]{border-color:var(--fg);color:var(--fg)}
.scroller{max-height:70vh;overflow:auto;border:1px solid var(--rule);border-radius:var(--r-lg);background:var(--surface)}
.scroller table{min-width:840px}

/* ---------- saját értékelés ---------- */
.rexp{margin-top:14px;padding:11px 15px;background:var(--surface);border:1px solid var(--rule);
  border-radius:var(--r-md);display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center}
.rexp .lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.rexp code{font-family:var(--mono);font-size:11.5px;color:var(--fg);word-break:break-all;flex:1 1 260px}
.rexp .none{font-family:var(--mono);font-size:11.5px;color:var(--dim)}
.rate-top{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;
  padding:14px 17px;background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-md);
  box-shadow:var(--sh-sm);margin-bottom:20px}
.rate-top .prog{font-family:var(--mono);font-size:12px;color:var(--dim)}
.rate-top .prog b{color:var(--fg);font-weight:500}
.rate-acts{display:flex;gap:8px;flex-wrap:wrap}
.rgroup{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-lg);
  box-shadow:var(--sh-sm);overflow:hidden;margin-bottom:20px}
.rgroup > header{display:flex;align-items:baseline;gap:11px;padding:14px 18px;
  border-bottom:1px solid var(--rule);background:var(--surface-2)}
.rgroup > header h3{margin:0;font-size:17px;font-weight:600}
.rgroup > header .step{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--bg);background:var(--fg);border-radius:999px;padding:2px 8px}
.rgroup > header .hint{font-family:var(--mono);font-size:10.5px;color:var(--dim);margin-left:auto}
.rrow{display:grid;grid-template-columns:112px 1fr 210px;gap:14px;align-items:center;
  padding:13px 18px;border-bottom:1px solid var(--rule)}
.rrow:last-child{border-bottom:0}
.rrow.done{background:color-mix(in oklab,var(--coral) 5%,transparent)}
.rwho{min-width:0}
.rwho b{display:block;font-size:15px;font-weight:600}
.rwho span{font-family:var(--mono);font-size:9.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}
.rplayers{display:flex;flex-wrap:wrap;gap:6px;min-width:0}
.rp{display:inline-flex;align-items:center;gap:5px;padding:2px 8px 2px 3px;border-radius:999px;
  border:1px solid var(--rule);font-size:12.5px}
.rp .chip{min-width:30px;font-size:10px;padding:1px 5px}
.rp em{font-style:normal;font-family:var(--mono);font-size:8.5px;color:var(--dim);letter-spacing:.04em}
.rctl{display:flex;align-items:center;gap:11px}
.rctl input[type=range]{flex:1 1 auto;width:100%;accent-color:var(--coral);height:22px;cursor:pointer}
.rval{font-family:var(--mono);font-size:20px;font-weight:500;min-width:34px;text-align:right;
  font-variant-numeric:tabular-nums}
.rval.set{color:var(--coral)}
.rval.unset{color:var(--dim)}
.rscale{display:flex;justify-content:space-between;font-family:var(--mono);font-size:8.5px;
  color:var(--dim);letter-spacing:.05em;padding:0 18px 10px 144px}
.mybtn{padding:6px 13px;border-radius:999px;border:1.5px solid var(--rule);background:transparent;
  color:var(--dim);cursor:pointer;font-family:var(--mono);font-size:11px;letter-spacing:.05em}
.mybtn:hover{border-color:var(--fg);color:var(--fg)}
.mybtn[aria-pressed="true"]{border-color:var(--coral);color:var(--coral)}
@media (max-width:760px){
  .rrow{grid-template-columns:1fr;gap:9px}
  .rscale{padding:0 18px 10px 18px}
}
.blind .rp .chip{visibility:hidden}
.blind .rp em{visibility:hidden}

/* ---------- összevetés: párhuzamos listák ---------- */
.cmp-wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r-lg)}
.cmp{display:grid;gap:1px;background:var(--rule)}
.cmp-col{background:var(--surface);min-width:0}
.cmp-h{padding:12px 13px;border-bottom:1px solid var(--rule);background:var(--surface-2)}
.cmp-h a,.cmp-h span.nolink{display:block;font-size:14.5px;font-weight:600;color:var(--fg);text-decoration:none}
.cmp-h a:hover{color:var(--coral)}
.cmp-h a::after{content:" ↗";font-size:10px;color:var(--dim)}
.cmp-h small{display:block;font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--dim);margin-top:2px}
.cmp-list{list-style:none;margin:0;padding:0}
.cmp-list li{display:flex;align-items:baseline;gap:8px;padding:5px 13px;font-size:13.5px;
  border-bottom:1px solid color-mix(in oklab,var(--rule) 45%,transparent);cursor:pointer}
.cmp-list li:last-child{border-bottom:0}
.cmp-list li:hover{background:var(--surface-2)}
.cmp-list li.on{background:var(--coral);color:#fff}
.cmp-list li.on .r,.cmp-list li.on .cl,.cmp-list li.on .ow{color:rgba(255,255,255,.82)}
.cmp-list .r{font-family:var(--mono);font-size:10.5px;color:var(--dim);min-width:26px;text-align:right;flex:0 0 auto}
.cmp-list .nmx{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cmp-list .cl{font-family:var(--mono);font-size:9px;letter-spacing:.05em;color:var(--dim);flex:0 0 auto}
.cmp-list .ow{font-family:var(--mono);font-size:8.5px;letter-spacing:.05em;flex:0 0 auto;
  color:var(--bg);background:var(--dim);border-radius:var(--r-sm);padding:0 4px}
.cmp-list li.on .ow{background:rgba(255,255,255,.9);color:var(--coral)}
.cmp-list li.free .nmx{color:var(--dim)}
.readout{position:sticky;top:0;z-index:5;margin-bottom:14px;padding:13px 16px;background:var(--surface);
  border:1px solid var(--rule);border-radius:var(--r-md);box-shadow:var(--sh-md)}
.readout .rname{font-size:17px;font-weight:600}
.readout .rmeta{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--dim)}
.rranks{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.rranks span{font-family:var(--mono);font-size:11px;padding:3px 9px;border-radius:999px;
  border:1px solid var(--rule);color:var(--dim)}
.rranks span b{color:var(--fg);font-weight:500}
.rranks span.mn{border-color:var(--coral);color:var(--coral)}
.rranks span.mn b{color:var(--coral)}
.readout .empty{font-family:var(--mono);font-size:11.5px;color:var(--dim)}
.srclinks{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.srclinks a{font-family:var(--mono);font-size:11px;letter-spacing:.04em;padding:5px 11px;border-radius:999px;
  border:1px solid var(--rule);color:var(--dim);text-decoration:none}
.srclinks a:hover{border-color:var(--coral);color:var(--coral)}

/* ---------- draft-tábla ---------- */
.dboard{overflow-x:auto;border:1px solid var(--rule);border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--sh-sm)}
.dboard table{min-width:900px;border-collapse:separate;border-spacing:0}
.dboard th{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);
  font-weight:400;padding:12px 10px;border-bottom:1px solid var(--rule);text-align:left;
  position:sticky;top:0;background:var(--surface);z-index:1}
.dboard th.rd{width:44px;text-align:center}
.dboard td{padding:0;border-bottom:1px solid var(--rule);border-right:1px solid var(--rule);vertical-align:top}
.dboard td:last-child{border-right:0}
.dboard td.rd{font-family:var(--mono);font-size:11px;color:var(--dim);text-align:center;padding:10px 0;background:var(--surface-2)}
.cell{display:block;padding:9px 10px;min-width:132px}
.cell .top{display:flex;align-items:center;gap:7px;margin-bottom:3px}
.cell .who{font-size:13.5px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cell .meta{font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;color:var(--dim);display:flex;gap:7px}
.sur{font-family:var(--mono);font-size:9.5px;padding:0 4px;border-radius:var(--r-sm)}
.sur.pos{color:var(--coral);border:1px solid var(--coral)}
.sur.neg{color:var(--dim);border:1px solid var(--rule)}
.warn{margin:11px 0 0;padding:9px 12px;border-radius:var(--r-sm);border:1px solid var(--coral);
  font-family:var(--mono);font-size:11px;line-height:1.6;color:var(--fg);
  background:color-mix(in oklab, var(--coral) 12%, transparent)}
.note{margin-top:clamp(36px,5vw,60px);padding-top:18px;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:11px;line-height:1.75;color:var(--dim);max-width:82ch}
.note b{color:var(--fg);font-weight:500}
:focus-visible{outline:2px solid var(--coral);outline-offset:2px}
</style>

<div class="wrap">
  <p class="kicker" id="kick"></p>
  <h1>Ki draftolt a legjobban?</h1>
  <p class="lede">Minden játékos annyi pontot ér, ahányadik a választott rangsoron. A 15 keret-tag
  pontja összeadva a csapat pontszáma — <b>minél kevesebb, annál jobb</b>. Öt független rangsor van
  betöltve; <b>váltogasd őket</b>, és látszik, mennyire bírja a végeredmény a forrásváltást.</p>

  <div class="picker">
    <h2 id="pickh">Rangsor-forrás</h2>
    <div class="pills" id="pills" role="group" aria-labelledby="pickh"></div>
    <p class="picker-note" id="pnote"></p>
    <p class="warn" id="warn" hidden></p>
    <button class="starbtn" id="star" aria-pressed="false">★ ezt tartom a legjobbnak</button>
  </div>
  <div class="rexp" id="rexp"></div>

  </div>

  <div class="tabs" role="tablist">
    <button class="tab" role="tab" id="t-teams"  aria-selected="true"  aria-controls="v-teams">Csapatok</button>
    <button class="tab" role="tab" id="t-draft"  aria-selected="false" aria-controls="v-draft">Draft-tábla</button>
    <button class="tab" role="tab" id="t-rate"   aria-selected="false" aria-controls="v-rate">Saját értékelés</button>
    <button class="tab" role="tab" id="t-cmp"    aria-selected="false" aria-controls="v-cmp">Összevetés</button>
    <button class="tab" role="tab" id="t-boards" aria-selected="false" aria-controls="v-boards">Rangsorok</button>
  </div>

  <!-- =========== CSAPATOK =========== -->
  <div id="v-teams" role="tabpanel" aria-labelledby="t-teams">
    <div class="sec">
      <div class="sec-h"><h2>Összesítés</h2><p id="lb-note"></p></div>
      <div class="tw"><table id="lb"></table></div>
      <ul class="legend">
        <li><span class="sw t1"></span>1–10 elit</li>
        <li><span class="sw t2"></span>11–50 kezdő</li>
        <li><span class="sw t3"></span>51–100 rotáció</li>
        <li><span class="sw t4"></span>101+ mélység</li>
        <li><span class="sw nr"></span>nincs a rangsoron</li>
      </ul>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>Vonal-bajnokságok</h2><p>pozíciónkénti átlagpont, kevesebb a jobb</p></div>
      <div class="lgrid" id="lines"></div>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>A hat keret</h2><p>vonalonként rangsorolva &middot; „cs" = cserén a GW1-ben</p></div>
      <div class="grid" id="cards"></div>
    </div>
  </div>

  <!-- =========== SAJÁT ÉRTÉKELÉS =========== -->
  <div id="v-rate" role="tabpanel" aria-labelledby="t-rate" hidden>
    <div class="sec">
      <div class="sec-h"><h2>Húzd be te</h2>
        <p>vonalanként, kapustól a csatárokig &middot; 1 = leggyengébb, 5 = legjobb &middot; a böngésző megjegyzi</p></div>
      <div class="rate-top">
        <span class="prog" id="rprog"></span>
        <span class="rate-acts">
          <button class="mybtn" id="rblind" aria-pressed="false">vak mód — rangok elrejtése</button>
          <button class="mybtn" id="rreset">nulláz</button>
        </span>
      </div>
      <div id="rgroups"></div>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>A te tabellád</h2><p id="rsum-note"></p></div>
      <div class="tw"><table id="rsum"></table></div>
    </div>
  </div>

  <!-- =========== DRAFT-TÁBLA =========== -->
  <div id="v-draft" role="tabpanel" aria-labelledby="t-draft" hidden>
    <div class="sec">
      <div class="sec-h"><h2>Ahogy lement</h2><p id="db-note"></p></div>
      <div class="dboard"><table id="dbtbl"></table></div>
      <ul class="legend">
        <li><span class="sur pos">BPA</span>a rangsor szerinti legjobb elérhetőt vitte</li>
        <li><span class="sur neg">−n</span>ennyi ranggal maradt a legjobb elérhető alatt</li>
      </ul>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>Mennyit hagytak az asztalon</h2><p>a 15 pick összesített elszalasztott rangja &middot; kevesebb a jobb</p></div>
      <div class="tw"><table id="surtbl"></table></div>
    </div>
  </div>

  <!-- =========== ÖSSZEVETÉS =========== -->
  <div id="v-cmp" role="tabpanel" aria-labelledby="t-cmp" hidden>
    <div class="sec">
      <div class="sec-h"><h2>A hat lista egymás mellett</h2>
        <p>kattints bárkire — végig kiemelődik mindegyik listában &middot;
        a szürke monogram a birtokos, világos név = még szabad</p></div>
      <div class="srclinks" id="srclinks"></div>
      <div class="filters" id="cfilters"></div>
      <div class="readout" id="readout"></div>
      <div class="cmp-wrap"><div class="cmp" id="cmp"></div></div>
    </div>
  </div>

  <!-- =========== RANGSOROK =========== -->
  <div id="v-boards" role="tabpanel" aria-labelledby="t-boards" hidden>
    <div class="sec">
      <div class="sec-h"><h2>Az öt forrás</h2><p>ki mit fed le, és mennyire egyezik a többivel</p></div>
      <div class="tw"><table id="srcs"></table></div>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>Egyezés-mátrix</h2><p>Spearman-rho a közös játékosokon &middot; 1,0 = azonos sorrend</p></div>
      <div class="tw mx"><table id="mx"></table></div>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>Ahol a szakértők vitáznak</h2><p>a legnagyobb rang-szórás a konszenzus top 100-ban</p></div>
      <div class="tw"><table id="disp"></table></div>
    </div>
    <div class="sec">
      <div class="sec-h"><h2>A teljes tábla</h2><p id="board-note"></p></div>
      <div class="filters" id="bfilters"></div>
      <div class="scroller"><table id="board"></table></div>
    </div>
  </div>

  <p class="note" id="foot"></p>
</div>

<script id="payload" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('payload').textContent);
const P = D.players, SRC = D.sources;
const REAL = SRC.filter(s => s.slug !== 'consensus');
const SIZE = Object.fromEntries(SRC.map(s => [s.slug, s.size]));
const ABBR = {draftsociety:'Draft Society', draftfantasy:'DraftFantasy', official:'FPL', onefpl:'OneFPL', rotowire:'RotoWire'};
const POS = [['GKP','Kapus'],['DEF','Védelem'],['MID','Középpálya'],['FWD','Támadók']];
const POSN = Object.fromEntries(POS);
const HAS_TEAM = D.managers.some(m => m.team);

let active = 'consensus';
let starred = null;
try { starred = localStorage.getItem('vk-draft-src'); } catch (e) {}
if (starred && SIZE[starred]) active = starred;

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const rankOf = (id, src) => P[id] ? (P[id].r[src] ?? null) : null;
const pointOf = (id, src) => rankOf(id, src) ?? SIZE[src] + 1;   // rangsoron kívül: a lista vége + 1
const tier = r => r === null ? 'nr' : r <= 10 ? 't1' : r <= 50 ? 't2' : r <= 100 ? 't3' : 't4';
const chip = r => `<span class="chip ${tier(r)}">${r === null ? 'NR' : r}</span>`;
const art = n => (n === 1 || n === 5) ? 'az' : 'a';
const avg = a => a.length ? Math.round(a.reduce((x, y) => x + y, 0) / a.length * 10) / 10 : null;

/* ---------- elszalasztott rang: a tényleges pick-sorrend alapján ----------
   Minden picknél: a választott játékos rangja mínusz az akkor még elérhető legjobb rangja.
   Mindig >= 0. 0 = a rangsor szerinti legjobb elérhetőt vitte (BPA). */
function opportunity(src) {
  const ids = Object.keys(P).map(Number);
  const pt = Object.fromEntries(ids.map(i => [i, pointOf(i, src)]));
  const pool = ids.slice().sort((a, b) => pt[a] - pt[b]);   // rang szerint növekvő
  const taken = new Set();
  const cost = {};
  let head = 0;
  for (const o of D.order) {
    while (head < pool.length && taken.has(pool[head])) head++;
    const bestAvail = head < pool.length ? pt[pool[head]] : null;
    cost[o.element] = bestAvail === null ? 0 : Math.max(0, pt[o.element] - bestAvail);
    taken.add(o.element);
  }
  return cost;
}

/* ---------- pontozás ---------- */
function evaluate(src) {
  const cost = opportunity(src);
  const ms = D.managers.map(m => {
    const picks = m.squad.map(s => {
      const p = P[s.id], r = rankOf(s.id, src);
      return {id: s.id, start: s.start, n: p.n, club: p.c, pos: p.p, rank: r,
              pt: r ?? SIZE[src] + 1, pick: s.pick, round: s.round, cost: cost[s.id] ?? 0};
    }).sort((a, b) => a.pt - b.pt);
    const lines = {};
    for (const [k] of POS) {
      const g = picks.filter(p => p.pos === k);
      lines[k] = {n: g.length, sum: g.reduce((a, p) => a + p.pt, 0), avg: avg(g.map(p => p.pt))};
    }
    const xi = picks.filter(p => p.start);
    const byCost = [...picks].sort((a, b) => a.cost - b.cost);
    return {name: m.name, first: m.first, team: m.team, initials: m.initials, entry: m.entry,
      slot: m.squad[0].pick, picks, lines,
      left: picks.reduce((a, p) => a + p.cost, 0),
      bpa: picks.filter(p => p.cost === 0).length,
      sharp: byCost[0], reach: byCost[byCost.length - 1],
      total: picks.reduce((a, p) => a + p.pt, 0),
      avg: avg(picks.map(p => p.pt)),
      xi: xi.reduce((a, p) => a + p.pt, 0),
      top50: picks.filter(p => p.rank !== null && p.rank <= 50).length,
      nr: picks.filter(p => p.rank === null).length,
      best: picks[0], worst: picks[picks.length - 1]};
  }).sort((a, b) => a.total - b.total);
  ms.forEach((m, i) => m.place = i + 1);
  for (const [k] of POS) {
    [...ms].sort((a, b) => a.lines[k].avg - b.lines[k].avg)
           .forEach((m, i) => m.lines[k].place = i + 1);
  }
  return ms;
}

/* ---------- render: csapatok ---------- */
function renderTeams(ms, src) {
  const s = SRC.find(x => x.slug === src);
  document.getElementById('lb-note').textContent =
    `${s.label} szerint · a pozíció-oszlopokban az átlagpont, pirossal a vonal győztese`;

  document.getElementById('lb').innerHTML =
    `<thead><tr><th class="l">#</th><th class="l">Manager</th><th class="l">Csapat</th>
      <th>Össz.</th><th>Átlag</th><th>Kezdő XI</th><th>Top-50</th><th>NR</th><th title="elszalasztott rang">Asztalon</th>` +
      POS.map(([, l]) => `<th>${l}</th>`).join('') + `</tr></thead><tbody>` +
    ms.map(m => `<tr class="${m.place === 1 ? 'hi' : ''}">
      <td class="l mono">${m.place}.</td><td class="l nm">${esc(m.name)}</td>
      ${HAS_TEAM ? `<td class="l dimc">${esc(m.team)}</td>` : ''}
      <td class="strong">${m.total}</td><td class="dimc">${m.avg}</td>
      <td class="dimc">${m.xi}</td><td class="dimc">${m.top50}</td>
      <td class="dimc">${m.nr || '–'}</td>
      <td class="dimc">${m.left}</td>` +
      POS.map(([k]) => `<td class="${m.lines[k].place === 1 ? 'best' : 'dimc'}">${m.lines[k].avg}</td>`).join('') +
      `</tr>`).join('') + `</tbody>`;

  document.getElementById('lines').innerHTML = POS.map(([k, label]) => {
    const order = [...ms].sort((a, b) => a.lines[k].avg - b.lines[k].avg);
    return `<article class="lcard"><h3>${label}</h3>
      <p class="lsub">győztes: ${esc(order[0].name)}</p><ol class="lrank">` +
      order.map((m, i) => `<li><span class="place p${i + 1}">${i + 1}.</span>
        <span class="ln">${esc(m.name)}</span><span class="lv">${m.lines[k].avg}</span></li>`).join('') +
      `</ol></article>`;
  }).join('');

  document.getElementById('cards').innerHTML = ms.map(m => `
    <article class="card">
      <header class="card-h">
        <span class="badge">${esc(m.initials)}</span>
        <div class="card-id"><h3>${esc(m.first)}</h3>
          <p class="sub">${m.team ? esc(m.team) + ' &middot; ' : ''}${m.place}. hely</p></div>
        <div class="card-score"><span class="score">${m.total}</span><span class="score-l">pont</span></div>
      </header>
      <div class="kpis">
        <div><span class="k">átlag</span><b>${m.avg}</b></div>
        <div><span class="k">kezdő XI</span><b>${m.xi}</b></div>
        <div><span class="k">top-50</span><b>${m.top50}</b></div>
        <div><span class="k">rangsor&shy;on kívül</span><b>${m.nr || '–'}</b></div>
      </div>
      <div>` + POS.map(([k, label]) => {
        const g = m.picks.filter(p => p.pos === k);
        return `<section class="line">
          <header class="line-h"><h4>${label}</h4>
            <span class="line-avg">${m.lines[k].avg}</span>
            <span class="place p${m.lines[k].place}">${m.lines[k].place}.</span></header>
          <ol class="picks">` + g.map(p => `<li>${chip(p.rank)}
            <span class="pname">${esc(p.n)}</span><span class="pclub">${esc(p.club)}</span>
            ${p.start ? '' : '<span class="bench">cs</span>'}</li>`).join('') + `</ol></section>`;
      }).join('') + `</div>
      <footer class="card-f">
        <span>legjobb: <b>${esc(m.best.n)}</b> · ${m.best.rank === null ? 'NR' : '#' + m.best.rank}</span>
        <span>leggyengébb: <b>${esc(m.worst.n)}</b> · ${m.worst.rank === null ? 'NR' : '#' + m.worst.rank}</span>
        <span>legnagyobb túlnyúlás: <b>${esc(m.reach.n)}</b> · ${m.reach.cost}</span>
        <span>${m.bpa}/15 pick a legjobb elérhető</span>
        <span>${m.slot}. helyről draftolt</span>
      </footer>
      <div class="zz" aria-hidden="true"></div>
    </article>`).join('');
}

/* ---------- render: draft-tábla ---------- */
function renderDraft(ms, src) {
  const cols = [...ms].sort((a, b) => a.slot - b.slot);
  const rounds = D.league.rounds;
  const cell = (m, rd) => {
    const p = m.picks.find(x => x.round === rd);
    if (!p) return '<td></td>';
    return `<td><span class="cell">
      <span class="top">${chip(p.rank)}<span class="who">${esc(p.n)}</span></span>
      <span class="meta"><span>${esc(p.club)} · ${p.pos}</span><span>#${p.pick}</span>
      <span class="sur ${p.cost === 0 ? 'pos' : 'neg'}">${p.cost === 0 ? 'BPA' : '−' + p.cost}</span>
      </span></span></td>`;
  };
  document.getElementById('db-note').textContent =
    `${D.league.rounds} kör · kígyó-sorrend · a chip a ${SRC.find(s => s.slug === src).label} rangja`;
  document.getElementById('dbtbl').innerHTML =
    `<thead><tr><th class="rd">Kör</th>` +
    cols.map(m => `<th>${esc(m.first)} <span class="dimc">${esc(m.initials)}</span></th>`).join('') +
    `</tr></thead><tbody>` +
    Array.from({length: rounds}, (_, i) => i + 1).map(rd =>
      `<tr><td class="rd">${rd}</td>` + cols.map(m => cell(m, rd)).join('') + `</tr>`).join('') +
    `</tbody>`;

  const byLeft = [...ms].sort((a, b) => a.left - b.left);
  document.getElementById('surtbl').innerHTML =
    `<thead><tr><th class="l">#</th><th class="l">Manager</th><th>Asztalon hagyva</th>
      <th>BPA-pickek</th><th class="l">Legnagyobb túlnyúlás</th></tr></thead><tbody>` +
    byLeft.map((m, i) => `<tr class="${i === 0 ? 'hi' : ''}">
      <td class="l mono">${i + 1}.</td><td class="l nm">${esc(m.name)}</td>
      <td class="strong">${m.left}</td>
      <td class="${m.bpa ? 'best' : 'dimc'}">${m.bpa}/15</td>
      <td class="l">${esc(m.reach.n)} <span class="pclub">${m.reach.cost} ranggal · pick ${m.reach.pick}</span></td>
    </tr>`).join('') + `</tbody>`;
}

/* ---------- saját értékelés: vonalanként 1–5 ---------- */
const RKEY = 'vk-draft-rating';
let myR = {};                      // `${entry}|${pos}` -> 1..5
let blind = false;
try { myR = JSON.parse(localStorage.getItem(RKEY) || 'null'); } catch (e) { myR = null; }
if (!myR || !Object.keys(myR).length) myR = {...(D.my_rating || {})};   // beépített alapérték
const saveR = () => { try { localStorage.setItem(RKEY, JSON.stringify(myR)); } catch (e) {} };
const rkey = (entry, pos) => `${entry}|${pos}`;
const SCALE = ['–', 'gyenge', 'közepes', 'jó', 'erős', 'a legjobb'];

function renderRate(ms, src) {
  const cols = [...ms].sort((a, b) => a.slot - b.slot);   // draft-sorrend: semleges
  document.getElementById('rgroups').innerHTML = POS.map(([k, label], gi) => `
    <section class="rgroup${blind ? ' blind' : ''}">
      <header><span class="step">${gi + 1}/4</span><h3>${label}</h3>
        <span class="hint">${cols[0].lines[k].n} játékos fejenként</span></header>
      ${cols.map(m => {
        const v = myR[rkey(m.entry, k)] || 0;
        return `<div class="rrow${v ? ' done' : ''}" data-row="${rkey(m.entry, k)}">
          <span class="rwho"><b>${esc(m.first)}</b><span>${esc(m.initials)} · ${m.slot}. pick</span></span>
          <span class="rplayers">${m.picks.filter(p => p.pos === k).map(p =>
            `<span class="rp">${chip(p.rank)}<span>${esc(p.n)}</span><em>${esc(p.club)}</em></span>`).join('')}</span>
          <span class="rctl">
            <input type="range" min="0" max="5" step="1" value="${v}"
              data-e="${m.entry}" data-p="${k}"
              aria-label="${esc(m.first)} – ${label} értékelése 1-től 5-ig">
            <span class="rval ${v ? 'set' : 'unset'}">${v || '–'}</span>
          </span>
        </div>`;
      }).join('')}
      <div class="rscale"><span>nincs</span><span>1 gyenge</span><span>3 jó</span><span>5 a legjobb</span></div>
    </section>`).join('');
  drawRateSummary(ms, src);
}

function drawExport(ms) {
  const cols = [...ms].sort((a, b) => a.slot - b.slot);
  const parts = POS.map(([k, label]) => {
    const vals = cols.map(m => myR[rkey(m.entry, k)] || 0);
    return vals.some(v => v) ? `${label.slice(0, 3).toUpperCase()} ${vals.map(v => v || '-').join('')}` : null;
  }).filter(Boolean);
  const el = document.getElementById('rexp');
  el.innerHTML = parts.length
    ? `<span class="lbl">saját értékelés · mentés-kód</span>
       <code>${cols.map(m => m.initials).join(' ')} &nbsp;|&nbsp; ${parts.join(' · ')}</code>
       <button class="mybtn" id="rcopy">másold ki</button>`
    : `<span class="lbl">saját értékelés</span><span class="none">még nincs kitöltve —
       a „Saját értékelés" fülön húzd be vonalanként, és itt megjelenik a mentés-kód</span>`;
}

function drawRateSummary(ms, src) {
  drawExport(ms);
  const filled = Object.values(myR).filter(v => v > 0).length;
  document.getElementById('rprog').innerHTML =
    `<b>${filled}</b>/24 értékelve` + (filled < 24 ? ' — a tabella a kitöltött vonalakból számol' : ' — kész');

  const rows = ms.map(m => {
    const per = Object.fromEntries(POS.map(([k]) => [k, myR[rkey(m.entry, k)] || 0]));
    const vals = Object.values(per).filter(v => v > 0);
    return {m, per, sum: vals.reduce((a, v) => a + v, 0), n: vals.length};
  });
  const rated = rows.filter(r => r.n > 0).sort((a, b) => b.sum - a.sum || b.n - a.n);
  rated.forEach((r, i) => r.myPlace = i + 1);

  const label = SRC.find(s => s.slug === src).label;
  document.getElementById('rsum-note').textContent = filled
    ? `a te pontjaid mellett a ${label} szerinti helyezés — ahol eltér, ott vitatkozol a rangsorral`
    : 'húzd be a csúszkákat, és itt összeáll a saját tabellád';

  document.getElementById('rsum').innerHTML =
    `<thead><tr><th class="l">#</th><th class="l">Manager</th>` +
    POS.map(([, l]) => `<th>${l}</th>`).join('') +
    `<th>Összesen</th><th>${esc(label)}</th><th class="l">Eltérés</th></tr></thead><tbody>` +
    rows.sort((a, b) => (b.sum - a.sum) || (a.m.place - b.m.place)).map(r => {
      const diff = r.myPlace ? r.m.place - r.myPlace : null;
      return `<tr class="${r.myPlace === 1 ? 'hi' : ''}">
        <td class="l mono">${r.myPlace ? r.myPlace + '.' : '–'}</td>
        <td class="l nm">${esc(r.m.first)}</td>` +
        POS.map(([k]) => `<td class="${r.per[k] ? '' : 'dimc'}">${r.per[k] || '–'}</td>`).join('') +
        `<td class="strong">${r.n ? r.sum : '–'}${r.n && r.n < 4 ? `<span class="dimc" style="font-size:11px"> /${r.n * 5}</span>` : ''}</td>
        <td class="dimc">${r.m.place}.</td>
        <td class="l ${diff ? 'best' : 'dimc'}">${diff === null ? '–'
          : diff === 0 ? 'egyezik'
          : diff > 0 ? `${diff} hellyel jobbnak tartod` : `${-diff} hellyel gyengébbnek tartod`}</td>
      </tr>`;
    }).join('') + `</tbody>`;
}

document.addEventListener('input', ev => {
  const inp = ev.target.closest('#rgroups input[type=range]');
  if (!inp) return;
  const v = +inp.value, k = rkey(inp.dataset.e, inp.dataset.p);
  if (v) myR[k] = v; else delete myR[k];
  saveR();
  const val = inp.parentElement.querySelector('.rval');
  val.textContent = v || '–';
  val.className = 'rval ' + (v ? 'set' : 'unset');
  inp.closest('.rrow').classList.toggle('done', !!v);
  drawRateSummary(evaluate(active), active);
});
document.addEventListener('click', ev => {
  if (ev.target.closest('#rblind')) {
    blind = !blind;
    ev.target.closest('#rblind').setAttribute('aria-pressed', blind);
    document.querySelectorAll('.rgroup').forEach(g => g.classList.toggle('blind', blind));
  }
  if (ev.target.closest('#rreset')) {
    myR = {}; saveR(); renderRate(evaluate(active), active);
  }
  const cp = ev.target.closest('#rcopy');
  if (cp) {
    const txt = document.querySelector('#rexp code').innerText;
    navigator.clipboard?.writeText(txt).then(() => { cp.textContent = 'kimásolva'; },
                                             () => { cp.textContent = 'nem sikerült'; });
  }
});

/* ---------- render: összevetés ---------- */
let sel = null, cdepth = 100, cpos = 'ALL';

function drawReadout() {
  const el = document.getElementById('readout');
  if (!sel || !P[sel]) {
    el.innerHTML = `<span class="empty">Válassz egy játékost bármelyik listából — ` +
      `megmutatom, hova tette mind a hat rangsor.</span>`;
    return;
  }
  const p = P[sel];
  const owner = D.managers.find(m => m.squad.some(s => s.id === +sel));
  const vals = SRC.map(s => ({s, r: p.r[s.slug] ?? null})).filter(x => x.r !== null);
  const mn = Math.min(...vals.filter(x => x.s.slug !== 'consensus').map(x => x.r));
  const mx = Math.max(...vals.filter(x => x.s.slug !== 'consensus').map(x => x.r));
  el.innerHTML =
    `<div class="rname">${esc(p.n)} <span class="rmeta">${esc(p.c)} · ${p.p} · ` +
    (owner ? `${esc(owner.first)} vitte ${art(p.pk)} ${p.pk}. pickkel` : 'nem draftolták') + `</span></div>
    <div class="rranks">` + SRC.map(s => {
      const r = p.r[s.slug] ?? null;
      const cls = (r !== null && s.slug !== 'consensus' && (r === mn || r === mx)) ? ' class="mn"' : '';
      return `<span${cls}>${esc(s.ab)} <b>${r === null ? 'NR' : '#' + r}</b></span>`;
    }).join('') +
    `<span>szórás <b>${p.sp === null ? '–' : p.sp}</b></span>
     <span>fedés <b>${p.cv}/5</b></span></div>`;
}

function renderCompare() {
  document.getElementById('srclinks').innerHTML = SRC.filter(s => s.url).map(s =>
    `<a href="${s.url}" target="_blank" rel="noopener">${esc(s.label)} ↗</a>`).join('');

  const owner = {};
  D.managers.forEach(m => m.squad.forEach(s => owner[s.id] = m.initials));
  const cmp = document.getElementById('cmp');
  cmp.style.gridTemplateColumns = `repeat(${SRC.length}, minmax(148px, 1fr))`;
  cmp.innerHTML = SRC.map(s => {
    const list = Object.entries(P)
      .filter(([, p]) => p.r[s.slug] !== undefined && (cpos === 'ALL' || p.p === cpos))
      .sort((a, b) => a[1].r[s.slug] - b[1].r[s.slug])
      .slice(0, cdepth);
    return `<div class="cmp-col">
      <div class="cmp-h">${s.url
        ? `<a href="${s.url}" target="_blank" rel="noopener">${esc(s.label)}</a>`
        : `<span class="nolink">${esc(s.label)}</span>`}
        <small>${s.size} játékos · fedés ${s.covers}/${s.of}</small></div>
      <ol class="cmp-list">` + list.map(([id, p]) =>
        `<li data-id="${id}" class="${owner[id] ? '' : 'free'}">
          <span class="r">${p.r[s.slug]}</span>
          <span class="nmx">${esc(p.n)}</span>
          <span class="cl">${esc(p.c)}</span>
          ${owner[id] ? `<span class="ow">${esc(owner[id])}</span>` : ''}
        </li>`).join('') + `</ol></div>`;
  }).join('');
  if (sel) markSel();

  const depths = [50, 100, 200, 600];
  document.getElementById('cfilters').innerHTML =
    depths.map(d => `<button class="fbtn" data-d="${d}" aria-pressed="${d === cdepth}">top ${d === 600 ? 'mind' : d}</button>`).join('') +
    `<span style="width:12px"></span>` +
    [['ALL', 'mind'], ...POS].map(([k, l]) =>
      `<button class="fbtn" data-p="${k}" aria-pressed="${k === cpos}">${l}</button>`).join('');
}

function markSel() {
  document.querySelectorAll('.cmp-list li').forEach(li =>
    li.classList.toggle('on', li.dataset.id === String(sel)));
}

document.addEventListener('click', ev => {
  const li = ev.target.closest('.cmp-list li');
  if (li) { sel = +li.dataset.id; markSel(); drawReadout(); return; }
  const fb = ev.target.closest('#cfilters .fbtn');
  if (fb) {
    if (fb.dataset.d) cdepth = +fb.dataset.d; else cpos = fb.dataset.p;
    renderCompare();
  }
});

/* ---------- render: rangsorok ---------- */
const rho = (a, b) => (D.agreement[a + '|' + b] || D.agreement[b + '|' + a] || {}).rho ?? null;

function renderBoards() {
  const meanRho = s => avg(REAL.filter(o => o.slug !== s).map(o => rho(s, o.slug)).filter(v => v !== null));
  document.getElementById('srcs').innerHTML =
    `<thead><tr><th class="l">Forrás</th><th>Játékos</th><th>Fedés</th><th>Átlag&nbsp;rho</th>
      <th class="l">Módszer</th></tr></thead><tbody>` +
    REAL.map(s => `<tr><td class="l nm">${s.url
        ? `<a href="${s.url}" target="_blank" rel="noopener" style="color:inherit">${esc(s.label)} <span class="dimc">↗</span></a>`
        : esc(s.label)}</td><td>${s.size}</td>
      <td class="${s.covers < 80 ? 'best' : 'dimc'}">${s.covers}/${s.of}</td>
      <td class="dimc">${meanRho(s.slug).toFixed(2)}</td>
      <td class="l dimc" style="white-space:normal">${esc(s.note)}</td></tr>`).join('') +
    (() => { const c = SRC.find(x => x.slug === 'consensus');
      return `<tr class="hi"><td class="l nm">Konszenzus</td><td>${c.size}</td>
        <td class="dimc">${c.covers}/${c.of}</td><td class="dimc">–</td>
        <td class="l dimc" style="white-space:normal">${esc(c.note)}</td></tr>`; })() + `</tbody>`;

  const shade = v => {
    const t = Math.max(0, Math.min(1, (v - 0.45) / 0.4));
    return `background:color-mix(in oklab, var(--coral) ${Math.round(t * 42)}%, transparent)`;
  };
  document.getElementById('mx').innerHTML =
    `<thead><tr><th class="l"></th>` + REAL.map(s => `<th>${esc(ABBR[s.slug])}</th>`).join('') + `</tr></thead><tbody>` +
    REAL.map(a => `<tr><td class="l nm">${esc(ABBR[a.slug])}</td>` + REAL.map(b => {
      if (a.slug === b.slug) return `<td class="mxc dimc">·</td>`;
      const v = rho(a.slug, b.slug);
      return `<td class="mxc"><span style="${shade(v)}">${v.toFixed(2)}</span></td>`;
    }).join('') + `</tr>`).join('') + `</tbody>`;

  const owner = {};
  D.managers.forEach(m => m.squad.forEach(s => owner[s.id] = m.first));
  const all = Object.entries(P).map(([id, p]) => ({id: +id, ...p, own: owner[id] || null}));

  const disp = all.filter(p => p.r.consensus <= 100 && p.sp !== null)
                  .sort((a, b) => b.sp - a.sp).slice(0, 20);
  document.getElementById('disp').innerHTML =
    `<thead><tr><th>Kons.</th><th class="l">Játékos</th><th>Szórás</th>` +
    REAL.map(s => `<th>${esc(ABBR[s.slug])}</th>`).join('') + `<th class="l">Kinél van</th></tr></thead><tbody>` +
    disp.map(p => `<tr><td class="mono">${p.r.consensus}</td>
      <td class="l nm">${esc(p.n)} <span class="pclub">${esc(p.c)} · ${p.p}</span></td>
      <td class="best mono">${p.sp}</td>` +
      REAL.map(s => `<td class="dimc mono">${p.r[s.slug] ?? '–'}</td>`).join('') +
      `<td class="l">${p.own ? esc(p.own) : '<span class="tag">szabad</span>'}</td></tr>`).join('') + `</tbody>`;

  let filt = 'ALL';
  const drawBoard = () => {
    const rows = all.filter(p => filt === 'ALL' ? true : filt === 'FREE' ? !p.own : p.p === filt)
                    .sort((a, b) => a.r[active] - b.r[active] || a.r.consensus - b.r.consensus)
                    .slice(0, 300);
    document.getElementById('board-note').textContent =
      `${SRC.find(s => s.slug === active).label} sorrendjében · ${rows.length} sor`;
    document.getElementById('board').innerHTML =
      `<thead><tr><th>#</th><th class="l">Játékos</th><th class="l">Klub</th><th>Poz</th>` +
      REAL.map(s => `<th>${esc(ABBR[s.slug])}</th>`).join('') +
      `<th>Fedés</th><th class="l">Kinél van</th></tr></thead><tbody>` +
      rows.map(p => `<tr${p.own ? '' : ' class="hi"'}>
        <td class="mono">${p.r[active] ?? '–'}</td>
        <td class="l nm">${esc(p.n)}</td><td class="l pclub">${esc(p.c)}</td>
        <td class="dimc mono">${p.p}</td>` +
        REAL.map(s => `<td class="dimc mono">${p.r[s.slug] ?? '–'}</td>`).join('') +
        `<td class="dimc mono">${p.cv}/5</td>
        <td class="l">${p.own ? esc(p.own) : '<span class="tag">szabad</span>'}</td></tr>`).join('') + `</tbody>`;
  };
  const fs = [['ALL','mind'],['FREE','csak szabad'],...POS.map(([k,l])=>[k,l])];
  document.getElementById('bfilters').innerHTML = fs.map(([k, l]) =>
    `<button class="fbtn" data-f="${k}" aria-pressed="${k === 'ALL'}">${l}</button>`).join('');
  document.getElementById('bfilters').addEventListener('click', ev => {
    const b = ev.target.closest('.fbtn'); if (!b) return;
    filt = b.dataset.f;
    document.querySelectorAll('#bfilters .fbtn').forEach(x => x.setAttribute('aria-pressed', x === b));
    drawBoard();
  });
  window.__drawBoard = drawBoard;
  drawBoard();
}

/* ---------- vezérlés ---------- */
function paintPills() {
  document.getElementById('pills').innerHTML = SRC.map(s =>
    `<button class="pill" data-s="${s.slug}" aria-pressed="${s.slug === active}">
      ${starred === s.slug ? '<span class="st">★</span>' : ''}${esc(s.label)}
      <span class="n">${s.size}</span></button>`).join('');
  const s = SRC.find(x => x.slug === active);
  const winner = evaluate(active)[0];
  document.getElementById('pnote').innerHTML =
    `<b>${esc(s.label)}</b> — ${esc(s.note)}. ${s.size} játékos; aki nincs rajta, ` +
    `<b>${s.size + 1}</b> pontot kap. Ezzel a rangsorral <b>${esc(winner.name)}</b> vezet.` +
    (starred ? ` A ★ a te választásod: <b>${esc(SRC.find(x => x.slug === starred).label)}</b>.` : '');
  const w = document.getElementById('warn');
  if (s.covers < 80) {
    w.hidden = false;
    w.innerHTML = `Ez a lista a 90 draftolt játékosból csak <b>${s.covers}</b>-et rangsorol, ` +
      `${s.of - s.covers} tehát egységesen ${s.size + 1} pontot kap. A sorrend ezért nagyrészt azt ` +
      `méri, kinek van több „ismert" játékosa — összehasonlításra a bővebb listák jobbak.`;
  } else { w.hidden = true; }
  const sb = document.getElementById('star');
  sb.setAttribute('aria-pressed', starred === active);
  sb.textContent = starred === active ? '★ ezt tartod a legjobbnak' : '★ ezt tartom a legjobbnak';
}

function refresh() {
  paintPills();
  const ms = evaluate(active);
  document.getElementById('kick').textContent =
    `${D.league.name} · ${D.league.size} csapat · ${D.league.rounds} kör · FPL Draft 2026/27`;
  renderTeams(ms, active);
  renderDraft(ms, active);
  renderRate(ms, active);
  drawExport(ms);
  if (window.__drawBoard) window.__drawBoard();
  const foot = SRC.filter(s => s.slug !== 'consensus').map(s => esc(s.label)).join(', ');
  document.getElementById('foot').innerHTML =
    `<b>Források.</b> ${foot} — mind FPL <code>element_id</code>-ra kötve a ` +
    `<code>draft.premierleague.com/api/bootstrap-static</code> törzsből, klub + pozíció szerinti ` +
    `egyediség-ellenőrzéssel.<br>
    <b>Keretek.</b> A nyílt Draft API-ból élőben: <code>league/${D.league.id}/element-status</code> ` +
    `(aktuális birtoklás, csere után is helyes) és <code>draft/${D.league.id}/choices</code> ` +
    `(a 90 pick körrel és sorszámmal). A képernyőképekből olvasott keretek mind a hat csapatnál ` +
    `egyeztek az API-val. A kezdő XI a képernyőképekből — a deadline előtt az API nem adja ki.<br>
    <b>Miért összeg?</b> A draft-rangsor a draft-sorrendet tükrözi, nem a várható pontot — a pozíciós
    szűkösség bele van árazva. Az összeg ezért a keret <b>mélységét</b> is méri: egy elitcsatár nem hoz
    vissza öt mélységi védőt.<br>
    <b>Forrásfüggés.</b> A rangsorok Spearman-egyezése 0,48–0,79 — ugyanaz a keret más forráson más
    helyre kerül. Ezért van a választó: a végeredmény robusztussága maga is információ.`;
}

document.getElementById('pills').addEventListener('click', ev => {
  const b = ev.target.closest('.pill'); if (!b) return;
  active = b.dataset.s; refresh();
});
document.getElementById('star').addEventListener('click', () => {
  starred = starred === active ? null : active;
  try { starred ? localStorage.setItem('vk-draft-src', starred) : localStorage.removeItem('vk-draft-src'); } catch (e) {}
  paintPills();
});
document.querySelectorAll('[role="tab"]').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('[role="tab"]').forEach(x => {
    const on = x === t;
    x.setAttribute('aria-selected', on);
    document.getElementById(x.getAttribute('aria-controls')).hidden = !on;
  });
}));

renderBoards();
renderCompare();
drawReadout();
refresh();
</script>
"""

out = pathlib.Path(A.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(TPL.replace("__TITLE__", A.title).replace("__DATA__", DATA), encoding="utf-8")
print(f"{out}: {len(TPL) + len(DATA)} bájt")

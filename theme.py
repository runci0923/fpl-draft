"""Közös Vikingo Design System fejrész — mindkét lap ezt használja,
hogy a tokenek ne csússzanak szét a draft- és a forduló-oldal között.
A `<style>` NYITVA marad: a lapok a saját szabályaikat utána fűzik.
"""

HEAD = r'''<link rel="preconnect" href="https://fonts.googleapis.com">
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
'''

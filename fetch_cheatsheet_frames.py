#!/usr/bin/env python3
"""FPL Fran cheat sheet: videóból képkockák, hogy ne kelljen kézzel fotózni.

A videó FEJEZETEI pontosan a cheat sheet tábláit jelölik (Midfielders 5m-6.5m,
Midfielders 6.5m+, Forwards, Defenders), ezért nem vaktában mintázunk: fejezeten
belül sűrűn, az introt kihagyva. Az egymást követő szinte azonos kockákat az
ffmpeg mpdecimate szűrője dobja el, így nem 120 képet kell átnézni, hanem annyit,
ahány tényleg más táblarészt mutat.

    python3 fetch_cheatsheet_frames.py                  # a csatorna legutóbbi cheat sheetje
    python3 fetch_cheatsheet_frames.py <url|videoID>
    python3 fetch_cheatsheet_frames.py --every 12 --height 1080

Kimenet: cheatsheet/frames/<videoID>/<fejezet>/f_<mmss>.jpg + manifest.json
"""
import argparse, json, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CHANNEL = "https://www.youtube.com/@FPLFran/videos"
TITLE_RE = re.compile(r"cheat\s*sheet", re.I)

ap = argparse.ArgumentParser()
ap.add_argument("video", nargs="?", help="URL vagy videó-ID; üresen a legutóbbi cheat sheet")
ap.add_argument("--every", type=int, default=15, help="fejezeten belül ennyi másodpercenként (15)")
ap.add_argument("--height", type=int, default=1080, help="videó-magasság (1080)")
ap.add_argument("--crop", type=float, default=0.76,
                help="a képnek ekkora BAL része a tábla (0.76); a webkamerát ki kell vágni, "
                     "különben a folyamatos mozgás miatt a duplikátum-szűrő nem fog")
ap.add_argument("--skip-intro", action="store_true", default=True)
ap.add_argument("--keep-video", action="store_true", help="a letöltött videó maradjon meg")
A = ap.parse_args()

for tool in ("yt-dlp", "ffmpeg"):
    if not shutil.which(tool): sys.exit(f"nincs meg: {tool} (brew install {tool})")

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout

def newest_cheatsheet():
    out = run(["yt-dlp", "--no-update", "--flat-playlist", "--playlist-end", "12",
               "--print", "%(id)s\t%(title)s", CHANNEL])
    for line in out.splitlines():
        vid, _, title = line.partition("\t")
        if TITLE_RE.search(title):
            print(f"legutóbbi cheat sheet: {title}")
            return vid
    sys.exit("a csatorna utolsó 12 videója közt nincs cheat sheet")

vid = A.video or newest_cheatsheet()
if "youtube.com" in vid or "youtu.be" in vid:
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", vid)
    vid = m.group(1) if m else sys.exit(f"nem tudom kiolvasni a videó-ID-t: {vid}")
url = f"https://www.youtube.com/watch?v={vid}"

meta = json.loads(run(["yt-dlp", "--no-update", "--skip-download", "--print-json", url]))
chapters = meta.get("chapters") or [{"start_time": 0, "end_time": meta["duration"],
                                     "title": "teljes videó"}]
if A.skip_intro:
    chapters = [c for c in chapters if not re.match(r"intro", c["title"], re.I)] or chapters
print(f'{meta["title"]}\n{len(chapters)} fejezet, {meta["duration"]}s')

OUT = HERE / "cheatsheet" / "frames" / vid
OUT.mkdir(parents=True, exist_ok=True)
mp4 = OUT / "video.mp4"
if not mp4.exists():
    print("letöltés (csak videósáv, hang nélkül)…")
    subprocess.run(["yt-dlp", "--no-update", "-q", "--progress",
                    "-f", f"bv*[height<={A.height}][vcodec^=avc1]/bv*[height<={A.height}]",
                    "-o", str(mp4), url], check=True)
print(f"videó: {mp4.stat().st_size/1e6:.0f} MB")

def slug(t):
    t = re.sub(r"[^\w\s.-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:40] or "fejezet"

man = {"video": vid, "title": meta["title"], "url": url,
       "uploaded": meta.get("upload_date"), "duration": meta["duration"],
       "every": A.every, "height": A.height, "crop": A.crop, "chapters": []}
total = 0
for c in chapters:
    a, b = int(c["start_time"]), int(c["end_time"])
    d = OUT / slug(c["title"])
    d.mkdir(exist_ok=True)
    for f in d.glob("*.jpg"): f.unlink()
    # fejezeten belül every másodpercenként, majd a szinte azonos kockák eldobása
    # a vágás ELŐBB jön, mint a duplikátum-szűrő: a webkamera mozgása különben minden
    # kockát „különbözőnek" mutat, és 118 kép helyett sem lesz kevesebb
    vf = (f"crop=iw*{A.crop}:ih:0:0,fps=1/{A.every},"
          "mpdecimate=hi=64*14:lo=64*5:frac=0.12")
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", str(a), "-to", str(b),
                    "-i", str(mp4), "-vf", vf,
                    "-fps_mode", "vfr", "-q:v", "2", str(d / "f_%03d.jpg")], check=True)
    fr = sorted(d.glob("*.jpg"))
    # a fájlnév-index -> hozzávetőleges időbélyeg (a kidobott kockák miatt csak becslés)
    man["chapters"].append({"title": c["title"], "start": a, "end": b, "dir": d.name,
                            "frames": [f.name for f in fr]})
    total += len(fr)
    print(f'  {c["title"]:<26} {b-a:4d}s -> {len(fr):3d} kép  ({d.relative_to(HERE)})')

(OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
if not A.keep_video:
    mp4.unlink(); print("videó törölve (--keep-video, ha kell)")
print(f"\n{total} kép: {OUT.relative_to(HERE)}")

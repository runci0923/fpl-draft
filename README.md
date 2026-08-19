# FPL Draft — Vadkelet scorecard

Egy draft-rendszerű FPL liga értékelése: **több független rangsor**, saját vonal-pontozás,
és fordulónkénti **projektált vs. valós** H2H eredmény.

**Élő oldal:** https://runci0923.github.io/fpl-draft/ — a forduló (landing) ·
[draft-elemzés](https://runci0923.github.io/fpl-draft/draft.html)

A publikus oldalon a résztvevők csak keresztnévvel szerepelnek, csapatnév nélkül.

## Pipeline

```bash
python3 build_idmap.py         # draft <-> fő FPL element_id  -> idmap.json
python3 fetch_rankings.py      # 5 draft-rangsor              -> sources/
python3 fetch_league.py        # liga, keretek, 90 pick       -> league.json
python3 build.py               # összefűzés + konszenzus      -> data.json
python3 fetch_projections.py   # projekció-snapshot           -> proj/
python3 build_h2h.py           # projektált H2H eredmények    -> h2h.json
python3 render.py              # a lap (teljes nevekkel)      -> index.html
python3 publish_pages.py       # publikus build               -> docs/
```

`league.json` és `data.json` szándékosan nincs verziókövetve (valódi neveket tartalmaznak),
de bármikor újragenerálhatók a nyílt API-ból.

## Adatforrások

**Rangsorok** — [The Draft Society](https://www.thedraftsociety.com/fpl-draft-rankings) ·
[DraftFantasy](https://www.draftfantasy.com/fpl/draft-cheat-sheet) ·
[FPL hivatalos](https://draft.premierleague.com/draft) ·
[OneFPL](https://onefpl.com/blog/fpl-draft-rankings-top-100-2026-27) ·
[RotoWire](https://www.rotowire.com/soccer/article/fantasy-premier-league-fpl-rankings-top-400-for-2026-27-season-124261)

**Projekciók** — [FPL Form](https://fplform.com/fpl-predicted-points) (fordulónkénti, ingyenes,
automatizált) · [Fantasy Football Hub](https://www.fantasyfootballhub.co.uk/predictions) PRO
(fordulónkénti pont + várható perc + gól/gólpassz; **fizetős**, kézi lépés, nyílt webre nem kerül)

### Projekciós források — mi jött be és mi nem

| Forrás | Állapot | Miért |
|---|---|---|
| FPL Form | ✅ automatizált | POST-export CSV-t ad, kulcs nélkül |
| FPL Hub PRO | ✅ kézi lépés | `public-api…/league/players`, `after` kurzor, bearer a `/auth/access-token`-ből. Bejelentkezés kell -> nem CI-zhető |
| FPL hivatalos `ep_next` | ❌ kivéve | szezon előtt lapos placeholder (Haaland = Raya = 4,0) |
| [Solio](https://fpl.solioanalytics.com/) | ⛔ elakadt | a rács **canvasra** rajzol, árnyék-DOM-ban; a 21 soros akadálymentességi tükör teljes pontossággal olvasható, de görgetésre nem frissül. Projekciós végpont nem került elő (`/api/initial-fpl-plan-data/{a}/{b}` csak terv-metaadat) |
| [fplestimator](https://www.fplestimator.com/best-picks) | ⛔ elakadt | az xPts **kliens oldalon** számolódik. Supabase-ben a `players`/`fixtures`/`events` anon-olvasható, de a `player_gameweek_stats` és `player_xpts_snapshot` RLS-zárt; a `get_xpts_snapshots_range(start_gw,end_gw)` RPC üres (befagyasztott visszamérés, szezon előtt nincs). A DOM-ból 558 sor kinyerhető (5 fordulós **összeg**, nem per-forduló), de a lap CSP-je blokkolja a localhost-átadást |
| [daniel-mehta/FPL-Expected-Points](https://github.com/daniel-mehta/FPL-Expected-Points) | ❌ kiesik | nem publikált becslés, hanem futtatható modell; a CSV-k 2024 novemberiek |

**Liga** — a nyílt `draft.premierleague.com/api` (auth nélkül)

## Amiért érdemes elolvasni a kódot

- A **Draft és a fő FPL `element_id` nem ugyanaz az id-tér** — 595-ből 24 más játékost jelöl.
  Tzolis a Draftban 554, a fő API-ban 557 (ott Penders, egy kapus). Minden külső projekció
  a fő id-t használja. Leképezés nélkül a becslés csendben rossz játékosra kerül.
- A **projektált meccspontszám a becslés szerinti legjobb legális kezdő XI**-ből számol
  (11 fő, 1 GK, DEF 3–5, MID 2–5, FWD 1–3). Deadline előtt a valós XI nem kérhető le.
- **Snapshot, nem felülírás:** minden projekció-futás külön fájl időbélyeggel. A deadline
  előtti utolsó a kanonikus — az az információ, amiből dönteni lehetett.
- **Az időbélyeg MINDIG UTC, `Z` utótaggal.** A fejlesztőgép CEST, a CI-runner UTC; naiv
  időbélyeggel a fájlnév lexikai rendezése a RÉGEBBI snapshotot hiszi frissebbnek
  (18:03 UTC vs. 19:55 CEST). A `build_h2h.py` ezen felül a fájl `taken_at` mezője szerint
  rendez, nem fájlnév szerint — ez a második védelmi vonal.
- A **forrás dönti el, ki nyer.** A rangsorok Spearman-egyezése 0,48–0,79.
- **Az igazolásokat nem kell külön követni.** Publikus tranzakció-végpont nincs (404), de az
  `element-status` mindig az aktuális birtoklást adja, és minden futás ebből épít. A változás
  a `rosters.json` git-diffjében olvasható: `git log -p rosters.json`.
- **A snapshot-nyesés nem veszteség.** Fordulónként 3 marad a munkakönyvtárban; a törölteket
  a git megőrzi (`git log --diff-filter=D --name-only -- proj/`).

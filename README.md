# FPL Draft — Vadkelet scorecard

Egy draft-rendszerű FPL liga értékelése: **több független rangsor**, saját vonal-pontozás,
és fordulónkénti **projektált vs. valós** H2H eredmény.

**Élő oldal:** https://runci0923.github.io/fpl-draft/

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

**Projekciók** — [FPL Form](https://fplform.com/fpl-predicted-points) (fordulónkénti, ingyenes) ·
FPL hivatalos `ep_next` (baseline)

**Liga** — a nyílt `draft.premierleague.com/api` (auth nélkül)

## Amiért érdemes elolvasni a kódot

- A **Draft és a fő FPL `element_id` nem ugyanaz az id-tér** — 595-ből 24 más játékost jelöl.
  Tzolis a Draftban 554, a fő API-ban 557 (ott Penders, egy kapus). Minden külső projekció
  a fő id-t használja. Leképezés nélkül a becslés csendben rossz játékosra kerül.
- A **projektált meccspontszám a becslés szerinti legjobb legális kezdő XI**-ből számol
  (11 fő, 1 GK, DEF 3–5, MID 2–5, FWD 1–3). Deadline előtt a valós XI nem kérhető le.
- **Snapshot, nem felülírás:** minden projekció-futás külön fájl időbélyeggel. A deadline
  előtti utolsó a kanonikus — az az információ, amiből dönteni lehetett.
- A **forrás dönti el, ki nyer.** A rangsorok Spearman-egyezése 0,48–0,79.

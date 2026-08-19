# Draft-értékelő — Vadkelet (FPL Draft 2026/27)

Egy lap, ami a hat keretet több független draft-rangsor szerint pontozza.
Kevesebb pont = jobb keret.

## Futtatás

```bash
cd ../..                        # FPL projekt-gyökér
.venv/bin/python draft/rank/fetch_rankings.py   # 5 rangsor letöltése -> sources/
.venv/bin/python draft/rank/fetch_league.py     # a liga élő adata   -> league.json
.venv/bin/python draft/rank/build.py            # összefűzés         -> data.json
.venv/bin/python draft/rank/render.py           # a lap             -> index.html
```

## Adatforrások

| Fájl | Mi | Honnan |
|---|---|---|
| `sources/_players.csv` | 595 játékos + hivatalos `draft_rank` | `draft.premierleague.com/api/bootstrap-static` |
| `sources/official.csv` | FPL hivatalos sorrend, 595 | ugyanaz |
| `sources/draftsociety.csv` | The Draft Society Top 200 | a site Google Sheetje (CSV-export) |
| `sources/draftfantasy.csv` | DraftFantasy Top 240, xP+VORP | `draftfantasy.com/fpl/draft-cheat-sheet` |
| `sources/rotowire.csv` | RotoWire Top 400 | rotowire.com cikk-tábla |
| `sources/onefpl.csv` | OneFPL Top 100 | onefpl.com |
| `league.json` | keretek, birtoklás, 90 pick | `api/league/20944/…` + `api/draft/20944/choices` |
| `squads.json` | **csak** a GW1 kezdő XI | a Draft-app képernyőképeiből |

## A lap öt nézete

`Csapatok` · `Draft-tábla` · `Saját értékelés` · `Összevetés` · `Rangsorok`

A **Saját értékelés** kliens-oldali: vonalanként (kapus → védelem → közép → támadó) 1–5
csúszka managerenként, `localStorage`-ban tárolva (`vk-draft-rating`). A „vak mód" elrejti a
rang-chipeket, hogy az értékelés ne horgonyozzon a rangsorra. A tabella a kitöltött vonalakból
számol, és kiírja, hol tér el a saját sorrend a választott forrásétól.

## Amit szándékosan NEM csinálunk

**Nincs kézi rang-korrekció.** Volt rá mechanizmus (`overrides.json`), és a Tzolis-eset
indokolta is volna (DraftFantasy #202, mert bizonytalan játékidőt árazott, holott azóta
kiderült, hogy Arsenal kezdő balszélső — a többi négy forrás #52/#55/#76/#120-ra teszi).
A tulaj döntése: **elavult értéket nem írunk át**, mert minden korrekció újabb szubjektív
döntés, és túl sok lenne belőle. Helyette a lap „Ahol a szakértők vitáznak" szekciója
és a rang-szórás jelzi ezeket az eseteket — Tzolisnál 150 a szórás.

## Projektált vs. valós H2H (épül)

```bash
.venv/bin/python draft/rank/build_idmap.py        # draft <-> fő FPL id  -> idmap.json
.venv/bin/python draft/rank/fetch_projections.py  # projekció-snapshot   -> proj/
.venv/bin/python draft/rank/build_h2h.py          # projektált eredmények -> h2h.json
```

`fetch_projections.py` **snapshot-elvű**: minden futás külön fájl időbélyeggel. A deadline
előtti utolsó snapshot a kanonikus — az az információ, amiből dönteni lehetett.

`build_h2h.py` a projektált meccspontszámot a **becslés szerinti legjobb legális kezdő XI**-ből
számolja (11 fő, 1 GK, DEF 3–5, MID 2–5, FWD 1–3). Deadline előtt a valós XI nem kérhető le,
és a racionális manager amúgy is ezt állítaná. Mind a 36 generált XI szabályos, és csak a saját
keretből válogat — ez ellenőrzött.

**Ami időhöz kötött:** a szerencse-mérleg (valós mínusz projektált) és a forrás-pontossági
rangsor csak lejátszott fordulókból áll össze. GW1 előtt nulla lezárt meccs van, tehát ezek
a táblák hetente hízni fognak, nem egy futásból készen.

## Kőbe vésett tények

- **A Draft API ugyanúgy nyílt, mint a sima FPL-é.** Auth nélkül megy:
  `bootstrap-static`, `game`, `league/{id}/details`, `league/{id}/element-status`,
  `draft/{id}/choices`, `entry/{id}/public`. Auth CSAK a `bootstrap-dynamic`-hoz kell
  (az adja a saját liga-ID-t: liga **20944** „Vadkelet", entry **106153** „Vikingo").
- **A `bootstrap-static` minden játékosnál ad `draft_rank`-et** — kész hivatalos rangsor
  mind az 595 játékosra, külön scraping nélkül.
- **Az `element-status` és a `choices` `entry_id`-t használ (106153…), NEM a
  `league_entries[].id`-t (106523…).** A kettő összekeverése csendben 0 találatot ad.
- **A kezdő XI a deadline előtt nem kérhető le**: `entry/{id}/event/1` → „No pick history".
  Ezért van a képernyőkép-alapú `squads.json` — a keret-tagságot viszont az API adja.
- **A `choices` a draft tényleges sorrendje** (`index`, `round`, `pick`, `was_auto`).
  Ebből számol a lap „mennyit hagytak az asztalon" metrikája.
- **A forrás dönti el, ki nyer.** A rangsorok Spearman-egyezése csak 0,48–0,79.
  Konszenzus / DraftFantasy / FPL szerint Krisztián, Draft Society / RotoWire / OneFPL
  szerint Daniel vezet. Ezért választható a forrás a lapon.
- **A fedés fontosabb, mint a lista hossza.** Az OneFPL 100-as listája a 90 draftolt
  közül csak 66-ot rangsorol, a többi egységesen büntetőpontot kap → az a sorrend
  nagyrészt azt méri, kinek van több „ismert" játékosa. A lap figyelmeztet rá.
- **Az összeg-alapú pont mélységet is mér**, nem csak sztárokat: egy elitcsatár nem hoz
  vissza öt mélységi védőt. A draft-rangsor eleve draft-sorrend, nem várható pont.
- **A „pick mínusz rang" mérleg mindenkinél negatív** (a draft mélyebbre megy, mint a
  rangsor sűrű vége) → félrevezető. Helyette elszalasztott rang: a választott játékos
  rangja mínusz az akkor még elérhető legjobbé. Mindig ≥ 0, a 0 = BPA.
- **Névpárosítás: az egyediség elve** (klub + pozíció szűkítés, majd névalak-lépcső:
  web_name → családnév → `B.Fernandes`-alak → teljes név). Ehhez kell a török **`ı` → `i`**
  transzliteráció is (az NFKD nem bontja fel), különben a Kadıoğlu sosem párosul.
  Mind a 90 draftolt és mind az 5 forrás párosítása így megy, kézi kivétel nélkül.

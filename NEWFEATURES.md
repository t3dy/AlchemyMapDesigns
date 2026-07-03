# NEW FEATURES — the upgraded map toolkit

A showcase of everything built to spruce up the maps for ALCHEMYTIMELINEMAP.
Where the old map was a single grey pin-board on a modern street map, the toolkit is
now a **directable instrument**: you describe a map and the software builds it, in any
of four hand-tuned aesthetics, across several distinct *kinds* of map.

> Live demos assume a static server from the project root:
> `python -m http.server 8777` → open the URLs below. Everything is self-contained
> HTML (MapLibre GL + deck.gl from CDN); no build step.

**Start here:** the guided tour → `/tour/index.html` (9 chapters, scrollytelling).

---

## 1. The MapSpec compiler — *you describe it, the software builds it*

The core idea. A small JSON "recipe" compiles to a finished interactive map. Change a
word, get a different map; the recipe is reproducible and version-controllable.

```json
{
  "title": "Paracelsian Alchemy in Central Europe, Before the Rosicrucians",
  "scope": { "year_start": 1490, "year_end": 1610,
             "regions": ["Germany","Switzerland","Austria","Bohemia"],
             "themes": ["paracelsian-alchemy","iatrochemistry","spagyrics"] },
  "render": { "basemap": {"style":"parchment","show_modern_labels":false},
              "layers": ["points","flows","time-animation"], "color_by": "theme" },
  "narrative": { "intro": "…", "provenance_note": "Cutoff on the eve of the 1614 Fama." }
}
```

- Engine: `scripts/build_map.py` · contract: `specs/mapspec.schema.json`
- Vocabulary helper: `scripts/list_vocab.py` (prints valid concept/person/region slugs
  **with event counts**, so you know before authoring whether a theme is populated)
- The compiler now **validates the spec** (bad enums, inverted years/bboxes, unknown
  keys) and **refuses to build without `narrative.provenance_note`** — honesty is a
  build requirement, not a suggestion (`--allow-unsourced` for throwaway drafts).
- `render.basemap.style` now actually sets the map's opening theme, and
  `show_modern_labels` its label state (previously schema-only fields).
- Example output: `/prototypes/paracelsian-before-rosicrucians.mapspec.html`
  *(→ 34 events, 8 locations, 10 transmission arcs, borders c. 1530)*

---

## 2. The theme engine — six faces, switchable at runtime

One map, six complete visual identities, changeable from a dropdown (and a font
picker). Re-skins the basemap, palette, and typography live.

| Theme | Mood | Best for |
|-------|------|----------|
| **Modern Atlas** | clean, muted, legible | clarity; accessibility fallback |
| **Copperplate Engraving** | sepia line-work on cream | the printed alchemical corpus |
| **Illuminated Manuscript** | parchment + gold, Cinzel caps | courts, patronage, treasure |
| **Alchemical Noir** | near-black, luminous gold arcs | single lives, spectacle |
| **Woodcut & Rubric** *(new)* | stark black line + vermillion on cream | scholastic polemic, print wars, medieval material |
| **Lapis & Gold** *(new)* | ultramarine field, gilt points | late antiquity, Hermetica, celestial themes |

**Styles are now assigned, not defaulted** *(new)*: every generated map opens in
the style that suits its material — copperplate for print-culture subjects, lapis
for the late-antique, noir for hidden knowledge, woodcut for disputation — and
carries a `design_note` explaining the choice, shown on its gallery page. The six
styles are spread across the whole fleet (8–12 maps each), so browsing the gallery
is also a tour of the design system. The reader can always switch live.

Try it: open any map and use the **Theme** dropdown, or scroll Chapter III of the tour
(the Arabic map re-skins as you scroll).

---

## 3. Layered controls — "controls like a search engine"

Three tiers, so newcomers aren't overwhelmed and power users aren't limited:

- **Lenses** (one click reconfigures everything): `Transmission · Lives · Texts ·
  Themes · Density`.
- **Filter bar**: theme, font, colour-by (theme / region / era), layer toggles.
- **Advanced drawer**: arc width, point size, opacity, basemap labels, rich tooltips,
  legend on/off.

Colour is assigned at runtime from the active theme's palette, so changing theme or
colour-by re-skins instantly.

---

## 4. Visual layers

- **Base geography** *(new)* — every map embeds real coastlines, land, lakes,
  and major rivers (Natural Earth, slimmed to ~700 KB by
  `scripts/fetch_basegeo.py`, themed to the active aesthetic). The sea is the
  canvas; the land is drawn on it. This replaced the demotiles CDN basemap
  entirely — maps now *look like maps* even offline, and there is no external
  style dependency left.
- **Points** — places, sized by event count, coloured by category.
- **Transmission arcs** — knowledge in motion (person itineraries between centres).
- **Labels** — place names (deck.gl TextLayer), now **on by default** in every
  lens except Density.
- **Density heatmap** — centres of gravity (deck.gl HeatmapLayer).
- **Period borders** *(new)* — approximate historical political boundaries for the
  year nearest `basemap.historical_boundaries_year`, embedded from a local cache
  (`data/boundaries/`, sourced from *historical-basemaps*, slimmed to ~100 KB/year
  by `scripts/fetch_boundaries.py`). Toggleable layer chip; hover a border for the
  polity's name; the panel carries an automatic "approximate, for orientation"
  caveat. No more 16th-century alchemists on 21st-century borders.

All GPU-rendered (deck.gl) over the MapLibre vector basemap, in a single interleaved
canvas.

---

## 5. Time

A scrubber + **▶ Play** animates events accumulating through the years. Present on
every data map; on the journey it becomes a *progress-through-a-life*.

---

## 6. Map *types* — reusable templates

### 6a½. The Scholarship Shelf *(new)*
`scripts/build_scholarship.py` — one map per **most-cited study in the
collection's own historiography**. Citation counts are mined from scholar-surname
mentions across the 680 events (Principe 90 · Newman 60 · Smith 21 · Hanegraaff
19 · Fowden 15 · Copenhaver 13 · Pereira 8); each study gets its key topics and
figures scoped from the corpus, a style matched to its source base, and the
citation count in its provenance line. E.g. *Laboratories of Art* (Pamela Smith):
the artisan-practitioners — Agricola, Ercker, Zieglerin, Paracelsus, Maier — in
copperplate, the register of De re metallica's own plates.

### 6a. Data maps (era & century)
Generated in batch by `scripts/build_all.py` from the corpus:
- **6 era showcases** — Greco-Egyptian, Arabic Transmission, Latin Medieval,
  Renaissance Hermeticism, Paracelsian, English Chymistry. *(e.g. Arabic →
  231 events, 23 places, 44 arcs)*
- **11 century maps (8th–18th)** — transmission focus; scroll the tour's Chapter VI
  to watch the centre of gravity migrate Baghdad → al-Andalus → Latin Europe → north.

### 6b. The Journey template — *a life as a route*
`scripts/build_journey.py` reads a curated journey JSON and draws a **self-drawing
animated path that withholds the ending** — future stops never render, so the reader
can stop mid-life knowing nothing of the end. Legs are styled by evidence
(solid = documented, dashed = inferred); nodes sized by dwell time.

```json
{ "place": "Geneva", "lat": 46.2044, "lon": 6.1432,
  "year_start": 1579, "dwell": 1,
  "what": "After three obscure years wandering, surfaces in Calvinist Geneva…",
  "evidence": "attested", "leg_evidence": "inferred",
  "source": "Rowland 2008 (the 1576–79 route is undocumented)" }
```

Demo: `/prototypes/journey-bruno.html` (Giordano Bruno, 13 stops, 3 reconstructed legs).

### 6c. The Network template — *who knew whom*
`scripts/build_network.py` reads curated, typed, directed, weighted, evidence-bearing
person-to-person edges and renders an explorer over **four constellations**:
Rudolfine Prague · English Chymists · Paracelsian Movement · Republic of Letters.

```json
{ "source": "rudolf-ii", "target": "edward-kelley", "type": "patron-of",
  "direction": true, "weight": 3, "evidence": "attested", "survives": true,
  "note": "Knighted, then imprisoned Kelley until his death, 1591–98" }
```

- Edges coloured by **type**, width by **weight**, opacity by **confidence**,
  direction by a source→target colour gradient.
- **Click a node to pivot** — incident ties highlight, the rest dim.
- **Survival-bias toggle** — "only what survives" drops inferred ties and over-centres
  the archive-keepers (Republic of Letters collapses 7 edges → 4).

Demo: `/prototypes/network.html` · deep-link `?subject=republic-of-letters`.

---

## 7. Uncertainty treatments — four experiments, one map

The journey ships a selector demonstrating every approach to rendering doubt:

- **Lay** — clean story, no apparatus.
- **Understated** — quiet solid/dashed lines + citation on hover.
- **Scholar** — full citations + "this leg is reconstructed" notes.
- **Centerpiece** — doubt made visible: glowing ghost-routes, date halos, a live
  "What we don't know — so far" panel.

---

## 8. Honesty & provenance features

- Evidence encoded visually: **line style = evidence, opacity = confidence, colour =
  category** (never confidence — that's the commonest map lie).
- Every node/edge/stop carries a **source on hover**.
- A persistent **"What this map does NOT show"** note on network maps (the survival
  caveat).
- Curated layers are sourced (Yates/Rowland/Gatti for Bruno; Evans for Rudolfine
  Prague; Hartlib Papers for the correspondence).
- **Enforced at build time** *(new)*: a MapSpec without `narrative.provenance_note`
  is a build **error**, not a warning. Journey stops without `evidence` + `source`,
  and network edges without `type`/`evidence`/`note`/`survives`, likewise refuse to
  build. The `--allow-unsourced` escape hatch exists for drafts and says so loudly.
- **Compile-time truth-telling** *(new)*: the compiler warns when a requested theme
  matches 0 events (empty-lens trap) and when locations are ungeocoded.

---

## 9. Embedding, sharing & export

Every map is embeddable and drivable:
- **URL params**: `?ui=min` (hide chrome), `?theme=`, `?lens=`, `?year=`, `?subject=`,
  `?survive=1`, `?mode=` — plus *(new)* deep-state params `?color=`, `?layers=`
  (dot-separated), `?arcw=`, `?pts=`, `?op=`.
- **🔗 Link** *(new)* — one click copies a permalink that reproduces the exact
  current view: theme, lens or custom layer set, year, colour-by, and slider values.
- **⤓ PNG** *(new)* — exports the current view as a PNG with the title, the
  "through year", and the borders caveat burnt into a provenance strip at the foot
  (a map that leaves the toolkit still carries its honesty apparatus).
- **postMessage**: `{type:"mapctl"|"journeyctl"|"netctl", …}` to change theme, lens,
  year, stop, subject, or toggles from a parent page.

This is what lets the tour drive maps as you scroll.

## 9b. Accessibility (data maps)

- `prefers-reduced-motion` is honoured: Play becomes a discrete step-through-time
  button instead of an animation.
- Controls carry ARIA labels/roles; the year readout is a live region; layer chips
  are keyboard-operable (Tab + Enter/Space).

---

## 10. The scrollytelling tour

`/tour/index.html` — a 9-chapter guided experience that explains every feature for
web-dev beginners and cartography laymen, with live embedded maps that respond to
scroll: the data lacuna, the compiler, the four themes, the lenses, the era gallery,
the century migration, Bruno's withheld-ending journey, and the network survival-bias
reveal.

## 10b. The Map Gallery *(new)*

`/gallery/index.html` — every map in the project (50 at last build) as preview
cards grouped into eight families (directed examples, eras, centuries, themes,
figures, regions, journeys, networks), with a sticky family jump-nav. Each card carries a deterministic **SVG
preview drawn from the map's own compiled data** (points, arcs, journey paths,
network edges — no screenshots needed), and clicks through to a per-map page
with the live embedded map, its stats, its provenance note, a link to its JSON
recipe, and **accordion notes on the ideas that map is trying** (a shared
registry of 16 ideas: the compiler, period borders, the withheld ending,
survival bias, and so on). Generated by `scripts/build_gallery.py`; re-run it
after adding any map. The gallery also serves HTML renderings of the two new
reference docs:

- **`TOOLKIT.md`** (→ `/gallery/toolkit.html`) — the Developers Toolkit:
  architecture, the MapSpec contract, full CLI reference for every engine,
  curated-data formats, runtime APIs (URL params / postMessage / debug globals),
  the theme engine, extension recipes, testing, archival caveats.
- **`MANUAL.md`** (→ `/gallery/manual.html`) — the Instruction Manual for
  authors and readers: directing maps in plain language, reading each map type,
  the uncertainty treatments, sharing/export, how to read honestly,
  troubleshooting.

---

## 11. Command-line authoring (skills)

Run Claude Code from `C:\Dev\MAPRESEARCH` and type:

- **`/buildmap <region + era + theme>`** → a data map (e.g. "Paracelsian alchemy in
  Central Europe before the Rosicrucians").
- **`/journey <person>`** → a curated, sourced biographical journey (e.g. "Giordano
  Bruno").
- **`/network <circle>`** → a curated relationship/patronage map (e.g. "the Hartlib
  circle").

Each skill enforces the project's rules: provenance required, evidence marked
honestly, actor/analyst distinction preserved.

---

## Inventory

| Kind | Files |
|------|-------|
| Engines | `build_map.py`, `build_journey.py`, `build_network.py`, `build_all.py`, `build_showcase.py`, `build_gallery.py`, `list_vocab.py` |
| Data tooling | `fetch_boundaries.py` (period borders cache) · `test_smoke.py` (regression suite) |
| Skills | `/buildmap`, `/journey`, `/network` |
| Curated data | 3 journeys (`journey-bruno/paracelsus/dee.json`), `networks.json` (6 subjects), `data/boundaries/` (24 slimmed years, 100–1800 CE) |
| Generated maps | 43 HTML in `prototypes/` (6 eras + 11 centuries + 7 themes + 8 figures + 6 regions + 3 journeys + network explorer + example) |
| Specs | `specs/mapspec.schema.json` + 1 example + 17 generated + 21 showcase |
| Presentation | `gallery/` (48 cards + 48 map pages + docs) · `tour/index.html` (9 chapters) + `tour/manifest.json` |
| Docs | this file · `AUDIT.md` · `NEXTSTEPS.md` · `TOOLKIT.md` · `MANUAL.md` · `research/MAPTYPES_FRAMEWORK.md` · `README.md` · `CAPABILITIES.md` |

## Testing

`python scripts/test_smoke.py` — dependency-free suite: every spec on disk must
validate, carry provenance, compile to a non-empty map, and emit structurally
sound HTML; the validator must reject a deliberately bad spec; the boundary cache
must be present, plausible, and slim; curated journey/network data must pass its
evidence rules; the tour manifest must agree with the prototypes on disk.

## Known limitations (see AUDIT.md for the full picture)

- **Screenshots** can't be captured in the current sandbox (WebGL hangs the tool);
  verification is via `test_smoke.py` + DOM/state checks. Maps render normally in a
  real browser.
- **Period borders are approximate** — scholarly reconstructions from
  *historical-basemaps*, snapped to the nearest cached year; every map that shows
  them says so. Coastlines/lakes/rivers are real (embedded Natural Earth) but
  *modern* — period physical geography is future work.
- **Inferred network ties** show by opacity, not dash (curved arcs can't dash);
  journeys *do* dash their legs.
- The corpus has **no reliable relational/itinerary data**, so journeys and networks
  are necessarily **curated** layers, authored by hand with provenance.

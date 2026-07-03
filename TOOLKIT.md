# The Developers Toolkit

Technical reference for the MAPRESEARCH map toolkit — everything a developer
needs to build, extend, test, and embed the maps. The companion document for
*authors and readers* is [MANUAL.md](MANUAL.md); the browsable overview of all
built maps is the gallery (`gallery/index.html`).

---

## 1. Architecture

```
directive (natural language)
   │  Claude Code skill (/buildmap, /journey, /network)
   ▼
MapSpec / journey JSON / networks JSON        ← the CONTRACT (validated)
   │  Python generator (deterministic)
   ▼
self-contained HTML (MapLibre GL + deck.gl)   ← the ARTIFACT
   │  URL params + postMessage
   ▼
embedding surfaces (tour, gallery, any page)
```

Three principles hold everywhere:

1. **The contract is the unit of control.** Nothing renders that isn't in a
   versionable JSON spec. Change a word, get a different map, reproducibly.
2. **Provenance or it doesn't compile.** Every engine validates its input and
   refuses unsourced content (`--allow-unsourced` for drafts only).
3. **Artifacts are self-contained.** One HTML file per map, data embedded,
   no build step, no server-side anything. (CDN libs are the one exception —
   see §10.)

## 2. Repository layout

| Path | What |
|------|------|
| `scripts/` | All engines and tooling (below) |
| `specs/mapspec.schema.json` | The MapSpec JSON-Schema |
| `specs/examples/` | Hand-authored specs |
| `specs/generated/` | Specs authored by `build_all.py` (eras, centuries) |
| `specs/showcase/` | Specs authored by `build_showcase.py` (themes, figures, regions) |
| `data/journey-*.json` | Curated biographical journeys |
| `data/networks.json` | Curated network subjects (one file, many subjects) |
| `data/boundaries/` | Slimmed historical border GeoJSON by year |
| `prototypes/` | Generated map HTML |
| `gallery/` | Generated gallery site (index, per-map pages, docs) |
| `tour/` | The scrollytelling tour |

## 3. The MapSpec contract

Schema: `specs/mapspec.schema.json`. Shape:

```json
{
  "title": "…", "subtitle": "…",
  "directive": "the original natural-language request",
  "scope": {
    "year_start": 1490, "year_end": 1610,
    "era": ["RENAISSANCE"],
    "regions": ["Bohemia"], "region_bbox": [5, 45.5, 19, 54],
    "themes": ["paracelsian-alchemy"], "persons": [], "texts": [],
    "review_status": []
  },
  "render": {
    "engine": "maplibre",
    "basemap": { "style": "atlas", "show_modern_labels": false,
                 "historical_boundaries_year": 1560 },
    "layers": ["points", "flows", "time-animation", "labels"],
    "color_by": "theme"
  },
  "narrative": { "intro": "…", "provenance_note": "REQUIRED" }
}
```

Rules enforced by `build_map.py` (see `validate_spec()`):

- `title`, `scope`, `render`, and `narrative.provenance_note` are required.
- Enums checked: `era`, `layers`, `color_by`, `basemap.style`.
- `basemap.style` sets the map's **initial runtime theme**: `atlas`,
  `copperplate`, `illuminated`, `noir` (legacy aliases: `parchment`→illuminated,
  `sepia-toner`→copperplate, `muted-vector`/`modern-osm`→atlas).
- `historical_boundaries_year` embeds period borders from the **nearest cached
  year** in `data/boundaries/` and adds an automatic caveat to the panel.
- Inverted `year_start`/`year_end` and malformed/inverted `region_bbox` are errors.
- Unknown keys warn (forward compatibility) but don't fail.
- Post-compile, the engine warns when a requested theme matches 0 events and
  when events reference ungeocoded locations.

## 4. Engines & CLI reference

All engines are dependency-free Python 3 (stdlib only). Run from `scripts/`.

### build_map.py — the MapSpec compiler
```
python build_map.py <spec.mapspec.json> [--data <data.json>] [--out <out.html>] [--allow-unsourced]
```
Validates, compiles (filter/join/aggregate), emits self-contained HTML into
`prototypes/<spec-stem>.html`. Key internals: `validate_spec(spec)`,
`check_provenance(spec)`, `compile_spec(spec, data)`, `emit_html(compiled)` —
importable, which is how the batch builders and tests use them.

### build_all.py — eras + centuries batch
Authors 6 era + 11 century specs to `specs/generated/`, builds each, and writes
`tour/manifest.json` for the scrollytelling tour.

### build_showcase.py — themes + figures + regions batch
Authors the 21 showcase specs (7 theme, 8 figure, 6 region) to
`specs/showcase/` and builds each. Slugs and counts were chosen against
`list_vocab.py` output so no map compiles empty.

### build_scholarship.py — the scholarship shelf
Authors one map per most-cited study in the collection (citation counts mined
from scholar-surname mentions across the 680 events' texts). Each spec scopes
the corpus to the study's key topics/figures, wears a deliberately different
style, and carries a `design_note` explaining the choice. Specs to
`specs/scholarship/`.

### build_journey.py — the biographical journey template
```
python build_journey.py ../data/journey-<person>.json [--out …] [--allow-unsourced]
```
Validates each stop (`place/lat/lon/year_start/what/evidence/source` required;
evidence ∈ attested|inferred|approximate; stops must be year-ordered) and
emits the self-drawing, ending-withholding journey map.

### build_network.py — the network/patronage template
```
python build_network.py [--data ../data/networks.json] [--out …] [--allow-unsourced]
```
Validates every subject (unique node ids; edges resolve to nodes; edges carry
`type/evidence/note/survives`) and emits ONE explorer for all subjects
(`?subject=<slug>` deep-links).

### fetch_basegeo.py — the physical geography cache
```
python fetch_basegeo.py
```
Downloads Natural Earth land / lakes / major rivers (public domain), clips to
the project window (Sutherland–Hodgman for polygons, Liang–Barsky for lines),
simplifies, and writes ~700 KB total to `data/basegeo/`. Every map embeds these
three layers and draws them itself — sea-coloured canvas, themed land fill,
coastline stroke, lakes, rivers — so there is **no CDN basemap dependency**.
Run once; the compilers warn if the cache is missing.

### fetch_boundaries.py — the period-borders cache
```
python fetch_boundaries.py [year …]
```
Downloads `world_<year>.geojson` from aourednik/historical-basemaps, clips to
the project window, Douglas-Peucker-simplifies, rounds coordinates, keeps only
`NAME`, and writes ~75–145 KB files to `data/boundaries/`. Run once per new
year needed; the compiler snaps requests to the nearest cached year.

### list_vocab.py — the authoring vocabulary
Prints every concept/person/region slug **with its event count** plus schema
enums. Zero-count slugs are flagged. Always consult before authoring a spec.

### build_gallery.py — the gallery site
Scans all specs + curated data, compiles each map's data for an SVG preview,
and emits `gallery/index.html`, one `gallery/<slug>.html` detail page per map,
and HTML versions of TOOLKIT.md / MANUAL.md. Re-run after adding any map.

### test_smoke.py — the regression net
Dependency-free suite; see §9.

## 5. Data formats (curated layers)

### Journey JSON (`data/journey-*.json`)
```json
{ "title": "…", "subtitle": "…", "subject": "person-slug", "theme": "noir",
  "provenance_note": "REQUIRED — biographies used, what is reconstructed",
  "stops": [
    { "order": 1, "place": "Basel", "lat": 47.5596, "lon": 7.5886,
      "year_start": 1527, "year_end": 1528, "dwell": 1,
      "what": "1–3 sentences of story for the panel.",
      "evidence": "attested",          // this stop
      "leg_evidence": "inferred",      // the travel TO this stop (null for first)
      "source": "Webster 2008, ch.2" }
  ] }
```
`dwell` scales node size; `leg_evidence: inferred|approximate` renders dashed.

### Network JSON (`data/networks.json`)
One file, `subjects[]`. Each subject: `slug`, `title`, `subtitle`, `theme`,
`provenance_note`, `nodes[]` (`id`, `label`, `slug` (person page link or null),
`lat`, `lon`, `role`, `year`), `edges[]`:
```json
{ "source": "id", "target": "id", "type": "patron-of",
  "direction": true, "weight": 3, "evidence": "attested",
  "survives": true, "note": "citation / claim (REQUIRED)" }
```
Edge types with assigned colours: patron-of, collaborated, cited, collected,
corresponded, influenced, polemicized-against, taught, studied-under.
`survives` drives the survival-bias toggle — set it honestly.

### Boundary cache (`data/boundaries/world_<year>.geojson`)
FeatureCollection with `year` and `attribution` top-level keys; features carry
only `NAME`. Approximate by nature — every map that shows them says so.

## 6. Runtime APIs (every emitted map)

### URL parameters
| Param | Maps | Meaning |
|-------|------|---------|
| `ui=min` | all | hide chrome (embedding) |
| `theme=` | all | atlas · copperplate · illuminated · noir |
| `year=` | data | time-scrubber position |
| `lens=` | data | transmission · lives · texts · themes · density |
| `color=` | data | theme · region · era |
| `layers=` | data | dot-separated: `points.arcs.borders` |
| `arcw=` `pts=` `op=` | data | slider values (arc width, point scale, opacity) |
| `subject=` | network | subject slug |
| `survive=1` | network | survival toggle on |
| `mode=` | journey | lay · understated · scholar · centerpiece |

### postMessage (embedding)
Send to the iframe: `{type:"mapctl", theme, lens, year, colorBy}` ·
`{type:"journeyctl", goto, mode, theme, play}` ·
`{type:"netctl", subject, theme, survive, select}`.

### Debug globals
Every map exposes `window._map` (MapLibre), `window._overlay` (deck.gl
overlay), `window._STATE` (live state object) for console inspection and tests.

## 7. The theme engine

Six themes: **atlas** (Modern Atlas), **copperplate** (Copperplate Engraving),
**illuminated** (Illuminated Manuscript), **noir** (Alchemical Noir),
**woodcut** (Woodcut & Rubric — stark black line + vermillion on cream), and
**lapis** (Lapis & Gold — ultramarine field + gilt). Themes are token objects
in the emitted JS (`THEMES` in the template): page, ink, muted, panel,
panel-border, accent, chip, fonts, water/land/border basemap colours, and a
10-colour categorical palette. To add a theme: add one entry to `THEMES` in
`build_map.py`'s template (and the option to the theme `<select>`), plus the
alias in `STYLE_TO_THEME` so specs can request it, and a matching entry in
`build_gallery.py`'s `PALETTE`/`THEME_LABEL`/`WATER` so previews and badges
follow. Colour is assigned at runtime, so new themes re-skin existing maps
without recompiling their data.

House rule (see the memory note and `narrative.design_note`): batch builders
assign each map an *initial* style deliberately — the fleet doubles as a design
showcase — and the gallery surfaces the rationale on every map page.

## 8. Extending

**A new layer** (data maps): add a deck.gl layer constructor in `makeLayers()`,
a key in `STATE.layers`, and (optionally) a chip in `buildControls()` — follow
the `borders` layer as the worked example (conditional on data presence).

**A new map type**: copy the closest engine (journey is the smallest), keep the
three invariants — validated contract in, self-contained HTML out, provenance
enforced — and give it a `?ui=min` mode plus a postMessage handler so the tour
and gallery can drive it.

**A new dataset**: currently hard-coupled to ALCHEMYTIMELINEMAP's `data.json`
(`--data` flag notwithstanding, field names are assumed). The adapter design is
NEXTSTEPS.md Tier 1 §2 — read that before attempting.

## 9. Testing & QA

```
python scripts/test_smoke.py
```
Every spec on disk must: validate, carry provenance, compile to >0 events,
emit HTML with no unreplaced tokens and with the export/permalink/reduced-motion
machinery present, and (if it requests borders) embed them. Plus: the validator
must reject a deliberately bad spec; the boundary cache must exist, parse, and
stay under 300 KB/file; journey and network data must pass their evidence rules;
the tour manifest and gallery must agree with the prototypes on disk.

The suite is structural — WebGL rendering is verified manually in a browser
(the sandbox cannot screenshot WebGL; see NEXTSTEPS.md §7 for the visual-QA plan).

## 10. Dependencies & archival caveats

Runtime (CDN, pinned): MapLibre GL 4.7.1 and deck.gl 9.0.33 JS, plus Google
Fonts. The basemap itself is **fully embedded** (Natural Earth geography +
historical borders live inside each HTML file), so an offline map still shows
land, sea, lakes, rivers, and borders — but the JS libraries still need
vendoring for true archival use (NEXTSTEPS.md Tier 2 §4). Build-time: Python 3
stdlib only — nothing to install.

Historical boundaries are from aourednik/historical-basemaps (approximate
scholarly reconstructions); physical geography is Natural Earth (public
domain). Attribution is embedded in every cache file and every map.

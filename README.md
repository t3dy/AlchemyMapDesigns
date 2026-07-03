# MAPRESEARCH

**🌍 Live site: <https://t3dy.github.io/AlchemyMapDesigns/>** — the Map Gallery:
all 57 maps with preview cards, style badges, design notes, relational browsing
by era / topic / figure / region, the guided tour, and the full documentation
(Instruction Manual · Developers Toolkit).

A focused R&D project to fix the map problem for **ALCHEMYTIMELINEMAP**.

Goal: a map a builder can *direct from the command line* — "build me a map of
Paracelsian alchemy in Central Europe before the Rosicrucians" — and get back a
scholarly, period-appropriate, focused interactive map. Not "all 62 dots, filter
yourself."

## Why this exists

The current map (`../ALCHEMYTIMELINEMAP/site/assets/map.js`) is a generic Leaflet
dot-map on a modern OpenStreetMap basemap. It has three problems:

1. **Anachronistic basemap** — modern borders/roads/labels under ancient/early-modern events.
2. **Underuses the data** — 602 geocoded events linked to persons/texts/concepts,
   but only static dots are shown. No flows, no time, no networks.
3. **No authoring control** — can't ask for a focused view; you get everything.

## The core idea: the **MapSpec compiler**

The unit of "control" is a **MapSpec** — a small JSON contract that sits between
fuzzy natural language and deterministic rendering.

```
"Paracelsian alchemy in Central Europe          MapSpec               self-contained
 before the Rosicrucians"          ──Claude──▶  (JSON)   ──generator──▶  map.html
       (you type this)                          (the contract)          (the artifact)
```

- You type a directive in Claude Code.
- Claude translates it into a `*.mapspec.json` (region bbox, year range, theme =
  concept slugs, persons, basemap style, which layers to draw).
- A Python generator reads the alchemy `data.json`, filters/joins, and emits a
  standalone HTML map styled to spec.

The MapSpec is the whole game: it makes vague intent *reproducible* and *editable*.

See `specs/mapspec.schema.json` for the contract and
`specs/examples/paracelsian-before-rosicrucians.mapspec.json` for the worked
version of your exact example.

## Layout

| Path | Purpose |
|------|---------|
| `gallery/` | **Start here in a browser** — all 50 maps as cards, with idea notes |
| `TOOLKIT.md` | Developers Toolkit: contracts, engines, APIs, extending |
| `MANUAL.md` | Instruction Manual: directing, reading, and sharing the maps |
| `CAPABILITIES.md` | Tour of the tools available to build this |
| `NEWFEATURES.md` | Showcase of everything the toolkit now does |
| `AUDIT.md` | Unsparing progress audit against the module vision |
| `NEXTSTEPS.md` | The worked forward plan |
| `specs/mapspec.schema.json` | The MapSpec contract |
| `specs/examples/` | Worked MapSpecs, including your Paracelsian one |
| `scripts/` | Engines: `build_map/journey/network/all`, `fetch_boundaries`, `list_vocab`, `test_smoke` |
| `prototypes/` | Generated maps (6 eras, 11 centuries, journey, network, example) |
| `data/` | Curated layers + `boundaries/` (cached period borders by year) |
| `research/` | Notes on historical basemaps, projections, sources |

Provenance is enforced: a MapSpec without `narrative.provenance_note` does not
compile. Run `python scripts/test_smoke.py` before trusting a refactor.

## Data source

Reads from `../ALCHEMYTIMELINEMAP/site/data/data.json` (and the SQLite DB).
This project does **not** own the content — it owns the *rendering and authoring*.

---
name: buildmap
description: Turn a natural-language map directive (region + era + theme, e.g. "Paracelsian alchemy in Central Europe before the Rosicrucians") into a validated MapSpec and render it as a MapLibre + deck.gl map. Use when the user wants to build, generate, or focus an alchemy map.
---

# buildmap — the MapSpec compiler

You are compiling a builder's directive into a **MapSpec** and rendering it. The
MapSpec is the contract; the renderer is deterministic. Follow this loop exactly.

## Inputs
- The directive is in `$ARGUMENTS` (e.g. "Paracelsian alchemy in Central Europe
  before the Rosicrucians"). If empty, ask the user for one sentence: region + era + theme.

## Step 1 — Read the contract and the data vocabulary
- Read `specs/mapspec.schema.json` (the MapSpec shape).
- Read the available slugs from the data so every reference RESOLVES (project
  Invariant #4). Run:
  ```
  python scripts/list_vocab.py
  ```
  This prints valid concept slugs, person slugs, region names, and the year range —
  each with the count of events that actually carry it. Map the directive's fuzzy
  terms to REAL slugs. Never invent a slug, and prefer slugs with non-zero counts:
  a zero-count theme compiles but contributes nothing (the compiler will warn).

## Step 2 — Compose the MapSpec
Translate the directive into a spec object:
- **Time**: convert era language to `year_start`/`year_end`. Watch for "before X"
  / "after X" cutoffs (e.g. "before the Rosicrucians" = end at ~1610, eve of the
  1614 Fama Fraternitatis). State the cutoff logic in `narrative.provenance_note`.
- **Place**: map region words to `regions` (named) and/or a `region_bbox`
  [west, south, east, north] for the viewport.
- **Theme**: map to `themes` (concept slugs). Include closely-related concepts that
  exist in the vocab, in priority order (first match drives the point's colour).
- **persons/texts**: only as HARD filters if the directive restricts to them.
  Person itineraries are drawn as transmission arcs automatically — you do NOT
  need to list persons to get their movement lines.
- **review_status**: only filter if the user asks for vetted content. NOTE: much of
  the data is DRAFT; filtering to REVIEWED+ may empty the map. If you filter, say so.
- **render**: default `engine: maplibre`, `basemap.style: parchment` (= the
  illuminated theme; also valid: atlas, copperplate, noir — this sets the map's
  initial look), `basemap.show_modern_labels: false`,
  `layers: [points, flows, time-animation, labels]`, `color_by: theme`.
  Set `basemap.historical_boundaries_year` to a representative mid-point year of
  the scope — the compiler embeds period political borders from the nearest cached
  year in `data/boundaries/` (a toggleable "Borders" layer with an automatic
  provenance caveat). If the compiler warns that no boundary cache exists, run
  `python scripts/fetch_boundaries.py` once.
- **narrative.intro**: 2-3 sentences of scholarly framing. Honor the actor/analyst
  distinction (Invariant #3). No endorsement of transmutation (Invariant #2).
- **narrative.provenance_note is REQUIRED** — the compiler refuses to build without
  it. Say where the map's claims come from, what the cutoffs mean, and what the map
  does NOT show. (`--allow-unsourced` exists for throwaway drafts only; never use it
  for a map you hand to the user.)
- Always fill `directive` with the original request (provenance).

Write the spec to `specs/<kebab-title>.mapspec.json`.

## Step 3 — Render
```
python scripts/build_map.py specs/<kebab-title>.mapspec.json
```
Read the printed stats: `events / locations / arcs`. If `events` is 0 or tiny, the
scope is too narrow — loosen a filter (often review_status or an over-specific
theme) and rebuild. If it warns about ungeocoded location slugs, report them; they
are content gaps to fill later, not failures.

## Step 4 — Report
Tell the user: the title, the event/location/arc counts, any cutoff logic you
applied, the output path (`prototypes/<name>.html`), and the local URL if a
preview server is running (`python -m http.server 8777` from the project root, then
`/prototypes/<name>.html`). Surface any ungeocoded slugs as the next data task.

## Guardrails
- Every slug in the spec must exist in the vocab from Step 1.
- Enum values (era, basemap.style, layers, color_by) must match the schema exactly.
- Prefer loosening scope over shipping an empty map; never silently return nothing.

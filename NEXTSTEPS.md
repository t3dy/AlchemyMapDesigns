# NEXTSTEPS — moving the map toolkit from application to module

Written at the close of the Fable review sprint (July 2026), which checked the
work recorded in `NEWFEATURES.md` against the vision in `AUDIT.md` and shipped
ten improvements (list at the bottom). This file is the forward plan: what to do
next, in what order, and why.

**Where we stand in one sentence:** the *rendering and honesty craft* is now
largely done and defended by tests; the two things gating the vision are the
**data underneath** and **decoupling from ALCHEMYTIMELINEMAP** — both unglamorous,
both now unmistakably the critical path.

---

## Tier 1 — the critical path (do these before more features)

### 1. Corpus theme re-tagging (the load-bearing data fix)
The Themes lens is still mostly empty because events carry process labels
(`distillation` 237) while conceptual themes go unused (`iatrochemistry` 2 —
the compiler now *warns* about this at build time, but warning ≠ fixed).

- Run a verifier-gated agent sweep over the 602 events in the ALCHEMYTIMELINEMAP
  DB: propose 1–3 conceptual theme tags per event, **each with a source line**,
  then a second-pass verifier accepts/rejects. Reject unsourced tags outright —
  same rule the map engines now enforce.
- Acceptance test: `python scripts/list_vocab.py` shows the top ~15 conceptual
  themes with ≥20 events each; the Paracelsian example map stops warning.
- This unlocks: honest theme maps, meaningful `color_by: theme`, and the
  `/buildmap` skill working as designed for theme-led directives.

### 2. Decouple into a module (the stated vision)
Everything reads a hard-coded path into `../ALCHEMYTIMELINEMAP/site/data/data.json`
and assumes its field names. To be a DH *module*:

- **Data adapter**: a small `project.config.json` per dataset mapping the
  engine's expected fields (`events[].date_start_year`, `location_slug`,
  `concepts_involved`, …) onto whatever the host dataset calls them, plus
  entity file paths. The engines read *only* through the adapter.
- Move `FALLBACK_LOCATIONS`, `LOCATION_ALIASES`, `ERA_RANGES` out of
  `build_map.py` into that config (they are alchemy-project data, not engine
  code).
- Acceptance test: point the adapter at a *second* dataset (even a toy one — a
  dozen PKD-site events, or an EmblemRoguelike gazetteer) and get a working map
  with zero engine edits. That's the moment it's a module, not an app.
- Then: package `scripts/` as an installable (`pip install dh-mapkit` shape),
  with `data/boundaries/` as a fetchable resource.

### 3. Prove the skills at scale — ✅ largely done (gallery sprint, July 2026)
The authoring loop has now been stress-tested at scale: 21 new data maps
(themes/figures/regions via `build_showcase.py`), the Paracelsus and Dee
journeys, and the Hartlib-circle and Ficino-circle networks all authored
against the enforcement machinery — vocab counts steered slug choices, and no
map shipped empty or unsourced. What remains of this item: run the *skills
themselves* cold (`/buildmap` etc. driven conversationally rather than by batch
script) on a handful of directives, since the batch path exercises the engines
but not the natural-language translation step.

---

## Tier 2 — high-value, now cheap (foundations exist)

### 4. Vendor the CDN dependencies (archival integrity)
Maps die when unpkg does. Add `scripts/vendor_libs.py` to download pinned
MapLibre/deck.gl/fonts into `vendor/`, and a `--offline` flag on the three
builders that rewrites the `<script>`/`<link>` tags to relative paths. A DH
artifact should still open in ten years. (~half a day; do it before sharing
maps outside the project.)

### 5. Port accessibility to journey + network templates
Data maps now honour `prefers-reduced-motion`, carry ARIA roles, and have
keyboard-operable chips. The journey autoplay (a pure animation) and the network
click-to-pivot need the same treatment — reduced-motion should turn the journey
into stepped storytelling (the Next ▸ button already exists), and pivot needs a
keyboard path. Reuse the exact patterns just added to `build_map.py`.

### 6. Extend the boundary cache thoughtfully
- Add pre-100 CE years (the Greco-Egyptian era starts at 100; `world_bc1` etc.
  exist upstream) and any council-relevant years a directive asks for.
- Consider a "borders drift" affordance: on century maps, the time scrubber
  could swap the embedded boundary year at era breakpoints. Do this only if a
  real map needs it — it doubles embedded size per extra year.
- Keep the caveat language exactly as is: approximate, orientation-only.

### 7. Visual QA outside the sandbox
The 23-check smoke suite is structural; nobody has verified pixels
automatically. On a machine with working WebGL screenshots: a small Playwright
script that opens each prototype, waits for `map.loaded()`, screenshots, and
diffs against goldens. Store goldens per theme. (The sandbox limitation is
environmental — this needs a real browser run, so it may be a manual-trigger
script rather than CI.)

---

## Tier 3 — polish and reach (after the module exists)

8. **PDF/SVG export** — PNG with provenance strip exists; scholars will want
   vector for print. deck.gl doesn't do SVG; the honest path is a high-DPI PNG
   (render at 2–3× and downscale) plus a separate typeset caption block.
9. **Saved views / annotations** — the permalink now captures full view state;
   a "named views" panel (localStorage + exportable JSON) would let an author
   script a lecture from one map.
10. **Historical gazetteer** — period place names (Byzantion → Constantinople)
    keyed by year, as a `labels` layer variant; Pleiades/GeoNames-historical as
    sources. Pairs naturally with the borders layer.
11. **Tour chapter for the borders layer** — the scrollytelling tour predates
    period borders; add a chapter showing the same map with modern-vs-1530
    borders (the postMessage API can already drive the toggle: add `layers` to
    the `mapctl` handler if needed).
12. **Edge-enrichment pipeline** — longer term: mine the corpus texts/letters
    for candidate person-person edges, emitted as *suggestions* into a review
    queue, never directly onto maps. The curated-with-provenance rule stays.

---

## Standing rules (unchanged, now partially machine-enforced)

- Provenance-or-it-doesn't-compile — **enforced** in all three engines.
- Evidence → line style; confidence → opacity; category → colour; never
  colour-for-confidence.
- Journeys and networks are curated layers with sources, not corpus dumps.
- Every map says what it does *not* show.
- Run `python scripts/test_smoke.py` after touching any engine; keep it green.

---

## Appendix C — display-correctness sweep (July 2026, third pass)

A dedicated bug hunt through every emitted map, prompted by "make sure
everything is displaying properly." Two real, confirmed-in-browser bugs found
and fixed, both now locked in by smoke-test assertions:

1. **Mobile layout was fully broken.** The data-map template's info panel and
   control drawer are two independently absolutely-positioned corner boxes
   with fixed pixel widths (330px + 268px) and no responsive breakpoint —
   verified in-browser to fully overlap on any viewport under ~625px wide
   (i.e., every phone). A missing `box-sizing:border-box` reset compounded it,
   making padding inflate elements past their declared `max-width`/`max-height`.
   The journey template had the same problem across four corner boxes
   (`#ctl`/`.legend`/`#doubt`/`#story`). Fixed with a `@media (max-width:760px)`
   breakpoint that stacks each vh-capped and independently scrollable, plus the
   missing box-sizing reset. Network's explorer already had a `max-width:86vw`
   clamp and needed no fix. Verified overlap-free at 320/375/400px widths.
2. **Diacritics were silently dropped from map labels.** deck.gl 9.0.33's
   TextLayer ignores `characterSet:"auto"` (which the fix's first attempt used)
   and falls back to a plain-ASCII glyph set, so "Córdoba", "Kraków", and
   "Třeboň" rendered with missing/blank characters in their on-map labels
   (story-panel and tooltip text, which are plain HTML, were unaffected).
   Fixed with an explicit ASCII + Latin-1 Supplement + Latin Extended-A/B
   character range across all three templates.

Also removed a harmless dead reference (`t.accentRGB`, never defined in any
theme, always fell through to the correct fallback) found in passing.

**Method note:** this pass's key lesson was that `preview_resize` +
`location.href` navigation doesn't reliably re-evaluate CSS media queries in
this tool — always `preview_resize` *then* `location.reload(true)` before
reading computed styles, or measurements reflect the previous viewport. The
`preview_console_logs` buffer also accumulates/duplicates rather than
reporting fresh-since-last-check; a single test `console.warn()` reappeared
4×, so a stale warning is not evidence of a live bug — restart the preview
server for a clean read when a warning's provenance is in doubt. Screenshots
still time out (confirmed root cause this pass: the preview tab reports
`document.hidden === true`, which pauses requestAnimationFrame — the same
reason a live PNG-export click didn't complete in-sandbox; the code path
itself checked out correct on inspection, and a normal visible browser tab
is unaffected).

---

## Appendix B — what the gallery sprint shipped (July 2026, second pass)

1. **25 new maps** (43 prototypes total): 7 theme maps, 8 figure maps, 6 region
   maps (`scripts/build_showcase.py`, specs in `specs/showcase/`), 2 new curated
   journeys (Paracelsus after Webster/Ball/Pagel; John Dee after Parry/French),
   and 2 new network constellations (the Hartlib Circle after the Hartlib
   Papers and Newman & Principe; the Florentine Academy after Hankins and
   Copenhaver) — every one borders-enabled, sourced, and validation-clean.
2. **The Map Gallery** (`gallery/`, generated by `scripts/build_gallery.py`):
   48 preview cards in eight families, each with a deterministic SVG preview
   drawn from the map's own compiled data; 48 per-map pages with the live
   embedded map, stats, provenance, recipe link, and accordion notes; a shared
   registry of 16 "ideas we're trying" wired to families and pages.
3. **TOOLKIT.md** (Developers Toolkit) and **MANUAL.md** (Instruction Manual),
   also served as HTML inside the gallery via a built-in markdown renderer.
4. **Test suite grown to 47 checks** — now covers all journeys, the new specs
   automatically, and gallery completeness (every map must have a card and page).
5. Verified in a live browser session: gallery DOM, docs rendering, and an
   embedded map initializing inside a gallery page (state, lenses, borders,
   export button all live).
5b. *(variety pass)* **Visual variety as policy.** Two new themes (Woodcut &
   Rubric; Lapis & Gold → six total); every generated map now *opens* in a
   deliberately assigned style with a `narrative.design_note` explaining how the
   aesthetic serves the material (era maps: one style each; centuries: rotating
   wardrobe; showcase/figures/regions: hand-assigned; distribution 8–12 maps per
   style). The gallery shows a style badge on every card, a Design-&-Tools block
   on every page (which deck.gl layers, borders year, interactions), a six-swatch
   strip in the hero, and two new idea accordions (style-as-argument,
   scholarship-maps). Plus **the Scholarship Shelf**: 7 maps keyed to the
   collection's most-cited studies (mined from scholar-surname mentions across
   events: Principe 90 · Newman 60 · Smith 21 · Hanegraaff 19 · Fowden 15 ·
   Copenhaver 13 · Pereira 8), incl. the requested *Laboratories of Art* /
   Pamela Smith artisanal-culture map. 57 maps, 58 checks green. Preference
   recorded in memory (demo-visual-variety).
6. *(basemap pass)* **"I want it to look like a map" — fixed.** All 44
   prototypes now embed real physical geography (Natural Earth land, lakes,
   major rivers via `scripts/fetch_basegeo.py`: window-clipped, simplified,
   ~700 KB) drawn as themed deck.gl layers over a sea-coloured canvas, with
   place labels on by default. The demotiles CDN basemap — flat, featureless,
   and a single point of failure — is **gone entirely**; the smoke suite now
   fails if it, or a geography-less map, ever comes back. Gallery preview cards
   gained the same land silhouettes. Remaining basemap gap (recorded in
   AUDIT.md): the geography is modern, and there is no historical gazetteer.
7. *(continuation pass)* Two cold-run directed maps — **Women in the Art**
   (sparsity-as-argument: 8 events, 5 women, the gendered survival of evidence)
   and **The Byzantine Bridge** (Byzantium as the tradition's cold storage) —
   exercising the hand-authored spec path end-to-end, which surfaced and fixed
   a real bug (gallery iframes 404'd for `*.mapspec.html`-named prototypes; the
   smoke suite now asserts every gallery iframe target exists). Gallery gained
   a sticky family jump-nav, "Read more" links from every idea accordion into
   anchored Toolkit/Manual sections, and an HTML NEXTSTEPS page; the tour now
   links to the gallery at top and close, and its stale "period boundaries =
   future work" claim is corrected. 50 maps, 49 checks green.

## Appendix A — what the Fable review sprint shipped (July 2026)

1. **Period political borders, wired end-to-end** — `scripts/fetch_boundaries.py`
   downloads and slims historical-basemaps GeoJSON (Douglas-Peucker + precision
   rounding + window clip; 24 years cached, 100–1800 CE, ~75–145 KB each);
   `historical_boundaries_year` now embeds the nearest cached year as a
   toggleable, hoverable "Borders" layer with an automatic provenance caveat.
   All 17 generated maps + the example carry period borders.
2. **Provenance enforcement** — missing `narrative.provenance_note` fails the
   build (`build_map.py`, `build_all.py`); unsourced journey stops and untyped/
   unevidenced network edges fail theirs (`validate_journey`, `validate_network`).
   `--allow-unsourced` escape hatch for drafts, loudly labelled.
3. **MapSpec validation** — dependency-free `validate_spec()`: enum checks,
   inverted year/bbox detection, unknown-key warnings; exercised by tests.
4. **Spec-driven appearance** — `render.basemap.style` (now incl. atlas/
   copperplate/illuminated/noir; legacy names aliased) sets the initial theme,
   `show_modern_labels` the label state. Previously dead schema fields.
5. **PNG export** — one click, current view, title + "through year" + borders
   caveat burnt into a provenance strip at the foot.
6. **Deep-state permalinks** — 🔗 button copies a URL reproducing theme, lens or
   custom layer set, colour-by, year, and slider values; all params parsed on load.
7. **Accessibility (data maps)** — `prefers-reduced-motion` turns Play into
   discrete stepping; ARIA labels/roles/live regions; keyboard-operable chips.
8. **Compile-time data warnings** — zero-match themes and ungeocoded locations
   reported at build; `list_vocab.py` prints per-slug event counts.
9. **Smoke-test suite** — `scripts/test_smoke.py`: 23 checks over specs,
   compilation, emitted HTML, boundary cache, curated-data rules, tour manifest.
10. **Docs + skill brought true** — schema, README, NEWFEATURES, AUDIT scorecard,
    and the `/buildmap` skill updated to match reality (including the
    `rosicrokians` filename typo and stale stats).

# AUDIT — progress toward an interactive map module for digital humanities

**The vision (as stated):** a reusable, interactive map *module* for digital-humanities
projects — one a builder can direct from the command line to map any region, any era,
any theme, any figure's travels, or any network of people, in a scholarly and
honest way.

**This audit is deliberately unsparing.** The features doc (`NEWFEATURES.md`) shows
what works; this one says how far it is from the vision and what's load-bearing vs.
still missing. Date of audit: end of the current build sprint.

---

## Scorecard

| Dimension | Status | One-line verdict |
|-----------|:------:|------------------|
| Directability (describe → map) | 🟢 Strong | MapSpec compiler + 3 skills work end-to-end; specs now validated |
| Visual quality / aesthetics | 🟢 Strong | 6 runtime themes, real terrain colour + shaded relief (not flat fills), GPU layers |
| Map-type coverage | 🟢 Good | Data, journey, and network templates all built |
| User controls | 🟢 Good | Lenses + filter bar + advanced drawer + time |
| Scholarly honesty apparatus | 🟢 Good | Encodings built AND enforced: provenance-or-it-doesn't-compile, all 3 engines |
| Provenance integrity | 🟡 Partial | Curated layers sourced + validated; corpus tagging is still weak |
| **Data foundation** | 🔴 Weak | No reliable relational/itinerary/theme data (now *visible* via vocab counts + compile warnings, but not fixed) |
| Period-accurate cartography | 🟡 Partial | Period borders wired (24 cached years); real coastlines/lakes/rivers now embedded (Natural Earth, no CDN basemap) — but the physical geography is modern, and no historical gazetteer |
| Reusability as a *module* | 🔴 Weak | Hard-coupled to one project's `data.json` |
| Authoring at scale (skills tested) | 🟡 Unproven | Skills written; only hand-run examples exist |
| Accessibility | 🟡 Partial | Data maps: reduced-motion, ARIA, keyboard chips; journey/network templates not yet |
| Persistence / export / sharing | 🟡 Partial | PNG export with provenance strip + full deep-state permalinks; no PDF/SVG/saved views |
| Verification / QA | 🟡 Partial | `test_smoke.py` (23 checks: specs, compile, data rules, manifest); still no screenshot/visual QA |

🟢 solid · 🟡 partial · 🔴 weak/missing

---

## What is solidly built (the wins)

1. **The compiler pattern works.** A JSON recipe → a finished, self-contained,
   reproducible interactive map is real and proven across 20 generated maps.
2. **Three map archetypes exist**, not one: data maps (era/century), biographical
   journey, and scholarly-network/patronage — each a template with locked, defensible
   defaults.
3. **The theme engine is genuinely good** — four complete aesthetics, switchable live,
   re-skinning basemap + palette + type.
4. **The control philosophy landed** — lenses for newcomers, filters for regulars, an
   advanced drawer for power users.
5. **Honesty has a vocabulary** — evidence→line-style, confidence→opacity,
   category→colour; the survival-bias toggle; "what this map does NOT show."
6. **It teaches** — the 9-chapter scrollytelling tour explains itself to laymen.

---

## Closed since the last audit (the Fable review sprint)

- **Honesty is now mandatory.** A MapSpec without `narrative.provenance_note` is a
  build error in `build_map.py` and `build_all.py`; journey stops without
  evidence+source, and network edges without type/evidence/note/survives, likewise
  refuse to build. `--allow-unsourced` exists for drafts and announces itself.
- **Period political borders are wired.** `historical_boundaries_year` — previously
  a schema field nothing read — now embeds slimmed *historical-basemaps* polygons
  (24 cached years, 100–1800 CE, ~75–145 KB each via `fetch_boundaries.py`) as a
  toggleable, hoverable layer with an automatic "approximate" caveat.
- **Specs are validated** (bad enums, inverted years/bboxes, unknown keys), and
  `render.basemap.style` / `show_modern_labels` now actually drive the map's
  initial appearance instead of being dead schema fields.
- **Export + sharing exist**: PNG export with a burnt-in provenance strip, and
  permalinks that serialize the full view state (theme/lens/layers/year/sliders).
- **A regression net exists**: `scripts/test_smoke.py`, 23 dependency-free checks.
- **Accessibility on data maps**: `prefers-reduced-motion` honoured, ARIA
  labels/roles, keyboard-operable layer chips.
- **The data gap is visible at authoring time**: `list_vocab.py` prints event
  counts per slug; the compiler warns on zero-match themes.

---

## What is partial

- **Skills are written but unproven at scale.** `/buildmap`, `/journey`, `/network`
  exist and the hand-built examples render, but no one has run them cold on a dozen
  new subjects to see where the authoring breaks.
- **Accessibility on journey/network templates.** The data-map treatments
  (reduced motion, ARIA, keyboard) haven't been ported to the other two engines.
- **One stylistic compromise:** inferred network ties show by opacity, not dash
  (curved arcs can't carry a dash array). Journeys do dash. Minor, documented.

---

## What is not started

- **Period base geography.** Maps now draw real coastlines, lakes, and rivers
  from embedded Natural Earth data (the demotiles CDN basemap is gone entirely),
  but that geography is *modern* — no silted harbours, no shifted rivers — and
  there is no historical gazetteer (place names drift:
  Byzantion/Constantinople/Istanbul).
- **PDF/SVG export and saved views** (PNG + deep-state permalinks now exist).
- **Screenshot/visual QA.** The smoke suite is structural; nothing verifies pixels.
- **A real edge-enrichment pipeline.** Network/journey data is hand-curated per
  subject; there's no systematic ingestion of relationships from texts/letters.

---

## The data reality (the load-bearing problem)

The maps are better than the data underneath them. Findings from this sprint:

- **Theme tagging is inverted.** Events carry process labels (`operational-chemistry`
  278, `distillation` 237, `transmutation` 207); the rich concept-page themes are
  nearly unused (`iatrochemistry` 2, `magia-naturalis` 3, `paracelsian-alchemy` ≈0).
  → The **Themes lens is mostly empty** until this is fixed.
- **No relational data.** The `relationships` table is 8 *type-names*, not edges.
  Person co-presence yields ~7 weak pairs. → Networks **must** be curated by hand.
- **No reliable itinerary data.** Bruno's corpus events are mis-dated to 1515 (b.1548);
  auto "home" locations resolve Dee and Newton to *Alexandria* (a topic tag).
  → Journeys **must** be curated by hand.
- **Most content is DRAFT.** In the Paracelsian slice, 25 of 26 events are `DRAFT`,
  1 `REVIEWED`. → A `review_status: REVIEWED+` filter empties most maps.

**Implication:** the toolkit has, by necessity, become a *curated provenance layer that
sits beside the corpus*, not a pure visualization of it. That is the honest design —
but the vision needs the corpus itself enriched.

---

## The reusability gap (module vs. project)

The stated vision is a **module for DH projects** — plural. Today the toolkit is
**hard-coupled to ALCHEMYTIMELINEMAP**:

- Engines read a fixed path to `../ALCHEMYTIMELINEMAP/site/data/data.json`.
- The data schema (events/persons/texts/concepts/locations, era ranges, region names)
  is assumed throughout.
- Themes and vocabulary are alchemy-flavoured.

To become a module it needs: a **data adapter / config** (point it at any dataset that
provides geocoded entities + relations), schema-agnostic field mapping, a project
config file, and packaging. None of that exists yet — it's a strong *application*, not
yet a *module*.

---

## Technical debt & risks

- **CDN dependency at runtime** (MapLibre + deck.gl JS and Google Fonts only —
  the basemap itself is now fully embedded) — offline/archival use still needs
  the JS libraries vendored (a real DH concern, but a much smaller one now).
- **No tests**; refactors risk silent breakage.
- **Single-file HTML with embedded data** is great for portability, heavy for large
  datasets (fine at current scale: hundreds of features).
- **Screenshot/QA blind spot** in the current environment.

---

## Roadmap (highest leverage first — see NEXTSTEPS.md for the worked plan)

1. **Enrich the corpus tagging** — verifier-gated agent swarm re-tags the 602 events
   with real conceptual themes (source required per tag). *Unlocks the Themes lens and
   honest theme maps.*
2. ~~**Enforce provenance**~~ — ✅ done: missing `provenance_note` (and unsourced
   journey stops / untyped network edges) are now build errors.
3. ~~**Period boundaries**~~ — ✅ done for political borders (24 cached years, layer +
   caveat). Remaining: period coastlines/rivers and a historical gazetteer.
4. **Decouple into a module** — data adapter + project config so it runs on any DH
   dataset. *Turns the application into the stated vision. Now the top build item.*
5. **Export + accessibility + tests** — 🟡 partly done (PNG/permalinks; data-map
   a11y; smoke suite). Remaining: PDF/SVG, journey/network a11y, visual QA.

---

## Bottom line

**Where we are:** a genuinely strong, dazzling, directable map *application* for the
alchemy project, with three working map types, four aesthetics, layered controls, an
honesty vocabulary, command-line authoring, and a teaching tour. Roughly **70% of the
way to a great single-project tool.**

**Where the vision is:** a reusable DH *module*. For that, two things gate everything
else — **(a) the underlying data** (themes, relations, itineraries, review status) and
**(b) decoupling** from this one dataset. Both are squarely on the roadmap; neither is
done. Call it **~35% of the way to the module vision** — with the hardest and most
visible craft (rendering, interaction, honesty design) already behind us, and the
less glamorous foundations (data, config, packaging) still ahead.

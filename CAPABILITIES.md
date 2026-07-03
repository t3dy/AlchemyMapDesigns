# Capabilities Tour — what we can actually build with

Honest inventory of the tools I (Claude Code) can reach to make your map better,
grouped by the job they do. Each entry notes *what it's for* and *the tradeoff*,
so you can point at one and say "that."

---

## 1. Rendering engines (the front end the user sees)

| Engine | What it's good at | Tradeoff |
|--------|-------------------|----------|
| **Leaflet** (current) | Simple, raster tiles, huge plugin ecosystem | Looks generic; no smooth zoom; styling is CSS-on-top |
| **MapLibre GL JS** | Vector tiles, buttery zoom/rotate/tilt, **data-driven styling**, fully custom basemaps (parchment palettes, no modern labels) | Steeper setup; needs a style JSON |
| **deck.gl** | GPU layers: **arcs** (transmission flows), **trips/time animation**, heatmaps, 100k+ points | Overkill for small data; pairs best with MapLibre |
| **D3.js (geo)** | Total control of projection + aesthetic — true "antique map" hand-drawn feel, custom legends | You build everything yourself |
| **Kepler.gl** | Config-driven, time playback out of the box, good for exploration | Heavy; opinionated UI; less "designed" feel |

**Recommendation for you:** MapLibre GL as the base (so the basemap can finally look
historical) + deck.gl for flow/time layers. This single change fixes problems #1 and #2.

---

## 2. Period-appropriate basemaps (fixing the anachronism)

The biggest immersion fix. Options, cheapest-first:

- **Restyled vector basemap** — a MapLibre style with a muted parchment/sepia palette
  and **modern labels & borders turned off**. Cheap, immediate, huge improvement.
- **`historical-basemaps`** (open GeoJSON, world political boundaries per year, 123 BC–1994).
  Drop in the boundary set for the event's year so Paracelsus's world shows *1500s*
  polities, not modern nations.
- **World Historical Gazetteer (WHG)** + **Pleiades/Pelagios** — historical place
  names and coordinates for ancient/medieval sites, with provenance (fits Invariant #1).
- **Stadia/Stamen "toner" or "watercolor" tiles** — quick aged aesthetic if you want
  raster instead of vector.

---

## 3. Python libraries (the build pipeline — already your idiom)

Your project already runs idempotent generators in `scripts/`. The map generator is
the same pattern. Libraries:

- **geopandas / shapely** — clip boundaries to a region bbox, spatial joins.
- **GeoJSON emit** — turn filtered events/locations into layers the front end reads.
- **networkx** — model transmission/translation networks from your `relationships`
  + co-occurrence of persons/texts across events (→ deck.gl arcs).
- **pydeck / folium** — Python-side prototyping (deck.gl / Leaflet) to compare looks fast.
- **requests** — pull WHG/gazetteer coords to fill geocoding gaps.

---

## 4. The MapSpec compiler (the "control" you asked for)

This is the answer to *"I don't know what to ask for."* You don't memorize options —
you describe intent, and the schema makes me ask for the missing pieces.

- **MapSpec schema** (`specs/mapspec.schema.json`) — locks fuzzy NL into deterministic
  params: region, year range, theme (concept slugs), persons, basemap style, layers.
- A **`/buildmap` skill** — you type `/buildmap Paracelsian alchemy in the German lands
  before the Rosicrucians`; I produce the MapSpec, you eyeball/tweak it, the generator
  renders. Reproducible and version-controllable.
- **Presets** — "transmission map", "single-figure life map", "theme diffusion over time"
  as named templates so you don't re-specify from scratch.

This is *context engineering*: a stable contract between your words and the renderer.
It's why this folder leads with the schema, not the code.

---

## 5. Agentic / swarm capabilities (where they genuinely help)

I can spin up subagents and multi-agent **workflows**. Honest scoping — these help with
*content gaps and verification*, not with the rendering itself:

- **Fill geocoding/boundary gaps** — fan out one agent per region to find missing
  historical coordinates + period boundaries, one agent to verify each against a source.
- **Network extraction** — agents mine your 602 events for person↔person and
  text↔place transmission edges to feed the flow layer.
- **Adversarial provenance check** — for any auto-added place/significance blurb, a
  verifier agent that tries to *refute* it (enforces Invariant #1) before it lands.

I will **not** oversell swarms for a UI problem. The map quality is mostly a
rendering-stack + basemap + MapSpec decision. Swarms come in once we're enriching data.

---

## 6. Verification (so I stop "dropping the ball")

I can run the map and *show you it works* instead of claiming it does:

- **preview tools** — start a dev server, take screenshots, read console errors,
  click/inspect elements. Every map build gets a screenshot back as proof.
- This closes the loop you've been frustrated by: changes get *seen*, not asserted.

---

## What I recommend we lock first

1. **Rendering stack**: MapLibre GL + deck.gl.
2. **Basemap**: restyled vector + `historical-basemaps` boundaries by year.
3. **Control surface**: MapSpec schema + a `/buildmap` directive.
4. **Proof**: screenshot every build via preview tools.

Pick or veto any of these and I'll build the first prototype against your real data.

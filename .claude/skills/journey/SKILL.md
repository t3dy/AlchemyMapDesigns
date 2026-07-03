---
name: journey
description: Author a biographical-journey map — a single life traced as a route across space and time (e.g. "/journey Giordano Bruno"). Produces a curated, evidence-typed journey JSON and renders a self-drawing animated path. Use when the user wants to map one person's travels.
---

# journey — the biographical-journey template

You are authoring a curated journey and rendering it. The corpus has NO reliable
itinerary geodata (events are mis-dated, locations are topic-tags), so a journey is a
**curated, provenance-bearing artifact you author by hand** from reliable history —
that is the honest design, not a workaround. Follow this loop.

## Inputs
- The subject (a person) is in `$ARGUMENTS`. If empty, ask who.

## Step 1 — Establish the itinerary from history
Reconstruct the person's life as an ORDERED list of stops from well-established
biography (your knowledge; if unsure, say so and keep the stop sparse). For each stop
capture: place, lat, lon, year_start, year_end, dwell (years), a 1-2 sentence "what"
(what happened there), and a `source` (a named scholar or primary source).

## Step 2 — Mark evidence honestly (the historian's hard rule)
- `evidence` on each STOP: `attested` | `approximate` (date uncertain) | `inferred`.
- `leg_evidence` on each stop = evidence for the TRAVEL INTO it from the previous
  stop: `attested` (route documented) | `inferred` (route reconstructed) |
  `approximate`. The first stop has `leg_evidence: null`.
- Do NOT smooth over gaps. A reconstructed route MUST be marked inferred — the map
  renders it as a dashed/ghost line, and that honesty is the point.

## Step 3 — Withhold the ending (project voice decision)
The renderer draws the path stop-by-stop and never shows future stops. Write the
stops so the arc reads forward — the subject did not live toward their ending. Put any
teleological framing only in `provenance_note`, never baked into early stops.

## Step 4 — Write the file and render
Write `data/journey-<slug>.json` with keys: `title`, `subtitle`, `subject` (slug if in
corpus), `theme` (default `noir` for a single mortal life; `atlas` for neutral),
`provenance_note` (cite your sources + state which legs/dates are reconstructed), and
`stops` (the array above). Then:
```
python scripts/build_journey.py data/journey-<slug>.json
```
Open it; the reader can switch uncertainty treatment (lay / understated / scholar /
centerpiece) in the map itself.

## Step 5 — Report
Give the title, number of stops, how many legs are reconstructed (inferred), the
output path, and the local URL if a server runs
(`/prototypes/journey-<slug>.html`). Flag the biggest evidential gaps as caveats.

## Guardrails
- Every stop needs a `source`. Every reconstructed leg/date must be marked inferred/
  approximate — never presented as documented.
- Coordinates must be real places; keep stops in chronological order.
- See `data/journey-bruno.json` for the reference shape.

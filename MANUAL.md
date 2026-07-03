# The Instruction Manual

How to direct, read, and share the alchemy maps — written for authors and
readers, no web-dev background assumed. The developer-facing companion is
[TOOLKIT.md](TOOLKIT.md). The friendliest introduction of all is the guided
tour (`tour/index.html`), and every built map is browsable in the gallery
(`gallery/index.html`).

---

## 1. What you can make

Three kinds of map, each a template with defensible defaults:

- **Data maps** — "show me *this slice* of the corpus": a region, an era, a
  theme, a person's footprint. Points sized by activity, arcs showing
  knowledge in motion, a time scrubber, five one-click lenses.
- **Journeys** — one life as a route. The path draws itself stop by stop and
  *withholds the ending*; dashed legs mean reconstructed travel.
- **Networks** — who knew whom: patronage, correspondence, teaching. Click a
  figure to pivot; flip the survival toggle to see how archives lie.

## 2. Quick start

From the project root (`C:\Dev\MAPRESEARCH`):

```
python -m http.server 8777
```

Then open `http://localhost:8777/gallery/` — the gallery of every map, with
notes on what each one is trying. Or go straight to the guided tour at
`/tour/index.html`.

## 3. Directing a map in plain language (the skills)

Run Claude Code in the project directory and type one of:

- `/buildmap Paracelsian alchemy in Central Europe before the Rosicrucians`
- `/journey Giordano Bruno`
- `/network the Hartlib circle`

What happens: your sentence is translated into a **MapSpec** (a small JSON
recipe), validated, and compiled to a finished map in `prototypes/`. The recipe
is saved too, so the map is reproducible and editable — change one word in the
spec, rebuild, get the variant.

Two things the system will hold you to:

1. **Real vocabulary.** Every theme/person/region must exist in the data. The
   skill checks `list_vocab.py`, which also shows how many events each slug
   actually has — ask for a thinly-tagged theme and you'll be warned the map
   will be sparse.
2. **Provenance.** No map compiles without a `provenance_note` saying where its
   claims come from and what it does not show. This is deliberate.

## 4. Reading a data map

**Left panel** — title, framing, stats, legend, and the provenance note
(including the borders caveat when period boundaries are shown).

**Right panel, top to bottom:**

- **Lenses** — one click reconfigures everything: *Transmission* (arcs),
  *Lives* (arcs + labels), *Texts*, *Themes*, *Density* (heatmap).
- **Appearance & filters** — theme (four aesthetics, live), typeface,
  colour-by (theme / region / era), layer chips (Points, Arcs, Labels,
  Heatmap, and Borders when the map carries period boundaries).
- **Advanced** — arc width, point size, opacity, legend, rich tooltips.

Under everything sits real geography — coastlines, lakes, and major rivers,
embedded in the file itself and tinted to the active theme. Place labels are on
by default; toggle the Labels chip if you want a quieter map.

**Bottom bar** — the time scrubber. **▶ Play** animates events accumulating
year by year. Hover any point for its events; hover an arc for who moved and
when; hover a border line for the polity's name and the "approximate" caveat.

**The six styles:** Modern Atlas (clarity), Copperplate (the printed corpus),
Illuminated (courts and gold), Noir (single lives, spectacle), Woodcut & Rubric
(black line and vermillion — polemic and the medieval page), Lapis & Gold
(ultramarine and gilt — late antiquity and the celestial). Every map *opens* in
the style chosen for its material — the badge on its gallery card says which,
and its page's design note says why — but switching is always one dropdown away.
Under all six, the same real terrain — mountain shading, green lowlands, tan
uplands — shows through, tinted to match: parchment-gold under Illuminated,
near-monochrome engraving under Woodcut, a cool dark register under Noir.
Switching theme never changes the data — only the dress.

## 5. Reading a journey

Press **▶ Play** and the life draws itself. The camera moves ahead of the
path; future stops are never shown — you can stop mid-life knowing nothing of
the end. **Next ▸ / ◂** step manually.

- **Solid line** = documented travel. **Dashed** = reconstructed or approximate.
- Node size = how long they stayed.
- The story panel gives each stop's narrative; its source appears in the
  scholarly modes.

**Uncertainty treatments** (the dropdown): *Lay* (clean story), *Understated*
(quiet apparatus), *Scholar* (citations + gap notes), *Centerpiece* (doubt made
visible: ghost routes and a running "what we don't know" panel). Same data,
four editorial stances — pick the one your audience needs.

## 6. Reading a network

- Edges are **coloured by relationship type** (patronage, correspondence,
  teaching…), **width = strength**, **faint = inferred**. A colour gradient
  runs source → target on directed ties (patron darker → client).
- **Click a figure to pivot**: their ties light up, everything else dims. The
  centre of a network is a choice, not a fact.
- **"Show only what survives"** drops every tie whose documents are lost. Watch
  the network collapse toward the archive-keepers — that distortion is the
  single most important thing to understand about correspondence maps.
- The panel's "what this map does NOT show" note is part of the map. Read it.

## 7. Sharing and exporting

- **🔗 Link** copies a URL that reproduces your *exact* current view — theme,
  lens, layers, year, slider values. Send it; they see what you see.
- **⤓ PNG** downloads the current view with the title, the year, and the
  borders caveat burnt into the footer — the image stays honest when it leaves.
- **Embedding**: add `?ui=min` to any map URL for a chrome-less iframe; drive
  it from the parent page via postMessage (see TOOLKIT.md §6).

## 8. How to read these maps honestly

The encodings are consistent everywhere and worth memorizing:

- **Line style = evidence.** Solid is documented; dashed is reconstructed.
- **Opacity = confidence.** Faint means inferred.
- **Colour = category, never confidence.** A map that colours by certainty is
  editorializing; these don't.
- **Absence ≠ absence.** A gap on the map is a gap in the record. The
  transmission arcs trace *named individuals whose itineraries survive* — the
  anonymous carriers vastly outnumbered them.
- **Borders are orientation, not authority.** Period boundaries are approximate
  scholarly reconstructions, snapped to the nearest cached year, and every map
  that shows them says so.
- **Terrain is real but modern.** The colourful hills and shading under every
  map are actual physical geography (Natural Earth), not decoration — but it's
  today's terrain, not a period reconstruction; a map's panel says so whenever
  the relief layer is present, right alongside the borders caveat.
- **Corpus vs. curated.** Data maps visualize a database that is largely
  draft-status; journeys and networks are hand-curated from real scholarship
  with per-item sources. The gallery notes say which is which.

## 9. Authoring by hand (beyond the skills)

Write a `*.mapspec.json` (copy
`specs/examples/paracelsian-before-rosicrucians.mapspec.json`), then:

```
cd scripts
python build_map.py ../specs/your-map.mapspec.json
```

For a journey, copy `data/journey-dee.json` and keep every stop's `evidence`
and `source` honest — the builder rejects unsourced stops. For a network, add a
subject to `data/networks.json` and rebuild with `python build_network.py`.
After adding any map, run `python build_gallery.py` to refresh the gallery.

## 10. Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| "SPEC ERROR: narrative.provenance_note is required" | Working as intended — write the note. `--allow-unsourced` for throwaway drafts only. |
| "theme 'x' matches 0 events" warning | The corpus barely uses that tag (see `list_vocab.py`). Choose a populated theme or accept a sparse map. |
| Map compiles but is nearly empty | Scope too narrow — drop `review_status` filters, widen years, or check region spellings against the vocab. |
| "no boundary cache found" warning | Run `python scripts/fetch_boundaries.py` once (downloads ~24 years of border files). |
| Blank map in the browser | WebGL is disabled, or the MapLibre/deck.gl script CDNs are unreachable (the geography itself is embedded and needs no network). Try a normal browser profile. |
| No land/sea, just dots | Fixed — maps now embed their own coastlines, lakes, and rivers. If you still see it, the map predates the fix: rebuild it (`python scripts/build_map.py <spec>`). |
| Animation doesn't play | If your OS is set to reduced motion, ▶ becomes a step-through button by design. |

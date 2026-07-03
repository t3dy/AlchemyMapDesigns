#!/usr/bin/env python3
"""
build_gallery.py — generate the web gallery of every map in the project.

Scans specs/ (data maps), data/journey-*.json (journeys), and data/networks.json
(network subjects); compiles each data map once to draw a deterministic SVG
preview (no screenshots needed — the sandbox can't take them anyway); and emits:

  gallery/index.html      — preview cards grouped by family, with idea accordions
  gallery/<slug>.html     — one page per map: embedded map, provenance, stats,
                            and "ideas this map is trying" accordions
  gallery/toolkit.html    — HTML rendering of TOOLKIT.md
  gallery/manual.html     — HTML rendering of MANUAL.md

Re-run after adding any map:  python build_gallery.py
"""
import html as H
import json
import math
import re
from pathlib import Path

import build_map as bm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "gallery"
DATA = json.loads((ROOT.parent / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- ideas registry

IDEAS = {
    "mapspec-compiler": ("The MapSpec compiler",
        "The core idea of the whole project: a small JSON recipe sits between fuzzy natural "
        "language and deterministic rendering. You (or a Claude Code skill) describe a map; the "
        "description becomes a versionable <em>contract</em>; a Python generator compiles it to a "
        "finished artifact. Change one word in the recipe and rebuild — the variation is "
        "reproducible, diffable, and honest about what was asked for. Every data map in this "
        "gallery has its recipe linked at the top of its page."),
    "period-borders": ("Period-accurate borders",
        "Early-modern events used to float over 21st-century borders. Now a spec can say "
        "<code>historical_boundaries_year: 1560</code> and the compiler embeds approximate period "
        "polities from a locally cached, slimmed <em>historical-basemaps</em> dataset (snapped to "
        "the nearest cached year). It ships as a toggleable Borders layer — hover a line for the "
        "polity's name — and the map automatically gains a caveat: approximate, for orientation, "
        "never authority."),
    "theme-engine": ("The theme engine — four faces",
        "One map, four complete visual identities, switchable live: Modern Atlas (clarity), "
        "Copperplate Engraving (the printed corpus), Illuminated Manuscript (courts and gold), "
        "Alchemical Noir (single lives, spectacle). Colour is assigned at runtime from the active "
        "theme's palette, so re-skinning never touches the data. The experiment: does aesthetic "
        "register change what a reader trusts and notices? Try the same map in Atlas and Noir."),
    "lenses": ("Layered controls — lenses, filters, drawer",
        "Controls like a search engine: newcomers get five one-click <em>lenses</em> "
        "(Transmission · Lives · Texts · Themes · Density) that reconfigure everything at once; "
        "regulars get a filter bar (theme, colour-by, layer chips); power users get an advanced "
        "drawer (widths, sizes, opacity, tooltips). The bet: progressive disclosure beats both "
        "the empty-map-with-99-toggles and the locked-down infographic."),
    "time": ("Time as accumulation",
        "The scrubber doesn't slice time, it <em>accumulates</em> it — press Play and events pile "
        "up through the years, so centres of gravity visibly form and migrate. On journeys the "
        "same control becomes progress-through-a-life. Under reduced-motion settings Play turns "
        "into a discrete step-through: same story, no animation."),
    "transmission-arcs": ("Transmission arcs — knowledge in motion",
        "Arcs connect consecutive dated events of the same named person: alchemy moving as people "
        "moved. The honesty cost is stated on every map: arcs trace <em>named figures whose "
        "itineraries survive</em>; the anonymous carriers — merchants, manuscripts, students — "
        "vastly outnumbered them, and absence of an arc is absence of record."),
    "provenance-enforcement": ("Provenance or it doesn't compile",
        "Every engine refuses unsourced content: a MapSpec without a provenance note, a journey "
        "stop without evidence + source, a network edge without type/evidence/citation — all are "
        "build <em>errors</em>, not warnings. The historian's hard line, made mechanical. The "
        "note you see in each map's panel is the artifact of that rule."),
    "export-permalinks": ("Maps that travel honestly",
        "🔗 Link copies a URL reproducing the exact view (theme, lens, layers, year, sliders); "
        "⤓ PNG exports the current view with title, year, and the borders caveat burnt into a "
        "footer strip. The idea: when a map leaves the toolkit — into a slide, a tweet, a paper — "
        "its honesty apparatus should refuse to be left behind."),
    "vocab-counts": ("The data is the weather",
        "The corpus under-tags conceptual themes (distillation: 237 events; iatrochemistry: 9). "
        "Rather than hide that, the toolkit surfaces it: the vocabulary tool prints per-slug event "
        "counts, and the compiler warns when a requested theme matches zero events. Sparse maps "
        "are shown as sparse, with the sparseness explained — the alternative is a lens that "
        "silently shows nothing."),
    "withheld-ending": ("The withheld ending",
        "The journey draws itself stop by stop and never renders future stops — you can pause "
        "mid-life and genuinely not know what comes. An experiment in narrative cartography: maps "
        "usually spoil their own endings by showing the whole route at once; biography read that "
        "way loses its contingency. Here the road ahead is dark, as it was."),
    "uncertainty-treatments": ("Four uncertainty treatments",
        "The same journey ships four editorial stances, switchable live: <em>Lay</em> (clean "
        "story), <em>Understated</em> (quiet solid/dashed apparatus), <em>Scholar</em> (citations "
        "and gap notes), <em>Centerpiece</em> (doubt made visible — ghost routes, a running "
        "'what we don't know' panel). The experiment: uncertainty display is an editorial "
        "<em>choice</em>, so make it a control instead of a dogma."),
    "evidence-encoding": ("Evidence in the line itself",
        "A consistent visual grammar everywhere: line style = evidence (solid documented, dashed "
        "reconstructed), opacity = confidence, colour = category — and never colour for "
        "confidence, the commonest map lie. Every stop, arc, and edge carries its source on "
        "hover."),
    "survival-bias": ("The survival-bias toggle",
        "Correspondence networks are survival maps pretending to be sociability maps: whoever's "
        "archive survived looks central. The toggle makes the lie visible — 'show only what "
        "survives' drops reconstructed ties and watches the network collapse toward the "
        "archive-keepers. The distortion is the exhibit."),
    "pivot": ("The centre is a choice",
        "Click any figure to pivot the network around them: their ties light, the rest dims. "
        "There is no privileged centre — Rudolf II's Prague looks different centred on Kelley "
        "than on the emperor. A small interaction against the oldest network-diagram fallacy."),
    "curated-vs-corpus": ("Curated layers beside the corpus",
        "The database has no reliable relational or itinerary data, so journeys and networks are "
        "<em>hand-curated from real scholarship</em>, every item sourced, sitting beside the "
        "corpus rather than pretending to be derived from it. Data maps visualize the database; "
        "curated maps visualize the literature. Each page says which kind you're reading."),
    "style-as-argument": ("Style as argument",
        "Six full visual identities — Modern Atlas, Copperplate Engraving, Illuminated Manuscript, "
        "Alchemical Noir, Woodcut &amp; Rubric, Lapis &amp; Gold — and every map now <em>opens</em> in the "
        "one that suits its material: copperplate for print-culture subjects, lapis for late antiquity, "
        "noir for hidden and rejected knowledge, woodcut for scholastic polemic. Each map's page carries "
        "a design note saying why. The reader can always switch styles live — the assignment is a "
        "curatorial argument, not a lock."),
    "scholarship-maps": ("Maps keyed to the scholarship",
        "The collection knows its own historiography: 43 modern scholars appear in it, and their surname "
        "citations across the 680 events are countable (Principe 90 · Newman 60 · Smith 21 · Hanegraaff 19 "
        "· Fowden 15 · Copenhaver 13 · Pereira 8). The Scholarship Shelf gives each most-cited study its "
        "own map — the study's key topics and figures, scoped from the corpus, styled to the study's "
        "source base, with the citation count in the provenance line. A map as a book review."),
    "embedding": ("Drivable, embeddable artifacts",
        "Every map is a self-contained HTML file that accepts URL parameters (<code>?ui=min"
        "&theme=noir&year=1550</code>) and postMessage commands from a parent page. That's how "
        "the scrollytelling tour drives maps as you scroll, and how this gallery embeds them — "
        "the map is a component, not a screenshot."),
}

# deeper-reading links per idea (hrefs relative to gallery/)
IDEA_LINKS = {
    "mapspec-compiler": [("Toolkit §3 — the MapSpec contract", "toolkit.html#3-the-mapspec-contract"),
                         ("Manual §3 — directing a map in plain language", "manual.html#3-directing-a-map-in-plain-language-the-skills")],
    "period-borders": [("Toolkit §4 — fetch_boundaries.py", "toolkit.html#4-engines-cli-reference"),
                       ("Manual §8 — borders are orientation, not authority", "manual.html#8-how-to-read-these-maps-honestly")],
    "theme-engine": [("Toolkit §7 — the theme engine", "toolkit.html#7-the-theme-engine")],
    "lenses": [("Manual §4 — reading a data map", "manual.html#4-reading-a-data-map")],
    "time": [("Manual §4 — reading a data map", "manual.html#4-reading-a-data-map")],
    "transmission-arcs": [("Manual §8 — absence ≠ absence", "manual.html#8-how-to-read-these-maps-honestly")],
    "provenance-enforcement": [("Toolkit §1 — architecture & principles", "toolkit.html#1-architecture"),
                               ("Manual §10 — 'provenance_note is required'", "manual.html#10-troubleshooting")],
    "export-permalinks": [("Manual §7 — sharing and exporting", "manual.html#7-sharing-and-exporting")],
    "vocab-counts": [("Toolkit §4 — list_vocab.py", "toolkit.html#4-engines-cli-reference"),
                     ("Manual §10 — sparse maps", "manual.html#10-troubleshooting")],
    "withheld-ending": [("Manual §5 — reading a journey", "manual.html#5-reading-a-journey")],
    "uncertainty-treatments": [("Manual §5 — reading a journey", "manual.html#5-reading-a-journey")],
    "evidence-encoding": [("Manual §8 — how to read honestly", "manual.html#8-how-to-read-these-maps-honestly")],
    "survival-bias": [("Manual §6 — reading a network", "manual.html#6-reading-a-network")],
    "pivot": [("Manual §6 — reading a network", "manual.html#6-reading-a-network")],
    "curated-vs-corpus": [("Toolkit §5 — curated data formats", "toolkit.html#5-data-formats-curated-layers"),
                          ("Manual §8 — corpus vs. curated", "manual.html#8-how-to-read-these-maps-honestly")],
    "embedding": [("Toolkit §6 — runtime APIs", "toolkit.html#6-runtime-apis-every-emitted-map")],
    "style-as-argument": [("Toolkit §7 — the theme engine", "toolkit.html#7-the-theme-engine"),
                          ("Manual §4 — the six styles", "manual.html#4-reading-a-data-map")],
    "scholarship-maps": [("Toolkit §4 — build_scholarship.py", "toolkit.html#4-engines-cli-reference"),
                         ("Manual §8 — corpus vs. curated", "manual.html#8-how-to-read-these-maps-honestly")],
}

FAMILY_IDEAS = {
    "example": ["mapspec-compiler", "period-borders", "provenance-enforcement", "lenses", "theme-engine"],
    "era": ["style-as-argument", "mapspec-compiler", "time", "transmission-arcs", "period-borders"],
    "century": ["style-as-argument", "time", "transmission-arcs", "period-borders"],
    "theme": ["style-as-argument", "vocab-counts", "mapspec-compiler", "period-borders"],
    "figure": ["style-as-argument", "transmission-arcs", "curated-vs-corpus", "export-permalinks"],
    "region": ["style-as-argument", "mapspec-compiler", "time", "period-borders"],
    "study": ["scholarship-maps", "style-as-argument", "vocab-counts", "provenance-enforcement"],
    "journey": ["withheld-ending", "uncertainty-treatments", "evidence-encoding", "curated-vs-corpus", "style-as-argument"],
    "network": ["survival-bias", "pivot", "evidence-encoding", "curated-vs-corpus", "style-as-argument"],
}

FAMILY_META = {
    "example": ("Directed Examples", "One-sentence directives carried end-to-end: sentence → MapSpec → map. The Paracelsian map is the project's founding example; the others test the authoring loop on fresh questions — including a map whose deliberate sparseness is its argument."),
    "era": ("Six Eras", "One map per major era of alchemy, from Greco-Egyptian Alexandria to English chymistry. Batch-authored by build_all.py; the tour's spine."),
    "century": ("Eleven Centuries", "The 8th through 18th centuries as transmission maps. Scroll them in order and the centre of gravity migrates: Baghdad → al-Andalus → Latin Europe → the north."),
    "theme": ("Seven Themes", "One conceptual or operational theme each, traced across the whole corpus — chosen from tags that are actually populated (the counts are part of the story)."),
    "figure": ("Eight Figures", "One practitioner's evented footprint each, with itinerary arcs. These read the corpus; for sourced life-routes see the Journeys."),
    "region": ("Six Regions", "One regional alchemical culture each, through the full sweep of time, with period borders from the region's densest century."),
    "study": ("The Scholarship Shelf", "One map per most-cited study in the collection's own historiography — the study's key topics and figures scoped from the corpus, styled to its source base, citation counts in the provenance. Principe, Newman & Principe, Smith, Hanegraaff, Fowden, Copenhaver, Pereira."),
    "journey": ("Journeys", "Lives as routes: hand-curated, per-stop sourced, self-drawing, ending withheld. The uncertainty-treatment selector is the experiment here."),
    "network": ("Networks", "Constellations of people: typed, weighted, evidence-bearing ties. Six subjects in one explorer; the survival-bias toggle is the point."),
}

FAMILY_THEME = {"example": "illuminated", "era": "atlas", "century": "copperplate",
                "theme": "copperplate", "figure": "noir", "region": "illuminated",
                "study": "copperplate", "journey": "noir", "network": "atlas"}

PALETTE = {
    "atlas": {"bg": "#f7f6f3", "land": "#f0eee9", "ink": "#1f2937", "accent": "#3f6f8f",
              "pts": ["#3f6f8f", "#b05c35", "#3c8264", "#966e28", "#785696"]},
    "copperplate": {"bg": "#efe7d3", "land": "#e9e0c8", "ink": "#241c12", "accent": "#5a3c1d",
                    "pts": ["#3c2c1c", "#785028", "#5a462d", "#8c6437", "#463723"]},
    "illuminated": {"bg": "#f4ead2", "land": "#f0e3c2", "ink": "#3a1f12", "accent": "#9c2b2b",
                    "pts": ["#9c2b2b", "#b68c28", "#2a5a46", "#783278", "#285088"]},
    "noir": {"bg": "#0e0f12", "land": "#1b1f27", "ink": "#e9e2cf", "accent": "#c9a24b",
             "pts": ["#c9a24b", "#b4c8d2", "#78c8aa", "#c878a0", "#78a0dc"]},
    "woodcut": {"bg": "#f6efdc", "land": "#f3ecd6", "ink": "#171310", "accent": "#a3231b",
                "pts": ["#171310", "#a3231b", "#463c32", "#781e19", "#282320"]},
    "lapis": {"bg": "#101a30", "land": "#1d2c4f", "ink": "#e8e4d4", "accent": "#d4af37",
              "pts": ["#d4af37", "#82b4dc", "#dcdce6", "#6ec8be", "#dc8c64"]},
}
THEME_LABEL = {"atlas": "Modern Atlas", "copperplate": "Copperplate Engraving",
               "illuminated": "Illuminated Manuscript", "noir": "Alchemical Noir",
               "woodcut": "Woodcut & Rubric", "lapis": "Lapis & Gold"}
WATER = {"atlas": "#cdd8dd", "copperplate": "#dde3da", "illuminated": "#cfe0e6",
         "noir": "#11141a", "woodcut": "#e4ddc6", "lapis": "#0d1526"}

# ---------------------------------------------------------------- svg previews

W, PH = 320, 190

_LAND = json.loads((ROOT / "data" / "basegeo" / "land.geojson").read_text(encoding="utf-8"))["features"] \
    if (ROOT / "data" / "basegeo" / "land.geojson").exists() else []


def _land_paths(p, theme):
    """Land silhouettes behind a preview, projected with the card's projection."""
    t = PALETTE[theme]
    # visible lon/lat domain of the card (invert the projection at the corners)
    x0, y0 = p.inv(-10, PH + 10)
    x1, y1 = p.inv(W + 10, -10)
    paths = []
    for feat in _LAND:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            xs = [q[0] for q in ring]
            ys = [q[1] for q in ring]
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
                continue
            step = max(1, len(ring) // 220)
            pts = ring[::step]
            d = "M" + "L".join(f"{px:.0f},{py:.0f}" for px, py in (p(lon, lat) for lon, lat in pts)) + "Z"
            paths.append(d)
    if not paths:
        return ""
    return (f'<path d="{" ".join(paths)}" fill="{t["land"]}" stroke="{t["accent"]}" '
            f'stroke-opacity="0.35" stroke-width="0.7" fill-rule="evenodd"/>')


def _proj(lons, lats):
    if not lons:
        lons, lats = [15.0], [45.0]
    x0, x1, y0, y1 = min(lons), max(lons), min(lats), max(lats)
    x0, x1 = x0 - 1.5, x1 + 1.5
    y0, y1 = y0 - 1.5, y1 + 1.5
    sx, sy = (W - 24) / max(x1 - x0, 0.01), (PH - 24) / max(y1 - y0, 0.01)
    s = min(sx, sy)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def p(lon, lat):
        return (W / 2 + (lon - cx) * s, PH / 2 - (lat - cy) * s)

    def inv(x, y):
        return (cx + (x - W / 2) / s, cy - (y - PH / 2) / s)
    p.inv = inv
    return p


def svg_wrap(theme, body, land=""):
    # water-coloured canvas + real land silhouettes: the cards look like maps too
    return (f'<svg viewBox="0 0 {W} {PH}" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">'
            f'<rect width="{W}" height="{PH}" fill="{WATER[theme]}"/>'
            + land + body + "</svg>")


def preview_datamap(compiled, theme):
    t = PALETTE[theme]
    pts = compiled["points"]
    p = _proj([q["lon"] for q in pts], [q["lat"] for q in pts])
    out = []
    for a in compiled["arcs"][:60]:
        x1, y1 = p(*a["from"])
        x2, y2 = p(*a["to"])
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - max(6, abs(x2 - x1) * 0.18)
        out.append(f'<path d="M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}" fill="none" stroke="{t["accent"]}" stroke-opacity="0.45" stroke-width="1"/>')
    for i, q in enumerate(sorted(pts, key=lambda z: -z["count"])[:40]):
        x, y = p(q["lon"], q["lat"])
        r = min(11, 2.2 + math.sqrt(q["count"]) * 1.3)
        c = t["pts"][i % len(t["pts"])]
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{c}" fill-opacity="0.85" stroke="{t["bg"]}" stroke-width="1"/>')
    return svg_wrap(theme, "".join(out), land=_land_paths(p, theme))


def preview_journey(J, theme):
    t = PALETTE[theme]
    stops = J["stops"]
    p = _proj([s["lon"] for s in stops], [s["lat"] for s in stops])
    out = []
    for a, b in zip(stops, stops[1:]):
        x1, y1 = p(a["lon"], a["lat"])
        x2, y2 = p(b["lon"], b["lat"])
        dash = ' stroke-dasharray="4 3"' if b.get("leg_evidence") in ("inferred", "approximate") else ""
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{t["accent"]}" stroke-width="1.6" stroke-opacity="0.8"{dash}/>')
    for i, s in enumerate(stops):
        x, y = p(s["lon"], s["lat"])
        r = 2.5 + min(5, (s.get("dwell") or 1) * 0.45)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{t["accent"]}" stroke="{t["bg"]}" stroke-width="1"/>')
    return svg_wrap(theme, "".join(out), land=_land_paths(p, theme))


def preview_network(subj, theme):
    t = PALETTE[theme]
    nodes = {n["id"]: n for n in subj["nodes"]}
    p = _proj([n["lon"] for n in subj["nodes"]], [n["lat"] for n in subj["nodes"]])
    out = []
    for i, e in enumerate(subj["edges"]):
        a, b = nodes[e["source"]], nodes[e["target"]]
        x1, y1 = p(a["lon"], a["lat"])
        x2, y2 = p(b["lon"], b["lat"])
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 10
        c = t["pts"][i % len(t["pts"])]
        op = 0.35 if e.get("evidence") == "inferred" else 0.8
        out.append(f'<path d="M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}" fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="{1 + e.get("weight", 1) * 0.5:.1f}"/>')
    for n in subj["nodes"]:
        x, y = p(n["lon"], n["lat"])
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="{t["ink"]}" stroke="{t["bg"]}" stroke-width="1.2"/>')
    return svg_wrap(theme, "".join(out), land=_land_paths(p, theme))

# ---------------------------------------------------------------- catalog

def family_of(slug):
    for fam in ("era", "century", "theme", "figure", "region", "study"):
        if slug.startswith(fam + "-"):
            return fam
    return "example"


DATAMAP_TOOLS = {"points": "ScatterplotLayer (points)", "flows": "ArcLayer (transmission)",
                 "labels": "TextLayer (labels)", "heatmap": "HeatmapLayer (density)",
                 "time-animation": "time scrubber"}


def datamap_tools(spec, compiled):
    parts = [DATAMAP_TOOLS[l] for l in spec.get("render", {}).get("layers", []) if l in DATAMAP_TOOLS]
    parts.append("GeoJsonLayer (coastlines · lakes · rivers)")
    if compiled.get("boundaries"):
        parts.append(f"GeoJsonLayer (borders c. {compiled['boundaries']['year']})")
    return "MapLibre GL canvas · deck.gl: " + " · ".join(parts)


def collect():
    cat = []
    for spec_path in sorted((ROOT / "specs").glob("**/*.mapspec.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        slug = spec_path.stem.replace(".mapspec", "")
        fam = family_of(slug)
        compiled = bm.compile_spec(spec, DATA)
        s = compiled["stats"]
        theme = compiled.get("initial_theme") or FAMILY_THEME.get(fam, "atlas")
        byear = compiled["boundaries"]["year"] if compiled.get("boundaries") else None
        # batch builders emit <slug>.html; build_map.py's default is <spec-stem>.html
        proto = f"{slug}.html" if (ROOT / "prototypes" / f"{slug}.html").exists() else f"{spec_path.stem}.html"
        if not (ROOT / "prototypes" / proto).exists():
            raise SystemExit(f"no prototype for spec {spec_path.name} — build it first")
        cat.append({
            "slug": slug, "family": fam, "title": spec["title"],
            "subtitle": spec.get("subtitle", ""),
            "note": (spec.get("narrative") or {}).get("intro", ""),
            "prov": (spec.get("narrative") or {}).get("provenance_note", ""),
            "directive": spec.get("directive", ""),
            "stats": f"{s['events']} events · {s['locations']} places · {s['arcs']} arcs"
                     + (f" · borders c. {byear}" if byear else ""),
            "map_url": f"../prototypes/{proto}",
            "spec_url": "../" + spec_path.relative_to(ROOT).as_posix(),
            "svg": preview_datamap(compiled, theme), "theme": theme,
            "design": (spec.get("narrative") or {}).get("design_note", ""),
            "tools": datamap_tools(spec, compiled),
            "kind": "corpus data map",
            "rel": {"years": [spec.get("scope", {}).get("year_start") or compiled["year_min"],
                              spec.get("scope", {}).get("year_end") or compiled["year_max"]],
                    "themes": set(spec.get("scope", {}).get("themes") or []),
                    "persons": set(spec.get("scope", {}).get("persons") or []),
                    "regions": set(spec.get("scope", {}).get("regions") or [])},
        })
    for jp in sorted((ROOT / "data").glob("journey-*.json")):
        J = json.loads(jp.read_text(encoding="utf-8"))
        slug = jp.stem
        rec = sum(1 for st in J["stops"] if st.get("leg_evidence") in ("inferred", "approximate"))
        cat.append({
            "slug": slug, "family": "journey", "title": J["title"],
            "subtitle": J.get("subtitle", ""),
            "note": J["stops"][0]["what"] if J.get("stops") else "",
            "prov": J.get("provenance_note", ""), "directive": f"/journey {J.get('subject', '')}",
            "stats": f"{len(J['stops'])} stops · {rec} reconstructed legs",
            "map_url": f"../prototypes/{slug}.html", "spec_url": "../data/" + jp.name,
            "svg": preview_journey(J, J.get("theme") if J.get("theme") in PALETTE else "noir"),
            "theme": J.get("theme") if J.get("theme") in PALETTE else "noir",
            "design": J.get("design_note", ""),
            "tools": ("MapLibre GL canvas · deck.gl: PathLayer + PathStyleExtension (dashed = reconstructed leg) · "
                      "self-drawing animated route with withheld ending · ScatterplotLayer nodes sized by dwell · "
                      "four switchable uncertainty treatments · GeoJsonLayer (coastlines · lakes · rivers)"),
            "kind": "curated journey",
            "rel": {"years": [min(s["year_start"] for s in J["stops"]),
                              max(s.get("year_end") or s["year_start"] for s in J["stops"])],
                    "themes": set(), "persons": {J.get("subject")} - {None, ""}, "regions": set()},
        })
    net = json.loads((ROOT / "data" / "networks.json").read_text(encoding="utf-8"))
    for subj in net["subjects"]:
        slug = "network-" + subj["slug"]
        theme = subj.get("theme", "atlas")
        if theme not in PALETTE:
            theme = "atlas"
        surv = sum(1 for e in subj["edges"] if e.get("survives"))
        cat.append({
            "slug": slug, "family": "network", "title": subj["title"],
            "subtitle": subj.get("subtitle", ""),
            "note": subj.get("provenance_note", ""),
            "prov": subj.get("provenance_note", ""), "directive": f"/network {subj['slug']}",
            "stats": f"{len(subj['nodes'])} figures · {len(subj['edges'])} ties ({surv} survive)",
            "map_url": f"../prototypes/network.html?subject={subj['slug']}",
            "spec_url": "../data/networks.json",
            "svg": preview_network(subj, theme), "theme": theme,
            "design": subj.get("design_note", ""),
            "tools": ("MapLibre GL canvas · deck.gl: ArcLayer edges (colour = tie type, width = weight, "
                      "opacity = confidence, gradient = direction) · click-to-pivot · survival-bias toggle · "
                      "GeoJsonLayer (coastlines · lakes · rivers)"),
            "kind": "curated network",
            "rel": {"years": [min((n.get("year") or 1500) for n in subj["nodes"]),
                              max((n.get("year") or 1500) for n in subj["nodes"]) + 40],
                    "themes": set(),
                    "persons": {n["slug"] for n in subj["nodes"] if n.get("slug")},
                    "regions": set()},
        })
    return cat


def compute_related(cat):
    """Relational browsing: link each map to its era/topic/figure/region kin."""
    def overlap(a, b):
        ya, yb = a["rel"]["years"], b["rel"]["years"]
        if None in ya or None in yb or ya == [0, 0] or yb == [0, 0]:
            return False
        return ya[0] <= yb[1] and yb[0] <= ya[1]

    for e in cat:
        rel = {"era": [], "topic": [], "figure": [], "region": []}
        for x in cat:
            if x is e:
                continue
            if x["family"] in ("era", "century") and e["family"] not in ("era", "century") and overlap(e, x):
                rel["era"].append(x)
            if e["rel"]["themes"] & x["rel"]["themes"]:
                rel["topic"].append(x)
            if e["rel"]["persons"] & x["rel"]["persons"]:
                rel["figure"].append(x)
            if e["rel"]["regions"] & x["rel"]["regions"]:
                rel["region"].append(x)
        # era/century maps relate to each other by overlap too
        if e["family"] in ("era", "century"):
            rel["era"] = [x for x in cat if x is not e and x["family"] in ("era", "century") and overlap(e, x)]
        e["related"] = {k: v[:8] for k, v in rel.items() if v}

# ---------------------------------------------------------------- tiny markdown

def md_to_html(md):
    out, i = [], 0
    lines = md.split("\n")

    def inline(s):
        s = H.escape(s, quote=False)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            block = []
            while j < len(lines) and not lines[j].startswith("```"):
                block.append(lines[j])
                j += 1
            out.append("<pre><code>" + H.escape("\n".join(block)) + "</code></pre>")
            i = j + 1
            continue
        if re.match(r"^#{1,4} ", ln):
            n = len(ln) - len(ln.lstrip("#"))
            text = ln[n + 1:]
            anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append(f'<h{n} id="{anchor}">{inline(text)}</h{n}>')
        elif ln.strip() == "---":
            out.append("<hr>")
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            i -= 1
            body = rows[2:] if len(rows) > 1 and set("".join(rows[1])) <= set("-: ") else rows[1:]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table>")
        elif re.match(r"^(-|\d+\.) ", ln):
            tag = "ul" if ln.startswith("- ") else "ol"
            items = []
            while i < len(lines) and (re.match(r"^(-|\d+\.) ", lines[i]) or lines[i].startswith("  ")):
                if re.match(r"^(-|\d+\.) ", lines[i]):
                    items.append(re.sub(r"^(-|\d+\.) ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            i -= 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
        elif ln.strip():
            para = [ln]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|```|\||-|\d+\.|---)", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        i += 1
    return "\n".join(out)

# ---------------------------------------------------------------- html shell

CSS = """
:root{--bg:#f2ead8;--panel:#faf4e4;--ink:#2b1d10;--muted:#7a5a36;--accent:#9c2b2b;
  --gold:#b68c28;--bd:#d8c49a;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"EB Garamond",Georgia,serif;
  background-image:radial-gradient(ellipse at 20% 0%,#f8f0dc 0%,#f2ead8 55%,#ecdfc4 100%);}
a{color:var(--accent);}
header.site{padding:42px 24px 18px;text-align:center;}
header.site h1{font-family:"Cinzel",Georgia,serif;font-size:clamp(26px,4.5vw,44px);margin:0 0 6px;letter-spacing:.04em;}
header.site .sub{font-style:italic;color:var(--muted);font-size:17px;max-width:760px;margin:0 auto;}
.counts{margin:14px auto 0;font-size:13px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;}
nav.docs{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:22px auto 8px;max-width:900px;}
nav.docs a{display:block;background:var(--panel);border:1px solid var(--bd);border-radius:10px;
  padding:10px 18px;text-decoration:none;color:var(--ink);font-size:14.5px;box-shadow:0 4px 14px rgba(60,40,10,.08);}
nav.docs a b{font-family:"Cinzel",serif;font-size:13px;letter-spacing:.05em;color:var(--accent);display:block;}
main{max-width:1180px;margin:0 auto;padding:10px 24px 80px;}
section.family{margin-top:46px;}
section.family>h2{font-family:"Cinzel",serif;font-size:22px;letter-spacing:.06em;margin:0 0 4px;
  border-bottom:2px solid var(--bd);padding-bottom:6px;}
section.family>.blurb{color:var(--muted);font-size:15.5px;font-style:italic;margin:6px 0 12px;max-width:840px;}
.ideas{margin:0 0 18px;}
details.idea{background:var(--panel);border:1px solid var(--bd);border-radius:9px;margin:6px 0;overflow:hidden;}
details.idea summary{cursor:pointer;padding:9px 14px;font-size:14.5px;font-weight:600;list-style:none;}
details.idea summary::before{content:"❧ ";color:var(--gold);}
details.idea[open] summary{border-bottom:1px solid var(--bd);background:#f5edd8;}
details.idea .body{padding:10px 16px 12px;font-size:14.5px;line-height:1.55;}
details.idea .body p.more{margin:8px 0 0;font-size:13px;color:var(--muted);border-top:1px dashed var(--bd);padding-top:7px;}
nav.jump{position:sticky;top:0;z-index:9;background:rgba(242,234,216,.94);backdrop-filter:blur(3px);
  border-bottom:1px solid var(--bd);display:flex;gap:4px;justify-content:center;flex-wrap:wrap;padding:8px 10px;}
nav.jump a{font-size:12.5px;letter-spacing:.05em;text-decoration:none;color:var(--ink);
  border:1px solid transparent;border-radius:999px;padding:4px 11px;}
nav.jump a:hover{border-color:var(--bd);background:var(--panel);}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;}
a.card{display:block;background:var(--panel);border:1px solid var(--bd);border-radius:12px;overflow:hidden;
  text-decoration:none;color:var(--ink);box-shadow:0 6px 18px rgba(60,40,10,.10);transition:transform .15s,box-shadow .15s;}
a.card:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(60,40,10,.18);}
a.card svg{display:block;width:100%;height:auto;border-bottom:1px solid var(--bd);}
a.card .pad{padding:11px 14px 13px;}
a.card h3{font-family:"Cinzel",serif;font-size:15.5px;margin:0 0 2px;line-height:1.25;}
a.card .st{font-size:12.5px;color:var(--muted);font-style:italic;margin:0 0 7px;line-height:1.35;}
a.card .stats{font-size:11.5px;color:var(--muted);letter-spacing:.03em;}
a.card .kind{display:inline-block;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);
  border:1px solid var(--bd);border-radius:999px;padding:2px 8px;margin-bottom:7px;}
.stylebadge{display:inline-flex;align-items:center;gap:5px;font-size:10px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);border:1px solid var(--bd);border-radius:999px;
  padding:2px 8px;margin-bottom:7px;}
.stylebadge .dot{width:10px;height:10px;border-radius:50%;border:2px solid;display:inline-block;}
.designnote{border-left:3px solid var(--accent);padding:10px 14px;background:var(--panel);
  font-size:14.5px;line-height:1.5;margin:14px 0;max-width:860px;}
.swatches{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:16px auto 0;}
.swatches .sw{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted);
  letter-spacing:.04em;}
.swatches .sq{width:22px;height:14px;border-radius:3px;border:1px solid var(--bd);display:inline-block;}
.relgroup{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin:8px 0;}
.relgroup .rl{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
  min-width:96px;font-weight:600;}
a.relchip{display:inline-block;background:var(--panel);border:1px solid var(--bd);border-radius:999px;
  padding:4px 12px;font-size:13px;text-decoration:none;color:var(--ink);}
a.relchip:hover{border-color:var(--accent);}
footer{color:var(--muted);text-align:center;font-size:12.5px;padding:30px 20px 40px;font-style:italic;}
/* detail + doc pages */
.crumb{font-size:13.5px;margin:18px 0 8px;}
.mapframe{width:100%;height:72vh;border:1px solid var(--bd);border-radius:12px;background:#fff;
  box-shadow:0 10px 30px rgba(60,40,10,.15);}
.metabar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 4px;font-size:13.5px;}
.metabar a{background:var(--panel);border:1px solid var(--bd);border-radius:8px;padding:6px 12px;text-decoration:none;}
.prose{background:var(--panel);border:1px solid var(--bd);border-radius:12px;padding:22px 28px;margin:16px 0;
  line-height:1.6;font-size:16px;}
.prose h1{font-family:"Cinzel",serif;font-size:26px;}
.prose h2{font-family:"Cinzel",serif;font-size:19px;border-bottom:1px solid var(--bd);padding-bottom:4px;margin-top:28px;}
.prose h3{font-size:16.5px;}
.prose pre{background:#2b2416;color:#f0e6c8;padding:12px 14px;border-radius:8px;overflow:auto;font-size:13px;}
.prose code{background:#ece0c2;border-radius:4px;padding:1px 5px;font-size:.9em;}
.prose pre code{background:none;padding:0;}
.prose table{border-collapse:collapse;width:100%;font-size:14.5px;}
.prose th,.prose td{border:1px solid var(--bd);padding:6px 9px;text-align:left;}
.prose th{background:#f0e5c8;font-family:"Cinzel",serif;font-size:12.5px;letter-spacing:.04em;}
.provnote{border-left:3px solid var(--gold);padding:8px 14px;background:var(--panel);
  font-size:14px;color:var(--muted);font-style:italic;margin:14px 0;}
@media (prefers-reduced-motion: reduce){a.card{transition:none;}}
"""

HEAD = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=EB+Garamond:ital@0;1&display=swap" rel="stylesheet">
<style>{css}</style></head><body>"""

FOOT = ('<footer>MAPRESEARCH — an R&amp;D project in honest, directable historical cartography. '
        'Borders are approximate; absence is absence of record; the maps say so.</footer></body></html>')


def idea_details(ids, open_first=False):
    out = []
    for k, iid in enumerate(ids):
        title, body = IDEAS[iid]
        op = " open" if (open_first and k == 0) else ""
        links = IDEA_LINKS.get(iid, [])
        more = ""
        if links:
            more = ('<p class="more">Read more: '
                    + " · ".join(f'<a href="{href}">{H.escape(label)}</a>' for label, href in links)
                    + "</p>")
        out.append(f'<details class="idea"{op}><summary>{H.escape(title)}</summary>'
                   f'<div class="body">{body}{more}</div></details>')
    return "\n".join(out)


def style_badge(theme):
    t = PALETTE[theme]
    return (f'<span class="stylebadge"><span class="dot" style="background:{t["land"]};'
            f'border-color:{t["accent"]}"></span>{H.escape(THEME_LABEL[theme])}</span>')


def card(e):
    return (f'<a class="card" href="{e["slug"]}.html">{e["svg"]}<div class="pad">'
            f'<span class="kind">{H.escape(e["kind"])}</span> {style_badge(e["theme"])}'
            f'<h3>{H.escape(e["title"])}</h3>'
            f'<p class="st">{H.escape(e["subtitle"])}</p>'
            f'<div class="stats">{H.escape(e["stats"])}</div></div></a>')


def detail_page(e):
    ids = FAMILY_IDEAS[e["family"]]
    note = f'<p style="font-size:16px;line-height:1.55;max-width:860px">{H.escape(e["note"])}</p>' if e["note"] else ""
    prov = f'<div class="provnote">{H.escape(e["prov"])}</div>' if e["prov"] else ""
    direc = f'<p style="font-size:13.5px;color:var(--muted)">Directive: <em>{H.escape(e["directive"])}</em></p>' if e["directive"] else ""
    design = ""
    if e.get("design") or e.get("tools"):
        dn = f'<p style="margin:6px 0 0">{H.escape(e["design"])}</p>' if e.get("design") else ""
        tl = (f'<p style="margin:8px 0 0;font-size:12.5px;color:var(--muted)"><b>Tools:</b> '
              f'{H.escape(e["tools"])}</p>') if e.get("tools") else ""
        design = (f'<div class="designnote"><b>Design — {H.escape(THEME_LABEL[e["theme"]])}.</b>{dn}{tl}</div>')
    REL_LABEL = {"era": "Same era", "topic": "Same topics", "figure": "Same figures", "region": "Same regions"}
    relblock = ""
    if e.get("related"):
        groups = []
        for key in ("era", "topic", "figure", "region"):
            xs = e["related"].get(key)
            if not xs:
                continue
            chips = "".join(f'<a class="relchip" href="{x["slug"]}.html">{H.escape(x["title"])}</a>' for x in xs)
            groups.append(f'<div class="relgroup"><span class="rl">{REL_LABEL[key]}</span>{chips}</div>')
        if groups:
            relblock = ('<h2 style="font-family:Cinzel,serif;font-size:19px;margin-top:26px">Browse related maps</h2>'
                        + "".join(groups))
    return (HEAD.format(title=H.escape(e["title"]) + " — Map Gallery", css=CSS)
            + '<main><div class="crumb"><a href="index.html">← All maps</a></div>'
            + f'<h1 style="font-family:Cinzel,serif;margin:6px 0 2px">{H.escape(e["title"])}</h1>'
            + f'<p style="font-style:italic;color:var(--muted);margin:0 0 12px">{H.escape(e["subtitle"])}</p>'
            + f'<iframe class="mapframe" src="{e["map_url"]}" title="{H.escape(e["title"])}" loading="lazy"></iframe>'
            + f'<div class="metabar"><a href="{e["map_url"]}" target="_blank">Open full screen ↗</a>'
            + f'<a href="{e["spec_url"]}" target="_blank">View the recipe (JSON) ↗</a>'
            + f'<span style="align-self:center;color:var(--muted)">{H.escape(e["stats"])}</span></div>'
            + note + design + direc + prov + relblock
            + '<h2 style="font-family:Cinzel,serif;font-size:19px;margin-top:26px">Ideas this map is trying</h2>'
            + '<div class="ideas">' + idea_details(ids, open_first=True) + "</div></main>" + FOOT)


def doc_page(md_path, title):
    body = md_to_html(md_path.read_text(encoding="utf-8"))
    return (HEAD.format(title=title, css=CSS)
            + '<main><div class="crumb"><a href="index.html">← All maps</a></div>'
            + f'<div class="prose">{body}</div></main>' + FOOT)


def index_page(cat):
    n_data = sum(1 for e in cat if e["kind"] == "corpus data map")
    n_j = sum(1 for e in cat if e["family"] == "journey")
    n_n = sum(1 for e in cat if e["family"] == "network")
    swatches = "".join(
        f'<span class="sw"><span class="sq" style="background:linear-gradient(135deg,{PALETTE[k]["land"]} 55%,{PALETTE[k]["accent"]} 55%)"></span>{H.escape(v)}</span>'
        for k, v in THEME_LABEL.items())
    parts = [HEAD.format(title="The Map Gallery — MAPRESEARCH", css=CSS)]
    parts.append(f"""<header class="site">
<h1>The Map Gallery</h1>
<p class="sub">Every map the toolkit has built — {len(cat)} in all — each one an experiment in
honest, directable historical cartography. Six visual styles are distributed deliberately
across the fleet (the badge on each card says which, and each map's page explains why).
Click a card for the living map; open the accordions under each family for the ideas.</p>
<div class="counts">{n_data} corpus data maps · {n_j} curated journeys · {n_n} curated networks</div>
<div class="swatches">{swatches}</div>
<nav class="docs">
<a href="../tour/index.html"><b>The Guided Tour</b>9 scrollytelling chapters — start here</a>
<a href="manual.html"><b>Instruction Manual</b>directing, reading &amp; sharing the maps</a>
<a href="toolkit.html"><b>Developers Toolkit</b>contracts, engines, APIs, extending</a>
<a href="nextsteps.html"><b>Next Steps</b>where the project goes from here</a>
</nav></header>""")
    order = ["example", "study", "era", "century", "theme", "figure", "region", "journey", "network"]
    jump = "".join(f'<a href="#fam-{fam}">{H.escape(FAMILY_META[fam][0])}</a>'
                   for fam in order if any(e["family"] == fam for e in cat))
    parts.append(f'<nav class="jump" aria-label="Map families">{jump}</nav><main>')
    for fam in order:
        entries = [e for e in cat if e["family"] == fam]
        if not entries:
            continue
        title, blurb = FAMILY_META[fam]
        parts.append(f'<section class="family" id="fam-{fam}"><h2>{H.escape(title)}</h2>'
                     f'<p class="blurb">{H.escape(blurb)}</p>'
                     f'<div class="ideas">{idea_details(FAMILY_IDEAS[fam])}</div>'
                     f'<div class="grid">{"".join(card(e) for e in entries)}</div></section>')
    parts.append("</main>" + FOOT)
    return "".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat = collect()
    compute_related(cat)
    (OUT / "index.html").write_text(index_page(cat), encoding="utf-8")
    for e in cat:
        (OUT / f"{e['slug']}.html").write_text(detail_page(e), encoding="utf-8")
    (OUT / "toolkit.html").write_text(doc_page(ROOT / "TOOLKIT.md", "Developers Toolkit — MAPRESEARCH"), encoding="utf-8")
    (OUT / "manual.html").write_text(doc_page(ROOT / "MANUAL.md", "Instruction Manual — MAPRESEARCH"), encoding="utf-8")
    (OUT / "nextsteps.html").write_text(doc_page(ROOT / "NEXTSTEPS.md", "Next Steps — MAPRESEARCH"), encoding="utf-8")
    fams = {}
    for e in cat:
        fams[e["family"]] = fams.get(e["family"], 0) + 1
    print(f"Gallery: {len(cat)} maps -> gallery/ ({', '.join(f'{v} {k}' for k, v in fams.items())})")
    print(f"  + index.html, toolkit.html, manual.html, nextsteps.html")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_map.py — the MapSpec compiler (v2).

Reads a *.mapspec.json + the ALCHEMYTIMELINEMAP data.json, filters/joins, and
emits a self-contained MapLibre GL + deck.gl HTML map with:
  - a runtime THEME ENGINE (copperplate / illuminated / atlas / noir) + font picker
  - LAYERED controls: curated lenses, a search-style filter bar, a power-user drawer
  - layers: points, transmission arcs, text labels, density heatmap
  - a time scrubber, and a postMessage / URL-param API so the map is embeddable and
    drivable by the scrollytelling tour.

Colour is assigned at RUNTIME (in JS) from the active theme's palette, so switching
theme or color-by re-skins instantly. Python only emits each point's category values.

Usage:
    python build_map.py <mapspec.json> [--data <data.json>] [--out <out.html>]
"""
from __future__ import annotations
import argparse, json, html, re
from pathlib import Path

# ---------------------------------------------------------------- data helpers

def parse_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            p = json.loads(v)
            return p if isinstance(p, list) else []
        except Exception:
            return [x.strip() for x in v.split(",") if x.strip()]
    return []

FALLBACK_LOCATIONS = {
    "amsterdam": (52.3676, 4.9041, "Low Countries", "Amsterdam"),
    "antwerp": (51.2194, 4.4025, "Low Countries", "Antwerp"),
    "athens": (37.9838, 23.7275, "Greece", "Athens"),
    "bruges": (51.2093, 3.2247, "Low Countries", "Bruges"),
    "cambridge": (52.2053, 0.1218, "England", "Cambridge"),
    "canterbury": (51.2802, 1.0789, "England", "Canterbury"),
    "cluny": (46.4336, 4.6602, "France", "Cluny"),
    "constantinople": (41.0082, 28.9784, "Byzantium", "Constantinople"),
    "fulda": (50.5558, 9.6836, "Germany", "Fulda"),
    "lisbon": (38.7223, -9.1393, "Iberia", "Lisbon"),
    "madrid": (40.4168, -3.7038, "Iberia", "Madrid"),
    "monte-cassino": (41.4917, 13.8116, "Italy", "Monte Cassino"),
    "salerno": (40.6824, 14.7681, "Italy", "Salerno"),
    "ven-island": (55.9125, 12.7211, "Denmark/Sweden", "Ven Island (Hven)"),
}
LOCATION_ALIASES = {"rayy": "ray", "basel": "basle"}

ERA_RANGES = {
    "ANTIQUITY": (-9999, 300), "LATE_ANTIQUE": (300, 600), "MEDIEVAL": (600, 1450),
    "RENAISSANCE": (1450, 1550), "EARLY_MODERN": (1550, 1700), "ENLIGHTENMENT": (1700, 9999),
}
ERA_LABEL = {
    "ANTIQUITY": "Antiquity", "LATE_ANTIQUE": "Late Antique", "MEDIEVAL": "Medieval",
    "RENAISSANCE": "Renaissance", "EARLY_MODERN": "Early Modern", "ENLIGHTENMENT": "Enlightenment",
}


def era_for_year(y):
    if not isinstance(y, int):
        return None
    for k, (a, b) in ERA_RANGES.items():
        if a <= y < b:
            return k
    return None


def norm_slug(s):
    s = (s or "").strip()
    return LOCATION_ALIASES.get(s, s)


def build_location_index(data):
    idx = {}
    for loc in data.get("locations", []):
        if not loc.get("slug"):
            continue
        rec = {"slug": loc["slug"], "name": loc.get("place_name") or loc["slug"],
               "lat": loc.get("latitude"), "lon": loc.get("longitude"),
               "region": loc.get("region") or "", "significance": loc.get("alchemical_significance") or ""}
        idx[loc["slug"]] = rec
        idx[norm_slug(loc["slug"])] = rec
    for slug, (lat, lon, region, name) in FALLBACK_LOCATIONS.items():
        idx.setdefault(slug, {"slug": slug, "name": name, "lat": lat, "lon": lon,
                              "region": region, "significance": ""})
    return idx


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("&nbsp;", " ").strip()

# ---------------------------------------------------------------- spec validation

# Legacy schema style names map onto the four runtime themes.
STYLE_TO_THEME = {
    "parchment": "illuminated", "sepia-toner": "copperplate",
    "muted-vector": "atlas", "modern-osm": "atlas",
    "atlas": "atlas", "copperplate": "copperplate",
    "illuminated": "illuminated", "noir": "noir",
    "woodcut": "woodcut", "lapis": "lapis",
}
VALID_LAYERS = {"points", "flows", "time-animation", "heatmap", "network", "labels"}
VALID_COLOR_BY = {"region", "theme", "era", "person"}
KNOWN_TOP = {"title", "subtitle", "directive", "scope", "render", "narrative"}
KNOWN_SCOPE = {"year_start", "year_end", "era", "region_bbox", "regions", "themes",
               "persons", "texts", "review_status"}
KNOWN_RENDER = {"engine", "basemap", "layers", "color_by", "legend"}


def validate_spec(spec):
    """Cheap dependency-free MapSpec validation. Returns (errors, warnings)."""
    errors, warnings = [], []
    if not isinstance(spec, dict):
        return ["spec must be a JSON object"], []
    if not spec.get("title"):
        errors.append("'title' is required")
    scope = spec.get("scope")
    render = spec.get("render")
    if not isinstance(scope, dict):
        errors.append("'scope' (object) is required")
        scope = {}
    if not isinstance(render, dict):
        errors.append("'render' (object) is required")
        render = {}
    for k in spec:
        if k not in KNOWN_TOP:
            warnings.append(f"unknown top-level key '{k}' (ignored)")
    for k in scope:
        if k not in KNOWN_SCOPE:
            warnings.append(f"unknown scope key '{k}' (ignored)")
    for k in render:
        if k not in KNOWN_RENDER:
            warnings.append(f"unknown render key '{k}' (ignored)")
    ys, ye = scope.get("year_start"), scope.get("year_end")
    if ys is not None and ye is not None and ys > ye:
        errors.append(f"scope.year_start ({ys}) > scope.year_end ({ye})")
    bbox = scope.get("region_bbox")
    if bbox is not None:
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox)):
            errors.append("scope.region_bbox must be [west, south, east, north] numbers")
        elif bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            errors.append(f"scope.region_bbox is inverted: {bbox} (want west<east, south<north)")
    for e in scope.get("era") or []:
        if e not in ERA_RANGES:
            errors.append(f"unknown era '{e}' (valid: {' '.join(ERA_RANGES)})")
    for l in render.get("layers") or []:
        if l not in VALID_LAYERS:
            errors.append(f"unknown layer '{l}' (valid: {' '.join(sorted(VALID_LAYERS))})")
    cb = render.get("color_by")
    if cb is not None and cb not in VALID_COLOR_BY:
        errors.append(f"unknown color_by '{cb}' (valid: {' '.join(sorted(VALID_COLOR_BY))})")
    basemap = render.get("basemap") or {}
    style = basemap.get("style")
    if style is not None and style not in STYLE_TO_THEME:
        errors.append(f"unknown basemap.style '{style}' (valid: {' '.join(sorted(STYLE_TO_THEME))})")
    byear = basemap.get("historical_boundaries_year")
    if byear is not None and not isinstance(byear, int):
        errors.append("basemap.historical_boundaries_year must be an integer year")
    return errors, warnings


def check_provenance(spec):
    """The historian's hard line: no provenance note, no map."""
    note = (spec.get("narrative") or {}).get("provenance_note") or ""
    return bool(note.strip())

# ---------------------------------------------------------------- base geography

BASEGEO_DIR = Path(__file__).resolve().parents[1] / "data" / "basegeo"
_BASEGEO_CACHE = None


def load_basegeo():
    """Embedded physical geography (Natural Earth: land/lakes/rivers) so every
    map draws real coastlines with no CDN basemap. None if cache missing."""
    global _BASEGEO_CACHE
    if _BASEGEO_CACHE is not None:
        return _BASEGEO_CACHE or None
    geo = {}
    for name in ("land", "lakes", "rivers"):
        p = BASEGEO_DIR / f"{name}.geojson"
        if not p.exists():
            _BASEGEO_CACHE = False
            return None
        gj = json.loads(p.read_text(encoding="utf-8"))
        geo[name] = {"type": "FeatureCollection", "features": gj.get("features", [])}
    _BASEGEO_CACHE = geo
    return geo

# ---------------------------------------------------------------- historical boundaries

BOUNDS_DIR = Path(__file__).resolve().parents[1] / "data" / "boundaries"


def load_boundaries(year):
    """Load the cached historical-basemaps file nearest the requested year.
    Returns None (with no error) if no boundary cache exists at all."""
    avail = []
    for p in BOUNDS_DIR.glob("world_*.geojson"):
        m = re.match(r"world_(\d+)\.geojson$", p.name)
        if m:
            avail.append((int(m.group(1)), p))
    if not avail:
        return None
    snap_year, path = min(avail, key=lambda t: abs(t[0] - year))
    gj = json.loads(path.read_text(encoding="utf-8"))
    return {
        "requested_year": year, "year": snap_year,
        "attribution": gj.get("attribution", ""),
        "geojson": {"type": "FeatureCollection", "features": gj.get("features", [])},
    }

# ---------------------------------------------------------------- filtering

def event_matches(ev, scope):
    y = ev.get("date_start_year")
    yr = y if isinstance(y, int) else None
    if scope.get("year_start") is not None and (yr is None or yr < scope["year_start"]):
        return False
    if scope.get("year_end") is not None and (yr is None or yr > scope["year_end"]):
        return False
    eras = scope.get("era") or []
    if eras and not any(ERA_RANGES.get(e, (0, 0))[0] <= (yr if yr is not None else -10**9) < ERA_RANGES.get(e, (0, 0))[1] for e in eras):
        return False
    regions = set(scope.get("regions") or [])
    if regions and ev.get("region") not in regions:
        return False
    themes = set(scope.get("themes") or [])
    if themes and not (set(parse_list(ev.get("concepts_involved"))) & themes):
        return False
    persons = set(scope.get("persons") or [])
    if persons and not (set(parse_list(ev.get("persons_involved"))) & persons):
        return False
    texts = set(scope.get("texts") or [])
    if texts and not (set(parse_list(ev.get("texts_involved"))) & texts):
        return False
    rs = set(scope.get("review_status") or [])
    if rs and ev.get("review_status") not in rs:
        return False
    return True

# ---------------------------------------------------------------- compile

def compile_spec(spec, data):
    scope = spec.get("scope", {})
    locidx = build_location_index(data)
    persons_by_slug = {p["slug"]: p for p in data.get("persons", [])}
    concepts_by_slug = {c["slug"]: c for c in data.get("concepts", [])}
    theme_order = scope.get("themes") or []

    matching = [e for e in data.get("events", []) if event_matches(e, scope)]

    def theme_label(slug):
        c = concepts_by_slug.get(slug)
        return c["label"] if c else slug.replace("-", " ").title()

    def primary_theme(ev):
        evt = parse_list(ev.get("concepts_involved"))
        for t in theme_order:
            if t in evt:
                return theme_label(t)
        return theme_label(evt[0]) if evt else "(untagged)"

    # ---- points: aggregate matching events by location ----
    points, missing = {}, set()
    for e in matching:
        slug = norm_slug(e.get("location_slug"))
        loc = locidx.get(slug)
        if not loc or loc.get("lat") is None:
            missing.add(e.get("location_slug"))
            continue
        p = points.get(slug)
        if not p:
            p = {"name": loc["name"], "lon": loc["lon"], "lat": loc["lat"], "region": loc["region"],
                 "significance": loc["significance"], "events": []}
            points[slug] = p
        p["events"].append({"year": e.get("date_start_year"), "date_label": e.get("date_label") or "",
                            "title": strip_html(e.get("summary") or e.get("description") or "")[:160],
                            "theme": primary_theme(e)})

    point_list = []
    for p in points.values():
        years = [ev["year"] for ev in p["events"] if isinstance(ev["year"], int)]
        # dominant theme & era for this point
        tcount = {}
        for ev in p["events"]:
            tcount[ev["theme"]] = tcount.get(ev["theme"], 0) + 1
        dom_theme = max(tcount, key=tcount.get) if tcount else "(untagged)"
        rep_year = min(years) if years else None
        point_list.append({
            "name": p["name"], "lon": p["lon"], "lat": p["lat"], "region": p["region"] or "(unknown)",
            "significance": p["significance"], "count": len(p["events"]),
            "year_min": min(years) if years else None, "year_max": max(years) if years else None,
            "theme": dom_theme, "era": ERA_LABEL.get(era_for_year(rep_year), "(undated)"),
            "events": sorted(p["events"], key=lambda x: x["year"] if isinstance(x["year"], int) else 0),
        })

    # ---- arcs: person itineraries (transmission as motion) ----
    person_scope = scope.get("persons") or []
    person_events = {}
    for e in matching:
        slug = norm_slug(e.get("location_slug"))
        loc = locidx.get(slug)
        if not loc or loc.get("lat") is None:
            continue
        for ps in parse_list(e.get("persons_involved")):
            if person_scope and ps not in person_scope:
                continue
            person_events.setdefault(ps, []).append((e.get("date_start_year"), slug, loc))

    arcs = []
    for ps, evs in person_events.items():
        evs = sorted([x for x in evs if isinstance(x[0], int)], key=lambda x: x[0])
        person = persons_by_slug.get(ps)
        pname = person["name"] if person else ps.replace("-", " ").title()
        for (y1, s1, l1), (y2, s2, l2) in zip(evs, evs[1:]):
            if s1 == s2:
                continue
            arcs.append({"from": [l1["lon"], l1["lat"]], "to": [l2["lon"], l2["lat"]],
                         "person": pname, "year": y2, "region": l2["region"] or "(unknown)",
                         "label": f"{pname}: {l1['name']} → {l2['name']} ({y2})"})
    if not person_scope and len(arcs) > 300:
        arcs = sorted(arcs, key=lambda a: a["year"])[:300]

    years_all = [ev["year"] for p in point_list for ev in p["events"] if isinstance(ev["year"], int)]
    year_min, year_max = (min(years_all), max(years_all)) if years_all else (0, 0)

    bbox = scope.get("region_bbox")
    if bbox and len(bbox) == 4:
        center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
    elif point_list:
        center = [sum(p["lon"] for p in point_list) / len(point_list),
                  sum(p["lat"] for p in point_list) / len(point_list)]
    else:
        center = [15, 45]

    # how many matching events each requested theme actually carries —
    # so an author learns at compile time that a lens will come up empty
    theme_counts = {}
    for t in theme_order:
        theme_counts[t] = sum(1 for e in matching if t in parse_list(e.get("concepts_involved")))

    basemap = spec.get("render", {}).get("basemap", {}) or {}
    initial_theme = STYLE_TO_THEME.get(basemap.get("style") or "", "atlas")
    boundaries = None
    byear = basemap.get("historical_boundaries_year")
    if isinstance(byear, int):
        boundaries = load_boundaries(byear)

    return {
        "title": spec.get("title", "Untitled Map"), "subtitle": spec.get("subtitle", ""),
        "directive": spec.get("directive", ""), "narrative": spec.get("narrative", {}),
        "render": spec.get("render", {}), "points": point_list, "arcs": arcs,
        "color_by": spec.get("render", {}).get("color_by", "theme"),
        "initial_theme": initial_theme,
        "initial_labels": bool(basemap.get("show_modern_labels", False)),
        "boundaries": boundaries,
        "basegeo": load_basegeo(),
        "year_min": year_min, "year_max": year_max, "center": center, "bbox": bbox,
        "stats": {"events": len(matching), "locations": len(point_list), "arcs": len(arcs),
                  "missing_locations": sorted(x for x in missing if x),
                  "theme_counts": theme_counts},
    }

# ---------------------------------------------------------------- HTML

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@9.0.33/dist.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=EB+Garamond:ital@0;1&family=IM+Fell+English:ital@0;1&family=Inter:wght@400;600&family=Spectral:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root{
    --page:#fff; --ink:#1f2937; --muted:#6b7280; --panel:#ffffff; --panel-bd:#e5e7eb;
    --accent:#7a4a25; --chip:#f1efe9; --font:"Spectral",Georgia,serif; --head:"Spectral",Georgia,serif;
    --shadow:0 12px 34px rgba(40,30,15,.18);
  }
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;font-family:var(--font);color:var(--ink);background:var(--page);}
  #map{position:absolute;inset:0;background:var(--page);}
  .card{background:var(--panel);border:1px solid var(--panel-bd);border-radius:12px;box-shadow:var(--shadow);}
  button,select{font-family:var(--font);color:var(--ink);}
  /* title panel */
  #panel{position:absolute;top:14px;left:14px;max-width:330px;padding:15px 17px;z-index:6;
    max-height:84vh;overflow:auto;}
  #panel h1{font-family:var(--head);font-size:18px;margin:0 0 2px;line-height:1.2;}
  #panel h2{font-size:12.5px;font-weight:normal;font-style:italic;color:var(--muted);margin:0 0 9px;}
  #panel p{font-size:12.5px;line-height:1.5;margin:7px 0;}
  .stats{font-size:11px;color:var(--muted);margin:6px 0;}
  .legend{margin-top:9px;border-top:1px solid var(--panel-bd);padding-top:8px;}
  .legend .ttl{font-weight:600;margin-bottom:4px;font-size:12px;}
  .legend div.row{display:flex;align-items:center;font-size:12px;margin:3px 0;}
  .legend span.sw{width:13px;height:13px;border-radius:50%;margin-right:8px;border:1px solid #00000022;flex:none;}
  .prov{font-size:10.5px;color:var(--muted);border-top:1px solid var(--panel-bd);padding-top:8px;margin-top:9px;}
  /* control stack top-right */
  #controls{position:absolute;top:14px;right:14px;z-index:6;width:268px;display:flex;flex-direction:column;gap:10px;
    max-height:88vh;overflow:auto;}
  #controls .card{padding:11px 12px;}
  .grp-title{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:0 0 7px;font-weight:600;}
  .lenses{display:flex;flex-wrap:wrap;gap:6px;}
  .lens{flex:1 1 auto;border:1px solid var(--panel-bd);background:var(--chip);border-radius:999px;
    padding:6px 10px;font-size:11.5px;cursor:pointer;}
  .lens.active{background:var(--accent);color:#fff;border-color:var(--accent);}
  .field{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:7px 0;font-size:12px;}
  .field select{flex:1;padding:4px 6px;border:1px solid var(--panel-bd);border-radius:7px;background:var(--page);}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;}
  .chip{border:1px solid var(--panel-bd);background:var(--chip);border-radius:7px;padding:5px 9px;font-size:11.5px;cursor:pointer;}
  .chip.on{background:var(--accent);color:#fff;border-color:var(--accent);}
  details.adv{border-top:1px solid var(--panel-bd);margin-top:6px;padding-top:6px;}
  details.adv summary{cursor:pointer;font-size:11.5px;color:var(--muted);font-weight:600;}
  .slider{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:11.5px;}
  .slider input{flex:1;}
  /* time bar */
  #timebar{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:6;padding:9px 15px;
    display:flex;align-items:center;gap:12px;width:min(620px,84vw);}
  #timebar input{flex:1;}
  #yearLabel{font-weight:700;min-width:120px;font-size:13px;}
  #playBtn,#pngBtn,#linkBtn{cursor:pointer;border:1px solid var(--panel-bd);background:var(--chip);border-radius:7px;padding:5px 12px;font-size:13px;white-space:nowrap;}
  #pngBtn,#linkBtn{font-size:12px;padding:5px 9px;}
  .maplibregl-popup-content{font-family:var(--font);max-width:300px;border-radius:10px;}
  body.ui-min #panel,body.ui-min #controls{display:none;}
  body.ui-min #timebar{bottom:10px;}
  /* mobile: panel + controls are both fixed-width absolutely-positioned boxes
     that collide on any viewport under ~625px wide. Stack them instead, each
     capped to a fraction of viewport height (they already scroll internally),
     and let the time bar wrap onto two rows rather than overflow sideways. */
  @media (max-width:760px){
    #panel{left:8px;right:8px;top:8px;max-width:none;width:auto;max-height:26vh;}
    #controls{left:8px;right:8px;top:calc(26vh + 20px);width:auto;
      max-height:calc(100vh - 26vh - 118px);}
    #timebar{left:8px;right:8px;bottom:8px;width:auto;transform:none;
      flex-wrap:wrap;justify-content:center;row-gap:6px;}
    #timebar input[type="range"]{flex:1 1 100%;order:3;}
    #yearLabel{min-width:0;font-size:12px;}
  }
</style>
</head>
<body>
<div id="map"></div>

<div id="panel" class="card" role="region" aria-label="About this map">
  <h1>__TITLE__</h1>
  <h2>__SUBTITLE__</h2>
  __INTRO__
  <div class="stats">__STATS__</div>
  <div class="legend" id="legend"></div>
  __PROV__
</div>

<div id="controls" role="region" aria-label="Map controls">
  <div class="card">
    <div class="grp-title">Lenses — one-click views</div>
    <div class="lenses" id="lenses"></div>
  </div>
  <div class="card">
    <div class="grp-title">Appearance &amp; filters</div>
    <div class="field"><label>Theme</label>
      <select id="selTheme" aria-label="Visual theme">
        <option value="atlas">Modern Atlas</option>
        <option value="copperplate">Copperplate Engraving</option>
        <option value="illuminated">Illuminated Manuscript</option>
        <option value="noir">Alchemical Noir</option>
        <option value="woodcut">Woodcut &amp; Rubric</option>
        <option value="lapis">Lapis &amp; Gold</option>
      </select></div>
    <div class="field"><label>Typeface</label>
      <select id="selFont">
        <option value="theme">Theme default</option>
        <option value='"EB Garamond",Georgia,serif'>EB Garamond</option>
        <option value='"Spectral",Georgia,serif'>Spectral</option>
        <option value='"IM Fell English",Georgia,serif'>IM Fell English</option>
        <option value='"Cinzel",Georgia,serif'>Cinzel</option>
        <option value='"Inter",system-ui,sans-serif'>Inter (sans)</option>
      </select></div>
    <div class="field"><label>Colour by</label>
      <select id="selColor">
        <option value="theme">Theme</option>
        <option value="region">Region</option>
        <option value="era">Era</option>
      </select></div>
    <div class="grp-title" style="margin-top:9px">Layers</div>
    <div class="chips" id="layerChips"></div>
    <details class="adv">
      <summary>Advanced</summary>
      <div class="slider"><label>Arc width</label><input id="sArc" type="range" min="0.5" max="6" step="0.5"></div>
      <div class="slider"><label>Point size</label><input id="sPoint" type="range" min="0.5" max="3" step="0.25"></div>
      <div class="slider"><label>Opacity</label><input id="sOpac" type="range" min="0.2" max="1" step="0.05"></div>
      <div class="chips">
        <div class="chip" data-adv="legend">Legend</div>
        <div class="chip" data-adv="tooltipRich">Rich tooltips</div>
      </div>
    </details>
  </div>
</div>

<div id="timebar" class="card" role="group" aria-label="Time controls">
  <button id="playBtn" aria-label="Play or pause the time animation" aria-pressed="false">▶ Play</button>
  <span id="yearLabel" aria-live="polite"></span>
  <input id="slider" type="range" aria-label="Show events through year">
  <button id="pngBtn" title="Export the current view as a PNG image" aria-label="Export PNG">⤓ PNG</button>
  <button id="linkBtn" title="Copy a link that reproduces this exact view" aria-label="Copy view link">🔗 Link</button>
</div>

<script>
const DATA = __DATA__;

// ---------- theme tokens ----------
const THEMES = {
  atlas: { page:"#f7f6f3", ink:"#1f2937", muted:"#6b7280", panel:"#ffffff", panelBd:"#e5e7eb",
    accent:"#3f6f8f", chip:"#eef1f3", font:'"Spectral",Georgia,serif', head:'"Spectral",Georgia,serif',
    water:"#cdd8dd", land:"#f0eee9", border:"#d8d2c6",
    palette:[[63,111,143],[176,92,53],[60,130,100],[150,110,40],[120,70,150],[150,55,70],[90,140,80],[200,110,60],[70,120,135],[110,100,55]] },
  copperplate: { page:"#efe7d3", ink:"#241c12", muted:"#6f6048", panel:"#f6efdc", panelBd:"#cbb98f",
    accent:"#5a3c1d", chip:"#e7dcc0", font:'"IM Fell English",Georgia,serif', head:'"IM Fell English",Georgia,serif',
    water:"#dde3da", land:"#e9e0c8", border:"#b59a6a",
    palette:[[60,44,28],[120,80,40],[90,70,45],[140,100,55],[70,55,35],[110,85,50],[95,72,40],[130,95,52],[80,62,38],[105,82,48]] },
  illuminated: { page:"#f4ead2", ink:"#3a1f12", muted:"#7a5a36", panel:"#faf2dc", panelBd:"#d8b465",
    accent:"#9c2b2b", chip:"#f0e2bf", font:'"EB Garamond",Georgia,serif', head:'"Cinzel",Georgia,serif',
    water:"#cfe0e6", land:"#f0e3c2", border:"#caa24e",
    palette:[[156,43,43],[182,140,40],[42,90,70],[120,50,120],[40,80,140],[150,80,30],[90,120,50],[170,60,90],[60,110,120],[140,100,40]] },
  noir: { page:"#0e0f12", ink:"#e9e2cf", muted:"#9aa0aa", panel:"#171a20", panelBd:"#2c3138",
    accent:"#c9a24b", chip:"#20242c", font:'"EB Garamond",Georgia,serif', head:'"Cinzel",Georgia,serif',
    water:"#11141a", land:"#1b1f27", border:"#333a44",
    palette:[[201,162,75],[180,200,210],[120,200,170],[200,120,160],[120,160,220],[220,150,90],[150,210,120],[230,120,120],[120,200,210],[200,180,120]] },
  woodcut: { page:"#f6efdc", ink:"#171310", muted:"#5f564a", panel:"#faf5e6", panelBd:"#171310",
    accent:"#a3231b", chip:"#ece3ca", font:'"IM Fell English",Georgia,serif', head:'"IM Fell English",Georgia,serif',
    water:"#e4ddc6", land:"#f3ecd6", border:"#171310",
    palette:[[23,19,16],[163,35,27],[70,60,50],[120,30,25],[40,35,30],[140,80,30],[90,80,70],[190,60,45],[55,48,40],[110,95,80]] },
  lapis: { page:"#101a30", ink:"#e8e4d4", muted:"#8d99b8", panel:"#16233f", panelBd:"#2c3d63",
    accent:"#d4af37", chip:"#1c2c4e", font:'"EB Garamond",Georgia,serif', head:'"Cinzel",Georgia,serif',
    water:"#0d1526", land:"#1d2c4f", border:"#3b4f7d",
    palette:[[212,175,55],[130,180,220],[220,220,230],[110,200,190],[220,140,100],[170,150,220],[240,200,120],[130,220,150],[230,120,140],[180,190,210]] },
};

// ---------- state ----------
const STATE = {
  theme:DATA.initial_theme||"atlas", font:"theme", colorBy:DATA.color_by||"theme", year:DATA.year_max,
  layers:{points:true, arcs:true, labels:true, heatmap:false, borders:!!DATA.boundaries},
  legend:true, tooltipRich:true,
  arcWidth:1.5, pointScale:1, opacity:0.85, lens:"transmission",
};
const REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const LENSES = {
  transmission:{label:"Transmission", layers:{points:true,arcs:true,labels:true,heatmap:false}, colorBy:"region"},
  lives:{label:"Lives", layers:{points:true,arcs:true,labels:true,heatmap:false}, colorBy:"region"},
  texts:{label:"Texts", layers:{points:true,arcs:false,labels:true,heatmap:false}, colorBy:"theme"},
  themes:{label:"Themes", layers:{points:true,arcs:false,labels:true,heatmap:false}, colorBy:"theme"},
  density:{label:"Density", layers:{points:false,arcs:false,labels:false,heatmap:true}, colorBy:"region"},
};

function qp(){ const u=new URLSearchParams(location.search); return {
  ui:u.get("ui"), theme:u.get("theme"), lens:u.get("lens"), year:u.get("year"),
  color:u.get("color"), layers:u.get("layers"), arcw:u.get("arcw"),
  pts:u.get("pts"), op:u.get("op"), font:u.get("font") }; }

// serialize the full view state into a shareable URL
function stateURL(){
  const u=new URL(location.href), p=u.searchParams;
  p.set("theme",STATE.theme);
  if(STATE.lens) p.set("lens",STATE.lens); else p.delete("lens");
  p.set("year",STATE.year); p.set("color",STATE.colorBy);
  p.set("layers",Object.keys(STATE.layers).filter(k=>STATE.layers[k]).join("."));
  p.set("arcw",STATE.arcWidth); p.set("pts",STATE.pointScale); p.set("op",STATE.opacity);
  if(document.body.classList.contains("ui-min")) p.set("ui","min"); else p.delete("ui");
  return u.toString();
}

// ---------- colour ----------
let legendKeys=[], keyIndex={};
function categoryOf(p){ return STATE.colorBy==="region"?p.region : STATE.colorBy==="era"?p.era : p.theme; }
function rebuildLegend(){
  const seen=[]; for(const p of DATA.points){ const k=categoryOf(p); if(!seen.includes(k)) seen.push(k); }
  legendKeys=seen; keyIndex={}; seen.forEach((k,i)=>keyIndex[k]=i);
  const pal=THEMES[STATE.theme].palette;
  const el=document.getElementById("legend");
  if(!STATE.legend){ el.innerHTML=""; return; }
  el.innerHTML='<div class="ttl">Colour: '+STATE.colorBy+'</div>'+
    seen.map((k,i)=>`<div class="row"><span class="sw" style="background:rgb(${pal[i%pal.length].join(',')})"></span>${k}</div>`).join("");
}
function colorOf(p){ const pal=THEMES[STATE.theme].palette; const i=keyIndex[categoryOf(p)]||0; return pal[i%pal.length]; }

// ---------- map ----------
// The basemap is fully local: a sea-coloured canvas + embedded Natural Earth
// land/lakes/rivers drawn as deck.gl layers. No CDN basemap dependency.
let map, overlay;
function baseStyle(){
  const t=THEMES[STATE.theme];
  return Promise.resolve({version:8,sources:{},
    layers:[{id:"background",type:"background",paint:{"background-color":t.water}}]});
}
function restyleBasemapLive(){
  const t=THEMES[STATE.theme];
  try{ map.setPaintProperty("background","background-color",t.water); }catch(e){}
}
function riverColor(t){
  // rivers must read as water but stay visible over land: lean toward the border tone
  const w=hexish(t.water), b=hexish(t.border);
  return [Math.round(w[0]*0.55+b[0]*0.45), Math.round(w[1]*0.55+b[1]*0.45), Math.round(w[2]*0.55+b[2]*0.45)];
}
function basegeoLayers(){
  if(!DATA.basegeo) return [];
  const t=THEMES[STATE.theme];
  return [
    new deck.GeoJsonLayer({id:"bg-land",data:DATA.basegeo.land,stroked:true,filled:true,
      getFillColor:[...hexish(t.land),255],getLineColor:[...hexish(t.border),200],
      getLineWidth:0.9,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-lakes",data:DATA.basegeo.lakes,stroked:true,filled:true,
      getFillColor:[...hexish(t.water),255],getLineColor:[...hexish(t.border),140],
      getLineWidth:0.6,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-rivers",data:DATA.basegeo.rivers,stroked:true,filled:false,
      getLineColor:[...riverColor(t),190],getLineWidth:0.8,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getLineColor:[STATE.theme]}}),
  ];
}

// ---------- theme application (CSS) ----------
function applyTheme(){
  const t=THEMES[STATE.theme], r=document.documentElement.style;
  r.setProperty("--page",t.page); r.setProperty("--ink",t.ink); r.setProperty("--muted",t.muted);
  r.setProperty("--panel",t.panel); r.setProperty("--panel-bd",t.panelBd); r.setProperty("--accent",t.accent);
  r.setProperty("--chip",t.chip); r.setProperty("--head",t.head);
  r.setProperty("--font", STATE.font==="theme"?t.font:STATE.font);
}

// ---------- layers ----------
function visiblePoints(){ return DATA.points.map(p=>{ const evs=p.events.filter(e=>e.year==null||e.year<=STATE.year); return {...p,vcount:evs.length}; }).filter(p=>p.vcount>0); }
function visibleArcs(){ return DATA.arcs.filter(a=>a.year==null||a.year<=STATE.year); }

function makeLayers(){
  const pts=visiblePoints(), t=THEMES[STATE.theme], L=[...basegeoLayers()];
  if(DATA.boundaries && STATE.layers.borders) L.push(new deck.GeoJsonLayer({id:"borders",
    data:DATA.boundaries.geojson, stroked:true, filled:false,
    getLineColor:[...hexish(t.accent),80], getLineWidth:1.1, lineWidthUnits:"pixels",
    pickable:true, updateTriggers:{getLineColor:[STATE.theme]}}));
  if(STATE.layers.heatmap) L.push(new deck.HeatmapLayer({id:"heat",data:pts,getPosition:d=>[d.lon,d.lat],getWeight:d=>d.vcount,radiusPixels:45,intensity:1,threshold:0.05}));
  if(STATE.layers.arcs) L.push(new deck.ArcLayer({id:"flows",data:visibleArcs(),getSourcePosition:d=>d.from,getTargetPosition:d=>d.to,
    getSourceColor:[...hexish(t.accent),120],getTargetColor:[...hexish(t.accent),210],getWidth:STATE.arcWidth,getHeight:0.4,pickable:true}));
  if(STATE.layers.points) L.push(new deck.ScatterplotLayer({id:"points",data:pts,getPosition:d=>[d.lon,d.lat],
    getRadius:d=>(5+Math.sqrt(d.vcount)*3)*STATE.pointScale,radiusUnits:"pixels",radiusMinPixels:4,
    getFillColor:d=>[...colorOf(d),Math.round(255*STATE.opacity)],getLineColor:(STATE.theme==="noir"||STATE.theme==="lapis")?[16,22,38,230]:[255,255,255,230],lineWidthMinPixels:1.2,stroked:true,pickable:true,
    updateTriggers:{getFillColor:[STATE.theme,STATE.colorBy,STATE.opacity],getRadius:[STATE.pointScale]}}));
  if(STATE.layers.labels) L.push(new deck.TextLayer({id:"labels",data:pts,getPosition:d=>[d.lon,d.lat],getText:d=>d.name,
    getSize:12,getColor:hexish(t.ink),getPixelOffset:[0,-14],fontFamily:"Georgia, serif",outlineWidth:2,outlineColor:hexish(t.page),fontSettings:{sdf:true},getAlignmentBaseline:"bottom",
    characterSet:LABEL_CHARS}));
  return L;
}
function hexish(h){ const m=h.replace("#",""); return [parseInt(m.substr(0,2),16),parseInt(m.substr(2,2),16),parseInt(m.substr(4,2),16)]; }
// Place names carry diacritics (Córdoba, Kraków, Třeboň…) that deck.gl's
// TextLayer default glyph set (plain ASCII) silently drops. Cover ASCII +
// Latin-1 Supplement + Latin Extended-A/B so accented labels render whole.
function charRange(a,b){ return Array.from({length:b-a+1},(_,i)=>String.fromCodePoint(a+i)); }
const LABEL_CHARS=[...charRange(32,126),...charRange(160,591)];

function render(){ overlay.setProps({layers:makeLayers()}); }

function setYear(y){ STATE.year=+y; document.getElementById("slider").value=STATE.year;
  document.getElementById("yearLabel").textContent="Through "+(STATE.year<0?(-STATE.year+" BCE"):STATE.year+" CE"); render(); }

function applyLens(name){ const l=LENSES[name]; if(!l) return; STATE.lens=name;
  STATE.layers={...l.layers, borders:STATE.layers.borders}; STATE.colorBy=l.colorBy;
  document.getElementById("selColor").value=STATE.colorBy;
  syncLayerChips(); syncLenses(); rebuildLegend(); render(); }

function syncLenses(){ document.querySelectorAll(".lens").forEach(b=>b.classList.toggle("active",b.dataset.lens===STATE.lens)); }
function syncLayerChips(){ document.querySelectorAll("#layerChips .chip").forEach(c=>c.classList.toggle("on",STATE.layers[c.dataset.layer])); }

// ---------- build UI ----------
function buildControls(){
  const lz=document.getElementById("lenses");
  lz.innerHTML=Object.entries(LENSES).map(([k,v])=>`<button class="lens" data-lens="${k}">${v.label}</button>`).join("");
  lz.addEventListener("click",e=>{ const b=e.target.closest(".lens"); if(b) applyLens(b.dataset.lens); });
  const lc=document.getElementById("layerChips");
  const layerKeys=["points","arcs","labels","heatmap"].concat(DATA.boundaries?["borders"]:[]);
  lc.innerHTML=layerKeys.map(k=>`<div class="chip" data-layer="${k}" role="button" tabindex="0">${k[0].toUpperCase()+k.slice(1)}</div>`).join("");
  lc.addEventListener("click",e=>{ const c=e.target.closest(".chip"); if(!c) return; STATE.layers[c.dataset.layer]=!STATE.layers[c.dataset.layer]; STATE.lens=""; syncLenses(); syncLayerChips(); render(); });
  lc.addEventListener("keydown",e=>{ if(e.key!=="Enter"&&e.key!==" ") return; const c=e.target.closest(".chip"); if(!c) return; e.preventDefault(); c.click(); });
  document.getElementById("selTheme").addEventListener("change",e=>{ STATE.theme=e.target.value; applyTheme(); restyleBasemapLive(); rebuildLegend(); render(); });
  document.getElementById("selFont").addEventListener("change",e=>{ STATE.font=e.target.value; applyTheme(); render(); });
  document.getElementById("selColor").addEventListener("change",e=>{ STATE.colorBy=e.target.value; STATE.lens=""; syncLenses(); rebuildLegend(); render(); });
  document.getElementById("sArc").value=STATE.arcWidth; document.getElementById("sArc").addEventListener("input",e=>{STATE.arcWidth=+e.target.value;render();});
  document.getElementById("sPoint").value=STATE.pointScale; document.getElementById("sPoint").addEventListener("input",e=>{STATE.pointScale=+e.target.value;render();});
  document.getElementById("sOpac").value=STATE.opacity; document.getElementById("sOpac").addEventListener("input",e=>{STATE.opacity=+e.target.value;render();});
  document.querySelectorAll('[data-adv]').forEach(c=>{ c.classList.toggle("on",STATE[c.dataset.adv]); c.addEventListener("click",()=>{
    STATE[c.dataset.adv]=!STATE[c.dataset.adv]; c.classList.toggle("on",STATE[c.dataset.adv]);
    if(c.dataset.adv==="legend") rebuildLegend(); }); });
}

// ---------- init ----------
(async function(){
  const p=qp();
  if(p.theme&&THEMES[p.theme]) STATE.theme=p.theme;
  if(p.ui==="min") document.body.classList.add("ui-min");
  applyTheme();
  buildControls();
  document.getElementById("selTheme").value=STATE.theme;

  const style=await baseStyle();
  map=new maplibregl.Map({container:"map",style,center:DATA.center,zoom:DATA.bbox?4.2:3.2,attributionControl:true,preserveDrawingBuffer:true});
  if(DATA.bbox) map.fitBounds([[DATA.bbox[0],DATA.bbox[1]],[DATA.bbox[2],DATA.bbox[3]]],{padding:60,duration:0});

  overlay=new deck.MapboxOverlay({interleaved:true,layers:[],getTooltip:({object,layer})=>{
    if(!object) return null;
    if(layer.id==="flows") return {html:`<b>${object.label}</b>`};
    if(layer.id==="borders"){ const n=(object.properties&&object.properties.NAME)||"";
      return {html:`<b>${n}</b><div style="font-size:10.5px;color:#888">borders c. ${DATA.boundaries.year} — approximate</div>`}; }
    if(layer.id!=="points") return null;
    const evs=object.events.filter(e=>e.year==null||e.year<=STATE.year);
    if(!STATE.tooltipRich) return {html:`<b>${object.name}</b> — ${evs.length} event(s)`};
    const list=evs.slice(0,6).map(e=>`<li>${e.date_label||e.year||'—'}: ${e.title}</li>`).join("");
    return {html:`<div style="font-family:var(--font);max-width:300px"><b>${object.name}</b>`+
      `<div style="font-size:11px;color:#888">${object.region} · ${evs.length} event(s)</div>`+
      `<ul style="margin:4px 0 0;padding-left:16px;font-size:11px">${list}</ul></div>`};
  }});
  map.addControl(overlay);
  window._map=map; window._overlay=overlay; window._STATE=STATE;
  map.on("error",e=>console.log("maplibre error:",e&&e.error&&e.error.message));

  const sl=document.getElementById("slider"); sl.min=DATA.year_min; sl.max=DATA.year_max;
  sl.addEventListener("input",e=>setYear(e.target.value));

  // lens / initial state, then per-param overrides (deep-state permalinks)
  applyLens(p.lens&&LENSES[p.lens]?p.lens:STATE.lens);
  if(p.color&&["theme","region","era"].includes(p.color)){ STATE.colorBy=p.color; document.getElementById("selColor").value=p.color; }
  if(p.layers){ const on=p.layers.split("."); for(const k of Object.keys(STATE.layers)) STATE.layers[k]=on.includes(k);
    if(!p.lens){ STATE.lens=""; syncLenses(); } syncLayerChips(); }
  if(p.arcw){ STATE.arcWidth=+p.arcw; document.getElementById("sArc").value=STATE.arcWidth; }
  if(p.pts){ STATE.pointScale=+p.pts; document.getElementById("sPoint").value=STATE.pointScale; }
  if(p.op){ STATE.opacity=+p.op; document.getElementById("sOpac").value=STATE.opacity; }
  rebuildLegend();
  setYear(p.year?+p.year:DATA.year_max);
  setTimeout(()=>{ try{map.resize();}catch(e){} },250);
  window.addEventListener("resize",()=>{try{map.resize();}catch(e){}});
  map.on("load",()=>{ restyleBasemapLive(); setYear(STATE.year); });

  // play (honours prefers-reduced-motion: steps by decade on demand, no auto-animation)
  let playing=null;
  document.getElementById("playBtn").addEventListener("click",function(){
    if(REDUCED){ const step=Math.max(10,Math.round((DATA.year_max-DATA.year_min)/12));
      setYear(Math.min(DATA.year_max, (STATE.year>=DATA.year_max?DATA.year_min:STATE.year)+step)); return; }
    if(playing){clearInterval(playing);playing=null;this.textContent="▶ Play";this.setAttribute("aria-pressed","false");return;}
    this.textContent="⏸ Pause"; this.setAttribute("aria-pressed","true");
    if(STATE.year>=DATA.year_max) STATE.year=DATA.year_min;
    playing=setInterval(()=>{ const step=Math.max(1,Math.round((DATA.year_max-DATA.year_min)/60));
      let ny=STATE.year+step; if(ny>=DATA.year_max){ny=DATA.year_max;clearInterval(playing);playing=null;const b=document.getElementById("playBtn");b.textContent="▶ Play";b.setAttribute("aria-pressed","false");}
      setYear(ny); },140);
  });

  // export: current view as PNG, with title + provenance strip burnt in
  document.getElementById("pngBtn").addEventListener("click",()=>{
    map.once("render",()=>{
      const src=map.getCanvas(), t=THEMES[STATE.theme];
      const c=document.createElement("canvas"); c.width=src.width; c.height=src.height;
      const g=c.getContext("2d"); g.drawImage(src,0,0);
      const s=(window.devicePixelRatio||1);
      g.fillStyle=t.panel; g.globalAlpha=0.85; g.fillRect(0,c.height-58*s,c.width,58*s); g.globalAlpha=1;
      g.fillStyle=t.ink; g.font=`600 ${16*s}px Georgia, serif`;
      g.fillText(DATA.title, 14*s, c.height-34*s);
      g.fillStyle=t.muted; g.font=`${11*s}px Georgia, serif`;
      const bits=["through "+(STATE.year<0?(-STATE.year+" BCE"):STATE.year+" CE"),
        DATA.boundaries?("borders c. "+DATA.boundaries.year+" (approximate)"):"",
        "MapLibre / deck.gl"].filter(Boolean).join("  ·  ");
      g.fillText(bits, 14*s, c.height-14*s);
      const a=document.createElement("a");
      a.download=(DATA.title||"map").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")+".png";
      a.href=c.toDataURL("image/png"); a.click();
    });
    map.triggerRepaint();
  });

  // permalink: copy the full view state as a URL
  document.getElementById("linkBtn").addEventListener("click",function(){
    const url=stateURL(), btn=this;
    const done=()=>{ btn.textContent="✓ Copied"; setTimeout(()=>btn.textContent="🔗 Link",1400); };
    if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done,()=>prompt("Copy this link:",url));
    else prompt("Copy this link:",url);
  });

  // embedding API
  window.addEventListener("message",ev=>{ const d=ev.data||{}; if(d.type!=="mapctl") return;
    if(d.theme&&THEMES[d.theme]){STATE.theme=d.theme;document.getElementById("selTheme").value=d.theme;applyTheme();restyleBasemapLive();rebuildLegend();}
    if(d.lens&&LENSES[d.lens]) applyLens(d.lens);
    if(d.year!=null) setYear(d.year);
    if(d.colorBy){STATE.colorBy=d.colorBy;rebuildLegend();}
    render();
  });
})();
</script>
</body>
</html>
"""


def emit_html(c):
    nar = c.get("narrative") or {}
    intro = f"<p>{html.escape(nar['intro'])}</p>" if nar.get("intro") else ""
    prov = ""
    if nar.get("provenance_note") or c.get("directive") or c.get("boundaries"):
        bits = []
        if c.get("directive"):
            bits.append("Directive: <em>" + html.escape(c["directive"]) + "</em>")
        if nar.get("provenance_note"):
            bits.append(html.escape(nar["provenance_note"]))
        if c.get("boundaries"):
            b = c["boundaries"]
            bits.append(f"Political borders c. {b['year']} — approximate scholarly reconstruction, "
                        "after <em>historical-basemaps</em> (aourednik); for orientation, not authority.")
        prov = '<div class="prov">' + "<br>".join(bits) + "</div>"
    s = c["stats"]
    stats = f"{s['events']} events · {s['locations']} locations · {s['arcs']} transmission arcs"
    if s["missing_locations"]:
        stats += f" · ⚠ {len(s['missing_locations'])} ungeocoded"
    out = TEMPLATE
    for tok, val in [("__TITLE__", html.escape(c["title"])), ("__SUBTITLE__", html.escape(c["subtitle"])),
                     ("__INTRO__", intro), ("__PROV__", prov), ("__STATS__", stats),
                     ("__DATA__", json.dumps(c, ensure_ascii=False))]:
        out = out.replace(tok, val)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapspec")
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[2] / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-unsourced", action="store_true",
                    help="build even without a narrative.provenance_note (drafts only)")
    args = ap.parse_args()
    spec = json.loads(Path(args.mapspec).read_text(encoding="utf-8"))

    errors, warnings = validate_spec(spec)
    for w in warnings:
        print(f"  spec warning: {w}")
    if errors:
        for e in errors:
            print(f"  SPEC ERROR: {e}")
        raise SystemExit(2)
    if not check_provenance(spec):
        if args.allow_unsourced:
            print("  spec warning: no narrative.provenance_note — building anyway (--allow-unsourced)")
        else:
            print("  SPEC ERROR: narrative.provenance_note is required — say where this map's "
                  "claims come from and what it does not show. (Override with --allow-unsourced.)")
            raise SystemExit(2)

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    compiled = compile_spec(spec, data)
    out_path = Path(args.out) if args.out else (Path(__file__).resolve().parents[1] / "prototypes" / (Path(args.mapspec).stem + ".html"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(emit_html(compiled), encoding="utf-8")
    s = compiled["stats"]
    print(f"Built: {out_path}")
    print(f"  events={s['events']} locations={s['locations']} arcs={s['arcs']}")
    if compiled.get("boundaries"):
        b = compiled["boundaries"]
        snap = "" if b["year"] == b["requested_year"] else f" (nearest to requested {b['requested_year']})"
        print(f"  period borders: c. {b['year']}{snap}, {len(b['geojson']['features'])} polities embedded")
    elif (spec.get("render", {}).get("basemap", {}) or {}).get("historical_boundaries_year"):
        print("  WARNING: historical_boundaries_year set but no boundary cache found — "
              "run scripts/fetch_boundaries.py first")
    for t, n in s.get("theme_counts", {}).items():
        if n == 0:
            print(f"  WARNING: theme '{t}' matches 0 events in scope — the Themes lens will not show it")
    if s["missing_locations"]:
        print(f"  WARNING ungeocoded: {s['missing_locations'][:8]}{'...' if len(s['missing_locations'])>8 else ''}")
    return compiled


if __name__ == "__main__":
    main()

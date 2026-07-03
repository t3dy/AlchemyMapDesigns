#!/usr/bin/env python3
"""
fetch_basegeo.py — download + slim the physical base geography.

Source: Natural Earth (public domain) via the nvkelso/natural-earth-vector
GeoJSON mirror. Produces the land / lakes / rivers that every map embeds so it
LOOKS like a map — coastlines, seas, lakes, rivers — with no CDN basemap
dependency and no modern political content (period borders are a separate,
year-aware layer).

Layers written to data/basegeo/:
  land.geojson    — ne_10m_land   (10m detail: regional maps need real coasts)
  lakes.geojson   — ne_10m_lakes  (major lakes only, by scalerank)
  rivers.geojson  — ne_10m_rivers_lake_centerlines (major rivers, by scalerank)

Same slimming as the boundary cache: window clip, Douglas-Peucker, coordinate
rounding. Usage:  python fetch_basegeo.py
"""
import json
import urllib.request
from pathlib import Path

from fetch_boundaries import dp_simplify

RAW = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{name}.geojson"
OUTDIR = Path(__file__).resolve().parents[1] / "data" / "basegeo"

# Generous window: Atlantic to Central Asia, Sahara to the North Cape,
# so panning past the data still shows geography.
WINDOW = (-30.0, 8.0, 80.0, 72.0)


def clip_ring_bbox(ring):
    w, s, e, n = WINDOW
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return not (max(xs) < w or min(xs) > e or max(ys) < s or min(ys) > n)


def clip_polygon_rect(ring):
    """Sutherland–Hodgman: clip a ring to the WINDOW rectangle."""
    w, s, e, n = WINDOW
    edges = [
        (lambda p: p[0] >= w, lambda a, b: (w, a[1] + (b[1] - a[1]) * (w - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= e, lambda a, b: (e, a[1] + (b[1] - a[1]) * (e - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= s, lambda a, b: (a[0] + (b[0] - a[0]) * (s - a[1]) / (b[1] - a[1]), s)),
        (lambda p: p[1] <= n, lambda a, b: (a[0] + (b[0] - a[0]) * (n - a[1]) / (b[1] - a[1]), n)),
    ]
    poly = [tuple(p) for p in ring]
    for inside, intersect in edges:
        if not poly:
            return []
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(intersect(prev, cur))
        poly = out
    return [list(p) for p in poly]


def clip_line_rect(line):
    """Split a line into runs clipped to the WINDOW (segment-wise Liang–Barsky)."""
    w, s, e, n = WINDOW

    def clip_seg(a, b):
        t0, t1 = 0.0, 1.0
        dx, dy = b[0] - a[0], b[1] - a[1]
        for p, q in ((-dx, a[0] - w), (dx, e - a[0]), (-dy, a[1] - s), (dy, n - a[1])):
            if p == 0:
                if q < 0:
                    return None
            else:
                r = q / p
                if p < 0:
                    if r > t1:
                        return None
                    t0 = max(t0, r)
                else:
                    if r < t0:
                        return None
                    t1 = min(t1, r)
        return ((a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy))

    runs, cur = [], []
    for a, b in zip(line, line[1:]):
        seg = clip_seg(a, b)
        if seg is None:
            if len(cur) >= 2:
                runs.append(cur)
            cur = []
            continue
        (x1, y1), (x2, y2) = seg
        if not cur or cur[-1] != [x1, y1]:
            if len(cur) >= 2:
                runs.append(cur)
            cur = [[x1, y1]]
        cur.append([x2, y2])
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def slim_ring(ring, tol):
    ring = dp_simplify(ring, tol)
    out, prev = [], None
    for lon, lat in ring:
        pt = [round(lon, 2), round(lat, 2)]
        if pt != prev:
            out.append(pt)
        prev = pt
    return out if len(out) >= 4 else None


def slim_line(line, tol):
    line = dp_simplify(line, tol)
    out, prev = [], None
    for lon, lat in line:
        pt = [round(lon, 2), round(lat, 2)]
        if pt != prev:
            out.append(pt)
        prev = pt
    return out if len(out) >= 2 else None


def slim_feature(feat, tol, keep_props=()):
    geom = feat.get("geometry") or {}
    gtype, coords = geom.get("type"), geom.get("coordinates")
    props = feat.get("properties") or {}
    kept = {k: props.get(k) for k in keep_props if props.get(k) is not None}

    if gtype in ("Polygon", "MultiPolygon"):
        polys = coords if gtype == "MultiPolygon" else [coords]
        out_polys = []
        for poly in polys:
            if not poly or not clip_ring_bbox(poly[0]):
                continue
            rings = []
            for ring in poly:
                clipped = clip_polygon_rect(ring)
                if len(clipped) >= 4 or (len(clipped) == 3 and clipped[0] != clipped[-1]):
                    sl = slim_ring(clipped + ([clipped[0]] if clipped[0] != clipped[-1] else []), tol)
                    if sl:
                        rings.append(sl)
            if rings:
                out_polys.append(rings)
        if not out_polys:
            return None
        geometry = ({"type": "Polygon", "coordinates": out_polys[0]} if len(out_polys) == 1
                    else {"type": "MultiPolygon", "coordinates": out_polys})
    elif gtype in ("LineString", "MultiLineString"):
        lines = coords if gtype == "MultiLineString" else [coords]
        out_lines = []
        for line in lines:
            if not line or not clip_ring_bbox(line):
                continue
            for run in clip_line_rect(line):
                sl = slim_line(run, tol)
                if sl:
                    out_lines.append(sl)
        if not out_lines:
            return None
        geometry = ({"type": "LineString", "coordinates": out_lines[0]} if len(out_lines) == 1
                    else {"type": "MultiLineString", "coordinates": out_lines})
    else:
        return None
    return {"type": "Feature", "properties": kept, "geometry": geometry}


def fetch(name, out_name, tol, keep_props=(), feature_filter=None):
    with urllib.request.urlopen(RAW.format(name=name), timeout=120) as r:
        raw = json.loads(r.read().decode("utf-8"))
    feats = []
    for ft in raw.get("features", []):
        if feature_filter and not feature_filter(ft.get("properties") or {}):
            continue
        slim = slim_feature(ft, tol, keep_props)
        if slim:
            feats.append(slim)
    out = {"type": "FeatureCollection",
           "attribution": "Physical geography: Natural Earth (public domain)",
           "features": feats}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    path = OUTDIR / f"{out_name}.geojson"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {out_name:<8} {len(feats):>4} features, {path.stat().st_size/1024:.0f} KB")


def main():
    # land: keep every polygon (islands matter to this story: Ven, Britain, Sicily)
    fetch("ne_10m_land", "land", tol=0.015)
    # lakes: only sizeable ones
    fetch("ne_10m_lakes", "lakes", tol=0.01, keep_props=("name",),
          feature_filter=lambda p: (p.get("scalerank") or 9) <= 5)
    # rivers: the majors, with names for tooltips someday
    fetch("ne_10m_rivers_lake_centerlines", "rivers", tol=0.01, keep_props=("name",),
          feature_filter=lambda p: (p.get("scalerank") or 12) <= 8)


if __name__ == "__main__":
    main()

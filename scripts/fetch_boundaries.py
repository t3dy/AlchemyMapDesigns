#!/usr/bin/env python3
"""
fetch_boundaries.py — download + slim historical political boundaries.

Source: https://github.com/aourednik/historical-basemaps (world_YYYY.geojson).
These are *approximate* scholarly reconstructions; the maps must (and do) say so.

For each requested year this script:
  1. downloads the world file,
  2. keeps only features whose bbox intersects the project window
     (the alchemical world: Atlantic to Persia, Sahara to Scandinavia),
  3. simplifies rings (Douglas-Peucker) and rounds coords to 2 decimals,
  4. keeps only the NAME property,
and writes data/boundaries/world_YYYY.geojson small enough to embed in a
self-contained map HTML.

Usage:
    python fetch_boundaries.py            # fetch the default year set
    python fetch_boundaries.py 1600 1650  # fetch specific years
"""
import json
import sys
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/world_{y}.geojson"
OUTDIR = Path(__file__).resolve().parents[1] / "data" / "boundaries"

# The alchemical world, generous margins: [west, south, east, north]
WINDOW = (-15.0, 18.0, 68.0, 64.0)
TOLERANCE = 0.02  # degrees (~2 km) — plenty for continental-scale borders
DEFAULT_YEARS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200,
                 1279, 1300, 1400, 1492, 1500, 1530, 1600, 1650, 1700, 1715, 1783, 1800]


def dp_simplify(pts, tol):
    """Iterative Douglas-Peucker on a list of [lon, lat]."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    if pts[0] == pts[-1]:
        # closed ring: identical endpoints defeat point-to-line distance —
        # anchor the vertex farthest from the start and split there
        x0, y0 = pts[0]
        m = max(range(1, len(pts) - 1),
                key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        keep[m] = True
        stack = [(0, m), (m, len(pts) - 1)]
    else:
        stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
        worst, wd = -1, tol
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs(dx * (ay - py) - dy * (ax - px)) / norm
            if d >= wd:
                worst, wd = i, d
        if worst > 0:
            keep[worst] = True
            stack.append((a, worst))
            stack.append((worst, b))
    return [p for p, k in zip(pts, keep) if k]


def slim_ring(ring):
    ring = dp_simplify(ring, TOLERANCE)
    out, prev = [], None
    for lon, lat in ring:
        pt = [round(lon, 2), round(lat, 2)]
        if pt != prev:
            out.append(pt)
        prev = pt
    return out if len(out) >= 4 else None


def ring_bbox_hits(ring):
    w, s, e, n = WINDOW
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return not (max(xs) < w or min(xs) > e or max(ys) < s or min(ys) > n)


def slim_feature(feat):
    geom = feat.get("geometry") or {}
    gtype, coords = geom.get("type"), geom.get("coordinates")
    polys = coords if gtype == "MultiPolygon" else [coords] if gtype == "Polygon" else []
    out_polys = []
    for poly in polys:
        if not poly or not ring_bbox_hits(poly[0]):
            continue
        rings = [r for r in (slim_ring(ring) for ring in poly) if r]
        if rings:
            out_polys.append(rings)
    if not out_polys:
        return None
    name = (feat.get("properties") or {}).get("NAME") or ""
    if len(out_polys) == 1:
        geometry = {"type": "Polygon", "coordinates": out_polys[0]}
    else:
        geometry = {"type": "MultiPolygon", "coordinates": out_polys}
    return {"type": "Feature", "properties": {"NAME": name}, "geometry": geometry}


def fetch_year(year):
    url = RAW.format(y=year)
    with urllib.request.urlopen(url, timeout=60) as r:
        raw = json.loads(r.read().decode("utf-8"))
    feats = [f for f in (slim_feature(ft) for ft in raw.get("features", [])) if f]
    out = {"type": "FeatureCollection",
           "year": year,
           "attribution": "Historical boundaries (approximate) after aourednik/historical-basemaps",
           "features": feats}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    path = OUTDIR / f"world_{year}.geojson"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path, len(feats)


def main():
    years = [int(a) for a in sys.argv[1:]] or DEFAULT_YEARS
    for y in years:
        try:
            path, n = fetch_year(y)
            print(f"  {y:>5}: {n:>3} features, {path.stat().st_size/1024:.0f} KB -> {path.name}")
        except Exception as e:  # noqa: BLE001 — report and continue with the other years
            print(f"  {y:>5}: FAILED ({e})")


if __name__ == "__main__":
    main()

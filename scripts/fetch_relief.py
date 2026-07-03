#!/usr/bin/env python3
"""
fetch_relief.py — download + crop the physical terrain-colour/shaded-relief
master image so maps can look like an atlas, not an abstraction.

Source: Natural Earth I with Shaded Relief and Water (public domain), the
1:50m raster — real hypsometric tinting (green lowlands, tan/brown uplands,
pale high-elevation and ice) plus real shaded relief (you can see the Alps,
the Atlas Mountains, the edge of the Himalaya). ~88 MB zipped, 10800x5400 px
globally; this script crops to the project window and downsamples to a
shared master cache that build_map.py re-crops per map at build time (same
"cache once, embed slices" pattern as fetch_boundaries.py/fetch_basegeo.py).

Usage:  python fetch_relief.py
"""
import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

URL = "https://naturalearth.s3.amazonaws.com/50m_raster/NE1_50M_SR_W.zip"
WINDOW = (-30.0, 8.0, 80.0, 72.0)  # matches fetch_basegeo.py's project window
MASTER_WIDTH = 2600  # px; ~1 deg per 23.6px over the window — plenty for per-map crops
OUT = Path(__file__).resolve().parents[1] / "data" / "relief" / "world_relief.jpg"
WORK = Path(__file__).resolve().parent / "_relief_work"

# Georeferencing of the source TIF (from its accompanying .tfw): top-left
# corner and pixel size, in degrees. Confirmed against the extracted file.
ORIGIN_LON, ORIGIN_LAT, PX_DEG = -179.98333333333333, 89.98333333333333, 0.03333333333333


def lonlat_to_px(lon, lat):
    return int((lon - ORIGIN_LON) / PX_DEG), int((ORIGIN_LAT - lat) / PX_DEG)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    zip_path = WORK / "ne1.zip"
    if not zip_path.exists():
        print("  downloading NE1_50M_SR_W.zip (~88 MB)...")
        with urllib.request.urlopen(URL, timeout=300) as r:
            zip_path.write_bytes(r.read())

    print("  extracting...")
    with zipfile.ZipFile(zip_path) as z:
        tif_name = next(n for n in z.namelist() if n.endswith(".tif"))
        with z.open(tif_name) as f:
            im = Image.open(io.BytesIO(f.read()))
            im.load()

    w, s, e, n = WINDOW
    x0, y0 = lonlat_to_px(w, n)
    x1, y1 = lonlat_to_px(e, s)
    crop = im.crop((x0, y0, x1, y1))
    print(f"  cropped to project window: {crop.size}")

    scale = MASTER_WIDTH / crop.width
    master = crop.resize((MASTER_WIDTH, round(crop.height * scale)), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    master.convert("RGB").save(OUT, "JPEG", quality=88)
    print(f"  master cache: {OUT} ({master.size}, {OUT.stat().st_size/1024:.0f} KB)")

    shutil.rmtree(WORK, ignore_errors=True)
    print("  cleaned up working files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
test_smoke.py — dependency-free regression net for the map toolkit.

The sandbox can't screenshot WebGL, so this is the deterministic layer of QA:
every spec validates, every map compiles, every emitted HTML is structurally
sound, and the curated journey/network data passes its evidence rules.

Usage:  python scripts/test_smoke.py     (exit 0 = all pass)
"""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_map as bm          # noqa: E402
import build_journey as bj      # noqa: E402
import build_network as bn      # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT.parent / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json"

PASS, FAIL = 0, []


def check(name, fn):
    global PASS
    try:
        fn()
        PASS += 1
        print(f"  ok    {name}")
    except AssertionError as e:
        FAIL.append((name, str(e)))
        print(f"  FAIL  {name}: {e}")
    except Exception:
        FAIL.append((name, traceback.format_exc(limit=2)))
        print(f"  ERROR {name}:\n{traceback.format_exc(limit=2)}")


MAX_PROTO_BYTES = 2_500_000  # canary: a relief crop gone wrong (full master embedded) would blow past this


def html_is_sound(out, expect_boundaries=None, expect_relief=None):
    assert "__DATA__" not in out and "__TITLE__" not in out, "unreplaced template token"
    assert "const DATA =" in out, "embedded DATA missing"
    assert 'id="pngBtn"' in out and 'id="linkBtn"' in out, "export/permalink buttons missing"
    assert "preserveDrawingBuffer" in out, "PNG export needs preserveDrawingBuffer"
    assert "prefers-reduced-motion" in out, "reduced-motion support missing"
    assert "bg-land" in out and '"basegeo"' in out, "base geography not embedded — map won't look like a map"
    assert "demotiles" not in out, "CDN basemap dependency crept back in"
    if expect_boundaries:
        assert '"boundaries": {' in out or '"boundaries":{' in out, "boundaries not embedded"
    # terrain colour + shaded relief: real Natural Earth I imagery, tinted per
    # theme, so maps read like an atlas plate instead of a flat abstraction
    assert "BitmapLayer" in out, "relief layer machinery missing"
    if expect_relief:
        assert '"relief": {' in out or '"relief":{' in out, "relief crop not embedded"
        assert "data:image/jpeg;base64," in out, "relief image not embedded as a data URI"
    assert len(out.encode("utf-8")) < MAX_PROTO_BYTES, f"file too large ({len(out)} bytes) — relief crop may not be downsampled"
    # mobile layout: #panel/#controls (data maps) are independently absolutely-
    # positioned corner boxes with fixed pixel widths — verified by hand in a
    # real browser (375/320px viewports) to fully overlap without both (a) a
    # box-sizing:border-box reset so max-height/width arithmetic is accurate,
    # and (b) a mobile breakpoint that re-stacks them. Never let either regress.
    assert "box-sizing:border-box" in out, "no box-sizing reset — mobile stacking math will be wrong"
    assert "@media (max-width:760px)" in out, "no mobile breakpoint — #panel/#controls overlap under ~625px wide"
    # place-name labels (Córdoba, Kraków…) need an explicit glyph range — deck.gl
    # 9.0.33 silently ignores characterSet:"auto" and drops any accented letter
    assert 'characterSet:LABEL_CHARS' in out, "TextLayer missing the diacritics character-set fix"
    assert 'characterSet:"auto"' not in out, "TextLayer using characterSet:'auto', which this deck.gl build ignores"


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # ---- every spec on disk validates and compiles ----
    specs = sorted((ROOT / "specs").glob("**/*.mapspec.json"))
    assert specs, "no specs found"
    for sp in specs:
        spec = json.loads(sp.read_text(encoding="utf-8"))

        def one(sp=sp, spec=spec):
            errors, _ = bm.validate_spec(spec)
            assert not errors, f"validation: {errors}"
            assert bm.check_provenance(spec), "missing provenance_note"
            c = bm.compile_spec(spec, data)
            assert c["stats"]["events"] > 0, "compiled to 0 events"
            wants_borders = (spec.get("render", {}).get("basemap", {}) or {}).get("historical_boundaries_year")
            if wants_borders:
                assert c["boundaries"], "boundaries requested but not loaded"
                assert c["boundaries"]["geojson"]["features"], "boundary layer empty"
            relief_available = bm.RELIEF_PATH.exists()
            if relief_available:
                assert c["relief"], "relief cache present but this spec compiled without a crop"
            out = bm.emit_html(c)
            html_is_sound(out, expect_boundaries=wants_borders, expect_relief=relief_available)

        check(f"spec {sp.relative_to(ROOT)}", one)

    # ---- validator actually rejects bad specs ----
    def rejects():
        bad = {"title": "x", "scope": {"year_start": 1700, "year_end": 1500,
                                       "era": ["BRONZE_AGE"], "region_bbox": [1, 2, 3]},
               "render": {"layers": ["points", "wormholes"], "color_by": "mood",
                          "basemap": {"style": "vaporwave"}}}
        errors, _ = bm.validate_spec(bad)
        for frag in ("year_start", "era", "region_bbox", "wormholes", "color_by", "basemap.style"):
            assert any(frag in e for e in errors), f"validator missed: {frag}"
        assert not bm.check_provenance(bad), "provenance check passed a spec with no narrative"
    check("validator rejects a deliberately bad spec", rejects)

    # ---- boundary cache: loadable, plausible, slim ----
    def boundaries():
        files = sorted((ROOT / "data" / "boundaries").glob("world_*.geojson"))
        assert files, "no boundary cache (run fetch_boundaries.py)"
        for f in files:
            gj = json.loads(f.read_text(encoding="utf-8"))
            assert gj["features"], f"{f.name}: empty"
            assert f.stat().st_size < 300_000, f"{f.name}: too big to embed"
        b = bm.load_boundaries(1560)
        assert b and abs(b["year"] - 1560) <= 40, f"nearest-year snap looks wrong: {b and b['year']}"
    check("boundary cache", boundaries)

    # ---- base geography cache: present, plausible, slim ----
    def basegeo():
        for name, cap in (("land", 700_000), ("lakes", 250_000), ("rivers", 500_000)):
            f = ROOT / "data" / "basegeo" / f"{name}.geojson"
            assert f.exists(), f"basegeo/{name}.geojson missing (run fetch_basegeo.py)"
            gj = json.loads(f.read_text(encoding="utf-8"))
            assert gj["features"], f"{name}: empty"
            assert f.stat().st_size < cap, f"{name}: too big to embed ({f.stat().st_size})"
        assert bm.load_basegeo(), "load_basegeo() returned nothing"
    check("base geography cache", basegeo)

    # ---- relief master cache: present, plausible, slim ----
    def relief_cache():
        f = ROOT / "data" / "relief" / "world_relief.jpg"
        assert f.exists(), "relief master cache missing (run fetch_relief.py)"
        assert f.stat().st_size < 2_000_000, f"relief master unexpectedly large ({f.stat().st_size} bytes)"
        crop = bm.load_relief_crop([2.0, 44.0, 21.0, 55.0])
        assert crop and crop["data_uri"].startswith("data:image/jpeg;base64,"), "relief crop did not produce a JPEG data URI"
        assert len(crop["data_uri"]) < 400_000, "a single relief crop is unexpectedly large"
    check("relief master cache", relief_cache)

    # ---- journey/network prototypes carry geography, no CDN basemap ----
    def curated_protos():
        protos = [p for p in (ROOT / "prototypes").glob("journey-*.html")]
        protos += [ROOT / "prototypes" / "network.html"]
        for p in protos:
            out = p.read_text(encoding="utf-8")
            assert "bg-land" in out and '"basegeo"' in out, f"{p.name}: base geography not embedded"
            assert "demotiles" not in out, f"{p.name}: CDN basemap dependency"
            assert "box-sizing:border-box" in out, f"{p.name}: no box-sizing reset"
            assert 'characterSet:LABEL_CHARS' in out, f"{p.name}: TextLayer missing the diacritics character-set fix"
            assert 'characterSet:"auto"' not in out, f"{p.name}: TextLayer using characterSet:'auto', which this deck.gl build ignores"
            assert "BitmapLayer" in out, f"{p.name}: relief layer machinery missing"
            if bm.RELIEF_PATH.exists():
                assert '"relief": {' in out or '"relief":{' in out, f"{p.name}: relief cache present but no crop embedded"
            assert len(out.encode("utf-8")) < MAX_PROTO_BYTES, f"{p.name}: file too large ({len(out)} bytes)"
    check("journey/network prototypes embed geography", curated_protos)

    # ---- journey prototypes stack #ctl/.legend/#doubt/#story on mobile ----
    # (verified by hand in-browser at 320-400px: these four independently
    # absolutely-positioned corner boxes overlap without this breakpoint)
    def journey_mobile_layout():
        for p in (ROOT / "prototypes").glob("journey-*.html"):
            out = p.read_text(encoding="utf-8")
            assert "@media (max-width:760px)" in out, f"{p.name}: no mobile breakpoint"
    check("journey prototypes have a mobile layout", journey_mobile_layout)

    # ---- curated journey data obeys its evidence rules ----
    for jp in sorted((ROOT / "data").glob("journey-*.json")):
        def journey(jp=jp):
            J = json.loads(jp.read_text(encoding="utf-8"))
            errs = bj.validate_journey(J)
            assert not errs, errs
        check(f"{jp.name} evidence rules", journey)

    # ---- curated network data obeys its evidence rules ----
    def network():
        net = json.loads((ROOT / "data" / "networks.json").read_text(encoding="utf-8"))
        errs = bn.validate_network(net)
        assert not errs, errs
    check("networks.json evidence rules", network)

    # ---- gallery covers every map on disk ----
    def gallery():
        gdir = ROOT / "gallery"
        idx = (gdir / "index.html")
        assert idx.exists(), "gallery/index.html missing (run build_gallery.py)"
        index_html = idx.read_text(encoding="utf-8")
        expected = [p.stem.replace(".mapspec", "") for p in (ROOT / "specs").glob("**/*.mapspec.json")]
        expected += [p.stem for p in (ROOT / "data").glob("journey-*.json")]
        net = json.loads((ROOT / "data" / "networks.json").read_text(encoding="utf-8"))
        expected += ["network-" + s["slug"] for s in net["subjects"]]
        import re as _re
        for slug in expected:
            page = gdir / f"{slug}.html"
            assert page.exists(), f"gallery page missing: {slug}.html"
            assert f'href="{slug}.html"' in index_html, f"index has no card for {slug}"
            m = _re.search(r'iframe class="mapframe" src="([^"?]+)', page.read_text(encoding="utf-8"))
            assert m, f"{slug}.html: no map iframe"
            target = (gdir / m.group(1)).resolve()
            assert target.exists(), f"{slug}.html embeds missing map: {m.group(1)}"
        for doc in ("toolkit.html", "manual.html", "nextsteps.html"):
            assert (gdir / doc).exists(), f"gallery/{doc} missing"
    check("gallery covers every map + docs", gallery)

    # ---- tour manifest agrees with the prototypes on disk ----
    def manifest():
        man = json.loads((ROOT / "tour" / "manifest.json").read_text(encoding="utf-8"))
        for group in ("eras", "centuries"):
            for entry in man[group]:
                p = ROOT / "prototypes" / f"{entry['slug']}.html"
                assert p.exists(), f"manifest references missing {p.name}"
    check("tour manifest vs prototypes", manifest)

    print(f"\n{PASS} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())

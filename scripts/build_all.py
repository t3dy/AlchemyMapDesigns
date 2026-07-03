#!/usr/bin/env python3
"""
build_all.py — author + render the full map set for the tour.

Generates two families of MapSpec and compiles each with build_map.compile_spec:
  1. ERA SHOWCASE — one map per major era of alchemy, to dramatize the data.
  2. CENTURY TRANSMISSION — one map per century 8th..18th, transmission-flow focus,
     showing the centre of gravity migrating Baghdad -> al-Andalus -> Latin Europe -> the north.

Writes specs to specs/generated/ and HTML to prototypes/, prints a manifest the tour reads.
"""
import json
from pathlib import Path
import build_map as bm

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT.parent / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json").read_text(encoding="utf-8"))
SPECDIR = ROOT / "specs" / "generated"
OUTDIR = ROOT / "prototypes"
SPECDIR.mkdir(parents=True, exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)

# Whole Mediterranean + Europe + Near East — the alchemical world.
WORLD_BBOX = [-10.0, 24.0, 60.0, 60.0]

# A shared, honest note about what these corpus-driven maps can and cannot claim.
CORPUS_PROVENANCE = ("Events from the ALCHEMYTIMELINEMAP corpus (largely draft-status entries); "
                     "locations are event geocodes, not residences. Transmission arcs are reconstructed "
                     "from the dated itineraries of named figures — absence of an arc reflects gaps in "
                     "the record, not certainty of no contact.")

ERA_SHOWCASE = [
    {"slug":"era-greco-egyptian","title":"Greco-Egyptian Alchemy","subtitle":"Late-antique Alexandria and the first alchemical writers, c. 200–600 CE",
     "scope":{"year_start":100,"year_end":650,"region_bbox":[10,22,40,46]},"borders_year":400,
     "intro":"The earliest surviving alchemical corpus is Greek and Egyptian — Zosimos of Panopolis, Maria the Jewess, the Leiden and Stockholm papyri. Activity clusters tightly in Egypt: this is alchemy before it travels."},
    {"slug":"era-arabic","title":"The Arabic Transmission","subtitle":"Baghdad, Persia, and al-Andalus, 8th–12th centuries",
     "scope":{"year_start":700,"year_end":1200,"region_bbox":WORLD_BBOX},"borders_year":1000,
     "intro":"Greek learning is translated into Arabic and transformed — Jabir ibn Hayyan, al-Razi, the sulphur–mercury theory, the rise of distillation. Watch the weight shift east to Baghdad and Persia, then west into Muslim Spain."},
    {"slug":"era-latin-medieval","title":"Translation into Latin Europe","subtitle":"Toledo, Paris, and the scholastic reception, 12th–14th centuries",
     "scope":{"year_start":1100,"year_end":1400,"region_bbox":WORLD_BBOX},"borders_year":1300,
     "intro":"Arabic alchemy crosses into Latin Christendom through Iberian translation centres. The pseudo-Geberian Summa Perfectionis becomes the canonical Latin theory; transmutation debates enter the universities."},
    {"slug":"era-renaissance","title":"Renaissance Hermeticism","subtitle":"Florence, the Corpus Hermeticum, and the quintessence, 15th–16th centuries",
     "scope":{"year_start":1400,"year_end":1560,"region_bbox":[-2,38,20,54]},"borders_year":1500,
     "intro":"Ficino's translation of the Hermetic corpus reframes alchemy within a prisca theologia. Italy and the Low Countries dominate; alchemy fuses with natural philosophy and the search for a quintessence."},
    {"slug":"era-paracelsian","title":"Paracelsian Iatrochemistry","subtitle":"Chymical medicine in the German lands, c. 1490–1610",
     "scope":{"year_start":1490,"year_end":1610,"regions":["Germany","Germany/Saxony","Switzerland","Austria","Bohemia","France/Alsace"],"region_bbox":[5,45.5,19,54]},"borders_year":1600,
     "intro":"Paracelsus recasts alchemy as iatrochemistry — medicine made by the fire. The map traces his itinerant career and the diffusion of Paracelsian ideas before they fuse with Rosicrucian currents after 1614."},
    {"slug":"era-english-chymistry","title":"English Chymistry","subtitle":"From Ripley to the Royal Society, 16th–17th centuries",
     "scope":{"year_start":1500,"year_end":1700,"region_bbox":[-8,49,8,57]},"borders_year":1650,
     "intro":"England develops a distinctive chymical culture — the Ripley tradition, John Dee, Elias Ashmole, and Robert Boyle — bridging late-medieval transmutation and the new experimental philosophy."},
]

RENDER_DEFAULT = {"engine":"maplibre","basemap":{"style":"atlas","show_modern_labels":False},
                  "layers":["points","flows","time-animation"],"color_by":"region"}

# every era wears a different face — the fleet doubles as a style showcase
ERA_STYLE = {
    "era-greco-egyptian": ("lapis", "Lapis & Gold: the tradition's deep past in late-antique ultramarine — gilt points on a temple-ceiling blue."),
    "era-arabic": ("illuminated", "Illuminated Manuscript: gold-on-parchment for a corpus that lived in manuscript, from Baghdad's paper mills to al-Andalus."),
    "era-latin-medieval": ("woodcut", "Woodcut & Rubric: black letter and red rubric for the scholastic reception — quaestiones, condemnations, university Latin."),
    "era-renaissance": ("copperplate", "Copperplate Engraving: the era print culture took over; sepia line-work is the register of the humanist printed book."),
    "era-paracelsian": ("atlas", "Modern Atlas: iatrochemistry read plainly — a medical-reform movement mapped with clinical legibility."),
    "era-english-chymistry": ("noir", "Alchemical Noir: secretive manuscripts, pseudonyms, and private laboratories on the way to the Royal Society — gold arcs out of darkness."),
}
CENTURY_STYLES = ["illuminated", "lapis", "woodcut", "copperplate", "atlas", "noir"]
STYLE_LABEL = {"atlas": "Modern Atlas", "copperplate": "Copperplate Engraving",
               "illuminated": "Illuminated Manuscript", "noir": "Alchemical Noir",
               "woodcut": "Woodcut & Rubric", "lapis": "Lapis & Gold"}


def render_with_borders(year, style="atlas"):
    r = dict(RENDER_DEFAULT)
    r["basemap"] = {**RENDER_DEFAULT["basemap"], "style": style, "historical_boundaries_year": year}
    return r


def ordinal(n):
    return f"{n}th" if 11<=n%100<=13 else {1:"st",2:"nd",3:"rd"}.get(n%10,"th").rjust(2)


def ord_word(n):
    return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"


def build(spec, slug):
    errors, warnings = bm.validate_spec(spec)
    if errors or not bm.check_provenance(spec):
        for e in errors:
            print(f"  SPEC ERROR ({slug}): {e}")
        if not bm.check_provenance(spec):
            print(f"  SPEC ERROR ({slug}): missing narrative.provenance_note")
        raise SystemExit(2)
    (SPECDIR / f"{slug}.mapspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    compiled = bm.compile_spec(spec, DATA)
    (OUTDIR / f"{slug}.html").write_text(bm.emit_html(compiled), encoding="utf-8")
    return compiled["stats"]


def main():
    manifest = {"eras": [], "centuries": []}

    for e in ERA_SHOWCASE:
        style, design = ERA_STYLE[e["slug"]]
        spec = {"title": e["title"], "subtitle": e["subtitle"], "directive": f"era showcase: {e['title']}",
                "scope": e["scope"], "render": render_with_borders(e["borders_year"], style),
                "narrative": {"intro": e["intro"], "provenance_note": CORPUS_PROVENANCE,
                              "design_note": design}}
        st = build(spec, e["slug"])
        manifest["eras"].append({"slug": e["slug"], "title": e["title"], "subtitle": e["subtitle"], **st})
        print(f"ERA  {e['slug']:<24} events={st['events']:>3} loc={st['locations']:>2} arcs={st['arcs']:>3}")

    for c in range(8, 19):  # 8th..18th centuries
        y0, y1 = (c - 1) * 100, c * 100 - 1
        slug = f"century-{c:02d}"
        title = f"The {ord_word(c)} Century"
        style = CENTURY_STYLES[(c - 8) % len(CENTURY_STYLES)]
        spec = {"title": title, "subtitle": f"Transmission of alchemical knowledge, {y0}–{y1} CE",
                "directive": f"significant movements of the {ord_word(c)} century",
                "scope": {"year_start": y0, "year_end": y1, "region_bbox": WORLD_BBOX},
                "render": {**render_with_borders(y0 + 50, style), "color_by": "region"},
                "narrative": {"intro": f"Alchemical activity in the {ord_word(c)} century. Arcs trace where individual practitioners and translators carried knowledge between centres.",
                              "provenance_note": "Transmission arcs are reconstructed from the recorded itineraries of named figures; absence of an arc reflects gaps in the record, not certainty of no contact.",
                              "design_note": f"{STYLE_LABEL[style]}: the century series rotates the full six-style wardrobe, so reading the centuries in order is also a tour of the theme engine — and consecutive chapters never look alike."}}
        st = build(spec, slug)
        manifest["centuries"].append({"slug": slug, "century": c, "title": title, "years": [y0, y1], **st})
        print(f"CENT {slug:<24} events={st['events']:>3} loc={st['locations']:>2} arcs={st['arcs']:>3}")

    (ROOT / "tour" / "manifest.json").parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "tour" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest -> tour/manifest.json  ({len(manifest['eras'])} eras, {len(manifest['centuries'])} centuries)")


if __name__ == "__main__":
    main()

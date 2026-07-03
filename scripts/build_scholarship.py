#!/usr/bin/env python3
"""
build_scholarship.py — the SCHOLARSHIP SHELF: one map per most-cited study.

"Most cited" is measured from the collection itself: surname mentions of the
corpus's 43 SCHOLAR persons across event descriptions/grounding notes
(Principe 90 · Newman 60 · Smith 21 · Hanegraaff 19 · Fowden 15 ·
Copenhaver 13 · Pereira 8 at last count). Each map takes one study, scopes the
corpus to the study's key topics/figures, and — deliberately — wears a
DIFFERENT visual style, with a design_note explaining how the aesthetic serves
the argument. Specs to specs/scholarship/, HTML to prototypes/.
"""
import json
from pathlib import Path
import build_map as bm

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT.parent / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json").read_text(encoding="utf-8"))
SPECDIR = ROOT / "specs" / "scholarship"
OUTDIR = ROOT / "prototypes"
SPECDIR.mkdir(parents=True, exist_ok=True)

WORLD_BBOX = [-10.0, 24.0, 60.0, 60.0]

STUDIES = [
    {"slug": "study-principe-secrets",
     "title": "The Secrets of Alchemy",
     "subtitle": "After Lawrence Principe (2013) — chrysopoeia taken seriously, from Zosimos to Boyle",
     "cites": 90, "style": "woodcut", "color_by": "era", "borders": 1500,
     "scope": {"themes": ["chrysopoeia", "philosophers-stone", "transmutation"], "region_bbox": WORLD_BBOX},
     "intro": "Principe's central move is to take gold-making seriously as rational, replicable laboratory practice rather than mysticism or fraud. This map follows his subject across the whole tradition: everywhere the corpus records transmutation claimed, tested, defended, or banned.",
     "prov": "Keyed to Lawrence M. Principe, The Secrets of Alchemy (2013) — the most-cited study in this collection (90 event-level citations). Scope = events tagged chrysopoeia, philosophers-stone, or transmutation. The map records claims and debates, and endorses none of them.",
     "design": "Woodcut & Rubric: stark black line and vermillion accent, the idiom of the early printed alchemical book Principe reads so closely. High contrast suits his argument — sharp claims, testable procedures, nothing misty."},
    {"slug": "study-newman-principe-fire",
     "title": "Alchemy Tried in the Fire",
     "subtitle": "After Newman & Principe (2002) — Starkey, Boyle, and Helmontian laboratory practice",
     "cites": 60, "style": "atlas", "color_by": "region", "borders": 1650,
     "scope": {"persons": ["george-starkey", "robert-boyle", "jan-van-helmont"], "region_bbox": [-12, 47, 8, 58]},
     "intro": "Newman and Principe reconstructed George Starkey's laboratory notebooks to show quantitative, Helmontian chymistry behind the 'Philalethes' legend — and Boyle learning at Starkey's bench. This map plots that triangle: Helmont's Brussels, Starkey's London, Boyle's Oxford.",
     "prov": "Keyed to William R. Newman & Lawrence M. Principe, Alchemy Tried in the Fire (2002); Newman is the collection's second most-cited scholar (60 event-level citations). Scope = events involving Starkey, Boyle, or van Helmont.",
     "design": "Modern Atlas: the cleanest, most quantitative of the six styles — graph-paper sensibility for a book about laboratory notebooks, mass balances, and reproducible experiment."},
    {"slug": "study-smith-artisans",
     "title": "Laboratories of Art",
     "subtitle": "After Pamela Smith — artisanal culture, embodied knowledge, and the alchemical workshop",
     "cites": 21, "style": "copperplate", "color_by": "region", "borders": 1600,
     "scope": {"persons": ["george-agricola", "lazarus-ercker", "anna-zieglerin", "paracelsus", "michael-maier"],
               "region_bbox": [4, 44, 20, 55]},
     "intro": "Smith reads alchemy as embodied, material practice — furnaces, assay balances, vermilion, the hands of craftspeople — against any purely textual or mystical reading. This map gathers the collection's artisan-practitioners: Agricola among the mines, Ercker in the assay house, Zieglerin staking her life on the lion's blood, Paracelsus the itinerant surgeon-chymist, and Maier, whose Atalanta Fugiens Smith reads as encoded laboratory procedure.",
     "prov": "Keyed to Pamela H. Smith's work on artisanal epistemology (The Business of Alchemy; cf. Dupré ed., Laboratories of Art) — third most-cited scholar in this collection (21 event-level citations). Scope = events involving Agricola, Ercker, Zieglerin, Paracelsus, or Maier: the artisanal-imperial workshop world.",
     "design": "Copperplate Engraving: sepia line-work on cream, the register of Agricola's De re metallica plates and the printed technical book — craft knowledge as image. The style *is* Smith's source base."},
    {"slug": "study-hanegraaff-academy",
     "title": "Esotericism and the Academy",
     "subtitle": "After Wouter Hanegraaff (2012) — the knowledge the university rejected",
     "cites": 19, "style": "noir", "color_by": "theme", "borders": 1500,
     "scope": {"themes": ["hermeticism", "magia-naturalis", "prisca-theologia"], "region_bbox": WORLD_BBOX},
     "intro": "Hanegraaff's history is of a body of learning — Hermetic, magical, 'ancient wisdom' — that the academy first embraced, then expelled, then forgot it had expelled. The map plots where that rejected knowledge actually lived and moved while it still had a home.",
     "prov": "Keyed to Wouter J. Hanegraaff, Esotericism and the Academy (2012) — 19 event-level citations in this collection. Scope = events tagged hermeticism, magia naturalis, or prisca theologia. Thin tagging of conceptual themes (see AUDIT.md) makes this a floor, not a census.",
     "design": "Alchemical Noir: luminous points on near-black — rejected knowledge as light in a darkened archive. The dark field literalizes Hanegraaff's thesis that this material was made invisible."},
    {"slug": "study-fowden-hermes",
     "title": "The Egyptian Hermes",
     "subtitle": "After Garth Fowden (1986) — Hermetism's late-antique Egyptian milieu",
     "cites": 15, "style": "lapis", "color_by": "era", "borders": 300,
     "scope": {"persons": ["hermes-trismegistus", "zosimos-of-panopolis", "bolos-of-mendes", "maria-the-jewess",
                            "ostanes", "stephanus-of-alexandria", "theosebeia"],
               "region_bbox": [18, 20, 42, 42]},
     "intro": "Fowden anchored the Hermetica in a real place and society: Greco-Egyptian temple culture in decline, where technical and philosophical Hermetism were one milieu. This map gathers that circle — Zosimos and Theosebeia, Maria, Bolos, the Hermetic name itself — in its Egyptian and east-Mediterranean home.",
     "prov": "Keyed to Garth Fowden, The Egyptian Hermes (1986) — 15 event-level citations in this collection. Scope = events involving the late-antique Hermetic-alchemical circle.",
     "design": "Lapis & Gold: ultramarine field and gilt points — the palette of late-antique luxury manuscripts and temple ceilings. A night-sky register for a corpus that claimed the authority of Egyptian priestly astrology."},
    {"slug": "study-copenhaver-hermetica",
     "title": "Hermetica",
     "subtitle": "After Brian Copenhaver (1992) — one manuscript's journey and its Renaissance detonation",
     "cites": 13, "style": "illuminated", "color_by": "region", "borders": 1492,
     "scope": {"persons": ["hermes-trismegistus", "marsilio-ficino", "pico-della-mirandola"], "region_bbox": [8, 34, 42, 48]},
     "intro": "Copenhaver's edition made the Corpus Hermeticum legible again — and told the story of its travel: composed in Roman Egypt, preserved in Byzantium, carried to Florence in 1460, translated by Ficino before Plato because Cosimo wanted Hermes first. This map draws that arc and its Renaissance consequences.",
     "prov": "Keyed to Brian P. Copenhaver, Hermetica (1992) — 13 event-level citations in this collection. Scope = events involving Hermes Trismegistus (as attributed author), Ficino, or Pico.",
     "design": "Illuminated Manuscript: parchment and gold with Cinzel capitals — the object at the centre of this story is a manuscript, and the map is dressed as one."},
    {"slug": "study-pereira-lull",
     "title": "The Alchemical Corpus Attributed to Raymond Lull",
     "subtitle": "After Michela Pereira (1989) — a corpus its author never wrote",
     "cites": 8, "style": "woodcut", "color_by": "era", "borders": 1400,
     "scope": {"persons": ["raymond-lull", "arnaud-de-villanova", "john-of-rupescissa"], "region_bbox": [-10, 35, 20, 52]},
     "intro": "Pereira mapped a paradox: medieval Europe's most influential alchemical corpus is attributed to a man who denounced alchemy. The pseudo-Lullian writings grew in the Catalan-Provençal world of Arnau de Vilanova and Rupescissa's prophetic pharmacy. A deliberately thin map of a deliberately slippery corpus.",
     "prov": "Keyed to Michela Pereira, The Alchemical Corpus Attributed to Raymond Lull (1989) — 8 event-level citations in this collection. Scope = events involving Lull, Arnau de Vilanova, or John of Rupescissa; the corpus's pseudepigraphy means every attribution here is the *tradition's* claim, not the map's.",
     "design": "Woodcut & Rubric: the pseudo-Lullian corpus lived through late-medieval and early-print copying — black letter and red rubric. The sparse, high-contrast page makes the thinness of the evidence part of the picture."},
]


def build(study):
    spec = {
        "title": study["title"], "subtitle": study["subtitle"],
        "directive": f"scholarship map: {study['title']} ({study['cites']} citations in collection)",
        "scope": study["scope"],
        "render": {"engine": "maplibre",
                   "basemap": {"style": study["style"], "show_modern_labels": False,
                               "historical_boundaries_year": study["borders"]},
                   "layers": ["points", "flows", "time-animation", "labels"],
                   "color_by": study["color_by"]},
        "narrative": {"intro": study["intro"], "provenance_note": study["prov"],
                      "design_note": study["design"]},
    }
    errors, _ = bm.validate_spec(spec)
    assert not errors and bm.check_provenance(spec), f"{study['slug']}: {errors}"
    (SPECDIR / f"{study['slug']}.mapspec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    compiled = bm.compile_spec(spec, DATA)
    (OUTDIR / f"{study['slug']}.html").write_text(bm.emit_html(compiled), encoding="utf-8")
    return compiled["stats"]


def main():
    for s in STUDIES:
        st = build(s)
        print(f"  {s['slug']:<28} [{s['style']:<11}] events={st['events']:>3} loc={st['locations']:>2} arcs={st['arcs']:>2}  ({s['cites']} cites)")
    print(f"\n{len(STUDIES)} scholarship maps -> prototypes/, specs -> specs/scholarship/")


if __name__ == "__main__":
    main()

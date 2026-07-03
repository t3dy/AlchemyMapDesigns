#!/usr/bin/env python3
"""
build_showcase.py — author + render the SHOWCASE map set for the gallery.

Three families beyond build_all.py's eras/centuries, chosen from vocabulary
slugs that are actually populated (checked against list_vocab.py counts):
  THEME maps   — one conceptual/operational theme traced across the whole corpus
  FIGURE maps  — one practitioner's evented footprint (points + itinerary arcs)
  REGION maps  — one region's alchemical culture through time

Writes specs to specs/showcase/ and HTML to prototypes/, and prints a manifest
line per map. All specs carry provenance notes and period borders (enforced).
"""
import json
from pathlib import Path
import build_map as bm

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT.parent / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json").read_text(encoding="utf-8"))
SPECDIR = ROOT / "specs" / "showcase"
OUTDIR = ROOT / "prototypes"
SPECDIR.mkdir(parents=True, exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)

WORLD_BBOX = [-10.0, 24.0, 60.0, 60.0]

CORPUS_NOTE = ("Events from the ALCHEMYTIMELINEMAP corpus (largely draft-status); locations are "
               "event geocodes, not residences. Absence on this map reflects gaps in the record.")

THEME_MAPS = [
    {"slug": "theme-distillation", "style": "atlas",
     "design": "Modern Atlas: the toolkit's cleanest register for its most technical theme — distillation as apparatus and procedure, read like a lab chart.", "title": "The Still and the Alembic",
     "subtitle": "Distillation across the alchemical world",
     "themes": ["distillation"], "color_by": "era", "borders": 900,
     "intro": "Distillation is alchemy's signature operation — the technique that travelled furthest and changed most hands. From late-antique Egypt through the Arabic laboratories to the Latin West, the still is the thread the whole tradition hangs on.",
     "prov": "Theme = events tagged 'distillation' (237 in corpus). " + CORPUS_NOTE},
    {"slug": "theme-transmutation", "style": "woodcut",
     "design": "Woodcut & Rubric: transmutation lived in printed polemic — decretals, disputations, broadsheets. Black line and red accent give it that pamphlet-war voice.", "title": "The Great Work",
     "subtitle": "Transmutation claims, debates, and prohibitions",
     "themes": ["transmutation"], "color_by": "era", "borders": 1300,
     "intro": "Where transmutation was claimed, tested, defended, and banned. The map records the *debate* as much as the practice — scholastic quaestiones, papal decretals, and courtroom assays all leave dots here.",
     "prov": "Theme = events tagged 'transmutation' (240 in corpus). The map records claims and debates about transmutation, and endorses none of them. " + CORPUS_NOTE},
    {"slug": "theme-quintessence", "style": "lapis",
     "design": "Lapis & Gold: the fifth essence was celestial matter brought down into the still. A night-sky field suits an idea that pointed above the elements.", "title": "The Quintessence",
     "subtitle": "The fifth essence and the medicine of long life",
     "themes": ["quintessence"], "color_by": "era", "borders": 1400,
     "intro": "John of Rupescissa's quinta essentia turned distillation toward medicine: the incorruptible essence extracted from wine, promising preservation of the body. Watch the idea radiate from 14th-century France.",
     "prov": "Theme = events tagged 'quintessence' (46 in corpus). " + CORPUS_NOTE},
    {"slug": "theme-operational-chemistry", "style": "copperplate",
     "design": "Copperplate Engraving: the register of the technical plate — furnaces, alembics, assay benches — for the corpus's biggest hands-on category.", "title": "The Working Laboratory",
     "subtitle": "Operational chemistry: the craft behind the doctrine",
     "themes": ["operational-chemistry"], "color_by": "era", "borders": 1500,
     "intro": "The corpus's largest single category: hands-on laboratory operation — apparatus, assay, procedure. This is alchemy as work rather than as text, and its geography is the geography of workshops, mints, and mines.",
     "prov": "Theme = events tagged 'operational-chemistry' (280 in corpus). " + CORPUS_NOTE},
    {"slug": "theme-fire-operations", "style": "noir",
     "design": "Alchemical Noir: three operations of fire drawn as fire — luminous points on darkness, one glowing colour per operation.", "title": "Operations of the Fire",
     "subtitle": "Sublimation, calcination, fermentation",
     "themes": ["sublimation", "calcination", "fermentation"], "color_by": "theme", "borders": 1200,
     "intro": "Three canonical operations, three colours. Sublimation raises, calcination reduces, fermentation quickens — a working vocabulary shared from Alexandria to Amsterdam.",
     "prov": "Themes = events tagged sublimation (44), calcination (42), or fermentation (35). Colour = first matching theme. " + CORPUS_NOTE},
    {"slug": "theme-philosophers-stone", "style": "illuminated",
     "design": "Illuminated Manuscript: parchment and gold for the tradition's great treasure-object; the Stone always belonged to the courtly, gilded register.", "title": "The Stone Itself",
     "subtitle": "Where the Philosopher's Stone was written about, sought, and staged",
     "themes": ["philosophers-stone", "chrysopoeia"], "color_by": "era", "borders": 1400,
     "intro": "The lapis philosophorum as an object of writing, patronage, and performance. Every dot is a claim about the Stone; none of them is the Stone.",
     "prov": "Themes = philosophers-stone (15) and chrysopoeia (5). The analyst's category here is 'claims and representations', never efficacy. " + CORPUS_NOTE},
    {"slug": "theme-hermetic-currents", "style": "lapis",
     "design": "Lapis & Gold: Hermetic learning claimed starry, priestly authority; ultramarine and gilt make the map read like the ceiling of a chapel.", "title": "Hermetic and Magical Currents",
     "subtitle": "Hermeticism, natural magic, and the emblematic turn",
     "themes": ["hermeticism", "magia-naturalis", "prisca-theologia", "emblem-alchemy", "emblematic-alchemy"],
     "color_by": "theme", "borders": 1500,
     "intro": "The learned-magical penumbra of alchemy: the Corpus Hermeticum's fortunes, magia naturalis, and the emblem books that turned laboratory doctrine into images.",
     "prov": "Themes = hermeticism (13), magia-naturalis (7), prisca-theologia, emblem-alchemy, emblematic-alchemy. A thin slice — the corpus under-tags conceptual themes (see AUDIT.md). " + CORPUS_NOTE},
]

FIGURE_MAPS = [
    {"slug": "figure-zosimos", "style": "lapis",
     "design": "Lapis & Gold: a visionary of late antiquity — dream-tribunals and spirit-stills — set on the deep blue of late-antique luxury pigment.", "title": "Zosimos of Panopolis",
     "subtitle": "The first alchemical author with a face, c. 300 CE",
     "persons": ["zosimos-of-panopolis"], "borders": 300, "bbox": [20, 22, 42, 42],
     "intro": "The earliest alchemist whose writings survive under his own name: visionary treatises, letters to Theosebeia, and working recipes, radiating from Greco-Roman Egypt.",
     "prov": "Events involving Zosimos (17 in corpus). Locations are where events are recorded, not a verified itinerary."},
    {"slug": "figure-jabir", "style": "illuminated",
     "design": "Illuminated Manuscript: the Jabirian corpus survives as manuscript culture; gold-on-parchment is its native dress.", "title": "Jabir ibn Hayyan",
     "subtitle": "The corpus that built Arabic alchemy, 8th–9th c.",
     "persons": ["jabir-ibn-hayyan"], "borders": 800, "bbox": None,
     "intro": "'Jabir' is as much a library as a man — hundreds of treatises, the sulphur–mercury theory, the science of balances. The dots trace where the corpus was written, read, and disputed.",
     "prov": "Events involving Jabir ibn Hayyan (14 in corpus). The historical Jabir is disputed; the map plots the corpus's footprint, not a biography."},
    {"slug": "figure-al-razi", "style": "atlas",
     "design": "Modern Atlas: the most operational author of early alchemy — apparatus lists and procedures — deserves the plainest, most legible style.", "title": "Abu Bakr al-Razi",
     "subtitle": "The physician-chymist of Rayy and Baghdad, c. 865–925",
     "persons": ["al-razi"], "borders": 900, "bbox": None,
     "intro": "Al-Razi's Secret of Secrets replaced allegory with apparatus lists and procedure — the most operational text of early alchemy, from the hospitals of Rayy and Baghdad.",
     "prov": "Events involving al-Razi (13 in corpus)."},
    {"slug": "figure-roger-bacon", "style": "woodcut",
     "design": "Woodcut & Rubric: scholastic black-letter for the Oxford Franciscan; stark contrast for a career of sharp claims and condemnations.", "title": "Roger Bacon",
     "subtitle": "Scientia experimentalis and the defence of alchemy, 13th c.",
     "persons": ["roger-bacon"], "borders": 1279, "bbox": None,
     "intro": "The Oxford Franciscan who folded alchemy into a programme of experimental science and prolongation of life — between Oxford, Paris, and the papal court.",
     "prov": "Events involving Roger Bacon (13 in corpus)."},
    {"slug": "figure-paracelsus", "style": "copperplate",
     "design": "Copperplate Engraving: Paracelsus's afterlife is a print phenomenon — surgery books, pamphlet wars — so the map wears the printed page.", "title": "Paracelsus in the Corpus",
     "subtitle": "The evented footprint of Theophrastus von Hohenheim",
     "persons": ["paracelsus"], "borders": 1530, "bbox": None,
     "intro": "The corpus's Paracelsus events — publications, appointments, condemnations. For the curated, sourced life-route, see the companion journey map.",
     "prov": "Events involving Paracelsus (14 in corpus). Complements the curated journey-paracelsus map, which is the sourced itinerary."},
    {"slug": "figure-michael-maier", "style": "copperplate",
     "design": "Copperplate Engraving: Atalanta Fugiens is literally a book of copperplate emblems (de Bry, 1617); the map borrows its own subject's medium.", "title": "Michael Maier",
     "subtitle": "Emblems, courts, and the Atalanta Fugiens, c. 1568–1622",
     "persons": ["michael-maier"], "borders": 1600, "bbox": None,
     "intro": "Imperial physician, Rosicrucian apologist, author of the multimedia emblem book Atalanta Fugiens — between Prague, the German courts, and England.",
     "prov": "Events involving Michael Maier (11 in corpus)."},
    {"slug": "figure-boyle-starkey", "style": "noir",
     "design": "Alchemical Noir: two careers half in shadow — Starkey behind the 'Philalethes' mask, Boyle's chymistry kept from print. Noir for the hidden half.", "title": "Boyle & Starkey",
     "subtitle": "The sceptical chymist and his American tutor, 17th c.",
     "persons": ["robert-boyle", "george-starkey"], "borders": 1650, "bbox": [-12, 48, 4, 58],
     "intro": "George Starkey — Harvard-trained, writing as 'Eirenaeus Philalethes' — taught Robert Boyle his laboratory chymistry. Two careers that between them bridge alchemy and the Royal Society.",
     "prov": "Events involving Boyle (8) or Starkey (6). Starkey's American years fall outside the corpus's geocoding."},
    {"slug": "figure-newton", "style": "noir",
     "design": "Alchemical Noir: a million secret words. The darkness is the point — Newton's alchemy was private for two centuries.", "title": "Newton the Chymist",
     "subtitle": "The private alchemy of a public natural philosopher",
     "persons": ["isaac-newton"], "borders": 1700, "bbox": [-8, 49, 4, 56],
     "intro": "Newton's million-plus words of chymical manuscript stayed private for centuries. The corpus events mark where that hidden labour surfaced — Cambridge, London, the Mint.",
     "prov": "Events involving Isaac Newton (5 in corpus). A deliberately thin map: most of Newton's alchemy is manuscript, not event."},
]

REGION_MAPS = [
    {"slug": "region-egypt", "style": "lapis",
     "design": "Lapis & Gold: Egypt is the tradition's sacred deep past; ultramarine and gilt give the taproot its temple-ceiling register.", "title": "Alchemical Egypt",
     "subtitle": "Alexandria, Panopolis, and the roots of the art",
     "regions": ["Egypt"], "bbox": [24, 21, 37, 33], "color_by": "era", "borders": 300,
     "intro": "The tradition's taproot: temple metallurgy, Greco-Egyptian recipe papyri, Zosimos's visions, and the Arabic inheritors. The densest single region in the corpus.",
     "prov": "Region = 'Egypt' (124 events). " + CORPUS_NOTE},
    {"slug": "region-italy", "style": "illuminated",
     "design": "Illuminated Manuscript: Medici patronage, humanist manuscripts, gilded court culture — Italy's alchemy arrived dressed like this.", "title": "Alchemical Italy",
     "subtitle": "Courts, universities, and the Hermetic revival",
     "regions": ["Italy"], "bbox": [6, 36, 19, 47.5], "color_by": "era", "borders": 1492,
     "intro": "From Salerno and the scholastic faculties to Ficino's Florence and the print shops of Venice — Italy is where alchemy met humanism.",
     "prov": "Region = 'Italy' (83 events). " + CORPUS_NOTE},
    {"slug": "region-england", "style": "copperplate",
     "design": "Copperplate Engraving: from Ripley's printed verse to Royal Society plates, English alchemy is a print-culture story.", "title": "Alchemical England",
     "subtitle": "From Ripley's verse to the Royal Society",
     "regions": ["England"], "bbox": [-6, 49.5, 2, 56], "color_by": "era", "borders": 1600,
     "intro": "A late but intense alchemical culture: monastic verse, Tudor patents and prosecutions, Dee's library, Ashmole's antiquarianism, and the chymistry of Boyle and Newton.",
     "prov": "Region = 'England' (77 events). " + CORPUS_NOTE},
    {"slug": "region-france", "style": "woodcut",
     "design": "Woodcut & Rubric: Paris condemnations and university disputation — black letter, red rubric, hard edges.", "title": "Alchemical France",
     "subtitle": "Universities, prophecy, and the quintessence",
     "regions": ["France", "France/Alsace"], "bbox": [-5, 42, 9, 51.5], "color_by": "era", "borders": 1300,
     "intro": "Paris condemnations, Montpellier medicine, Rupescissa's prophetic pharmacy, Flamel's posthumous legend — France as alchemy's argumentative centre.",
     "prov": "Regions = 'France' (67 events) + 'France/Alsace' (7). " + CORPUS_NOTE},
    {"slug": "region-iberia", "style": "atlas",
     "design": "Modern Atlas: the translation crossroads needs maximum legibility — routes and centres read plainly, nothing ornamental in the way.", "title": "Iberian Crossroads",
     "subtitle": "Translation, transmission, and the pseudo-Lullian corpus",
     "regions": ["Iberia", "Catalonia"], "bbox": [-10, 35, 4.5, 44.5], "color_by": "era", "borders": 1200,
     "intro": "Toledo and the translation movement made Iberia the door through which Arabic alchemy entered Latin Europe; later the peninsula grew its own pseudo-Lullian tradition.",
     "prov": "Regions = 'Iberia' (40 events) + 'Catalonia' (1). " + CORPUS_NOTE},
    {"slug": "region-bohemia-austria", "style": "noir",
     "design": "Alchemical Noir: Rudolfine Prague after dark — court spectacle, favour and imprisonment, gold arcs on black.", "title": "The Danubian World",
     "subtitle": "Bohemia and Austria: alchemy at the Habsburg courts",
     "regions": ["Bohemia", "Austria"], "bbox": [9, 46, 19.5, 51.5], "color_by": "era", "borders": 1600,
     "intro": "Rudolfine Prague and the Austrian lands: the most concentrated court patronage of alchemy in Europe, with its own economy of favour, imprisonment, and spectacle.",
     "prov": "Regions = 'Bohemia' (37 events) + 'Austria' (25). " + CORPUS_NOTE},
]


def render_block(color_by, borders, labels=True, style="atlas"):
    layers = ["points", "flows", "time-animation"] + (["labels"] if labels else [])
    return {"engine": "maplibre",
            "basemap": {"style": style, "show_modern_labels": False,
                        "historical_boundaries_year": borders},
            "layers": layers, "color_by": color_by}


def build(spec, slug):
    errors, _ = bm.validate_spec(spec)
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
    rows = []
    for m in THEME_MAPS:
        spec = {"title": m["title"], "subtitle": m["subtitle"],
                "directive": f"theme map: {', '.join(m['themes'])}",
                "scope": {"themes": m["themes"], "region_bbox": WORLD_BBOX},
                "render": render_block(m["color_by"], m["borders"], labels=False, style=m["style"]),
                "narrative": {"intro": m["intro"], "provenance_note": m["prov"], "design_note": m["design"]}}
        st = build(spec, m["slug"])
        rows.append((m["slug"], st))
    for m in FIGURE_MAPS:
        scope = {"persons": m["persons"]}
        if m.get("bbox"):
            scope["region_bbox"] = m["bbox"]
        spec = {"title": m["title"], "subtitle": m["subtitle"],
                "directive": f"figure map: {', '.join(m['persons'])}",
                "scope": scope,
                "render": render_block("region", m["borders"], labels=True, style=m["style"]),
                "narrative": {"intro": m["intro"], "provenance_note": m["prov"], "design_note": m["design"]}}
        st = build(spec, m["slug"])
        rows.append((m["slug"], st))
    for m in REGION_MAPS:
        spec = {"title": m["title"], "subtitle": m["subtitle"],
                "directive": f"region map: {', '.join(m['regions'])}",
                "scope": {"regions": m["regions"], "region_bbox": m["bbox"]},
                "render": render_block(m["color_by"], m["borders"], labels=False, style=m["style"]),
                "narrative": {"intro": m["intro"], "provenance_note": m["prov"], "design_note": m["design"]}}
        st = build(spec, m["slug"])
        rows.append((m["slug"], st))

    for slug, st in rows:
        print(f"  {slug:<28} events={st['events']:>3} loc={st['locations']:>2} arcs={st['arcs']:>3}")
    print(f"\n{len(rows)} showcase maps -> prototypes/, specs -> specs/showcase/")


if __name__ == "__main__":
    main()

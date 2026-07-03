#!/usr/bin/env python3
"""list_vocab.py — print the controlled vocabulary a MapSpec may reference.

So the /buildmap skill can map a fuzzy directive onto REAL slugs (Invariant #4)
without reading the whole data.json.

Each slug is printed with the number of events that actually carry it, so an
author knows at authoring time whether a theme/person will produce a populated
map or an empty one (the corpus's theme tagging is thin — see AUDIT.md).
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "ALCHEMYTIMELINEMAP" / "site" / "data" / "data.json"


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


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    events = d.get("events", [])

    concept_use, person_use, region_use = {}, {}, {}
    for e in events:
        for c in parse_list(e.get("concepts_involved")):
            concept_use[c] = concept_use.get(c, 0) + 1
        for p in parse_list(e.get("persons_involved")):
            person_use[p] = person_use.get(p, 0) + 1
        r = e.get("region")
        if r:
            region_use[r] = region_use.get(r, 0) + 1

    concepts = sorted((c["slug"], c.get("label", c["slug"])) for c in d.get("concepts", []))
    persons = sorted((p["slug"], p.get("name", p["slug"])) for p in d.get("persons", []))
    regions = sorted({l.get("region") for l in d.get("locations", []) if l.get("region")})
    years = [e.get("date_start_year") for e in events if isinstance(e.get("date_start_year"), int)]

    def flag(n):
        return "  (NO EVENTS)" if n == 0 else ""

    print("=== CONCEPT SLUGS (themes) — with event counts ===")
    for slug, label in concepts:
        n = concept_use.get(slug, 0)
        print(f"  {slug:<26} {n:>4}  {label}{flag(n)}")
    print("\n=== PERSON SLUGS — with event counts ===")
    for slug, name in persons:
        n = person_use.get(slug, 0)
        print(f"  {slug:<26} {n:>4}  {name}{flag(n)}")
    print("\n=== REGION NAMES — with event counts ===")
    for r in regions:
        print(f"  {r:<26} {region_use.get(r, 0):>4}")
    print(f"\n=== YEAR RANGE ===\n  {min(years)} to {max(years)}  ({len(events)} events)")
    print("\n=== ENUMS (from schema) ===")
    print("  era: ANTIQUITY LATE_ANTIQUE MEDIEVAL RENAISSANCE EARLY_MODERN ENLIGHTENMENT")
    print("  basemap.style: atlas copperplate illuminated noir woodcut lapis (legacy: parchment sepia-toner muted-vector modern-osm)")
    print("  layers: points flows time-animation heatmap network labels")
    print("  color_by: region theme era person")
    print("\nNote: a MapSpec will not compile without narrative.provenance_note.")


if __name__ == "__main__":
    main()

---
name: network
description: Author a scholarly-network or patronage map — relationships between people (correspondence, teacher-student, patron-client, citation), e.g. "/network the Hartlib circle". Adds a curated, typed, evidence-bearing subject to networks.json and renders it. Use when the user wants to map a constellation of people, not one person's travels.
---

# network — the scholarly-network / patronage template

You are authoring a curated network of person-to-person ties. The corpus has NO usable
relationship data (the `relationships` table is just type-names; co-presence is nearly
empty), so the network is a **curated, evidence-typed artifact you author by hand** —
the honest design the historian demanded. Follow this loop.

## Inputs
- The constellation (a circle / court / movement) is in `$ARGUMENTS`. If empty, ask.

## Step 1 — Decide the members (nodes)
List the people in the constellation. For each node: `id` (kebab slug), `label`,
`slug` (the ALCHEMYTIMELINEMAP person slug if one exists, else `null`), `lat`, `lon`
(their primary associated city — a real place), `role`, and `year` (when they enter
the story). Include non-corpus connectors (e.g. Hartlib, Mersenne) as nodes with
`slug: null` when the network needs them.

## Step 2 — Author the edges (the whole point)
Each edge is `{source, target, type, direction, weight, evidence, survives, note}`:
- `type` ∈ `corresponded | taught | studied-under | cited | collected |
  collaborated | influenced | polemicized-against | patron-of | dedicated-to`.
  Enmity counts — the Republic of Letters ran on feuds. `dedicated-to` is a CLAIM of
  patronage, not proof of it; keep it distinct from `patron-of`.
- `direction`: true for asymmetric ties (patron-of, taught, cited) where source→target
  is meaningful; false for mutual ties (corresponded, collaborated).
- `weight`: strength/magnitude (e.g. number of surviving letters, years of patronage).
- `evidence`: `attested` | `inferred`. `survives`: does direct documentary evidence
  survive? This drives the survival-bias toggle — set it honestly.
- `note`: the citation or the claim (a named scholar / primary source).

## Step 3 — Write the survival-bias caveat
In `provenance_note`, name what the map does NOT show — especially that surviving
correspondence is a survival map, not a sociability map, and which figures are
over-centred because their papers happened to survive.

## Step 4 — Add to networks.json and render
Append your subject (`slug`, `title`, `subtitle`, `theme`, `provenance_note`, `nodes`,
`edges`) to the `subjects` array in `data/networks.json` (default themes: patronage →
`illuminated`, lineage/citation → `copperplate`, movement → `atlas`, correspondence →
`noir`). Then:
```
python scripts/build_network.py
```
Deep-link your subject at `/prototypes/network.html?subject=<slug>`.

## Step 5 — Report
Give the title, node/edge counts, how many edges survive vs. are inferred, the
deep-link URL, and the survival caveat as the headline limitation.

## Guardrails
- Every edge needs a `note` (citation/claim) and an honest `evidence`/`survives`.
- Never auto-upgrade a `cited` edge into "influence" in prose — that's an analyst's
  category. Keep the actors' own language reachable in `note`.
- See `data/networks.json` for the reference shape (four worked subjects).

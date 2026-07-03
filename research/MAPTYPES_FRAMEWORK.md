# Map-Type Framework, Style Guide & Templates

Synthesis of a consultation between a historian of early-modern science (Yates /
Biagioli / Grafton lineage) and a narrative/experience designer (Inkle / Pudding /
Pentiment lineage), on extending the MapSpec toolkit with reusable **map-type
templates**. See `../tour/index.html` for current features.

## The one thing they both demanded first

**Promote the 8-row `relationships` table into typed, directed, weighted,
evidence-bearing person-to-person edges.** Today's arcs model *one person's
itinerary* (consecutive events at different places). That cannot express "A taught
B" or "patron → client." Without this edge model, the Network and Patronage
templates are — the designer's word — *vaporware*. This is the highest-leverage
single change in the system.

Proposed edge schema (new table or extension):
```
edge: { source_slug, target_slug, type, direction, weight, date_start, date_end,
        evidence, source_method, review_status, confidence }
  type      ∈ corresponded | taught | studied-under | cited | polemicized-against
            | co-present | patron-of | dedicated-to
  weight    = magnitude (e.g. # surviving letters, stipend size, years)
  evidence  = "attested" | "inferred" | "reconstructed-from-publication" | "lost"
```

## A template = three locked parts + one open part

| Part | Owns | Who fills it |
|------|------|--------------|
| **MapSpec preset** | scope query + lens + theme + layers, locked to defensible defaults | the template |
| **Uncertainty contract** | which evidence/confidence encodings are *mandatory* | the template |
| **Narrative scaffold** | fill-in-the-blank story prompts ("the turn", "the last beat") | the **author** (historian) |
| **Viewer onboarding** | one line naming the reading stance | the template |

A template should **refuse to compile without a populated `provenance_note`** and
per-feature citations. Honesty is the default, not an option.

---

## The three archetypes

### 1. `/journey` — Biographical Journey (e.g. Giordano Bruno)
- **Story shape:** picaresque that becomes a noose; freedom narrowing into fate.
- **Render:** a path that *draws itself* city-by-city, camera trucking ahead so the
  ending is unknown. Node size = dwell time (time-in-place), not just arrows.
- **Honesty (historian):** do NOT make the 1600 stake the teleological vanishing
  point — "he did not live toward the stake." The reveal must *withhold* the ending;
  a scrubber must let the reader stand in 1586 Wittenberg knowing nothing of Rome.
- **Segment types on every leg:** solid = attested presence · long-dash = inferred
  transit · dotted = reconstructed-from-publication (we often date him only by where
  a book was printed).
- **Defaults:** theme `noir`, lens `lives`, `play` on by default, single moving dot —
  hide all other people/texts/density. Mobile = scroll-to-advance.
- **Supported by today's data.** Build this first.

### 2. `/network` — Scholarly Network
- **Story shape:** accretion — a web thickening until structure becomes obvious;
  payoff is recognition ("they were all connected through Padua").
- **Core interaction:** pivot on a node — click a person, graph re-centers, >2-hop
  neighbors dim. The wow: clicking a *minor* figure reorganizes everything → "the
  centre is a choice, not a fact."
- **Where drama and rigor meet:** that same reorganization IS the historian's
  survival-bias warning — Mersenne looks central partly because his papers survived.
  Provide a toggle: *show only what survives* vs *show reconstructed*.
- **Render:** edges appear in chronological order; dead nodes fade to grey but stay
  (the dead anchor the living). Edge labels on hover only — no hairball.
- **Actor/analyst:** "network" and "influence" are our categories. Draw a citation
  edge; do not let the UI call it influence.
- **Blocked on the edge model above.**

### 3. `/patronage` — Patronage Map
- **Story shape:** flow and dependency; the menace of what happens when it stops.
  Register is power, not friendship.
- **Render:** directed arcs with arrowheads, thickness = magnitude/duration, anchored
  to courts as fixed gravity-well hubs. The wow: remove one patron (a death, a fall
  from favour) and dependent clients blink to precarity — fragility in one gesture.
- **Honesty (Biagioli):** patronage is asymmetric exchange (protection/legitimacy
  down, honour/credit up), unstable and time-bound. A dedication is a *claim* of
  patronage, often aspirational or refused — encode "dedication offered" ≠ "patronage
  documented."
- **Actor/analyst (the sharpest in the project):** actors spoke of love, service,
  friendship; we analyse a power economy. The map must *mark that it has translated*
  — keep the "devoted servant" language reachable on hover beneath the power arcs.
- **Defaults:** theme `illuminated` (courts, gold, wealth), reign-cycle scrubber.

---

## Style guide (binding conventions)

- **Line style = evidence:** solid = documented · long-dash = inferred · dotted =
  conjectural/lost.
- **Opacity = confidence. Colour = category, never confidence.** Conflating ordinal
  (confidence) with categorical (type) is the single commonest map lie.
- **Date uncertainty** = node halo or scrubber band, never a false point-date.
- **Citation is a layer, not a caption:** every node/edge hover shows its source
  (scholar or primary source) from `source_method` / `review_status` / `confidence`.
- **A persistent "what this map does NOT show" note** — the omissions are the
  argument. Network maps must state the survival caveat in plain language.
- **Motion:** ease-in-out always (linear reads as a machine; eased reads as breath);
  one moving thing at a time during a reveal.
- **Legend is progressive:** show only encodings currently live; animate the legend
  in *with* the layer it explains.
- **Accessibility:** respect `prefers-reduced-motion` (snap instead of animate);
  every reveal has a text transcript; never meaning-in-colour-alone (weight must also
  be a number on hover).
- **Theme ↔ type pairing (recommended, override-able):** noir → journey · copperplate
  → network · illuminated → patronage · atlas → neutral / accessibility fallback.
  The template recommends and *requires an explicit override* rather than free pick.

## Build order (both experts, converged)

1. **Person-to-person edge model** — unblocks Network + Patronage. Highest leverage.
2. **`/journey` end-to-end** — self-drawing animated path + narrative scaffold +
   scrollytelling embed. Fully supported by today's data; it's the one that makes
   people *feel* something.
3. **The narrative-scaffold mechanism** — the fill-in-the-blank prompt system all
   three templates share; keeps the historian writing meaning, not JSON.

> Historian's bottom line: "Get those three and you have a scholarly instrument. Skip
> them and you have a very beautiful way of being confidently wrong."

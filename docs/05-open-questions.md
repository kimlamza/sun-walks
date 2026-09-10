# 05 — Open questions

Ordered by what they block.

**Resolved so far:**
- Location: **Canmore, Alberta (51.09°N, 115.36°W), 50 km radius**
- Sequencing: **Phase 1** walk data and dog filter → **Phase 2** sun engine, with an early geometry spike
- Purpose: **a demonstration of method**, not a comprehensive production tool
- Shortlist: **10 walks**, selected for contrast rather than coverage
- The dog: **Jasper** — medium Lab-type, assumed 6–7 `[assumption]`
- Validation: **against physics and independent tools, not local experience** — see `07`
- Off-leash: recorded as metadata, **not used as a ranking axis** — it is a near-constant "no"

- Repository location: **`C:\Claude\Work\Sun-Walks\` is the repo.** Docs and code together; exclude code folders in Obsidian's Settings → Files & Links if the clutter irritates
- Time budget: **three blocks of 2–3 hours this week.** Plan recut in `08-three-session-plan.md`
- Scope for week one: **five walks, not ten** — the minimum contrast set, scaled up later

---

## Blocking — needed before code

### Q1. Can James answer three questions?
**Blocks:** nothing hard, but cheap and high-value if the answer is yes.

If James is reachable, three questions are worth more than a week of desk research:

1. **Jasper** — actual age, rough weight, anything that limits distance or heat tolerance? (Currently assumed 6–7, Lab-type, medium.)
2. **Any walks he already does**, and any he avoids?
3. **Sun and shade** — is there anywhere he knows is cold and shaded all winter, or anywhere that is reliably a sun trap?

Question 3 is a genuine validation data point of a kind nothing else on this project can supply. Not blocking — the model validates without it — but it converts a modelled claim into a corroborated one.

---

### Q2. Which five walks?
**Blocks:** session 3.

The contrast set in `08` needs five named candidates: a deep valley floor, a south-facing bench, an east-facing route, a west-facing route, and one high and open. All five are selectable from the DEM and a map without local knowledge — aspect, elevation and skyline height are all computable.

**I can propose five candidates from desk research if useful.** Otherwise James's answers to Q1 may name them.

---

## Shapes Phase 1

### Q3. Winter or summer first?
The shadow effect is dramatic Nov–Feb and mild Jun–Aug. In July the question inverts — you want **shade** for Jasper on hot rock, and Labs overheat badly.

Same engine either way, so this is about which to build and demonstrate first.

**Recommendation: winter.** The effect is strongest, the model is easiest to check, and a walk swapping from "sunny" to "shaded" between 09:00 and 15:00 is the most convincing thing the tool can show.

### Q4. Which passes should the tool assume?
Kananaskis Conservation Pass, Parks Canada annual, both, neither. For a demonstration it can simply display the requirement rather than filter on it.

**Recommendation: display only in v1.** Filtering needs a fact about James that nobody has.

---

## Decide during the build

### Q6. How much weather beyond sun?
Temperature and wind matter more here than the UK draft assumed — −25 °C with wind is a hard stop regardless of sunshine, and +25 °C is a hard stop for a Lab.

**Recommendation: temperature and wind chill as ranking factors with a stated floor and ceiling; rain and snow as displayed warnings.**

### Q7. Snow and trail conditions
Snow depth and packed-versus-unbroken change duration dramatically and are in no feed you can rely on.

**Recommendation: seasonal duration multiplier, stated as an approximation.**

### Q8. Does "% of route in sun" need weighting?
A route sunny on the ascent and shaded on the return may deserve a different score from one evenly half-shaded. Uniform sampling treats them identically.

**Recommendation: uniform for v1.**

### Q9. Threshold calibration
The DNI bands (`02` §4) and confidence bands (`02` §8) are reasoned starting points, not findings. They would need a season of real use to calibrate — which this project will not have.

**For a demonstration piece, that is fine, provided it is stated.** Flagged `[verify]` throughout; do not present them as established.

---

## Known unknowns — `[verify]` at build time

Canadian dataset and regulation details carry more uncertainty than the UK equivalents. Every one needs checking against a live source before it reaches user-facing text.

**Regulations and access**
- Banff National Park leash rules — believed leash-at-all-times, no off-leash anywhere in the park
- Kananaskis Country leash rules by park class
- Town of Canmore off-leash areas and wildlife corridor restrictions
- Kananaskis Conservation Pass and Parks Canada pass — pricing and exact boundaries
- Seasonal closure windows, including Kananaskis winter wildlife closures
- Elk calving and rut advisory zones and dates
- ~~Whether Alberta still observes DST~~ — **RESOLVED 10 Sep 2026.** The Official Time Act (18 June 2026) puts Alberta on permanent UTC−6 from November 2026. The 2021 referendum result has been reversed by legislation. Winter solstice: sunrise 09:46, sunset 17:30. See `01-data-sources.md` §D

**Data availability and format**
- Parks Canada trail layer on open.canada.ca — existence, format, currency
- Alberta Parks / GeoDiscover Alberta trail and boundary data
- Town of Canmore open data portal — existence and contents
- NRCan HRDEM or Alberta LiDAR coverage of the Bow Valley
- ATES ratings — Kananaskis coverage, and whether machine-readable
- Avalanche Canada API terms and current region names
- Whether closures are published in any machine-readable form
- Open-Meteo parameter names and the current HRDPS model identifier
- Streamlit Community Cloud resource limits

**Validation resources** — see `07`
- PVGIS horizon API coverage at 51°N in Canada
- Which Canmore, Banff, Alberta 511 and ski-area webcams are live, and their coordinates
- Whether GRASS or WhiteboxTools installs cleanly on Windows (WhiteboxTools is the easier of the two)

**The pattern worth noting:** trail geometry is well served by open data; **the rules about trails are not**. That is the single most important structural fact about building this in Canmore, and it is why `06` treats the rules layer as hand-curated with a review date rather than something to automate.

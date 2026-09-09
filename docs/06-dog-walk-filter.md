# 06 — The dog-walk filter (Phase 1)

**Verdict on your proposal: yes, do this first. It is the right sequencing, with one modification.**

Your instinct — find the walk data, filter it down to good dog walks, and only then look at the sun — is correct for four reasons:

1. **It de-risks the thing most likely to kill the project.** The sun engine is a solvable geometry problem. Curating a trustworthy walk list is a chore with no intellectual reward, and that is what usually stalls projects like this.
2. **The filter is severe enough to change the shape of everything downstream.** In the Bow Valley, jurisdiction, leash law, wildlife closures and avalanche terrain may remove most of the candidate set. If 400 OSM paths become 25 usable walks, that changes what the sun engine needs to be.
3. **The output is useful on its own.** "The definitive list of good dog walks within 50 km of Canmore, with season flags and pass requirements" has standalone value. If the sun piece never gets built, Phase 1 was still worth doing. Few first projects have that property.
4. **It is a gentler coding on-ramp.** Loading, filtering and joining tabular data is the easiest thing to learn in Python. Ray-marching a DEM is not.

**The modification: run a short sun-engine spike early, in parallel.** Synthetic test terrains plus one real DEM tile, roughly a hundred lines of code, one afternoon. The purpose is not to build the engine — it is to answer *"does this model reproduce shadow geometry I can verify independently?"* If the answer is no, the project premise is wrong, and you want to know that in week one rather than week six.

Since you have not been to Canmore, that spike is validated against **physics and independent implementations, not memory** — synthetic DEMs with hand-computable answers, then a cross-check against GRASS or QGIS. This turns out to be a stronger test than local experience anyway. See `07-validation-without-local-knowledge.md`.

Do the spike, park it, then spend the bulk of Phase 1 on the walk data.

---

## The jurisdictional picture

**This is the first thing to establish, because everything else derives from it.** Within 50 km of Canmore there are at least four authorities with different rules, different closures and different payment regimes.

| Jurisdiction | Authority | Dogs | Pass to park |
|---|---|---|---|
| **Town of Canmore** | Municipal | Leash bylaw, with **designated off-leash areas** (Quarry Lake and others) | None |
| **Banff National Park** | Parks Canada | **On leash at all times, everywhere. No off-leash anywhere in the park** | Parks Canada pass |
| **Kananaskis Country** — Bow Valley PP, Spray Valley PP, Bow Valley Wildland PP, Peter Lougheed PP | Alberta Parks | On leash; specifics vary by park class | **Kananaskis Conservation Pass** |
| **Canmore Nordic Centre PP** | Alberta Parks | Dogs on designated trails only; winter rules differ from summer | Kananaskis pass `[verify]` |
| **Stoney Nakoda Nation lands** | First Nation | Permission required — not public trails | N/A — exclude |

All `[verify]`. Regulations and boundaries change, and this is the layer most likely to go stale.

### The finding that changes the design

**Off-leash is not permitted on trails anywhere in the area** — Banff National Park, Kananaskis Country and the Town of Canmore all require a leash on trail. Banff enforces with fines up to **$25,000**.

**Designated off-leash *parks* do exist**, and an earlier version of this document was wrong to imply otherwise:

- **Quarry Lake, Canmore** — two official off-leash zones (the meadow and the dog pond). The 1 km loop trail has reverted to on-leash `[verify]`. Maximum three off-leash dogs per person under the updated animal control bylaw; off-leash fines start at $100
- **Elk Run**, Canmore — off-leash area
- **Banff townsite** has its own off-leash dog park

Consequence for the design is unchanged: **do not build off-leash as a ranking axis across hiking trails.** On trails it is a constant "no", and a column that always reads the same is noise dressed as information. Record it as metadata; do not weight it.

If off-leash is what actually matters, that is a different and much smaller tool — a list of the handful of designated off-leash areas, not a ranking system across walks.

---

## Hazards specific to dogs in the Bow Valley

Not a footnote. These drive hard filters and seasonal gates.

| Hazard | Season | Why it matters for a dog |
|---|---|---|
| **Grizzly and black bear** | ~April–November (denning Nov–April) | A dog — loose or leashed — can provoke a defensive charge, and a loose dog can bring a bear back to you. Drives most seasonal closures |
| **Cougar** | Year-round | Resident in the Bow Valley. A dog is prey-sized. Documented incidents |
| **Elk** | **Calving May–June; rut Aug–Oct** | Habituated Canmore and Banff elk charge dogs aggressively. Plausibly the **highest-frequency** risk of anything on this list |
| **Coyote, wolf** | Year-round | Coyotes will take small dogs |
| **Avalanche terrain** | Roughly Nov–May | Life-safety. See below |
| **Cold** | Nov–March | Below about −15 °C paw damage and frostbite become real; crusted snow cuts pads |
| **Heat and scree** | Jul–Aug | Exposed rock gets very hot; no water on many ridge routes |
| **Ticks** | Spring | Rocky Mountain wood tick |
| **Porcupine** | Year-round | A veterinary trip, not a danger |
| **Wildlife corridors** | Varies | Canmore has designated corridors with restrictions — the whole point is to keep people and dogs out of them |

`[verify]` all seasonal windows against current Parks Canada, Alberta Parks and Town of Canmore guidance before any of this appears in user-facing text.

### On avalanche terrain

**Design rule: the app surfaces the official rating and current bulletin, and defers. It never computes a judgement and never calls a route safe.**

- **ATES** — Avalanche Terrain Exposure Scale — rates terrain **Simple / Challenging / Complex**. Parks Canada publishes ratings for many Banff trails; Kananaskis coverage is patchier `[verify]`
- **Avalanche Canada** publishes daily bulletins for **Banff Yoho Kootenay** and **Kananaskis** `[verify] region names`

Default behaviour: routes rated Challenging or Complex are **excluded from winter results entirely**, with an explanation rather than silence. A user can see them by explicitly opting in, and even then the tool shows the rating and links the bulletin without interpreting either.

This is a scope boundary, not a technical limitation. Avalanche assessment needs training and current field observation. A sunshine-ranking tool has no business implying otherwise.

---

## The dog: Jasper

James's dog. **Medium-sized, Labrador-type, assumed 6–7 years old** — `[assumption]`, not a verified fact. If James can confirm age, weight and heat tolerance, several thresholds below get firmer.

What this profile actually implies for the filter:

| Attribute | Filter consequence |
|---|---|
| Medium/large, Lab-type | **Distance:** comfortable to 12 km, tolerable to 15. **Ascent:** fine to ~600 m |
| Lab coat and build | **Heat intolerant.** Labs overheat badly. Above roughly 22 °C, water access and shade become hard requirements, not preferences — this is what drives the "find shade" mode |
| Cold tolerance | Fine to around −15 °C for a moderate walk. **Paws are the limiting factor**, not the body — crusted snow and ice cut pads |
| Water-loving | Streams and lakes are a positive. ⚠ Also a hazard in shoulder season — thin ice, and cold mountain water |
| Age 6–7 | No real restriction. Avoid very long days and sustained steep descent, which is harder on older joints than ascent |
| Size | Not a coyote target, unlike a small dog. But **a large dog is more likely to *provoke* an elk or a bear**, not less. Every wildlife risk above still applies, and the elk risk arguably increases |

**Two firm exclusions follow from the profile:** no scrambling or exposure (Ha Ling's upper section, EEOR, anything with chains), and no sustained sharp scree, which shreds pads.

**Recommendation: use this profile as the initial filter.** It cuts the candidate set meaningfully before any hand review, and it is defensible in the write-up because every threshold traces to a stated attribute rather than a preference.

---

## How many walks — and chosen how

**Recommendation: 10. Chosen for contrast, not coverage.**

You floated 15–20 and then 10. Ten is right, for three reasons:

1. **Rules curation is the cost.** Done properly — jurisdiction, closures, ATES, passes, source URL, review date — each walk is 15–20 minutes. Ten is an afternoon. Twenty is a day and a half of the least rewarding work in the project
2. **The ranking logic stops getting more interesting past about ten.** Below five, ranking is trivial and demonstrates nothing. Above fifteen, every additional row is repetition
3. **Every row has to be defensible.** For a demonstration piece, ten walks you can each justify beats thirty you cannot

### The selection criterion is not "the ten best walks"

This is the important shift, and it follows from the project being a demonstration of method rather than a production tool.

**If all ten walks return similar answers, the tool shows nothing.** Pick walks that will *disagree with each other* — that is what makes the output legible and the method visible.

Suggested contrast set:

| # | Type | What it demonstrates |
|---|---|---|
| 2 | **Deep valley floor, high south skyline** | The extreme case — the winter shadow effect the project exists for |
| 2 | **South-facing bench or slope** | Sun traps. The opposite extreme |
| 2 | **East-facing** | Morning sun, afternoon shade — shows the *time* dimension, not just place |
| 2 | **West-facing** | The mirror image. Together with the east pair, this is what proves the model is doing real work |
| 1–2 | **High, open, minimal horizon** | Control case. Should be sunlit whenever the sun is up. If it is not, the model is broken |

Then layer practical spread over the top: **at least one walk in each of the three jurisdictions** so the filter has something to do, and a mix of pass-required and free.

An east-facing walk and a west-facing walk swapping places between a 09:00 and a 15:00 query is the single most convincing thing this tool can show. Choose the set so that happens.

**Then add more later.** The structure supports it — `data/walks.csv` grows a row at a time, and nothing else changes.

---

## The filter, in tiers

Run in order. Each tier is cheaper to evaluate than the one after it.

### Tier 0 — hard exclusions (permanent)

A walk is out, always:

- Dogs prohibited
- Not legally accessible — private land, Stoney Nakoda land without permission
- Requires scrambling or technical terrain (Ha Ling's upper section, EEOR, anything with chains or exposure)
- Permanently closed
- Outside distance or ascent bounds
- Outside the 50 km radius

### Tier 1 — seasonal gates (date-dependent)

A walk is out *for this date*:

- Active wildlife closure — bear activity, denning, seasonal restriction
- Elk calving zone in May–June, or rut zone Aug–Oct
- Avalanche terrain (ATES Challenging or Complex) during the winter window
- Seasonal access closure — some Kananaskis areas close Dec 1 – Jun 15 `[verify]`
- Fire closure

**Every Tier 1 exclusion must be shown, not hidden.** "Walk X excluded — elk calving closure until 30 June" is useful. Silent removal is not.

### Tier 2 — suitability score (ranking, not exclusion)

For survivors:

| Factor | Notes |
|---|---|
| Surface and footing | Rock, root, mud, scree — affects paws |
| Water availability | Streams and lakes; critical in summer |
| Exposure | Wind and sun on ridges |
| Trailhead parking | Size, and whether it fills early. Grassi Lakes and Ha Ling are the known problems |
| Pass required | None / Banff / Kananaskis |
| Drive time | Meaningful at a 50 km radius |
| Crowding | Some trails are unpleasant with a dog on a summer weekend |
| Shade availability | For the **inverse** summer query |

### Then, and only then: the sun engine

Runs on the Tier 2 survivors. Never on anything that failed Tier 0 or Tier 1.

---

## Phase 1 deliverable

A curated table — CSV — of **10 walks**, one row each:

```
id, name, area, jurisdiction, pass_required,
trailhead_lat, trailhead_lon, gpx_file,
distance_km, ascent_m, duration_est_min,        ← derived
dogs_allowed, leash_required, off_leash_permitted,
ates_rating, avalanche_terrain,
closure_windows,                                 ← structured date ranges
wildlife_notes, bear_season, elk_zone,
surface, water_available, shade_level,
parking_size, fills_early, drive_time_min,
source_url, last_reviewed
```

Two fields carry disproportionate weight:

- **`source_url`** — the live official page for this trail's rules. The app links out rather than asserting a cached claim
- **`last_reviewed`** — the date you checked. Displayed. A rules layer without a review date is a liability

---

## How to get from OSM to a shortlist

1. **Overpass query** — paths, footways and hiking route relations within 50 km of Canmore. Expect a few hundred results, most of them useless: driveways, connector segments, unnamed spurs
2. **Automatic thinning** — drop unnamed segments under a length threshold, drop anything inside town limits that is a sidewalk, drop duplicates
3. **Assemble routes** — where `route=hiking` relations exist, use them. Otherwise this is where you decide what a "walk" is. That is judgement, not code
4. **Jurisdiction join** — spatially intersect against park boundary polygons from Parks Canada and Alberta Parks. This assigns rules automatically and is the highest-value automated step in Phase 1
5. **Desk review to 10** — you have not been to Canmore, so this is done from sources rather than memory: Parks Canada and Alberta Parks trail descriptions, guidebooks, AllTrails reviews read as a human, forums, and James. Select against the **contrast set** above, not against "best"
6. **Rules curation** — for the ten survivors only, fill in the rules columns from official sources. An afternoon
7. **GPX** — for each survivor, extract geometry from OSM or draw it yourself

**Steps 4 and 5 are where the leverage is.** Step 4 because a spatial join replaces hours of lookup. Step 5 because it is where the ten walks are actually chosen — and where the contrast criterion earns its place, since aspect and skyline are visible from the map and the DEM without ever having stood there.

Note what step 5 no longer requires: local memory. Aspect, elevation, valley width and skyline height all come out of the DEM you already have. **You can pick a deliberately contrasting set of walks from a desk in England** — what you cannot do from here is judge whether a trail is pleasant, which is what sources and James are for. See `07-validation-without-local-knowledge.md` §5.

---

## Suggested Phase 1 order

| # | Step | Done when |
|---|---|---|
| 1 | Toolchain set up, repo created, first commit pushed | Repo visible on github.com |
| 2 | Overpass query, results loaded, count printed | You can see how many candidates exist |
| 3 | Plot all candidates on a map | The scale of the problem is visible |
| 4 | **Sun spike** — 2–3 hand-drawn routes, one DEM tile, one instant | Model agrees with what you know about January shade |
| 5 | Park boundaries loaded, spatial join done | Every candidate carries a jurisdiction |
| 6 | Automatic thinning applied | Candidate list is reviewable by a human |
| 7 | Desk review down to 10, against the contrast set | The shortlist exists |
| 8 | Rules curation | Every row has `source_url` and `last_reviewed` |
| 9 | Phase 1 output: the shortlist table | **Useful on its own, with or without Phase 2** |

Then Phase 2 — the sun engine proper, per `03-app-design.md`.

**Step 4 is deliberately out of sequence.** It is the only step that can invalidate the whole premise, so it goes early, and it stays small.

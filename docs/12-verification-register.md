# 12 — Verification register

Everything this project asserts that has not been checked against a primary source. Ordered by what it affects, not by how easy it is.

**How to use it:** work down Tier 1 first. For each item, either confirm it, correct it, or record that it could not be established. Then tell me and I will update the code and the docs together — several of these live in `data/walks.csv` and in prose at the same time, so they need changing in step.

**Why this exists.** The project's purpose is to demonstrate method. A tool whose unverified assumptions are catalogued is more credible than one whose numbers merely look tidy. This register is part of the deliverable, not a snag list.

---

## Tier 1 — could make the tool wrong or misleading

### 1.1 Are dogs actually allowed on all ten walks?

**Never checked for five of them.** The original five were researched in `09-candidate-walks.md`; the five added later were chosen for geographic contrast and their dog rules were assumed, not confirmed.

| Walk | Status |
|---|---|
| Grassi Lakes | Leashed dogs confirmed |
| Grotto Canyon | ⚠ **Sources conflicted** — most said leashed dogs fine, one said pets not allowed. Unresolved |
| Montane Traverse | Leashed dogs confirmed |
| Tunnel Mountain | Leashed, Banff NP law |
| Quarry Lake | Off-leash zones plus on-leash loop `[verify current status]` |
| **Cougar Creek** | ⚠ **Assumed** |
| **Goat Creek** | ⚠ **Assumed** |
| **Heart Creek** | ⚠ **Assumed** |
| **Troll Falls** | ⚠ **Assumed** |
| **Lake Minnewanka** | ⚠ **Assumed** |

Sources: Alberta Parks trail pages for Kananaskis; Parks Canada for Banff.

### 1.2 Which pass does each trailhead need?

Two are literally marked `verify` in `data/walks.csv`; the rest are inferred from which park I believe they sit in. The Town of Canmore / Bow Valley Wildland boundary runs through the Montane and Cougar Creek area and is not obvious on the ground.

What I need, per walk: **none / Kananaskis Conservation Pass / Parks Canada pass**, and ideally the trailhead's parking area.

> **✅ Montane Traverse and Cougar Creek resolved, 11 September 2026.**
>
> **No hiking permit is needed for the Montane Traverse.** The vehicle pass depends entirely on where you park. From the **Cougar Creek parking lot** — the usual trailhead — **no pass is required**: that is municipal land governed by the Town of Canmore and exempt from park fees. Accessing the trail via provincial park sections instead does require a Kananaskis Conservation Pass.
>
> Both are now recorded as `none (Cougar Creek lot)` rather than a bare "none", because the nuance is the point: the answer is a property of the car park, not of the trail. Sources: Town of Canmore, Alberta Parks trail report for Montane Traverse.
>
> This also resolves Cougar Creek, which shares that trailhead.

| Walk | Currently recorded | Confidence |
|---|---|---|
| Montane Traverse | none (Cougar Creek lot) | **confirmed** |
| Cougar Creek | none (Cougar Creek lot) | **confirmed** |
| Goat Creek | Kananaskis | low — Spray Valley PP assumed |
| Heart Creek | Kananaskis | low |
| Troll Falls | Kananaskis | medium |
| Lake Minnewanka | Parks Canada | medium–high |
| Grotto Canyon | Kananaskis | medium–high |
| Grassi Lakes | Kananaskis | high — sourced |
| Tunnel Mountain | Parks Canada | high |
| Quarry Lake | none | high |

### 1.3 Does the mapped geometry match the walk people actually do?

> **✅ Largely resolved 11 September 2026.** `inspect_route.py` was written to cluster a walk's points and find nearby car parks. Findings:
>
> - **Heart Creek was two trails.** 144 points running south-east into the canyon, and 74 running **due west along the Trans-Canada** — the Heart Creek Bunker Trail. A third of its sun percentage came from a different walk. Excluded by name; result moved 0/7/9 → 0/12/14
> - **Troll Falls included the Marmot Creek extension**, which climbs into shadier ground. Excluded; result moved 96/89/93 → **100/100/100**, taking it from fourth to first
> - **Lake Minnewanka spanned 18.9 km** against 8 km recorded — roughly 38 km out and back. Trimmed to 4 km from the day use area at 51.2482, −115.4968. Result moved 24/45/52 → **26/62/94**
> - **Cougar Creek is fine.** 4.8 km span is about 9.6 km out and back against 8 km recorded. **I was wrong to flag it**
> - **Montane Traverse had an unrelated trail merged in.** Bare "Montane" sits at −115.07, about **19 km east near Exshaw**, against the benchlands at −115.34. Excluded, along with "Montane Cutoff" which forms its own disconnected cluster. Start figure moved 76% → **92%**
> - **Grassi Lakes was two walks, not one.** Split into `grassi-lakes` (Interpretive + main) and `grassi-lakes-upper`. See below — this was the subtlest of the four
> - **Grotto Canyon, Tunnel Mountain** — checked on the map, both correct
> - **Goat Creek** — correct, but spanned 10.8 km against a 10 km out-and-back. Trimmed to 5 km from the trailhead at 51.0617, −115.4186
> - **Quarry Lake** — points are scattered rather than a clean loop, and some overlap the Powerline Trail. **Accepted deliberately:** it is a 2.5 km walk and everything within 120 m of the lake shares the same skyline, so the sun percentage is unaffected
>
> Fixing this also exposed a divergence: `app.py` read trimmed horizon profiles while `sun_on_walks.py` ray marched raw route files, so the two disagreed about Minnewanka in silence. Both now call `src/evaluate.py`.

### 1.3a Grassi Lakes was two walks — and the first test could not have found it

`compare_variants.py` computed each named variant separately. At **midwinter and midsummer all three agreed exactly** — 0% and 100%.

**That agreement proved nothing.** Under Ha Ling the whole hillside is shaded in December and lit in June, so any two routes must agree. It was a test that could only return one answer.

Sweeping every hour across four seasons for the point of *greatest* disagreement found **20 March at noon**:

| Variant | Sunlit |
|---|---|
| Grassi Lakes Interpretive Trail | 100% |
| Grassi Lakes Trail | 100% |
| **Upper Grassi Lakes Trail** | **13%** |

An 87-point spread. The Upper route climbs the headwall directly beneath the cliffs; the lower routes stay in the open. Same trailhead, same destination, different walks.

Now split into two rows. At the equinox they read 100% and 38%.

**Two things to carry forward.** `09-candidate-walks.md` had already flagged that two Grassi routes exist and said "pick one and record which" — and it was merged anyway; a flagged risk that gets designed around is not the same as one that gets handled. And **choosing when to evaluate is itself a design decision**, because the answers saturate at both ends of the year.

### 1.3b Which moment shows the model working

Solstices are the worst choice for comparing walks. In December everything under a large skyline is shaded; in June the sun clears almost everything. Walks that genuinely differ look identical at both.

**Mid-afternoon in February is the most discriminating**, tested across eleven walks at 15:00 — a clean spread from 100% to 0% with every walk at a distinct level. May at 15:00 puts eight of eleven at 100%.

`sun_on_walks.py` now runs four scenarios: three days out (with weather), midwinter 11:00 (the headline case), and February and May afternoons.

**The standout is Goat Creek in February: 100% → 50% → 0% across three hours.** You would set off in full sun and finish in complete shadow. A single midpoint figure of 50% describes neither half of that walk, and it is the clearest justification yet for reporting start, midpoint and end rather than one instant.



**This is the one most likely to be materially wrong**, and it is visible on the app's map. Several walks have more than one OpenStreetMap trail merged into them, because the fetch matches on name.

| Walk | Merged names | Concern |
|---|---|---|
| Heart Creek | Heart Creek Trail + **Heart Creek Bunker Trail** | The Bunker trail is a *separate* walk. Probably should not be included |
| Troll Falls | Troll Falls + **Troll Falls & Marmot Creek Trail** | Marmot Creek is a longer extension |
| Montane Traverse | Montane, Montane Cutoff, Montane Traverse | Cutoff may be a link, not part of the loop |
| Grassi Lakes | Interpretive + Trail + Upper | All the same hillside — probably fine |
| Goat Creek | "Goat Creek Tr (TCT)" + "Goat Creek Trail (TCT)" | Same trail, two spellings — fine |
| **Lake Minnewanka** | Minnewanka Tr + Minnewanka Trail, **836 points** | The full lakeshore trail runs 30 km+. `walks.csv` says 8 km. **The sun percentage is being computed over far more trail than anyone walks** |
| **Cougar Creek** | "Cougar Creek Route", **700 points** | Same concern — the full route to the headwaters, not the popular lower section |

**Check on the map, or against Google Maps / AllTrails:** does each amber-and-grey dot cluster follow the walk you would actually do? Lake Minnewanka and Cougar Creek are the two I expect to be wrong.

### 1.4a Cougar Creek is partly restricted, and the mapped route covers it

**Found 11 September 2026.** After severe rainfall and creek erosion, the Town of Canmore and Alberta Parks restrict access to the Cougar Creek canyon:

- **Foot traffic from the trailhead is limited to the Mount Lady MacDonald trail**
- **Travel past the Cougar Creek Debris Retention Structure** into the upper canyon creek bed is restricted or prohibited, due to unstable embankments
- On-site closure maps at the trailhead kiosk are the current authority

**The mapped geometry is the 4.8 km "Cougar Creek Route" up the drainage — largely the restricted ground.** So the walk being modelled is not the walk you are permitted to do. This is a *standing* restriction, not a weather closure.

Recorded as an `access_note` in `data/walks.csv`, shown as a warning in the app and flagged in the comparison table. **Not fixed** — two options, and both need a decision:

1. **Trim** to below the debris retention structure. Needs its coordinates; not guessing them, since guessed coordinates have produced two wrong answers already
2. **Swap** the walk for Mount Lady MacDonald, which is the permitted route from that trailhead

**The wider point this exposed:** OpenStreetMap describes where a trail *runs*, never whether you may currently walk it. A 100% sunlit result says nothing about access. The app's caveats now say so explicitly.

**✅ Resolved by swapping the walk, 11 September 2026.** Cougar Creek is replaced by **Mount Lady Macdonald** — the route you are actually permitted to walk from that trailhead. No guessed coordinates, and a better contrast-set member: a SW-facing climb rather than a shaded drainage.

Two things came out of the swap:

- **OSM splits it into "Lady MacDonald Trail" and "Mount Lady MacDonald Route"**, and `compare_variants.py` found a **70 point spread** at 17:00 on the solstice — 30% against 100%, because at a 2° sun angle the high ground catches light the valley slopes cannot. The Route is the exposed upper section already ruled out for a dog, so only the Trail is kept. **Third time that tool has found a split**, after Grassi Lakes. Where OSM gives a walk more than one name, the names usually mean something: the easy route and the hard route, the trail and the scramble
- **It finishes after dark.** 880 m of ascent gives a 4h30 Naismith estimate, so a 15:00 February start ends at 19:30, over an hour past sunset. The app now says so in red. Nothing in the design planned for this — it fell out of evaluating the end time, and it matters more than the sunshine figure does

### 1.4 Seasonal closures and wildlife restrictions

**Not implemented at all.** `06-dog-walk-filter.md` designs a Tier 1 seasonal gate; no code enforces it and the app says nothing.

- Bear closures, roughly April–November
- Elk calving zones, May–June; rut, August–October
- Kananaskis winter wildlife closures — some areas close 1 Dec – 15 June
- Wildlife corridor restrictions around Canmore, including near Quarry Lake

The app's caveat block currently says it does not assess safety and points at the authorities. That is honest but minimal.

---

## Tier 2 — affects accuracy, not correctness

### 2.1 Distance and ascent

All ten figures in `data/walks.csv` are desk research or recall. The five added later are the roughest. They feed Naismith, which sets the evaluation time, so an error shifts *when* each walk is assessed.

Fixed properly by ordering the OSM ways and deriving both from the DEM — the outstanding piece of work.

### 2.2 Drive times

**Every one is my estimate.** None checked. They drive a filter in the app.

### 2.3 Peak heights quoted throughout

Rundle 2,949 m · Three Sisters 2,936 m · Grotto 2,706 m · Lady Macdonald 2,606 m · Ha Ling 2,407 m · Assiniboine 3,618 m. Used in reasoning and in `prepare_dem.py`'s sanity check. Recalled, not sourced.

### 2.4 Jasper

Medium, Labrador-type, 6–7 years old — **an assumption**, and the distance, ascent and heat thresholds all derive from it. One question to James settles it.

### 2.5 Uncalibrated thresholds

| Threshold | Where | Note |
|---|---|---|
| DNI bands 600 / 300 / 100 W/m² | `src/weather.py` | Measurement showed DNI is close to bimodal, so four bands over-resolve it. Needs a season of observation |
| Confidence bands 2 / 5 / 10 / 16 days | `src/weather.py` | Reasoned, not measured |
| Naismith pace factor 1.3 | `src/duration.py` | Never checked against a real walk |
| ±5 percentage point precision floor | `app.py` | Derived from one comparison, and **too optimistic at low sun**. Quarry Lake's start figure moved 25% → 10% on a sampling change alone. Below about 10° of solar elevation the answer is extremely sensitive — the same walk swung 21% → 74% in 42 minutes — so sampling choice outweighs reprojection noise. Needs restating as two numbers: a midday floor and a low-sun one |

---

## Tier 3 — validation still owed

From `07-validation-without-local-knowledge.md`, these were planned and not done:

- **A4 — PVGIS horizon profiles.** Pull a computed horizon for a Canmore point and compare with ours. Two independent implementations of the same quantity. `[verify]` coverage at 51°N in Canada
- **B1 — public webcams.** Known location, known time, unambiguous sun or shade. The strongest real-world check available from England, and the record would be worth as much as the result
- **B4 — ask James.** Anywhere he knows is shaded all winter, or a reliable sun trap

Also never fetched: **ATES avalanche terrain ratings** and **Avalanche Canada bulletins**, both designed in `01-data-sources.md` §F.

---

## Resolved — kept for the record

| Question | Outcome |
|---|---|
| Does Alberta observe DST? | **No.** Official Time Act, 18 June 2026 — permanent UTC−6 from November 2026. The model was right, my hand calculation wrong |
| Is the noon sun above the southern skyline at Canmore? | Wrong question — the two peaks occur at different bearings. Replaced by per-azimuth testing |
| Is 22° azimuth sampling enough? | No. It read 14.8° where 2° reads 16.7°, flipping a midwinter answer |
| Is the terrain over-smoothed? | No. DEM maximum 3,554 m against Assiniboine's 3,618 m |
| Is Tunnel Mountain a valid control? | No. A 1,690 m hill between Rundle and Sulphur. No real walk can be a control here — the synthetic flat-plane test is the control |
| Does Quarry Lake get no winter sun? | No — that came from a coordinate 400 m off. It reads 25–75% |
| Why did HRDPS return nulls? | It only runs ~48 hours ahead and answers 200 OK with empty data beyond that. Now falls back to `gem_seamless` |
| Does the vectorised horizon match the scalar one? | Yes, to within 0.01° at every bearing. Asserted by test |

**Retired scripts.** `check_horizon.py` (superseded by `prepare_dem.py`), `check_winter_sun.py` (superseded by `precompute_horizons.py` and the app), and `check_dst.py` (converted into `tests/test_sun.py`). All three were one-off diagnostics whose findings mattered more than the scripts did — the pattern worth keeping is that **a finding worth remembering belongs in a test, not in a script somebody has to remember to run.** Ten tests now pass.

---

## What I need from you, in order

1. **Dog access** for the five unchecked walks, and a ruling on Grotto Canyon
2. **Pass required** for each of the ten
3. **Map check** — which walks show geometry that is not the walk, especially Lake Minnewanka and Cougar Creek
4. Anything from Tier 2 you can settle quickly — drive times are probably the fastest

Give me those and I will update `data/walks.csv`, the fetch scripts and the docs in one pass.

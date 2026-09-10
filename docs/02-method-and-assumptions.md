# 02 — Method and assumptions (Canmore, Alberta)

**Recommendations on the timing questions:**

| Question | Recommendation |
|---|---|
| Start of walk, or average point? | **Neither exactly.** Evaluate at **one instant** — start time plus half the estimated duration — but sample **many points along the route** at that instant. Output "% of route in direct sun" |
| Start point or whole route? | **Whole route, sampled.** Barely more compute, vastly more useful |
| How to combine sun geometry and weather? | **Do not combine them.** Report both, separately, always |

---

## 0. The Canmore geometry, up front

This matters enough to state before the method, because it is the reason the project is worth building here rather than anywhere else.

**Latitude 51.09°N. Solar noon elevation:**

| Date | Solar noon elevation |
|---|---|
| Summer solstice (~21 Jun) | **62.4°** |
| Equinoxes (~20 Mar, ~22 Sep) | **38.9°** |
| Winter solstice (~21 Dec) | **15.5°** |

**Terrain relief above the valley floor (~1,300 m):** 1,100–1,640 m from Ha Ling, Rundle, the Three Sisters, Grotto and Lady Macdonald.

**The horizon angle** — the angle from a point on the valley floor up to the skyline — is what actually decides the answer:

```
horizon angle = atan( relief / horizontal distance )
```

A summit 1,640 m above you and 4 km away sits at **atan(1640/4000) = 22.3°**. Set back 6 km, it is 15.3°.

So the southern skyline from much of the Canmore valley floor is roughly **20–25°**, against a winter noon sun of **15.5°**.

### ⚠ Superseded by measurement, 10 September 2026

The above reasoning was **too crude, and the estimate of a 20–25° representative skyline was too aggressive.** Measured against a Copernicus GLO-30 DEM at 2° azimuth resolution:

| Location | Ground | Highest southern skyline | Hours of direct sun, 08:00–16:00, 21 Dec |
|---|---|---|---|
| Benchlands / Montane | 1,620 m | 8.4° | **6 of 9** |
| Canmore town centre | 1,313 m | 16.7° | **4 of 9** |
| Quarry Lake | 1,405 m | 31.2° | **0 of 9** |
| Grotto Canyon area `[verify position]` | 1,623 m | 34.8° | **0 of 9** |
| Grassi Lakes area | 1,442 m | 41.7° | **0 of 9** |

**Two methodological errors are worth recording, because both were invisible until measured:**

1. **Coarse azimuth sampling understates the skyline.** At 22° steps, town centre's southern maximum read 14.8°; at 2° steps it reads 16.7°. The ray march was stepping over the ridge crest. **Sample at 2° or finer.**
2. **"Highest southern skyline versus noon sun elevation" is the wrong comparison entirely** — the two peaks occur at *different bearings*. Town centre's 16.7° maximum sits where the sun never reaches that height; at 14:00 the sun is at 15.4° on bearing 185°, where the skyline is only 10.3°, so it is sunlit. **The only valid test is per-azimuth, hour by hour.**

**What survives:** the effect is real and it is large, but it is a *location* phenomenon rather than a *valley* one. Quarry Lake and the Benchlands are 4 km apart; one gets no direct sun at all on the solstice, the other gets six hours. There is no useful blanket statement about "the valley floor" — which is the case for computing it per point rather than reasoning about it.

**What this validates:** every aspect prediction in `09-candidate-walks.md` — all flagged `[unverified inference]` — came out correct, including that Quarry Lake would be shaded despite being flat, open and treeless.

**Sanity checks passed:** DEM maximum 3,555 m (Mount Assiniboine sits inside the bounding box, so the terrain is not over-smoothed — the failure mode that would have invalidated everything). Modelled angles agree with hand geometry at all five points: Grassi Lakes `atan(965/1000) = 44°` against 41.7° modelled; Quarry Lake `atan(1000/1700) = 30.5°` against 31.2°.

*Original estimate, retained for the record: a representative 20–25° skyline would put the noon sun below the ridge from roughly early November to early February. Solar noon reaches 22° when declination is about −16.9°, around the first week of November and of February. The 22° figure was too high for the points actually measured.*

---

## 1. The timing decision

Three separable choices hide in "start or average".

### 1a. Which moment?

**Recommendation: start time + 50% of estimated duration.** Call it the *representative time*.

Not the start: on a two-hour walk the sun moves ~30° of azimuth and can drop 10° of elevation. The start is systematically the sunniest moment of an afternoon walk and the shadiest of a morning one — a bias in every answer.

Not the whole range: you ruled it out, correctly for v1. It multiplies compute and output complexity for insight that is small next to forecast uncertainty.

**Free secondary output:** once the machinery exists, evaluating at start and end costs almost nothing and enables *"sunny at the trailhead, in shadow by the time you're back"*. Add it after the core works.

### 1b. Which place?

**Recommendation: sample the whole route, 30–60 points.**

Sampling only the trailhead is close to worthless. In this valley a route can start in a sunlit parking lot and spend its entire length behind a ridge.

Sample at fixed spacing — every 100 m is fine. A 10 km route is 100 points, one horizon lookup each. Nothing, given precomputed horizons (§5).

### 1c. What to output?

**Recommendation: percentage of sampled points in direct sun.**

`"72% of this route is in direct sun at 14:00"` is more honest and more useful than a binary, and degrades gracefully — 0% and 100% are both meaningful.

Show it on the map: route line coloured warm where sunlit, cool grey where shaded. That single view explains more than any number and makes wrong answers obvious at a glance.

---

## 2. Sun position

A library returns two angles from (latitude, longitude, elevation, UTC time):

- **Azimuth (φ_sun)** — bearing, degrees clockwise from north
- **Elevation (θ_sun)** — degrees above horizon. Use the **apparent** value, which includes refraction

Refraction lifts the sun by ~0.5° near the horizon — about its own diameter — which at 5° elevation changes shadow length by roughly 10%.

**This calculation is effectively exact. Every error in the final answer comes from the terrain model or the forecast, never from here.**

If θ_sun ≤ 0 it is night or twilight — return that and stop.

**Timezone:** `America/Edmonton`. MST = UTC−7, MDT = UTC−6. Alberta observes DST (permanent-DST referendum rejected 2021) `[verify]`. Compute in UTC, display in local, convert once at the end.

---

## 3. Shadow — two mechanisms, both required

A point is in direct sun only if it passes **both** tests. Naive implementations do one and quietly get the other wrong.

### 3a. Self-shading — does the ground face the sun?

Standing on a north-facing slope with the sun in the south, you are in shade regardless of the horizon. The ground is turned away.

From the DEM compute **slope** (`s`, degrees) and **aspect** (`φ_aspect`, bearing the slope faces) — standard `numpy` gradients, or `gdaldem slope`/`aspect`.

```
cos(i) = sin(θ_sun)·cos(s) + cos(θ_sun)·sin(s)·cos(φ_sun − φ_aspect)
```

If `cos(i) ≤ 0` the surface faces away → **in shade**. One expression per point, no ray tracing.

This matters more in Canmore than in the UK. Slopes here are steep — 30–40° is routine — so aspect alone shades large areas. A north-facing traverse can be in shade at midday in March.

### 3b. Cast shadow — is something blocking the way?

Even on a sun-facing slope, a mountain between you and the sun blocks it. This needs a ray march.

**In words:** stand at your point, look toward the sun, walk outwards in steps. At each step compute the angle up to the terrain. If it ever exceeds the sun's elevation, the sun is hidden.

```
for d in steps out to max_distance:
    (x, y) = point + d · (sin φ_sun, cos φ_sun)
    h      = DEM height at (x, y)
    drop   = d² / (2 · R_eff)              # Earth curvature + refraction
    angle  = atan2(h − h_point − drop, d)
    if angle > θ_sun:
        return SHADOWED
return SUNLIT
```

| Parameter | Value | Reasoning |
|---|---|---|
| Step size | ≈ DEM cell size (30 m) | Smaller wastes time; larger steps over ridges |
| Max distance | **30 km** | 1,600 m relief at 5° sun casts 18.3 km. Peaks 30 km southwest exceed 3,000 m |
| `R_eff` | ≈ 7/6 × 6,371 km ≈ 7,433 km | Earth radius inflated for refraction — the standard approximation |

The curvature term matters. Ignore it and at 30 km you place distant terrain ~60 m too high, manufacturing shadows that do not exist.

**Optimisation, after it works:** grow the step size with distance — 30 m near, 200 m at 15 km, where each step subtends a negligible angle. Cuts the work by more than half.

### 3c. Combine

```
in_direct_sun = (θ_sun > 0) AND (cos(i) > 0) AND (not cast-shadowed)
```

---

## 4. Weather — the second, independent factor

Fetch hourly forecast for the route centre at the representative hour. **Direct Normal Irradiance** is the variable that matters.

| DNI (W/m²) | Interpretation |
|---|---|
| > 600 | Strong direct sun. Terrain shadow is the whole story |
| 300–600 | Hazy or broken. Shadow matters, with caveats |
| 100–300 | Thin or broken cloud. Weak shadows |
| < 100 | Effectively overcast. **Terrain shadow irrelevant — rank on something else** |

`[verify]` these bands against observation. Starting points, not findings.

**The short-circuit is a feature.** When DNI is low, say so plainly: *"Overcast across all options — no walk will be sunny today. Ranking on distance and drive time."*

### Why the two factors must not be blended

A single "sunniness score" of 0.4 could mean:
- Perfect geometry, overcast sky, **or**
- Brilliant clear day, route entirely behind a ridge

These demand opposite decisions — "go anywhere, it makes no difference" versus "go somewhere else". Blending destroys the information the user needs. **Always show both.**

### Canmore-specific: chinooks

Warm, dry föhn winds off the Rockies can raise temperature 20 °C in hours and clear the sky, or arrive as a chinook arch that keeps the valley overcast while the mountains are clear. Forecast models handle them poorly. Name this in the caveats — it is a locally known reason to distrust a forecast.

---

## 5. Performance — precompute the horizons

The single most important engineering decision in the project.

Ray marching 30 km at 30 m steps is 1,000 DEM lookups. For 100 route points that is 100,000 per walk per query. Across 30 walks, 3 million — seconds at best, repeated on every interaction.

**Instead: precompute a horizon profile once per route point.** Ray march in every direction — every 2°, giving 180 azimuths — and store the maximum terrain angle found in each. A 180-number fingerprint of the skyline from that spot.

At query time: look up the two azimuths either side of the sun, interpolate, compare to solar elevation. **One lookup. Microseconds.**

```
precompute:  route → point → azimuth  ⇒  horizon angle
query:       horizon[≈ φ_sun] < θ_sun  ⇒  sunlit
```

Minutes per route, once, cached to disk. Every query afterwards is instant, and the same profile answers **any date and any time**. It also means the app runs on free hosting with no heavy backend.

Store as Parquet or a small binary per route in `data/horizons/`. Regenerate only when the route or DEM changes.

---

## 6. Duration estimate

**Naismith's rule:** `duration = distance / 5 km/h + ascent / 600 m/h` — one hour per 5 km, plus one minute per 10 m of climb.

Naismith describes a fit walker on good ground and is optimistic for most real walks. Add a **user-set pace multiplier**, default ~1.3 — dogs stop, people take photographs.

**Canmore-specific corrections worth considering later:**
- **Altitude.** Trailheads sit at 1,300–1,800 m and routes climb well above. Naismith assumes sea level; expect to be slower.
- **Snow.** A trail in packed snow is slower; unbroken snow is dramatically slower. A seasonal multiplier is cruder than it deserves but better than nothing.

**Note the circularity:** duration sets the representative time, which sets the sun position. A 40-minute error on a January afternoon can flip the answer. State it, and let the user override the duration.

---

## 7. Ranking

**Filter first, then rank.**

**Gate 0 — dog suitability.** Applied before anything else. See `06-dog-walk-filter.md`. Walks that fail never reach the sun engine.

**Hard filters:** distance, ascent, drive time, pass availability, active closures, avalanche terrain in winter.

**Then rank survivors:**

| Factor | Weight | Notes |
|---|---|---|
| % of route in direct sun | High | The point of the tool |
| Direct beam availability (DNI) | High | Gates the above |
| Temperature and wind chill | **High in winter** | −25 °C with wind overrides everything |
| Drive time | Medium | |
| Ascent vs preference | Medium | |
| Crowding / parking risk | Medium | Ha Ling and Grassi Lakes fill early |
| Variety — not last week's walk | Low | Needs history |

**Do not hide this behind one number.** Show the top three with a line each on why, and a line on why the runner-up lost. A recommendation you cannot interrogate is one you cannot trust.

---

## 8. Assumptions and approximations — state these on screen

### Terrain model

| Assumption | Consequence |
|---|---|
| 30 m DEM resolution | Features narrower than ~60 m invisible: gullies, cliff bands, individual buildings |
| Bare-earth DTM | **No trees.** ⚠ **Matters more here than the UK draft assumed** — the Bow Valley has extensive closed-canopy lodgepole pine and spruce. Forested trails will read markedly sunnier than they are. This is the largest single known bias in the model |
| Terrain opaque and hard-edged | Correct for rock |
| Horizon sampled every 2° | Sub-degree interpolation error near sharp skylines. Small |
| Curvature via `R_eff = 7/6 R` | Standard approximation |

### Sun and shadow

| Assumption | Consequence |
|---|---|
| Sun as a point source | The solar disc is 0.53° wide; real shadow edges have a penumbra tens of metres across. Points near a boundary are genuinely ambiguous |
| Apparent elevation includes refraction | Good, but refraction is variable near the horizon. Below ~2°, treat everything as uncertain |
| Single instant | By design. The output must state which moment it refers to |
| Shadow treated as binary | **"In shadow" does not mean dark.** Diffuse skylight is often 10–20% of full illumination — and on snow, reflected light makes shade far brighter than it sounds. **Word it "no direct sun", never "dark"** |
| Snow reflectance ignored | Snow albedo is ~0.8. A shaded slope opposite a sunlit one is meaningfully brighter and warmer than the model implies. Not modelled |

### Weather

| Assumption | Consequence |
|---|---|
| Grid-cell forecast represents the route | Bow Valley weather is intensely local — valley cloud, upslope flow, chinooks. A 2.5 km model helps; it does not solve it |
| Forecast skill usable | Good to ~5 days, weak to ~10, unusable past ~14. **Dominant uncertainty for anything more than a few days out** |
| One forecast point per route | A long route can cross a weather boundary. v2 could sample three |

### Route and timing

| Assumption | Consequence |
|---|---|
| OSM / GPX geometry accurate | Varies. OSM Bow Valley coverage is good but not surveyed |
| Elevation from DEM, not GPX | More consistent; smooths short real climbs |
| Naismith × pace multiplier | Rough, and does not account for altitude or snow |
| Trail is passable | **Not modelled.** Snow depth, washouts, bridge closures. The tool assumes the trail exists as mapped |

### Out of scope entirely

| Not modelled | Note |
|---|---|
| Avalanche safety | Surfaced from Avalanche Canada and deferred. Never computed |
| Wildlife presence | Seasonal risk flags only. No prediction |
| Trail conditions and closures | Hand-curated with a review date, linked to the live official source |

### Confidence rule

| Condition | Confidence |
|---|---|
| ≤ 2 days ahead, solar elevation > 10° | **High** |
| 3–5 days ahead | **Medium** |
| 6–10 days ahead | **Low** |
| > 10 days ahead | **Very low — say so prominently** |
| Solar elevation < 5° | Downgrade one level — refraction and DEM error both bite hardest |
| Route substantially forested | Downgrade one level — the tree bias above |
| DNI < 100 W/m² | Geometry is real but irrelevant. Label it |

---

## 9. Validation — how to know the model works

**Full treatment in `07-validation-without-local-knowledge.md`.** Summary:

Nobody on this project has been to Canmore, so validation runs against physics rather than memory. That is not a compromise — it is a stronger test, because the only thing that can actually be wrong here is the code.

1. **Synthetic DEM tests.** Flat plane, single vertical wall of known height and distance, cone. Every answer hand-computable. **Highest value per hour in the project** — catches azimuth-convention, degree/radian and transposition errors that look entirely plausible on real terrain. Write these as `pytest` tests *before* the ray march
2. **Sunrise and sunset.** At a flat open point, the modelled transition should match published Canmore times within minutes. Validates solar position and the `America/Edmonton` timezone handling
3. **Independent implementation.** GRASS `r.horizon`, WhiteboxTools `HorizonAngle`, or `gdaldem hillshade` with the computed azimuth and altitude. **About an hour — do it before building any UI**
4. **PVGIS horizon profiles.** Free API returning computed terrain horizons for arbitrary coordinates. Two independent implementations of the same quantity `[verify] coverage at 51°N`
5. **Public webcams.** Known location, known time, unambiguous sun or shade. The best real-world check available from a desk in England
6. **Extremes.** Midsummer noon on an open summit → 100% sunlit. Midwinter, 30 minutes after sunrise, valley floor → 0%

Tests 1 and 3 together will catch essentially every serious error.

The §0 November-to-February estimate is now a **model output to be checked against independent tools**, not a claim to be checked against experience.

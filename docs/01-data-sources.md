# 01 — Data sources (Canmore, Alberta)

**Headline: the data situation here is materially better than the UK, but the problem has moved.**

In the UK the blocker was that no free, licence-clean database of curated day walks exists. In the Bow Valley, trail centrelines are genuinely available — Parks Canada and Alberta Parks publish open data under permissive Canadian government licences, and OpenStreetMap coverage of a major international recreation area is strong.

**The hard part here is not the trails. It is the rules about them.** Leash law by jurisdiction, seasonal wildlife closures, avalanche terrain ratings, which pass you need to park. That information exists, is authoritative, and is published almost entirely as human-readable web pages and PDFs rather than machine-readable feeds.

**Consequence for the build: the rules layer is hand-curated once and reviewed seasonally, not scraped live.** For 20–40 walks that is a few hours of work, and it is more reliable than any scraper.

| # | Input | Recommended source | Difficulty |
|---|---|---|---|
| A | **Trail geometry** | OSM + Parks Canada / Alberta Parks open data | Easy–moderate |
| B | **Rules, closures, hazards** | Hand-curated from official sources | ⚠ **The real work** |
| C | **Terrain heights** | Copernicus GLO-30, upgrade to NRCan HRDEM if covered | Easy |
| D | **Sun position** | Computed, not fetched — `pvlib` | Trivial |
| E | **Weather** | Open-Meteo, Environment Canada HRDPS model | Easy |
| F | **Avalanche** | Avalanche Canada | Easy to read, do not automate judgement |

---

## A. Trail geometry

### Options assessed

| Source | Coverage | Licence | Verdict |
|---|---|---|---|
| **OpenStreetMap** — `highway=path`, `highway=footway`, `route=hiking` relations, via Overpass API | Bow Valley coverage is **good** — heavily mapped international recreation area with an active local community | ODbL — free, attribution + share-alike | ✅ **Primary source.** Far better here than for UK local circulars |
| **Parks Canada open data** via open.canada.ca | Banff National Park trails | Open Government Licence – Canada 2.0 — very permissive | ✅ Authoritative for the Banff portion. `[verify]` current trail layer availability and format |
| **Alberta Parks / GeoDiscover Alberta** | Kananaskis Country, Bow Valley PP, Spray Valley PP, Bow Valley Wildland PP | Alberta open data licence — permissive | ✅ Authoritative for the Kananaskis portion. `[verify]` |
| **Town of Canmore open data** | Municipal trails, off-leash areas, wildlife corridors | Municipal open data | ✅ Likely the only clean source for off-leash zones and corridor boundaries. `[verify]` portal exists and what it holds |
| **Trailforks** (Outside Inc.) | Strong Bow Valley coverage, biking-led but includes hiking | Has a public API with a key, but **terms tightened after acquisition** | ⚠ `[verify]` current terms before any use. Do not build a dependency on it |
| **AllTrails, Gaia GPS, onX Backcountry** | Excellent curation | Proprietary, no open API, scraping breaches ToS | ❌ Do not |
| **Gem Trek maps, Daffern's *Kananaskis Country Trail Guide*** | Best curation that exists | Copyrighted print | ❌ As data. ✅ As **your own reading** to decide which trails to include |
| **Your own GPX** | Whatever you record | Yours | ✅ Always valid, and the right way to capture a route you know |

### Recommendation

**Use OSM as the geometry backbone, cross-checked against Parks Canada and Alberta Parks for the trails you shortlist.**

This is a real change from the UK plan. There, auto-discovery was a v2 research spike because the data did not exist. Here, an Overpass query over a 50 km radius will return a usable candidate set — likely several hundred named paths — and the work becomes *filtering down*, not *building up*.

That is exactly the sequencing you proposed, and it is right. See `06-dog-walk-filter.md`.

### On paywalls — the direct answer

**No meaningful paywall on trail data.** Canadian federal and Alberta provincial open data is free and permissively licensed, and OSM is free. The proprietary apps (AllTrails, Gaia, onX) are paywalled and off-limits, but you do not need them.

**There are two real paywalls, and they are on the ground, not the data:**

| Pass | Where | Notes |
|---|---|---|
| **Parks Canada pass** — daily or annual | Banff National Park | Required to stop anywhere in the park `[verify] current pricing` |
| **Kananaskis Conservation Pass** — daily or annual | Kananaskis Country and Bow Valley corridor | Introduced 2021. Required to park `[verify] current pricing and exact boundary` |

Town of Canmore trails are free. **Capture "pass required" as a metadata field** — it is a genuine decision factor and the boundary is not obvious from a map.

### Cleaning required

| Problem | Fix |
|---|---|
| OSM paths are **segments, not routes** — a named trail is many `way` objects | Assemble into routes. Where a `route=hiking` relation exists, use it. Otherwise stitch by name and connectivity, or hand-draw the route once |
| No loops — OSM gives a network, you want walks | This is the curation step. A "walk" is a decision you make over the network, not something the data hands you |
| Trail quality tags are inconsistent — `sac_scale`, `trail_visibility`, `surface` are patchy | Do not rely on them. Hand-set difficulty for the shortlist |
| Duplicate and conflicting geometry between OSM and government layers | Pick one as authoritative per trail. OSM is usually better shaped; government data is better attributed |
| Coordinate systems: OSM is WGS84 (EPSG:4326); Canadian government data is often NAD83 UTM Zone 11N (EPSG:26911) | **Reproject everything to EPSG:26911 for analysis.** Its units are metres, which makes distance and slope calculations honest. Convert to lat/lon only for display and API calls |
| GPX device noise and bad barometric elevation | Smooth or simplify; **discard GPX elevation entirely and re-sample from the DEM** |

The projection point catches every beginner. Mixing degrees and metres produces answers that look plausible and are wrong by orders of magnitude. In the UK draft this was EPSG:27700; here it is **EPSG:26911**.

---

## B. Rules, closures and hazards — the real work

**No single source. Three jurisdictions inside 50 km, each with its own rules and its own closure feed.**

| Jurisdiction | Authority | Dogs | Closures published as |
|---|---|---|---|
| **Town of Canmore** | Municipal | Leash bylaw; **designated off-leash areas exist** (Quarry Lake and others) | Town website, wildlife corridor notices |
| **Banff National Park** | Parks Canada | **On leash at all times, everywhere. No off-leash anywhere in the park** | Parks Canada "important bulletins" / trail conditions pages |
| **Kananaskis Country** (Bow Valley PP, Spray Valley PP, Bow Valley Wildland PP, Peter Lougheed PP) | Alberta Parks | On leash on trails; rules vary by park class | Alberta Parks advisories page |
| **Stoney Nakoda Nation lands** | First Nation | Permission required — not public trails | N/A |

All `[verify]` — regulations change, and this is the layer most likely to be out of date.

**The single most consequential finding: off-leash is essentially unavailable.** Within 50 km it is limited to the Town of Canmore's designated areas. Do not build off-leash as a ranking axis — it is a near-constant "no", and a filter that always returns the same answer is just a column of noise.

### Closure and hazard sources

| Source | What | Machine-readable? |
|---|---|---|
| Parks Canada trail conditions / bulletins (Banff) | Closures, warnings, area restrictions, mandatory group sizes | ⚠ Web pages. `[verify]` whether any feed exists |
| Alberta Parks advisories (Kananaskis) | Closures, wildlife warnings | ⚠ Web pages. `[verify]` |
| Town of Canmore | Wildlife corridor restrictions, seasonal closures | ⚠ `[verify]` |
| **Avalanche Canada** | Daily bulletins by region (Banff Yoho Kootenay; Kananaskis) | ✅ Has a public API `[verify] current terms` |
| **ATES ratings** (Avalanche Terrain Exposure Scale — Simple / Challenging / Complex) | Published by Parks Canada for many Banff trails; patchier in Kananaskis | ⚠ Partly PDF/map. `[verify]` |

**Recommendation: hand-curate the rules layer for the shortlist, with a `last_reviewed` date on every row, and link out to the live official page rather than caching a claim about it.** The app should show "Kananaskis — check current advisories" with a link, not assert "open".

This is a design decision about liability as much as engineering. The tool ranks walks for sunshine. It must not be the thing someone relies on for whether a trail is closed or whether avalanche terrain is safe.

---

## C. Terrain heights (the DEM)

A **DEM** is a grid of ground heights — a spreadsheet where each cell holds the height of a patch of ground. Use a **DTM** (bare earth), not a **DSM** (includes tree canopy), since trees are out of scope.

### Options

| Source | Resolution | Coverage | Licence | Verdict |
|---|---|---|---|---|
| **Copernicus DEM GLO-30** | 30 m | Global | Free (ESA) | ✅ **Start here.** Reliable, well-documented, definitely covers the area, easy to obtain |
| **NRCan HRDEM** (High Resolution DEM) | 1–2 m LiDAR | Canada, **partial and growing** | Open Government Licence – Canada | ✅ Upgrade path if the Bow Valley is covered. `[verify]` coverage |
| **Alberta provincial LiDAR** via GeoDiscover Alberta | 1–2 m | Alberta, extensive | Alberta open licence | ✅ Same. `[verify]` |
| **CDEM** (Canadian Digital Elevation Model) | ~20 m in the south, variable | Canada | OGL–Canada | Older, superseded. Usable fallback |
| **ALOS World 3D (AW3D30)** | 30 m | Global | Free (JAXA) | Fine alternative to Copernicus |

**30 m is sufficient and this is not a compromise.** Mountains casting 3–18 km shadows are resolved perfectly well at 30 m. LiDAR at 1 m buys cliff-band and gully detail that will not change "will this walk be in the sun", while multiplying data volume by 900.

`[verify]` whether NRCan HRDEM or Alberta LiDAR covers the Bow Valley — if so it is a free upgrade worth taking later, but do not block on it.

### How much DEM do you need?

Shadow length is `L = h / tan(θ)`. At Canmore's latitude, with 1,000–1,600 m of relief:

| Solar elevation | Shadow from 600 m | from 1,000 m | from 1,600 m |
|---|---|---|---|
| 62° (summer noon) | 0.3 km | 0.5 km | 0.8 km |
| 39° (equinox noon) | 0.7 km | 1.2 km | 2.0 km |
| **15.5° (winter noon)** | 2.2 km | **3.6 km** | **5.8 km** |
| 10° | 3.4 km | 5.7 km | 9.1 km |
| 5° | 6.9 km | 11.4 km | **18.3 km** |

**Rule: buffer the DEM by 30 km beyond the walk area.**

Walk radius 50 km + 30 km buffer = **DEM covering roughly an 80 km radius around Canmore** — a 160 km × 160 km box. At 30 m that is about 5,300 × 5,300 cells, roughly 110 MB as float32, considerably less as a compressed GeoTIFF.

That is too large to commit to GitHub comfortably. It goes in `.gitignore` with a download-and-prepare script alongside it.

*(Minor optimisation available: the sun is never in the far northern sky, so the northern buffer could be trimmed. Not worth the complexity — buffer uniformly.)*

### Cleaning required

| Problem | Fix |
|---|---|
| Downloads arrive as multiple tiles | Merge once into a single GeoTIFF with `rasterio.merge` |
| Mixed coordinate systems | Reproject to **EPSG:26911** (NAD83 / UTM 11N) at load, once |
| No-data values | Usually a sentinel like −9999 or −32768. Mask them, or they become a kilometre-deep hole that manufactures sunlight |
| Vertical datum differences between sources | Copernicus is above the EGM2008 geoid; Canadian data uses CGVD2013. Differs by a metre or two — irrelevant, but **never mix two DEMs in one calculation** |

---

## D. Sun position

Not a dataset — a calculation. Given latitude, longitude, elevation and a UTC timestamp, solar position is deterministic and effectively exact. No API, no key, no network.

Use **`pvlib`** (NREL SPA algorithm, ~0.0003°) or `astral` (~0.01°). Both are far more accurate than the terrain model, so choose on ergonomics. `[verify]` package APIs at build time.

Outputs: **azimuth** (bearing, degrees clockwise from north) and **apparent elevation** (degrees above horizon, including atmospheric refraction).

### ⚠ The timezone trap — resolved 10 September 2026

**Alberta no longer observes daylight saving.** The **Official Time Act**, passed **18 June 2026**, moves the province to permanent **UTC−6** — "Alberta Time" — effective **November 2026**. Clocks did not go back on 1 November 2026.

Historically Alberta ran MST (UTC−7) in winter and MDT (UTC−6) in summer, and a 2021 referendum narrowly *rejected* permanent daylight time (50.2% for keeping the changes). That decision has since been reversed by legislation.

**Practical consequences, and they are not cosmetic:**

- `America/Edmonton` with a current `tzdata` handles this correctly. **Do not hard-code offsets** — this is the second time in five years the rule has changed
- **Winter daylight now falls much later by the clock.** On the solstice, sunrise is **09:46** and sunset **17:30**, with solar noon at **13:40**. A 09:00 winter query returns darkness
- The usable winter walking window is roughly **10:00 to 17:00**, not 08:00 to 16:00
- Keep `tzdata` current. `pip install --upgrade tzdata` if winter results ever look an hour out

**How this was caught:** the model reported the sun 6.5° below the horizon at 09:00 on 21 December. A hand calculation assuming MST predicted +1°. The discrepancy looked exactly like a daylight-saving bug — but the timezone database was right and the hand calculation was wrong. Worth recording as a case where the disagreement was real and the model won.

**Rule: store and compute everything in UTC. Convert to local only at display, at the very last step.** Use `zoneinfo` with **`America/Edmonton`**. Never do the offset arithmetic yourself.

---

## E. Weather

**Recommendation: Open-Meteo.** Free, no API key, global coverage, and it exposes the variable that matters.

### The variable that matters

Not "cloud cover". **Direct Normal Irradiance (DNI)** — the strength of the direct beam from the sun's disc, in W/m². That is the light mountains block.

- **DNI near zero** → overcast → no beam to block → **terrain shadow is irrelevant that day**
- **DNI high** → the terrain shadow is the entire story

This gives a clean short-circuit and an honest failure mode: *"overcast everywhere, no walk will be sunny, ranking on distance instead"* is a legitimate answer.

### Variables to request

| Variable | Why |
|---|---|
| `direct_normal_irradiance` | **The key one** |
| `sunshine_duration` | Intuitive display figure |
| `cloud_cover`, `_low`, `_mid`, `_high` | Low cloud in mountains is valley fog and behaves nothing like cirrus |
| `temperature_2m`, `apparent_temperature` | **Matters more here than the UK.** −25 °C is a hard stop for a dog walk; +30 °C on exposed scree is another |
| `wind_speed_10m`, `wind_gusts_10m` | Wind chill is the real constraint in winter |
| `snowfall`, `snow_depth` | Trail condition, and a genuine seasonal gate |
| `precipitation_probability` | |

Request **hourly**, in **UTC**. `[verify]` exact parameter names — Open-Meteo has renamed variables before.

### Model choice

Request **Environment Canada's HRDPS** (High Resolution Deterministic Prediction System, ~2.5 km) rather than the default `best_match`. `[verify]` the current Open-Meteo identifier — it has been in the `gem_hrdps_continental` family.

A 2.5 km grid resolves individual valleys. Global models at 9–25 km will confidently report identical weather for Canmore and the summit of Mount Rundle.

**Alternative:** Environment and Climate Change Canada publish free open data directly (MSC Datamart, GeoMet API) — authoritative, more setup. `[verify]`. Not worth it for v1 when Open-Meteo serves the same underlying model.

### Handling

| Problem | Fix |
|---|---|
| Grid-cell forecast, not point truth | Cannot be fixed. **State it.** Bow Valley weather is intensely local — valley cloud, upslope flow, and chinooks that change everything in hours |
| **Chinooks** — Canmore-specific | Rapid warm dry föhn winds off the Rockies; temperature can swing 20 °C in hours and clear the sky. Forecasts handle them poorly. Worth naming in the caveats |
| Skill degrades with lead time | Drive a confidence badge. Good to ~5 days, weak to ~10, unusable past ~14 |
| Beyond forecast horizon | Refuse and say why. Do not fabricate |
| Rate limits | Cache to disk, keyed on (location, date, fetch hour) |

---

## F. Avalanche — read it, do not model it

**Avalanche Canada** publishes daily bulletins by region. The relevant regions are **Banff Yoho Kootenay** and **Kananaskis**. `[verify]` current region names and API terms.

**ATES** — Avalanche Terrain Exposure Scale — rates terrain as **Simple / Challenging / Complex**. Parks Canada publishes ATES ratings for many Banff trails; Kananaskis coverage is patchier. `[verify]`.

### The design rule

**The app surfaces the official rating and the current bulletin, and defers. It never computes an avalanche judgement, and it never says a route is safe.**

Concretely: a winter query on a route rated Challenging or Complex shows the ATES rating, the current danger rating, a link to the bulletin, and a statement that this tool does not assess avalanche safety. In the default configuration those routes are filtered out of winter results entirely.

This is a scope boundary, not a technical limitation. Avalanche assessment requires training and current field observations. A sunshine-ranking tool has no business implying otherwise.

---

## G. Walk metadata

### Derived automatically

Distance, total ascent (from the **DEM**, not GPX), max and start elevation, estimated duration (Naismith — see `02`), start coordinates, aspect profile.

### Hand-entered, per walk

| Field | Why |
|---|---|
| Name, area, jurisdiction | Drives every rule below |
| **Pass required** — none / Banff / Kananaskis | Real cost and planning factor |
| Leash requirement | Near-always "on leash". Record it anyway |
| Trailhead location, parking size, fills-up flag | Practical failure mode — Grassi Lakes and Ha Ling fill early |
| Drive time from home | Often the real deciding factor at a 50 km radius |
| Surface and difficulty | Hand-set; OSM tags are unreliable |
| **Wildlife exposure** — bear / cougar / elk notes and seasons | See `06` |
| **ATES rating** and whether the route crosses avalanche terrain | Winter gate |
| **Seasonal closure windows** | See `06` |
| Water availability for the dog | Genuinely matters in summer |
| Shade availability | The **inverse** query for hot days |
| Notes, `last_reviewed` date | The rules layer must carry a review date |

---

## Summary: what to acquire, in order

1. **Overpass query** over a 50 km radius around Canmore for paths and hiking routes. See what comes back before deciding anything else
2. **Two or three GPX routes** you know well — ideally one you know is shaded in January, as the validation case
3. **Copernicus GLO-30** clipped to an 80 km radius box, merged, reprojected to EPSG:26911
4. **Nothing** for sun position — it is a library
5. **The rules layer**, hand-curated, once the candidate list is down to a shortlist
6. **Weather and avalanche** last — both are short API clients and can wait

Build the shadow calculation against those two or three known routes first. If it cannot correctly tell you that a valley you know is shaded on a January afternoon, nothing downstream matters.

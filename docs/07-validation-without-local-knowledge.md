# 07 — Validating without local knowledge

**Recommendation: the shadow model does not need local knowledge to validate. It needs physics tests.**

Two separate things were bundled together in the earlier plan, and separating them makes one of them almost disappear:

| What needs validating | Needs local knowledge? | How to validate |
|---|---|---|
| **The shadow geometry** — is the model computing sun and shade correctly? | **No** | Synthetic test cases, independent implementations, published horizon data |
| **The walk selection** — is this a good dog walk? | **Yes, somewhat** | Official trail descriptions, guidebooks, forums, James |

Never having been to Canmore is a real gap for the second and almost irrelevant to the first. The first is the technically hard part and the part most likely to be wrong.

---

## 1. Why the geometry needs no local experience

Terrain shadow is deterministic:

- **Sun position** is computed from an astronomical algorithm accurate to a fraction of a degree. It is not a measurement or an estimate
- **The DEM** is a published measurement made by a satellite. It is the same number whether or not you have stood on it
- **The horizon calculation** is trigonometry

The only thing that can be wrong is **your code**. And code correctness is testable against things that are not opinions: hand-computable cases, independent implementations of the same physics, and published horizon profiles.

Local experience would be a pleasant sanity check. It was never the actual validation path — I framed it that way in the earlier draft and that was the wrong emphasis.

---

## 2. Tier A — validating the code

Do all four. None requires having been to Alberta. Together they will catch essentially every serious error.

### A1. Synthetic DEM tests — **highest value per hour in the whole project**

Build small artificial terrains where you already know the answer, and check the model reproduces it.

| Test terrain | Expected result |
|---|---|
| **Perfectly flat plane** | Sunlit whenever solar elevation > 0, shaded otherwise. Nothing else |
| **Single vertical wall**, height `h`, distance `d`, due south | Horizon angle exactly `atan(h/d)`. Shadow appears precisely when solar elevation drops below it |
| **Wall at a known bearing** | Shadow appears only when the sun's azimuth is within the wall's angular width |
| **Simple cone** | Shadow rotates smoothly around it through the day, always pointing away from the sun |
| **Slope of known aspect, no obstructions** | Self-shading kicks in exactly when `cos(i) ≤ 0` — hand-computable |

Roughly an hour of work. It catches the bugs that actually happen in this kind of code:

- Azimuth convention errors — clockwise from north versus anticlockwise from east; the single most common
- Degrees versus radians
- Sign errors in the aspect calculation
- Row/column versus x/y transposition when reading the raster
- Off-by-one in the ray march

These bugs produce output that looks entirely plausible on a real DEM. On a flat plane or a single wall they are immediately obvious.

**Write these as `pytest` tests before you write the ray march**, and you will spend a day on the geometry rather than a fortnight.

### A2. Sunrise and sunset

At an open, flat point, the model's shadow transition should match published sunrise and sunset times for Canmore to within a few minutes.

Validates: solar position, the timezone handling (`America/Edmonton`, MST/MDT), and the `horizon = 0` case. Cheap, and it catches the timezone error that would otherwise silently shift every answer by an hour.

### A3. An independent implementation

Compute the same thing with software written by someone else, on the same DEM, and compare.

| Tool | What to use |
|---|---|
| **GRASS GIS** `r.horizon` | Computes horizon angles directly — the closest match to what you are building |
| **WhiteboxTools** `HorizonAngle` | Same quantity, simpler to install |
| **QGIS / GDAL** `gdaldem hillshade` with `-az` and `-alt` set to your computed sun position | Renders a shaded relief image; cast shadows appear as black. Visual, immediate, convincing |

Agreement between two independent implementations of the same physics is strong evidence. Disagreement tells you exactly where to look.

**Do A3 before building any UI.** About an hour.

### A4. PVGIS horizon profiles

The EU Joint Research Centre's **PVGIS** service publishes computed terrain horizon profiles for arbitrary coordinates, free, through a documented web API. It is built for solar panel siting, which is the same physical question asked in a different accent.

Pull the horizon profile for a Canmore point, compare it against yours for the same point. Two independent implementations, two independent DEMs, same quantity.

`[verify]` coverage at 51°N in Canada and current API terms. PVGIS coverage is broad but not universal, and the underlying DEM may differ from yours — small disagreements are expected, large ones are a bug.

**Global Solar Atlas** (World Bank / Solargis) is a similar cross-check `[verify]`.

---

## 3. Tier B — validating against the real world, from here

### B1. Public webcams — the strongest real-world check available

**This is the best answer to "I've never been there".**

A fixed webcam gives you a known location, a known time, and an unambiguous view of whether a place is in sun or shade. That is precisely the observation you cannot make yourself, available on demand.

Candidate sources `[verify] all — availability changes`:

- **Town of Canmore** and **Banff** community webcams
- **Alberta 511** highway cameras along the Trans-Canada through the Bow Valley — numerous, and their coordinates are published
- **Ski areas** — Nakiska, Mt Norquay, Sunshine Village. High, fixed, and pointed at terrain
- Hotel and business cams around Canmore

**Method:**
1. Pick a camera; establish its coordinates and roughly which way it points
2. Note the time on the image
3. Run the model for that point and time
4. Compare: is the terrain in view sunlit or shaded, and does the model agree?

Repeat across a few times of day and a few weeks apart, and you have a real validation record — one you can put in the documentation, which for a demonstration project is worth as much as the result itself.

Two cautions: image timestamps are not always reliable, and **manual viewing for validation is fine; automated scraping is a separate question** with its own terms of service. Keep it manual.

### B2. Flickr and Wikimedia Commons — the workable version of your photo idea

This is your social media idea done in a way that actually functions:

- **Real EXIF GPS coordinates**, not a place-tag
- **Real capture timestamps**, not post times
- **Creative Commons licences** and a documented, permitted API
- Searchable by location and date

Signal is still weak and the selection bias you identified still applies — but it is legitimate, and a handful of well-geotagged mountain photographs with reliable timestamps is a genuine data point.

### B3. Official trail descriptions

Parks Canada and Alberta Parks trail pages, and guidebooks such as Daffern's *Kananaskis Country Trail Guide*, routinely mention aspect and sun: "gets morning sun", "cold and shaded until spring", "exposed, no shade". Corroborating rather than validating, but nearly free.

### B4. Ask James

If this is Jasper's walk list, James is a validation resource and probably a better one than any dataset. Even three answers — "which of these gets sun in winter, which is always cold, which would you avoid" — is a useful check on both the geometry and the shortlist.

---

## 4. Tier C — what not to do

### Instagram, TikTok and Strava geolocation

**Recommendation: don't.** You identified one problem with it. There are four worse ones:

| Problem | Why it kills the method |
|---|---|
| **Geotags are place-tags, not coordinates** | An Instagram post tagged "Grassi Lakes" could be anywhere within a couple of kilometres, or the car park, or someone's living room. The precision you need is tens of metres |
| **EXIF GPS is stripped on upload** | Every major platform removes it. The coordinates simply are not in the data you can get |
| **Post time ≠ capture time** | Often days apart. Without a capture timestamp the observation is unusable, because time is half the question |
| **Scraping breaches terms of service** | The same objection that ruled out AllTrails. And it involves harvesting identifiable people's location data |
| **Selection bias** — your point | One-directional. Nobody posts the shaded photo |

Effort is high, signal is low, and the legal position is poor. Flickr (B2) gives you the same idea with real coordinates, real timestamps and a licence that permits it.

---

## 5. What local knowledge is genuinely needed for

Not the geometry. **The walk selection** — whether a trail is a good dog walk, whether the parking is a nightmare, whether it is a slog through deadfall.

Substitutes, in rough order of usefulness:

1. **Official trail descriptions** — Parks Canada and Alberta Parks. Authoritative on rules, decent on character
2. **James** — see B4
3. **Guidebooks** — Daffern for Kananaskis; the Canadian Rockies Trail Guide. Reading them is entirely legitimate; it is only bulk-extracting them as data that is not
4. **AllTrails and similar, read as a human** — reading reviews is fine. It is automated extraction that breaches the terms
5. **Reddit, forums, local blogs** — good on the practical texture that official sources omit

**And a reframe that matters:** for a demonstration project, the shortlist does not have to be *the ten best dog walks near Canmore*. It has to be **ten defensible walks that produce interesting, differentiated answers**. That is a much lower bar, and one you can clear from a desk. See `06-dog-walk-filter.md`.

---

## 6. State the limitation in the output

The tool will end up **geometrically validated and locally unverified**. That is a perfectly respectable position, provided it is stated rather than hidden.

Suggested line in the caveats panel:

> Shadow model validated against independent terrain calculations and public webcam observations. Not validated by on-the-ground observation.

For a project whose stated purpose is to demonstrate method, being explicit about exactly how far the validation goes is not a weakness in the deliverable. It is the deliverable.

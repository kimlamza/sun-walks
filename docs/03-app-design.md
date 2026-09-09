# 03 — App design

**Recommendation: Python + Streamlit, repository on GitHub, edited in Cursor, deployed free on Streamlit Community Cloud.**

One language end to end, no separate frontend and backend to learn, maps and tables built in, and deployment is "push to GitHub". For a first coding project it gets you to something working in days, and the edit-commit-push-live loop is exactly what you said you want to learn.

**What would change the view:** if you later want this as a phone app or shared with others, you outgrow Streamlit and move to a web frontend with a Python API behind it. That is a rebuild of the interface only — the analysis code carries over unchanged, which is why the structure below separates them.

---

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3.13** | Best geospatial libraries by a distance. Readable. Not 3.14 — `rasterio` wheels lag a release on Windows. Not 3.12 — it is security-only now, with no Windows installer past 3.12.10 |
| UI | **Streamlit** | Turns a Python script into a web app. No HTML, CSS or JavaScript |
| Geospatial | `rasterio`, `numpy`, `pyproj`, `shapely`, `geopandas` | DEMs, coordinate transforms, geometry, spatial joins |
| Trail data | `requests` (Overpass API), `osmnx` optional | Pulling OSM paths |
| Routes | `gpxpy` | Reads GPX |
| Sun | `pvlib` | Solar position |
| Weather | `requests` | Open-Meteo needs nothing more |
| Map | `folium` via `streamlit-folium` | Leaflet map with routes drawn on it |
| Testing | `pytest` | |
| Hosting | **Streamlit Community Cloud** | Free, connects to GitHub, redeploys on push |

`geopandas` is the one addition from the UK draft, and it earns its place: the jurisdiction spatial join in Phase 1 is a two-line operation with it and a miserable afternoon without.

Deliberately **not** in v1: no database (files on disk are fine), no user accounts, no Docker, no cloud infrastructure.

---

## 2. Repository structure

```
sun-walks/
  README.md
  requirements.txt
  .gitignore
  app.py                        # Streamlit UI — thin
  src/
    trails.py                   # Overpass query, OSM assembly, thinning
    jurisdiction.py             # park boundary spatial join
    filter.py                   # Tier 0 / 1 / 2 dog-suitability filter
    routes.py                   # GPX load, clean, resample, derive stats
    terrain.py                  # DEM load, slope/aspect, horizon ray march
    sun.py                      # solar position, timezone handling
    weather.py                  # Open-Meteo client + disk cache
    avalanche.py                # Avalanche Canada bulletin fetch (display only)
    score.py                    # rank, explain
    precompute.py               # build horizon profiles — offline, not per query
  data/
    boundaries/                 # park polygons — small, commit
    routes/*.gpx                # small, commit
    walks.csv                   # THE shortlist + rules layer — commit
    dem/                        # LARGE — do NOT commit
    horizons/                   # generated cache — do not commit
  tests/
  docs/
```

**Design principle: `app.py` contains no analysis.** It collects inputs, calls into `src/`, displays results. Everything in `src/` is plain functions, testable without running the app, and survives if Streamlit is ever replaced.

**`data/walks.csv` is the most valuable file in the repository.** It is the Phase 1 deliverable, it holds hand-curated knowledge that exists nowhere else, and it is the thing that would be painful to lose. It is small — commit it, and let Git version it.

### What not to commit

GitHub rejects files over 100 MB and warns above 50 MB. The DEM for an 80 km radius at 30 m is roughly 110 MB uncompressed.

`.gitignore`:

```
data/dem/
data/horizons/
__pycache__/
*.pyc
.venv/
.env
.streamlit/secrets.toml
```

Write a script that downloads and prepares the DEM instead. The repository stays small and anyone — including future you on a new machine — can rebuild the data.

---

## 3. Data flow

```
              PHASE 1 — ONE-OFF, MOSTLY MANUAL
  Overpass (50 km radius) ──▶ candidate paths
                                    │
  park boundaries ──▶ spatial join ─┤
                                    ▼
                          automatic thinning
                                    │
                          hand review (you)
                                    │
                          rules curation
                                    ▼
                            data/walks.csv          ← the shortlist

              PHASE 2 — SETUP (offline, minutes)
  GPX ────┐
          ├──▶ resample to 100 m ──▶ sample points
  DEM ────┴──▶ merge, reproject ───▶ heights, slope, aspect
                          │
                          ▼
              ray march every 2° azimuth
                          │
                          ▼
              data/horizons/                        ← cached

              PER QUERY (live, milliseconds)
  date + time ──▶ solar azimuth + elevation
                          │
  walks.csv ──▶ Tier 0/1 filter for this date
                          │
                          ▼
        horizon lookup + self-shading per point
                          │
                          ▼
                % of route in direct sun
                          │
  lat/lon + hour ──▶ Open-Meteo ──▶ DNI, cloud, temp, wind
  region + date ───▶ Avalanche Canada ──▶ bulletin (display only)
                          │
                          ▼
          rank → recommend → caveats → display
```

Everything slow happens once, offline. Everything the user waits for is a lookup.

---

## 4. The interface

### Inputs

| Control | Default |
|---|---|
| Date | Today |
| Start time | 10:00 |
| Max drive time | 45 min |
| Distance range | 4–12 km |
| Max ascent | 500 m |
| Pace multiplier | 1.3 |
| Passes I hold | Kananaskis ☐ Banff ☐ |
| Mode | Find sun ⦿ / Find shade ○ |

Keep it to one screen. Every extra control is a decision before an answer.

The **passes** control is Canmore-specific and genuinely useful — it removes walks you would have to pay to reach today. The **find shade** toggle inverts the query for hot summer days.

### Outputs

**1. The recommendation**

> **Grotto Canyon** — 81% of the route in direct sun at 12:40.
> Strong direct sun forecast (DNI 690 W/m²). −8 °C, light wind.
> 4.2 km, 180 m ascent, ~1h30m, 18 min drive. Kananaskis pass required.
> **Confidence: High** — 1 day ahead.
>
> *Runner-up Grassi Lakes lost on sun: 24% — below the Ha Ling ridgeline until mid-afternoon in January.*

The "why not" line is as important as the recommendation. It makes the answer inspectable rather than oracular.

**2. The map** — route lines coloured by state at the evaluated instant, warm where sunlit, grey where shaded, on a terrain basemap. This single view explains more than any number and makes wrong answers obvious at a glance.

**3. The comparison table**

| Walk | Sun % | Direct beam | Temp | Distance | Ascent | Drive | Pass | Confidence |
|---|---|---|---|---|---|---|---|---|
| Grotto Canyon | 81% | Strong | −8 °C | 4.2 km | 180 m | 18 min | K-Country | High |
| Quarry Lake | 64% | Strong | −6 °C | 2.5 km | 40 m | 5 min | None | High |
| Grassi Lakes | 24% | Strong | −9 °C | 4.0 km | 230 m | 12 min | K-Country | High |

**4. Excluded walks — shown, not hidden**

> 6 walks excluded for this date:
> · 3 — avalanche terrain (ATES Challenging or Complex), winter
> · 2 — seasonal wildlife closure
> · 1 — outside distance range

**5. The caveats panel — always visible**

> Terrain shadow only. **Tree cover is not modelled** — forested trails will read sunnier than they are.
> Evaluated at a single moment (12:40), not across the walk.
> Terrain resolution 30 m; gullies and cliff bands not resolved.
> "In shadow" means no direct sun, not darkness — snow makes shade bright.
> Weather is a 2.5 km grid forecast; Bow Valley conditions are highly local.
> **This tool does not assess avalanche or wildlife safety.** Check Avalanche Canada and Parks Canada before you go.
> Trail rules last reviewed: [date].

---

## 5. Scope boundaries

### In scope for v1

- Dog-suitability filter across three jurisdictions, with seasonal gates
- Terrain-only shadow from a 30 m DEM
- Single evaluated instant per walk
- Curated shortlist of 20–40 walks
- Sun geometry and weather reported separately
- Map, ranked table, exclusion list, one recommendation with reasoning
- Explicit uncertainty and confidence
- Pass-required filtering
- Find-shade inverse mode

### Explicitly out of scope for v1

| Excluded | Why |
|---|---|
| Tree and forest canopy shade | Your call, and reasonable — but flag it as the largest known bias here. Needs canopy data |
| Buildings, structures | Irrelevant at this scale |
| Sun and shade changing over the walk | Your call. Multiplies compute and output complexity |
| **Avalanche safety assessment** | Out of scope permanently. Surface the official rating, defer |
| **Wildlife presence prediction** | Seasonal risk flags only |
| Live trail conditions, snow depth, washouts | Hand-curated with a review date, linked to the official source |
| Fully automatic trail discovery | Semi-automatic — Overpass gives candidates, you make the calls |
| Mobile app | Streamlit works in a phone browser |
| User accounts, saved history | No |
| Dates beyond the forecast horizon | **Refuse and say why** |
| Navigation | This picks a walk. It does not guide you round it |

### Deliberately deferred, likely v2

- Start-time and end-time results alongside the midpoint
- Multiple weather sample points on long routes
- Time-of-day slider showing shadows moving across the map
- "Best time today to do this walk" — invert the question
- Snow-adjusted duration
- Tree canopy from a DSM minus DTM comparison

---

## 6. Build order

Two phases. Each step produces something checkable. **Do not move on until the current step is verifiably right.**

### Phase 1 — the walk list (see `06-dog-walk-filter.md`)

| # | Step | Done when |
|---|---|---|
| 1 | Toolchain: Python, Git, Cursor, repo, first commit | Repo visible on github.com |
| 2 | Overpass query, candidates loaded | You can see how many exist |
| 3 | Plot candidates on a map | The scale of the problem is visible |
| 4 | **Sun spike** — 3 routes, one DEM tile, one instant | Model agrees with what you know about January shade |
| 5 | Park boundaries, spatial join | Every candidate carries a jurisdiction |
| 6 | Automatic thinning | List is human-reviewable |
| 7 | Hand review to 20–40 | Shortlist exists |
| 8 | Rules curation | Every row has `source_url` and `last_reviewed` |
| 9 | **`data/walks.csv`** | **Useful on its own** |

### Phase 2 — the sun engine

| # | Step | Done when |
|---|---|---|
| 10 | Load GPX, sample DEM heights along route | Elevation profile matches the real walk |
| 11 | Solar position | Sunrise matches a published table for Canmore |
| 12 | Ray march, one point, one moment | **Matches a QGIS hillshade for the same instant** |
| 13 | Precompute horizons for one route | Cache written; query instant |
| 14 | Sun % across a whole route | Correctly identifies a valley you know is shaded in January |
| 15 | Open-Meteo fetch | DNI values sane against the actual sky |
| 16 | Streamlit UI: inputs, map, table | Runs in a browser |
| 17 | Ranking, recommendation, exclusions, caveats | Answer is defensible when you disagree with it |
| 18 | Deploy to Streamlit Cloud | Reachable from your phone |

**Steps 4 and 12 are the crux.** Step 4 tells you early whether the premise holds. Step 12 is the validation that everything downstream rests on. Budget time for both, and do step 12 against an independent tool before building any UI.

---

## 7. Honest risk assessment

| Risk | Severity | Mitigation |
|---|---|---|
| **The rules layer goes stale and the app confidently reports a closed trail as open** | **High — and the one with real-world consequences** | Never assert. Link to the live official page, show `last_reviewed`, state plainly that the tool does not track closures |
| Coordinate system confusion produces plausible-looking wrong answers | High | Reproject everything to EPSG:26911 at load. Assert units in tests. Validate against QGIS early |
| Shadow model subtly wrong and never checked | High | Steps 4 and 12 are non-negotiable |
| **Tree cover makes forested results systematically wrong** | Medium–High | Known bias. Record a `shade_level` field per walk by hand, downgrade confidence on forested routes, state it in the caveats |
| Hand review and rules curation never gets done | Medium | Ship with 10 walks rather than waiting for 40. The table grows over time |
| Precompute skipped, app slow, project stalls on frustration | Medium | Build the cache at step 13, before the UI exists |
| Scope creep — canopy modelling, time animation, live conditions | Medium | The out-of-scope table above |
| Weather or Overpass API changes shape | Low | Isolated in one file each |

**Note how the top risk has changed from the UK draft.** There, the danger was that the walk data did not exist. Here it does — so the danger becomes stating something confidently and wrongly about a trail's rules or safety. Design for deference: the tool ranks sunshine, and points at the authorities for everything else.

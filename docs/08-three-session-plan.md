# 08 — The three-session plan

**Budget: three blocks of 2–3 hours. Roughly 6–9 hours total, as a complete beginner.**

This document supersedes the build order in `03-app-design.md` for the first week. That order is still the right shape for the full project; this is what actually fits in the time available.

---

## What 6–9 hours realistically buys

**Honestly: not a deployed web app with ten walks.** Anyone who tells you otherwise is not counting the hour you will lose to a PATH variable.

What it does buy, which is more valuable for a demonstration piece:

- A working, **validated** shadow engine — the technically hard part, done properly
- Five walks producing real, differentiated answers
- A repository with visible history, tests and documentation
- Every claim traceable to something you checked

**Deferred to later sessions, deliberately:** Overpass/OSM discovery, the geopandas jurisdiction join, the weather API, Streamlit, deployment, full rules curation. Each is a known quantity that can be added once the core works.

---

## Five walks, not ten — and it is not a compromise

You suggested dropping to five if the curation becomes repetitive. Agreed, and there is a better argument for it than time.

**Five is exactly the minimum contrast set.** Each one has a distinct job:

| # | Type | What it demonstrates |
|---|---|---|
| 1 | **Deep valley floor, high south skyline** | The winter shadow extreme — why the project exists |
| 2 | **South-facing bench** | The opposite extreme — a sun trap |
| 3 | **East-facing** | Morning sun, afternoon shade |
| 4 | **West-facing** | The mirror image |
| 5 | **High and open, minimal horizon** | Control case. Should be sunlit whenever the sun is up. **If it isn't, the model is broken** |

Nothing is padding. Walks 3 and 4 swapping rank between a 09:00 and a 15:00 query is the single most convincing output this tool can produce, and walk 5 is a live self-test that runs on every query.

Ten walks would add repetition, not capability. Scale up later by adding rows to a CSV — nothing else changes.

### A consequence worth stating

**At five walks, the dog filter is a spreadsheet, not a program.** Do not write code to filter five rows. The tiered filter designed in `06-dog-walk-filter.md` is real work and stays as the design — it just does not need to be *code* until there are forty walks. Hand-pick five that are obviously appropriate for Jasper and record why in the CSV.

Recognising when not to write code is part of what this exercise is meant to demonstrate.

---

## Session 1 — Toolchain, and one real answer (2–3 h)

**Goal: something pushed to GitHub that computes a result you can check.**

| Step | Time |
|---|---|
| Install Python 3.12 — **tick "Add python.exe to PATH"** | 15 min |
| Install Git; set `user.name` and `user.email` | 10 min |
| GitHub account, two-factor auth | 10 min |
| Install Cursor, sign in | 10 min |
| Turn `Sun-Walks` into a repo, connect to GitHub, push | 20 min |
| Virtual environment, `pip install pvlib pandas` | 10 min |
| Write `src/sun.py` — solar position for Canmore, hourly, today | 30 min |
| **Check computed sunrise/sunset against a published table** | 5 min |
| Commit and push | 5 min |
| **Buffer for things going wrong** | 30–45 min |

**Deliverable:** repo on GitHub; a script printing today's sun angles for Canmore; **validation test A2 passed** (`07` §2).

**Why sun position first, not the DEM:** `pvlib` installs cleanly with no geospatial dependencies, and sunrise time is independently checkable in ten seconds. It proves the whole toolchain end to end while avoiding every install trap.

**Expect friction.** The PATH checkbox, the PowerShell execution policy (`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`), and GitHub's first-time authentication each catch people. Losing 45 minutes here is normal and not a signal about your aptitude.

---

## Session 2 — The shadow engine (2–3 h)

**Goal: a ray march you have proved is correct.**

**The key insight: you can build and validate the entire shadow engine with nothing but `numpy`.** No DEM download, no coordinate systems, no geospatial libraries. That removes every install risk from the hardest part of the project.

| Step | Time |
|---|---|
| `pip install numpy pytest` | 5 min |
| Write `horizon_angle(dem, row, col, azimuth, max_dist)` in `src/terrain.py` | 45 min |
| **Synthetic tests** — flat plane, vertical wall at known height and distance | 45 min |
| Fetch a real DEM: **OpenTopography API**, bounding box around Canmore, one GeoTIFF | 30 min |
| `pip install rasterio`, load it, sample a height | 20 min |
| Horizon profile for one Canmore point — compare against the 20–25° estimate in `02` §0 | 20 min |
| Buffer | 20 min |

**Deliverable:** a validated shadow engine; a real horizon profile for a real point; **validation test A1 passed**.

### The synthetic tests, concretely

```
flat plane          → sunlit whenever solar elevation > 0, never otherwise
wall height h,      → horizon angle in that direction is exactly atan(h/d)
  distance d,          shadow appears precisely as the sun drops below it
  due south         → other directions unaffected
```

Both hand-computable. Both catch the bugs that actually occur: azimuth convention (clockwise from north versus anticlockwise from east — the most common by far), degrees versus radians, row/column transposition, sign errors in the aspect formula.

**Write these before the ray march, not after.** On real terrain these bugs produce entirely plausible output. On a single wall they are obvious.

### On the DEM

**Use the OpenTopography API rather than downloading tiles.** Request Copernicus GLO-30 for a bounding box and it returns one clipped GeoTIFF — no tile merging, no mosaicking. `[verify]` current API key requirements.

For this week, request a **40 km box around Canmore**, not the full 80 km radius from `01`. It is smaller, faster, and enough for a first horizon profile. The full buffer matters for winter low-sun accuracy and can wait.

**Do not install `geopandas` this week.** It is the most likely source of Windows install pain and nothing in these three sessions needs it.

---

## Session 3 — Five walks, one map (2–3 h)

**Goal: real answers for real routes, visible on a map.**

| Step | Time |
|---|---|
| Draw 5 routes at **gpx.studio** — free, browser-based, no account, exports GPX | 45 min |
| `pip install gpxpy`; load routes; resample to a point every 100 m | 30 min |
| Precompute horizon profiles for all sample points | 20 min |
| Compute % of route in direct sun for a chosen date and time | 20 min |
| Output: a map with routes coloured sunlit/shaded (`folium`) | 40 min |
| Buffer | 20 min |

**Deliverable:** five walks, each with a "% in direct sun" figure for any date and time, drawn on a map.

**The test that matters:** run the same five walks at 09:00 and at 15:00 on a January date. Walks 3 and 4 should swap. If they do, the model is doing real work and you have something worth showing.

**Stretch, if the session runs well:** Open-Meteo is roughly twenty lines and needs no API key. Adding direct normal irradiance turns "% in geometric sun" into the two-factor answer the design calls for.

---

## After the three sessions

In rough order of value added per hour:

1. **Open-Meteo weather** — if not already done. Small, high impact
2. **Streamlit UI** — replace the script with inputs and a browser view. 2–3 hours
3. **Walks 6–10** — a row at a time, no structural change
4. **The rules layer** — jurisdiction, passes, closures, `last_reviewed`. Curation, not code
5. **Deploy to Streamlit Community Cloud** — about an hour
6. **Webcam validation** (`07` §3) — the record is worth as much as the result
7. **Overpass discovery and the geopandas join** — only once there are enough walks to justify it

---

## If a session overruns

**Stop at a working commit, not mid-change.** The single most valuable habit in a project made of short scattered blocks: never leave the repository in a state where you have to remember what you were doing.

If session 2's synthetic tests take the whole session, that is fine — a validated ray march with no real DEM is more valuable than an unvalidated one with a beautiful map. **Correctness is the deliverable; the map is the presentation.**

# 11 — Session 2, step by step

**Goal: a ray march you have proved is correct.**

This is the core of the project. Everything before it was plumbing; everything after is presentation. If the shadow calculation is wrong, nothing downstream can be right — so the whole session is built around proving it, not just writing it.

**No new accounts, no downloads, nothing to install beyond two libraries** — until the last step, which is optional.

---

## Step 0 — Cursor, timeboxed to five minutes

Two things to try. If neither works, carry on in PowerShell exactly as you did in session 1 and we sort it another day. Do not spend your block on this.

1. In Cursor, press **`Ctrl+Shift+E`** — the standard shortcut to focus the file tree
2. Press **`Ctrl+Shift+P`**, type `explorer`, and pick any "View: Show Explorer" option

If the editor appears, open `C:\Claude\Work\Sun-Walks` and use its terminal. If not, open PowerShell from the Start menu.

Either way, start by activating the environment:

```powershell
cd C:\Claude\Work\Sun-Walks
.\.venv\Scripts\Activate.ps1
```

**✓ Check** — your prompt starts with `(.venv)`. If it doesn't, nothing else will work.

---

## Step 1 — Two more libraries

```powershell
pip install numpy pytest
```

`numpy` handles grids of numbers efficiently — a terrain model is just a grid of heights. `pytest` runs your tests.

*(`numpy` is already installed as a pvlib dependency; this makes it an explicit requirement of your own, which is honest.)*

---

## Step 2 — What you are actually building

One function. Everything else in this project is arranged around it.

> **`horizon_angle`** — standing at a point, looking in a given compass direction, how high above horizontal does the terrain rise?

If the sun's elevation is **above** that angle, you're in sunlight. If it's **below**, a mountain is in the way.

That's it. Sunrise on a flat plain is the special case where the horizon angle is zero — which is exactly what `sun.py` computed yesterday.

**How the ray march works, in words:** stand at your point. Face the direction you care about. Take a step. Work out the angle from your eye up to the ground there. Take another step, work it out again. Keep going for 30 km. The largest angle you found is the skyline in that direction.

Two subtleties that matter:

- **The ground you're standing on has height too.** You measure the angle from *your* height, not from sea level
- **The Earth curves.** Over 30 km, distant ground falls away below your local horizontal by about 60 m. Ignore that and you invent shadows that don't exist. The correction is `distance² / (2 × R)`, using an Earth radius inflated by 7/6 to approximate how the atmosphere bends light back down

---

## Step 3 — Write the ray march

Create `src/terrain.py`:

```python
"""
Terrain horizon calculations.

The one idea in this file: standing at a point and looking in a given
compass direction, how high above horizontal does the terrain rise?

If the sun is higher than that angle, you are in direct sunlight. If it is
lower, something is in the way. Sunrise on a flat plain is just the case
where that angle happens to be zero.
"""

import math

# Light bends downwards through the atmosphere, which makes the Earth
# behave as though it were about a sixth larger than it is. Standard
# approximation in surveying and radio propagation.
EARTH_RADIUS_M = 6_371_000
EFFECTIVE_RADIUS_M = EARTH_RADIUS_M * 7 / 6


def horizon_angle(dem, row, col, azimuth_deg, cell_size_m,
                  max_distance_m=30_000):
    """
    The highest angle above horizontal to the terrain, looking along a bearing.

    dem           2-D array of ground heights in metres
    row, col      where in the grid you are standing
    azimuth_deg   compass bearing, degrees clockwise from north
    cell_size_m   how much ground one grid cell covers
    max_distance_m  how far to look. 30 km, because a 1,600 m mountain
                  with the sun 5 degrees up throws an 18 km shadow

    Returns degrees. Negative means everything in that direction is
    below you.
    """
    observer_height = dem[row, col]
    n_rows, n_cols = dem.shape

    # North is decreasing row (up the array); east is increasing column.
    azimuth = math.radians(azimuth_deg)
    step_col = math.sin(azimuth)
    step_row = -math.cos(azimuth)

    highest = -90.0
    distance = cell_size_m

    while distance <= max_distance_m:
        cells_out = distance / cell_size_m
        r = int(round(row + step_row * cells_out))
        c = int(round(col + step_col * cells_out))

        # Walked off the edge of the terrain model — stop looking.
        if not (0 <= r < n_rows and 0 <= c < n_cols):
            break

        # Distant ground curves away below the local horizontal.
        drop = distance ** 2 / (2 * EFFECTIVE_RADIUS_M)
        rise = dem[r, c] - observer_height - drop

        angle = math.degrees(math.atan2(rise, distance))
        if angle > highest:
            highest = angle

        distance += cell_size_m

    return highest


def is_sunlit(horizon_deg, solar_elevation_deg):
    """True if the sun clears the skyline in that direction."""
    return solar_elevation_deg > horizon_deg
```

**Read it before running it.** In particular, work out why `step_row` is *negative* cosine. In an array, row 0 is the top — so going north means the row number goes *down*. Getting that backwards is the single most common bug in this kind of code, and the tests below are designed to catch exactly it.

---

## Step 4 — Prove it works

This is the point of the session.

You cannot check a shadow calculation on real terrain, because you don't know the right answer. So you build terrain where you **do** know the answer, and check against arithmetic you can do on paper.

Create a `tests` folder, and inside it `tests/test_terrain.py`:

```python
"""
Tests against terrain simple enough to check by hand.

A flat plane and a single wall are not interesting landscapes, but they
are landscapes where the correct answer is known in advance. Real terrain
can hide a wrong answer behind a plausible-looking one; a flat plane
cannot.
"""

import math

import numpy as np

from src.terrain import horizon_angle, is_sunlit

CELL_SIZE_M = 30
CENTRE = 100          # observer sits at row 100, col 100
WALL_DISTANCE_CELLS = 10
WALL_HEIGHT_M = 100.0

# 10 cells at 30 m each = 300 m away.
WALL_DISTANCE_M = WALL_DISTANCE_CELLS * CELL_SIZE_M
# atan(100 / 300) = 18.43 degrees. Worked out on paper, not by the code.
EXPECTED_WALL_ANGLE = math.degrees(math.atan(WALL_HEIGHT_M / WALL_DISTANCE_M))


def flat_terrain():
    return np.zeros((201, 201))


def test_flat_plane_has_no_horizon():
    """On a flat plane the skyline is at eye level in every direction."""
    dem = flat_terrain()
    for azimuth in (0, 45, 90, 135, 180, 225, 270, 315):
        angle = horizon_angle(dem, CENTRE, CENTRE, azimuth, CELL_SIZE_M)
        assert abs(angle) < 0.1, f"azimuth {azimuth} gave {angle}"


def test_wall_to_the_east():
    """A 100 m wall 300 m away should sit at atan(100/300) = 18.43 degrees."""
    dem = flat_terrain()
    dem[:, CENTRE + WALL_DISTANCE_CELLS] = WALL_HEIGHT_M

    angle = horizon_angle(dem, CENTRE, CENTRE, 90, CELL_SIZE_M)
    assert abs(angle - EXPECTED_WALL_ANGLE) < 0.1


def test_nothing_behind_you():
    """The same wall must be invisible when you look the other way."""
    dem = flat_terrain()
    dem[:, CENTRE + WALL_DISTANCE_CELLS] = WALL_HEIGHT_M

    angle = horizon_angle(dem, CENTRE, CENTRE, 270, CELL_SIZE_M)
    assert abs(angle) < 0.1


def test_north_is_not_south():
    """
    The azimuth convention test — the one that catches real bugs.

    North is decreasing row. A wall placed to the north must be found at
    bearing 0 and must NOT be found at bearing 180.
    """
    dem = flat_terrain()
    dem[CENTRE - WALL_DISTANCE_CELLS, :] = WALL_HEIGHT_M

    looking_north = horizon_angle(dem, CENTRE, CENTRE, 0, CELL_SIZE_M)
    looking_south = horizon_angle(dem, CENTRE, CENTRE, 180, CELL_SIZE_M)

    assert abs(looking_north - EXPECTED_WALL_ANGLE) < 0.1
    assert abs(looking_south) < 0.1


def test_sun_above_and_below_the_skyline():
    """The whole project, in four lines."""
    assert is_sunlit(EXPECTED_WALL_ANGLE, 20.0)      # sun clears the wall
    assert not is_sunlit(EXPECTED_WALL_ANGLE, 15.0)  # wall blocks the sun
```

You also need one small config file so `pytest` can find your `src` folder. Create `pytest.ini` in the repo root — not in `tests`:

```ini
[pytest]
pythonpath = .
```

That single line tells pytest to treat the project root as a place to import from, so `from src.terrain import ...` works.

**Run them:**

```powershell
pytest -v
```

**✓ Check** — five tests, all green:

```
tests/test_terrain.py::test_flat_plane_has_no_horizon PASSED
tests/test_terrain.py::test_wall_to_the_east PASSED
tests/test_terrain.py::test_nothing_behind_you PASSED
tests/test_terrain.py::test_north_is_not_south PASSED
tests/test_terrain.py::test_sun_above_and_below_the_skyline PASSED
```

**If `test_north_is_not_south` fails, that is the test earning its place.** The fix is the sign of `step_row` in `terrain.py`. Don't guess — work out on paper which way row numbers run, then change it.

**Commit here.** This is a real milestone:

```powershell
git add .
git commit -m "Add horizon ray march with synthetic terrain tests"
git push
```

You have now passed **validation test A1** from `07-validation-without-local-knowledge.md` — the highest-value check in the project, and the reason not having been to Canmore doesn't matter.

---

## Step 5 — Real terrain (optional, only if time remains)

**Everything above is the session's deliverable.** This part is a bonus, and it needs one free registration — so if your block is nearly gone, stop at step 4 and pick this up next time.

### Get a DEM

1. Register free at **[opentopography.org](https://opentopography.org)** and get an API key `[verify] current signup flow`
2. Request Copernicus GLO-30 for a box around Canmore. In a browser, substituting your key:

```
https://portal.opentopography.org/API/globaldem?demtype=COP30&south=50.8&north=51.4&west=-115.9&east=-114.9&outputFormat=GTiff&API_Key=YOUR_KEY
```

That's roughly a 40 km box — smaller than the 80 km the full project wants, but plenty for a first horizon profile.

3. Save the file as `data/dem/canmore.tif`

`data/dem/` is already in `.gitignore`, so it won't be committed. That's deliberate — large data is rebuilt by script, never stored in Git.

### Read it

```powershell
pip install rasterio
```

Then a short script to load the DEM, find the cell nearest Canmore town centre, and compute the horizon in every direction.

**What to look for:** `02-method-and-assumptions.md` §0 estimates the southern skyline from the valley floor at **20–25°**. See whether the model agrees. And compare that against the midwinter noon sun of **15.5°** — if the skyline is higher than the sun, the prediction that Canmore's valley floor gets no direct midday sun from November to February holds up.

**That is the moment this project either works or doesn't.** Worth arriving at unhurried.

---

## What you'll have at the end

- A ray march that computes terrain horizons
- Five tests proving it correct against arithmetic you can check on paper
- The most likely bug in the whole project caught before it could hide

**Session 3** is the five walks: draw them as GPX, sample points along each, precompute horizons, and produce "% of route in direct sun" for any date and time — then watch Grassi Lakes and Montane Traverse swap places between morning and afternoon.

---

## If something goes wrong

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | `pytest.ini` missing or in the wrong folder | It goes in the repo root, beside `README.md` |
| `ModuleNotFoundError: No module named 'numpy'` | Environment not activated | Look for `(.venv)`. Re-run the activate command |
| `pytest` not recognised | Same | Same |
| `test_north_is_not_south` fails | Azimuth convention — the classic bug | Sign of `step_row`. Reason it out before changing it |
| All tests fail with `IndexError` | Observer position outside the array | `CENTRE` must be well inside a 201 × 201 grid |
| Tests pass but you don't trust them | Healthy instinct | Break the code on purpose — flip a sign — and check the tests go red. A test that never fails is proving nothing |

That last one is worth doing once. A test suite you've never seen fail is a test suite you have no reason to believe.

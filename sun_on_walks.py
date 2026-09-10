"""
What fraction of each walk is in direct sunlight, at a given date and time?

This is the product, in miniature. For each trail:

  - take the points OpenStreetMap gave us
  - work out where the sun is at that moment
  - for each point, ray march towards the sun and see if terrain blocks it
  - report the percentage that comes out sunlit

Two simplifications, both deliberate and both documented in
docs/02-method-and-assumptions.md:

  1. One instant, not the whole walk. Section 1a.
  2. No separate self-shading calculation. Section 3a treats "the slope
     faces away from the sun" as a distinct test, but on a continuous
     slope the ray march already catches it - if the ground rises away
     from you towards the sun, the very first step uphill returns a large
     horizon angle. The two only diverge near sharp breaks in slope, at
     scales a 30 m terrain model cannot resolve anyway.

Run it with:  python sun_on_walks.py
"""

import json
from pathlib import Path

import pandas as pd
import pvlib
import rasterio
from pyproj import Transformer

from src.terrain import horizon_angle, is_sunlit

PROJECTED_DEM = "data/dem/canmore_utm.tif"
ROUTES_DIR = Path("data/routes")
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30
TIMEZONE = "America/Edmonton"

# The demonstration: a morning query and an afternoon one, in midwinter,
# when the effect is strongest.
#
# Note the winter times. Alberta moved to permanent UTC-6 ("Alberta Time")
# under the Official Time Act of 18 June 2026, effective November 2026 - so
# clocks no longer go back. On the solstice that puts sunrise at 09:46 and
# sunset at 17:30 by the clock. A 09:00 winter query is simply darkness, so
# the useful window is roughly 10:00 to 17:00.
WHEN = [
    ("2026-12-21 10:30", "Midwinter morning"),
    ("2026-12-21 15:30", "Midwinter afternoon"),
    ("2026-06-21 09:00", "Midsummer morning"),
    ("2026-06-21 14:00", "Midsummer afternoon"),
]

# Ray marching every point is slow in plain Python, and neighbouring points
# on a trail give almost identical answers. Every 3rd point is plenty.
SAMPLE_EVERY = 3


def load_terrain():
    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        rows, cols = dem.shape

        def grid_position(lat, lon):
            easting, northing = to_utm.transform(lon, lat)
            row, col = dem_file.index(easting, northing)
            if 0 <= row < rows and 0 <= col < cols:
                return row, col
            return None

        return dem, grid_position


def load_routes():
    routes = []
    for path in sorted(ROUTES_DIR.glob("*.json")):
        routes.append(json.loads(path.read_text()))
    return routes


def sun_position(lat, lon, height_m, when):
    """Solar elevation and bearing at one moment, at one place."""
    location = pvlib.location.Location(lat, lon, tz=TIMEZONE, altitude=height_m)
    times = pd.DatetimeIndex([when]).tz_localize(TIMEZONE)
    position = location.get_solarposition(times)
    return (
        float(position["apparent_elevation"].iloc[0]),
        float(position["azimuth"].iloc[0]),
    )


def fraction_in_sun(dem, grid_position, points, when):
    """Percentage of sampled points with a clear line to the sun."""
    sampled = points[::SAMPLE_EVERY]

    # The sun moves negligibly across a few kilometres of trail, so one
    # position for the whole route is fine.
    mid_lat, mid_lon = sampled[len(sampled) // 2]
    elevation, azimuth = sun_position(mid_lat, mid_lon, 1400, when)

    if elevation <= 0:
        return None, elevation, azimuth, 0

    lit = 0
    counted = 0
    for lat, lon in sampled:
        position = grid_position(lat, lon)
        if position is None:
            continue          # outside the terrain model
        row, col = position
        skyline = horizon_angle(dem, row, col, azimuth, CELL_SIZE_M)
        lit += is_sunlit(skyline, elevation)
        counted += 1

    if counted == 0:
        return None, elevation, azimuth, 0

    return 100 * lit / counted, elevation, azimuth, counted


if __name__ == "__main__":
    dem, grid_position = load_terrain()
    routes = load_routes()

    if not routes:
        raise SystemExit("No routes found. Run fetch_trails.py first.")

    for when, label in WHEN:
        print("=" * 70)
        print(f"{label}  -  {when}")

        results = []
        for route in routes:
            percent, elevation, azimuth, counted = fraction_in_sun(
                dem, grid_position, route["points"], when
            )
            results.append((percent, route, counted))

        if results[0][0] is None:
            print(f"  Sun is below the horizon ({elevation:.1f} deg). "
                  "Nothing to compute.")
            continue

        print(f"  Sun: {elevation:.1f} deg above horizon, "
              f"bearing {azimuth:.0f} deg\n")
        print(f"  {'Walk':22} {'In sun':>8}   {'Points':>6}   Role")

        for percent, route, counted in sorted(
            results, key=lambda r: -(r[0] or 0)
        ):
            shown = "n/a" if percent is None else f"{percent:5.0f}%"
            print(f"  {route['slug']:22} {shown:>8}   {counted:6}   "
                  f"{route['role']}")

    print("=" * 70)
    print("\nThe result to look for: walks changing places between the")
    print("morning and afternoon rows. If the ranking is identical at")
    print("09:00 and 14:00, the model is not doing any real work.")

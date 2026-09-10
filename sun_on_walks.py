"""
What fraction of each walk is in direct sunlight, if you set off at a
given time?

This is the product in miniature. For each walk:

  - read its distance and ascent from data/walks.csv
  - estimate how long it takes (Naismith, see src/duration.py)
  - work out the representative time: start plus half the duration
  - find where the sun is at that moment
  - ray march from each trail point towards it, and count how many have a
    clear line

The headline figure is the midpoint. Start and end are shown alongside,
because the measured results made the case: Montane Traverse runs 63%
sunlit at 10:30 and 100% at 15:30, so one number hides a lot on a long
winter walk. That is three instants, not a simulation - the design
constraint in docs/02 section 1a still holds.

Alberta is on permanent UTC-6 from November 2026 (Official Time Act,
18 June 2026), so on the solstice sunrise is 09:46 and sunset 17:30.
Winter start times before 10:00 are simply darkness.

Run it with:  python sun_on_walks.py
"""

import csv
import json
from pathlib import Path

import pandas as pd
import pvlib
import rasterio
from pyproj import Transformer

from src.duration import format_duration, walk_times
from src.terrain import horizon_angle, is_sunlit

PROJECTED_DEM = "data/dem/canmore_utm.tif"
ROUTES_DIR = Path("data/routes")
WALKS_CSV = Path("data/walks.csv")

LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30
TIMEZONE = "America/Edmonton"

# Neighbouring points on a trail give almost identical answers, and ray
# marching every one is slow in plain Python. Every 3rd is plenty.
SAMPLE_EVERY = 3

SCENARIOS = [
    ("2026-12-21", "11:00", "Midwinter, setting off at 11:00"),
    ("2026-06-21", "09:00", "Midsummer, setting off at 09:00"),
]


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


def load_walks():
    """Metadata for every walk, with trail geometry attached where we have it."""
    walks = []
    with WALKS_CSV.open() as handle:
        for row in csv.DictReader(handle):
            row["distance_km"] = float(row["distance_km"])
            row["ascent_m"] = float(row["ascent_m"])

            route_file = ROUTES_DIR / f"{row['slug']}.json"
            if route_file.exists():
                row["points"] = json.loads(route_file.read_text())["points"]
            else:
                row["points"] = None
            walks.append(row)
    return walks


def sun_position(lat, lon, height_m, when):
    location = pvlib.location.Location(lat, lon, tz=TIMEZONE, altitude=height_m)
    position = location.get_solarposition(pd.DatetimeIndex([when]))
    return (
        float(position["apparent_elevation"].iloc[0]),
        float(position["azimuth"].iloc[0]),
    )


def fraction_in_sun(dem, grid_position, points, when):
    """Percentage of sampled trail points with a clear line to the sun."""
    sampled = points[::SAMPLE_EVERY]

    # The sun moves negligibly across a few kilometres of trail, so one
    # position for the whole route is fine.
    mid_lat, mid_lon = sampled[len(sampled) // 2]
    elevation, azimuth = sun_position(mid_lat, mid_lon, 1400, when)

    if elevation <= 0:
        return None, 0

    lit = counted = 0
    for lat, lon in sampled:
        position = grid_position(lat, lon)
        if position is None:
            continue                      # outside the terrain model
        row, col = position
        skyline = horizon_angle(dem, row, col, azimuth, CELL_SIZE_M)
        lit += is_sunlit(skyline, elevation)
        counted += 1

    if counted == 0:
        return None, 0
    return 100 * lit / counted, counted


def percent(value):
    return "  dark" if value is None else f"{value:5.0f}%"


if __name__ == "__main__":
    dem, grid_position = load_terrain()
    walks = load_walks()

    for date, start_clock, label in SCENARIOS:
        start = pd.Timestamp(f"{date} {start_clock}", tz=TIMEZONE)

        print("=" * 78)
        print(label)
        print()
        print(f"  {'Walk':20} {'Takes':>6}  {'Eval at':>7}  "
              f"{'Start':>6} {'MIDPOINT':>9} {'End':>6}   Points")
        print("  " + "-" * 74)

        rows = []
        for walk in walks:
            begin, middle, finish, hours = walk_times(
                start, walk["distance_km"], walk["ascent_m"]
            )

            if walk["points"] is None:
                rows.append((None, walk, format_duration(hours), middle,
                             None, None, None, 0))
                continue

            at_start, _ = fraction_in_sun(
                dem, grid_position, walk["points"], begin)
            at_middle, counted = fraction_in_sun(
                dem, grid_position, walk["points"], middle)
            at_end, _ = fraction_in_sun(
                dem, grid_position, walk["points"], finish)

            rows.append((at_middle, walk, format_duration(hours), middle,
                         at_start, at_middle, at_end, counted))

        # Rank on the midpoint - the headline figure. Walks with no
        # geometry sort to the bottom.
        rows.sort(key=lambda r: -1 if r[0] is None else -r[0])

        for headline, walk, takes, middle, a, b, c, counted in rows:
            if walk["points"] is None:
                print(f"  {walk['slug']:20} {takes:>6}  {middle:%H:%M}    "
                      f"    no trail geometry yet - see docs/09")
                continue

            print(f"  {walk['slug']:20} {takes:>6}  {middle:%H:%M}  "
                  f"{percent(a)} {percent(b):>9} {percent(c)}   {counted:4}")

        print()
        print("  Ranked on the midpoint. Start and end show how much changes")
        print("  while you are out - they are three instants, not a simulation.")

    print("=" * 78)

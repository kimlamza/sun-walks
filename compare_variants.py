"""
Do the differently-named parts of a walk give different answers?

fetch_trails.py merges every OpenStreetMap way whose name matches into one
point cloud. For Heart Creek, Troll Falls and Montane Traverse that turned
out to merge unrelated trails, and the fix was to exclude them by name.

But some merges are legitimate. Grassi Lakes has an Interpretive route and
an Upper route that share both endpoints and take different lines between
them. Merging those is only safe if they give the same answer.

This computes each named variant separately so they can be compared. If
they agree, the merge is harmless. If they do not, they are really two
walks and should be two rows in walks.csv.

Run it with:  python compare_variants.py grassi-lakes
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from inspect_route import ways_by_name
from src.evaluate import TIMEZONE, sun_position
from src.terrain import horizon_profile, horizon_towards

PROJECTED_DEM = "data/dem/canmore_utm.tif"
ROUTES_DIR = Path("data/routes")
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30

AZIMUTHS = list(range(0, 360, 2))
MAX_POINTS = 30

WHEN = [
    ("2026-12-21 11:00", "Midwinter 11:00"),
    ("2026-12-21 13:00", "Midwinter 13:00"),
    ("2026-12-21 15:00", "Midwinter 15:00"),
    ("2026-06-21 09:00", "Midsummer 09:00"),
]


def evenly_spaced(points, limit):
    if len(points) <= limit:
        return points
    step = len(points) / limit
    return [points[int(i * step)] for i in range(limit)]


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "grassi-lakes"
    route = json.loads((ROUTES_DIR / f"{slug}.json").read_text())

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        n_rows, n_cols = dem.shape
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        index_of = dem_file.index

    print(f"{slug} - comparing each OpenStreetMap name separately\n")

    variants = {}
    for name, group in sorted(ways_by_name(route["search_term"]).items()):
        points = evenly_spaced(group, MAX_POINTS)

        kept, profiles = [], []
        for lat, lon in points:
            easting, northing = to_utm.transform(lon, lat)
            row, col = index_of(easting, northing)
            if 0 <= row < n_rows and 0 <= col < n_cols:
                profiles.append(
                    horizon_profile(dem, row, col, CELL_SIZE_M, AZIMUTHS)
                )
                kept.append([lat, lon])

        if profiles:
            variants[name] = (np.array(kept), np.array(profiles))

    if not variants:
        raise SystemExit("Nothing found.")

    def percent_at(points, profiles, moment):
        lat, lon = points.mean(axis=0)
        elevation, azimuth = sun_position(float(lat), float(lon), moment)
        if elevation <= 0:
            return None
        skyline = np.array([
            horizon_towards(p, AZIMUTHS, azimuth) for p in profiles
        ])
        return 100 * (elevation > skyline).mean()

    # Sweep whole days rather than checking a few chosen moments.
    #
    # Grassi Lakes reads 0% all winter and 100% on a summer morning
    # whichever variant you take - but those are saturated conditions,
    # where agreement is inevitable and proves nothing. A comparison is
    # only informative where the answer could have gone either way, so
    # find the hour of greatest disagreement instead of assuming one.
    print(f"  {'OpenStreetMap name':42} {'pts':>4}")
    for name, (points, _) in variants.items():
        print(f"  {name:42} {len(points):4}")

    worst = None
    for date in ("2026-12-21", "2026-03-20", "2026-06-21", "2026-09-22"):
        for hour in range(4, 22):
            moment = pd.Timestamp(f"{date} {hour:02d}:00", tz=TIMEZONE)
            values = {
                name: percent_at(points, profiles, moment)
                for name, (points, profiles) in variants.items()
            }
            known = [v for v in values.values() if v is not None]
            if len(known) < 2:
                continue

            spread = max(known) - min(known)
            if worst is None or spread > worst[0]:
                worst = (spread, moment, values)

    spread, moment, values = worst
    print(f"\nGreatest disagreement across four seasons, sweeping every hour:")
    print(f"  {moment:%d %B, %H:%M}\n")
    for name, value in values.items():
        print(f"  {name:42} {value:5.0f}%")

    print(f"\n  Spread: {spread:.0f} percentage points")
    if spread < 10:
        print("\n  These variants never meaningfully disagree. Merging them")
        print("  is safe - they are one walk taking slightly different lines.")
    else:
        print("\n  These variants DO disagree. They are really two walks and")
        print("  should be two rows in walks.csv with separate geometry.")

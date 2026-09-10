"""
Work out the skyline once, so the app never has to.

Ray marching is the expensive part of this project. Answering one query for
ten walks takes over a minute, which is fine for a script and useless for
something you click.

The fix, from docs/02-method-and-assumptions.md section 5: the skyline from
a given spot never changes. Mountains do not move. So compute the full
panorama once - the terrain angle in every direction - and store it. A query
then becomes "look up the angle towards the sun's bearing and compare", which
takes microseconds.

The same stored profile answers any date and any time, for ever.

Run this once after preparing a new DEM, or after adding walks:

    python prepare_dem.py
    python fetch_trails.py
    python precompute_horizons.py
"""

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

from src.terrain import horizon_profile

PROJECTED_DEM = "data/dem/canmore_utm.tif"
ROUTES_DIR = Path("data/routes")
HORIZONS_DIR = Path("data/horizons")
WALKS_CSV = Path("data/walks.csv")

LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30

# Every 2 degrees. Coarser sampling steps over ridge crests - at 22 degrees
# the skyline above Canmore read 14.8 degrees when it is really 16.7, which
# flipped a midwinter answer. See docs/02 section 0.
AZIMUTH_STEP = 2
AZIMUTHS = list(range(0, 360, AZIMUTH_STEP))

# Trail points are dense and neighbours give nearly identical answers.
# Fifty spread evenly along a walk is plenty to estimate a percentage.
MAX_POINTS_PER_WALK = 50


def evenly_spaced(points, limit):
    if len(points) <= limit:
        return points
    step = len(points) / limit
    return [points[int(i * step)] for i in range(limit)]


if __name__ == "__main__":
    HORIZONS_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        n_rows, n_cols = dem.shape
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        index_of = dem_file.index

    with WALKS_CSV.open() as handle:
        walks = list(csv.DictReader(handle))

    print(f"{len(AZIMUTHS)} bearings per point, "
          f"up to {MAX_POINTS_PER_WALK} points per walk\n")

    for walk in walks:
        slug = walk["slug"]
        route_file = ROUTES_DIR / f"{slug}.json"

        if not route_file.exists():
            print(f"{slug:20} no geometry - skipped")
            continue

        points = evenly_spaced(
            json.loads(route_file.read_text())["points"], MAX_POINTS_PER_WALK
        )

        kept_points = []
        profiles = []
        outside = 0

        for lat, lon in points:
            easting, northing = to_utm.transform(lon, lat)
            row, col = index_of(easting, northing)

            if not (0 <= row < n_rows and 0 <= col < n_cols):
                outside += 1
                continue

            profiles.append(
                horizon_profile(dem, row, col, CELL_SIZE_M, AZIMUTHS)
            )
            kept_points.append([lat, lon])

        if not profiles:
            print(f"{slug:20} every point outside the terrain model")
            continue

        np.savez_compressed(
            HORIZONS_DIR / f"{slug}.npz",
            azimuths=np.array(AZIMUTHS),
            points=np.array(kept_points),
            horizons=np.array(profiles),
        )

        skyline = np.array(profiles)
        note = f", {outside} outside the model" if outside else ""
        print(f"{slug:20} {len(kept_points):3} points{note}   "
              f"skyline {skyline.min():5.1f} to {skyline.max():5.1f} deg")

    print(f"\nWritten to {HORIZONS_DIR}/. Queries are now lookups.")
    print("Rerun this after changing the DEM or adding a walk.")

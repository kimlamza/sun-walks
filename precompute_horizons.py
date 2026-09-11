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


def trim_to_trailhead(points, walk, to_utm):
    """
    Keep only the part of a mapped trail that people actually walk.

    OpenStreetMap maps a trail end to end. Lake Minnewanka's runs 19 km
    along the shore - nearly 40 km out and back - while the walk anyone does
    from the day use area is about 8 km. Without trimming, the sun
    percentage describes the whole lakeshore rather than the walk.

    Where walks.csv gives a trailhead and a trim distance, points beyond
    that distance are dropped. Blank means keep everything.
    """
    if not walk.get("trim_km") or not walk.get("trailhead_lat"):
        return points, 0

    limit_m = float(walk["trim_km"]) * 1000
    head = to_utm.transform(
        float(walk["trailhead_lon"]), float(walk["trailhead_lat"])
    )

    kept = []
    for lat, lon in points:
        easting, northing = to_utm.transform(lon, lat)
        if np.hypot(easting - head[0], northing - head[1]) <= limit_m:
            kept.append([lat, lon])

    return kept, len(points) - len(kept)


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

        all_points = json.loads(route_file.read_text())["points"]
        all_points, trimmed = trim_to_trailhead(all_points, walk, to_utm)

        if not all_points:
            print(f"{slug:20} every point trimmed away - check trim_km")
            continue

        points = evenly_spaced(all_points, MAX_POINTS_PER_WALK)

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
        notes = []
        if trimmed:
            notes.append(f"{trimmed} beyond {walk['trim_km']} km of trailhead")
        if outside:
            notes.append(f"{outside} outside the model")
        note = f"  ({'; '.join(notes)})" if notes else ""

        print(f"{slug:20} {len(kept_points):3} points   "
              f"skyline {skyline.min():5.1f} to {skyline.max():5.1f} deg{note}")

    print(f"\nWritten to {HORIZONS_DIR}/. Queries are now lookups.")
    print("Rerun this after changing the DEM or adding a walk.")

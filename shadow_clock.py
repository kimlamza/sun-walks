"""
When does the sun reach this spot, and when does it leave?

The strongest form of validation B1. Checking whether a webcam shows sun or
shade right now is a weak test - you already know the answer before you
look, and it is easy to talk yourself into agreement. Predicting the minute
a shadow line crosses a specific place, and then watching it happen, is not.

    python shadow_clock.py 51.0894 -115.3592 2026-09-11

Reports every transition through the day, and how fast the shadow is
moving at each one. A transition where the margin changes slowly is a poor
test - a few minutes either way is within the model's error. One that
changes quickly is a sharp prediction and worth watching.
"""

import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

from src.evaluate import TIMEZONE, sun_position
from src.terrain import horizon_profile, horizon_towards

PROJECTED_DEM = "data/dem/canmore_utm.tif"
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30
AZIMUTHS = list(range(0, 360, 1))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(
            "Usage: python shadow_clock.py <lat> <lon> YYYY-MM-DD"
        )

    lat, lon, date = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        easting, northing = to_utm.transform(lon, lat)
        row, col = dem_file.index(easting, northing)

    skyline = horizon_profile(dem, row, col, CELL_SIZE_M, AZIMUTHS)

    minutes = pd.date_range(f"{date} 00:00", f"{date} 23:59",
                            freq="1min", tz=TIMEZONE)

    margins = []
    for moment in minutes:
        elevation, azimuth = sun_position(lat, lon, moment)
        if elevation <= 0:
            margins.append(None)
        else:
            margins.append(elevation - horizon_towards(skyline, AZIMUTHS,
                                                       azimuth))

    print(f"{lat}, {lon}   {date}")
    print(f"  Ground height {dem[row, col]:.0f} m")
    print(f"  Skyline ranges {skyline.min():.1f} to {skyline.max():.1f} deg\n")

    previous = None
    transitions = 0

    for moment, margin in zip(minutes, margins):
        lit = margin is not None and margin > 0
        if previous is not None and lit != previous:
            # How fast is the margin moving? A slow crossing is a weak
            # prediction - a few minutes either way sits inside the error.
            window = [m for m in margins[max(0, minutes.get_loc(moment) - 15):
                                         minutes.get_loc(moment) + 15]
                      if m is not None]
            speed = (max(window) - min(window)) / 30 if len(window) > 1 else 0

            verdict = ("sharp - worth watching" if speed > 0.15
                       else "slow - a few minutes either way is within error")
            print(f"  {moment:%H:%M}  ->  "
                  f"{'SUN arrives' if lit else 'SHADE arrives'}"
                  f"   ({speed * 60:.1f} deg/hour, {verdict})")
            transitions += 1
        previous = lit

    if not transitions:
        state = "in sun all day" if any(m and m > 0 for m in margins) \
            else "never in direct sun"
        print(f"  No transitions - {state}.")

    lit_minutes = sum(1 for m in margins if m is not None and m > 0)
    print(f"\n  Direct sun for {lit_minutes // 60}h{lit_minutes % 60:02d} "
          "of the day.")

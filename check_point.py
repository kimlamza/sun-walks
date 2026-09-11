"""
Is one spot in sun or shade at one moment?

Built for validation B1 in docs/07-validation-without-local-knowledge.md:
comparing the model against a public webcam. A webcam gives a known place,
a known time and an unambiguous answer, which is the one observation nobody
on this project can make in person.

    python check_point.py 51.0894 -115.3592 "2026-09-11 14:00"

The margin matters as much as the verdict. If the sun clears the skyline by
0.3 degrees, a webcam that disagrees proves nothing - the model is not
claiming that much precision. Disagreements are only meaningful when the
margin is comfortably larger than the error, which docs/02 puts at a few
degrees for the terrain model and more at low sun angles.
"""

import sys

import pandas as pd
import rasterio
from pyproj import Transformer

from src.evaluate import TIMEZONE, sun_position
from src.terrain import horizon_angle

PROJECTED_DEM = "data/dem/canmore_utm.tif"
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30


def compass_name(azimuth):
    points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return points[int(round(azimuth / 22.5)) % 16]


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(
            'Usage: python check_point.py <lat> <lon> "YYYY-MM-DD HH:MM"'
        )

    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    when = pd.Timestamp(sys.argv[3], tz=TIMEZONE)

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        rows, cols = dem.shape
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        easting, northing = to_utm.transform(lon, lat)
        row, col = dem_file.index(easting, northing)

    if not (0 <= row < rows and 0 <= col < cols):
        raise SystemExit("That point is outside the terrain model.")

    elevation, azimuth = sun_position(lat, lon, when)

    print(f"{lat}, {lon}  at  {when:%d %B %Y, %H:%M %Z}")
    print(f"  Ground height   {dem[row, col]:.0f} m")
    print(f"  Sun             {elevation:.1f} deg up, "
          f"bearing {azimuth:.0f} deg ({compass_name(azimuth)})")

    if elevation <= 0:
        print("\n  => Below the horizon. It is dark.")
        raise SystemExit

    skyline = horizon_angle(dem, row, col, azimuth, CELL_SIZE_M)
    margin = elevation - skyline

    print(f"  Skyline there   {skyline:.1f} deg up")
    print(f"  Margin          {margin:+.1f} deg")

    print()
    if margin > 0:
        print("  => IN DIRECT SUN")
    else:
        print("  => NO DIRECT SUN - terrain is in the way")

    if abs(margin) < 2:
        print("\n  MARGINAL. The model is not precise to better than a couple")
        print("  of degrees, so a webcam that disagrees here proves nothing.")
        print("  Pick a time when the margin is larger.")
    elif abs(margin) < 5 and elevation < 10:
        print("\n  Low sun and a modest margin. Error is largest here -")
        print("  treat a disagreement as inconclusive rather than as a bug.")
    else:
        print("\n  Comfortable margin. A webcam disagreeing with this WOULD")
        print("  be a real finding worth chasing.")

"""
The horizon skyline from the Canmore valley floor.

This answers the question posed in docs/02-method-and-assumptions.md section 0:
how high is the southern skyline, and does it sit above the midwinter noon
sun of 15.5 degrees? If it does, the prediction that much of the valley floor
gets no direct midday sun from November to February holds up.

Run it with:  python check_horizon.py
"""

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.warp import Resampling, calculate_default_transform, reproject

from src.terrain import horizon_angle

SOURCE_DEM = "data/dem/canmore.tif"
PROJECTED_DEM = "data/dem/canmore_utm.tif"

# The downloaded DEM is in degrees of latitude and longitude, where a "cell"
# is not a fixed number of metres — and at this latitude it is 31 m tall but
# only 19 m wide. Angles computed on that grid would be wrong. So we convert
# to UTM zone 11 North, whose units are metres, before doing any geometry.
# This is the coordinate-system trap warned about in docs/01-data-sources.md.
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30

# Canmore town centre, on the valley floor
LATITUDE = 51.0894
LONGITUDE = -115.3592

MIDWINTER_NOON_SUN = 15.5   # degrees, from docs/02 section 0
MIDSUMMER_NOON_SUN = 62.4


def reproject_to_metres(source_path, dest_path):
    """Convert a lat/lon DEM into UTM 11N, so one cell is 30 m square."""
    with rasterio.open(source_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, UTM_11N, src.width, src.height, *src.bounds,
            resolution=CELL_SIZE_M,
        )
        profile = src.profile.copy()
        profile.update(
            crs=UTM_11N, transform=transform, width=width, height=height,
        )

        with rasterio.open(dest_path, "w", **profile) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=UTM_11N,
                resampling=Resampling.bilinear,
            )


def compass_name(azimuth):
    points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return points[int(round(azimuth / 22.5)) % 16]


if __name__ == "__main__":
    print("Reprojecting the terrain model to metres...")
    reproject_to_metres(SOURCE_DEM, PROJECTED_DEM)

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)

        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        easting, northing = to_utm.transform(LONGITUDE, LATITUDE)
        row, col = dem_file.index(easting, northing)

    print(f"\nCanmore town centre — {LATITUDE}, {LONGITUDE}")
    print(f"  Grid position   row {row}, col {col} of {dem.shape}")
    print(f"  Ground height   {dem[row, col]:.0f} m")
    print("  (expect roughly 1,300 m — if it is wildly different, "
          "the DEM or the position is wrong)\n")

    print("Skyline height, looking in each direction:\n")
    print("  Bearing        Horizon")

    profile = {}
    for azimuth in range(0, 360, 22):
        angle = horizon_angle(dem, row, col, azimuth, CELL_SIZE_M)
        profile[azimuth] = angle
        print(f"  {azimuth:3d} deg {compass_name(azimuth):>4}    "
              f"{angle:5.1f} deg")

    southerly = [a for az, a in profile.items() if 135 <= az <= 225]
    highest_south = max(southerly)

    print(f"\nHighest skyline to the south: {highest_south:.1f} deg")
    print(f"Midwinter noon sun:           {MIDWINTER_NOON_SUN} deg")
    print(f"Midsummer noon sun:           {MIDSUMMER_NOON_SUN} deg")

    if highest_south > MIDWINTER_NOON_SUN:
        print("\n=> The midwinter noon sun does NOT clear the southern "
              "skyline from this point.")
        print("   The November-to-February prediction holds here.")
    else:
        print("\n=> The midwinter noon sun DOES clear the skyline here.")
        print("   The prediction does not hold at this particular point — "
              "worth checking others.")

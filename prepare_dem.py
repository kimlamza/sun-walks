"""
Turn the downloaded terrain model into one this project can do geometry on.

Run this once after downloading a new DEM, before anything else.

The file from OpenTopography is in degrees of latitude and longitude, where
a "cell" is not a fixed distance on the ground - at Canmore's latitude it is
about 31 m tall and only 19 m wide. Angles computed on that grid would be
wrong in a way that looks entirely plausible. So the first thing we do is
convert to UTM zone 11 North, whose units are metres.

This replaces check_horizon.py, which did the reprojection as a side effect
of an analysis that turned out to be flawed twice over: it sampled the
horizon every 22 degrees, which steps over ridge crests, and it compared the
highest southern skyline against the noon sun - two peaks that occur at
different bearings, so the comparison was meaningless. Both errors are
recorded in docs/02-method-and-assumptions.md section 0.

Run it with:  python prepare_dem.py
"""

import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject

SOURCE_DEM = "data/dem/canmore.tif"
PROJECTED_DEM = "data/dem/canmore_utm.tif"

LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30

# Peaks that should appear in a Bow Valley terrain model, as a sanity check.
LANDMARKS = [
    ("Ha Ling Peak", 2407),
    ("Grotto Mountain", 2706),
    ("Mount Rundle", 2949),
    ("Mount Assiniboine", 3618),
]


def reproject_to_metres(source_path, dest_path):
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


if __name__ == "__main__":
    print(f"Reprojecting {SOURCE_DEM} to metres...")
    reproject_to_metres(SOURCE_DEM, PROJECTED_DEM)

    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        bounds = dem_file.bounds

    valid = dem[dem > -100]
    width_km = (bounds.right - bounds.left) / 1000
    height_km = (bounds.top - bounds.bottom) / 1000

    print(f"\nWrote {PROJECTED_DEM}")
    print(f"  Grid        {dem.shape[0]} x {dem.shape[1]} cells "
          f"at {CELL_SIZE_M} m")
    print(f"  Covers      {width_km:.0f} km east-west, "
          f"{height_km:.0f} km north-south")
    print(f"  Lowest      {valid.min():.0f} m")
    print(f"  Highest     {valid.max():.0f} m")

    print("\nSanity check - the highest point should be at least as high as")
    print("whichever of these your bounding box reaches:")
    for name, height in LANDMARKS:
        reached = "<-- covered" if valid.max() >= height - 100 else ""
        print(f"  {name:22} {height:5} m  {reached}")

    print("\nA maximum well below these means the terrain is being")
    print("over-smoothed, which would make every horizon angle read too low")
    print("and every walk look sunnier than it is.")

    print("\nRays reach 30 km, so walks need that much terrain around them.")
    print("sun_on_walks.py warns where they do not.")

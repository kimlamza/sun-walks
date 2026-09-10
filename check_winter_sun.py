"""
Does the midwinter sun reach the Bow Valley floor, and for how long?

The first script asked a cruder question - is the noon sun above the southern
skyline - and got 14.8 degrees against a 15.5 degree sun. Too close to call.

This one is better in three ways:

  1. It samples the horizon every 2 degrees instead of every 22, so it cannot
     step over the highest part of a ridge.
  2. It checks several real locations, not just the town centre. The town
     centre is not where anybody walks.
  3. It checks the whole day rather than noon alone. Noon is the sun's best
     moment; the honest question is how many hours get any direct sun.

This is also the first time the two halves of the project meet: pvlib says
where the sun is, terrain.py says how high the mountains are, and the answer
is simply whether the first number exceeds the second.

Run it with:  python check_winter_sun.py
"""

import numpy as np
import pandas as pd
import pvlib
import rasterio
from pyproj import Transformer

from src.terrain import horizon_angle, is_sunlit

PROJECTED_DEM = "data/dem/canmore_utm.tif"
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30
TIMEZONE = "America/Edmonton"

AZIMUTH_STEP = 2
WINTER_DAY = "2026-12-21"
HOURS = range(8, 17)

# Approximate positions, good to a few hundred metres.
# [verify] against real trailhead coordinates before relying on these -
# they are here to compare locations against each other, not to be precise.
POINTS = {
    "Canmore town centre": (51.0894, -115.3592),
    "Quarry Lake":         (51.0706, -115.3706),
    "Grassi Lakes area":   (51.0736, -115.3936),
    "Benchlands / Montane": (51.1078, -115.3339),
    "Grotto Canyon area":  (51.0836, -115.1889),
}


def load_dem():
    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        # No-data shows up as a large negative number. Left alone it would
        # never be mistaken for a mountain, but it would distort ground
        # heights, so flatten it to sea level.
        dem[dem < -100] = 0.0
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)

        def grid_position(lat, lon):
            easting, northing = to_utm.transform(lon, lat)
            return dem_file.index(easting, northing)

        return dem, grid_position


def horizon_profile(dem, row, col):
    """Skyline height in every direction, every AZIMUTH_STEP degrees."""
    return {
        azimuth: horizon_angle(dem, row, col, azimuth, CELL_SIZE_M)
        for azimuth in range(0, 360, AZIMUTH_STEP)
    }


def horizon_towards(profile, azimuth):
    """The skyline height in the direction nearest to `azimuth`."""
    nearest = min(
        profile,
        key=lambda a: abs(((a - azimuth + 180) % 360) - 180),
    )
    return profile[nearest]


def sun_through_the_day(lat, lon, height_m, day, hours):
    """Solar elevation and bearing at each whole hour of `day`."""
    location = pvlib.location.Location(lat, lon, tz=TIMEZONE, altitude=height_m)
    times = pd.DatetimeIndex(
        [f"{day} {hour:02d}:00" for hour in hours]
    ).tz_localize(TIMEZONE)
    position = location.get_solarposition(times)
    return list(
        zip(hours, position["apparent_elevation"], position["azimuth"])
    )


if __name__ == "__main__":
    dem, grid_position = load_dem()

    print(f"Terrain model: {dem.shape[0]} x {dem.shape[1]} cells at "
          f"{CELL_SIZE_M} m")
    print(f"  Lowest point   {dem.min():.0f} m")
    print(f"  Highest point  {dem.max():.0f} m")
    print("  (expect a maximum near 2,900-3,000 m for Rundle and the Three")
    print("   Sisters. Much lower means the terrain is being over-smoothed,")
    print("   which would make every horizon angle read too low.)")

    print(f"\nMidwinter: {WINTER_DAY}\n")

    for name, (lat, lon) in POINTS.items():
        row, col = grid_position(lat, lon)
        ground = dem[row, col]

        profile = horizon_profile(dem, row, col)
        southerly = [
            angle for azimuth, angle in profile.items()
            if 135 <= azimuth <= 225
        ]

        print("=" * 62)
        print(f"{name}   ({ground:.0f} m)")
        print(f"  Highest southern skyline: {max(southerly):.1f} deg")
        print()
        print("   Time    Sun elevation   Sun bearing   Skyline   In sun?")

        sunlit_hours = 0
        for hour, elevation, azimuth in sun_through_the_day(
            lat, lon, ground, WINTER_DAY, HOURS
        ):
            if elevation <= 0:
                print(f"   {hour:02d}:00      below horizon")
                continue

            skyline = horizon_towards(profile, azimuth)
            lit = is_sunlit(skyline, elevation)
            sunlit_hours += lit

            print(f"   {hour:02d}:00       {elevation:5.1f} deg      "
                  f"{azimuth:5.1f} deg    {skyline:5.1f} deg    "
                  f"{'SUN' if lit else 'shade'}")

        print(f"\n  Hours with direct sun, 08:00-16:00: {sunlit_hours} of "
              f"{len(HOURS)}")

    print("=" * 62)
    print("\nWhat to look for: the locations should disagree with each other.")
    print("If every one of them returns the same answer, either the terrain")
    print("model or the position lookup is wrong - this valley is not")
    print("uniform.")

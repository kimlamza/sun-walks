"""
Check our horizon calculation against somebody else's.

Validation test A4 from docs/07-validation-without-local-knowledge.md.

PVGIS - the European Commission's Photovoltaic Geographical Information
System - computes terrain horizons for solar panel siting. That is the same
physical question this project asks, in a different accent: how high does
the ground rise in each direction, and when does it block the sun.

It is a genuinely independent check. Different organisation, different
code, different underlying elevation data. If two implementations agree,
both are probably right. If they disagree, one of them is wrong and the
disagreement shows you where to look.

THE TRAP THIS SCRIPT IS BUILT AROUND

Different tools measure azimuth from different places. Ours is degrees
clockwise from north, the compass convention. PVGIS has historically used
south as zero, with east negative and west positive. Two correct horizon
profiles in different conventions look completely wrong against each other.

So rather than assuming a convention, this tries every rotation and
reports which one fits best. If the answer is a clean 180 degrees, that is
a convention difference and nothing is broken. If nothing fits, the
disagreement is real.

Run it with:  python validate_pvgis.py
"""

import numpy as np
import rasterio
import requests
from pyproj import Transformer

from src.terrain import horizon_profile

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/printhorizon"
PROJECTED_DEM = "data/dem/canmore_utm.tif"

LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30

# A valley-floor point with a big skyline, so there is plenty to disagree
# about. A flat site would agree trivially and prove nothing - the same
# mistake the first Grassi Lakes comparison made.
TEST_POINTS = {
    "Canmore town centre": (51.0894, -115.3592),
    "Under Ha Ling (Grassi Lakes)": (51.0736, -115.3936),
}


def fetch_pvgis(lat, lon):
    """PVGIS horizon profile: a list of (azimuth, height) in degrees."""
    response = requests.get(
        PVGIS_URL,
        params={"lat": lat, "lon": lon, "outputformat": "json"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()

    profile = payload.get("outputs", {}).get("horizon_profile")
    if not profile:
        raise SystemExit(
            "PVGIS returned no horizon_profile. The API shape may have "
            f"changed - here is what came back:\n{str(payload)[:600]}"
        )

    azimuths = np.array([float(row["A"]) for row in profile])
    heights = np.array([float(row["H_hor"]) for row in profile])
    return azimuths, heights


def our_profile(dem, grid_position, lat, lon, azimuths_compass):
    row, col = grid_position(lat, lon)
    return horizon_profile(dem, row, col, CELL_SIZE_M, azimuths_compass)


def best_rotation(pvgis_az, pvgis_h, ours_at):
    """
    Try every rotation and report which fits best.

    `ours_at` takes an array of compass bearings and returns our horizon
    heights for them. Rotating by `offset` asks: if PVGIS's zero is
    actually `offset` degrees clockwise from north, do the two agree?
    """
    results = []
    for offset in range(0, 360, 5):
        compass = (pvgis_az + offset) % 360
        mine = ours_at(compass)
        difference = mine - pvgis_h
        results.append((
            float(np.sqrt(np.mean(difference ** 2))),   # RMS error
            offset,
            float(np.mean(difference)),                 # bias
            float(np.max(np.abs(difference))),          # worst case
        ))
    return sorted(results)


if __name__ == "__main__":
    with rasterio.open(PROJECTED_DEM) as dem_file:
        dem = dem_file.read(1).astype(float)
        dem[dem < -100] = 0.0
        to_utm = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
        index_of = dem_file.index

        def grid_position(lat, lon):
            easting, northing = to_utm.transform(lon, lat)
            return index_of(easting, northing)

    for name, (lat, lon) in TEST_POINTS.items():
        print("=" * 68)
        print(f"{name}  ({lat}, {lon})")

        try:
            pvgis_az, pvgis_h = fetch_pvgis(lat, lon)
        except Exception as error:
            print(f"  PVGIS request failed: {error}")
            continue

        print(f"  PVGIS returned {len(pvgis_az)} bearings, "
              f"{pvgis_az.min():.0f} to {pvgis_az.max():.0f} degrees, "
              f"horizon {pvgis_h.min():.1f} to {pvgis_h.max():.1f} degrees")

        ranked = best_rotation(
            pvgis_az, pvgis_h,
            lambda compass: our_profile(dem, grid_position, lat, lon, compass),
        )

        print("\n  Best-fitting rotations of the PVGIS bearings:\n")
        print(f"  {'offset':>7} {'RMS':>7} {'bias':>7} {'worst':>7}")
        for rms, offset, bias, worst in ranked[:3]:
            print(f"  {offset:6}d {rms:6.1f}d {bias:+6.1f}d {worst:6.1f}d")

        # PVGIS returns about 49 bearings, so it samples every ~7.5 degrees
        # and rotations closer than that are indistinguishable. When a
        # standard convention ties with a non-standard one, the standard
        # one is the answer - claiming otherwise invents a finding out of
        # sampling noise, which the first run of this script duly did.
        spacing = 360 / len(pvgis_az)
        close = [r for r in ranked if r[0] <= ranked[0][0] + 0.5]
        standard = [r for r in close if r[1] in (0, 180)]
        rms, offset, bias, worst = standard[0] if standard else ranked[0]

        print()
        if standard and len(close) > 1:
            others = ", ".join(f"{r[1]}d" for r in close if r[1] != offset)
            print(f"  ({others} fit equally well, but PVGIS samples every "
                  f"{spacing:.1f} degrees,")
            print("   so anything closer than that is a tie, not a result.)")

        if offset == 0:
            print("  => Same convention: both measure clockwise from north.")
        elif offset == 180:
            print("  => PVGIS measures from SOUTH. A convention difference,")
            print("     not an error - the profiles are the same shape.")
        else:
            print(f"  => Best fit at {offset} degrees, which matches no "
                  "standard convention.")
            print("     Treat that as unexplained rather than as agreement.")

        if rms < 5:
            print(f"  => Agreement is good (RMS {rms:.1f} deg). Both are "
                  "probably right.")
        elif rms < 10:
            print(f"  => Fair agreement (RMS {rms:.1f} deg). Expected: PVGIS "
                  "uses SRTM at")
            print("     90 m against our Copernicus at 30 m, so ridge crests "
                  "differ.")
        else:
            print(f"  => POOR agreement (RMS {rms:.1f} deg). Worth "
                  "investigating.")

"""
Which walk will actually be in the sun, if you set off at a given time?

The product, in miniature. For each walk:

  - read distance and ascent from data/walks.csv
  - estimate how long it takes (Naismith, src/duration.py)
  - the representative time is start plus half the duration
  - find where the sun is at that moment
  - ray march from each trail point towards it and count clear lines
  - ask Open-Meteo whether there will be any direct beam to block

The two factors stay separate and are never blended into one score. A
single number would hide which one drove the answer, and they fail in
completely different ways: perfect geometry under thick cloud calls for
"go anywhere, it makes no difference", while a brilliant day behind a
ridge calls for "go somewhere else".

Weather is only available inside the forecast horizon, about 16 days. For
anything further out the honest answer is geometry alone, clearly labelled.

Alberta is on permanent UTC-6 from November 2026 (Official Time Act,
18 June 2026), so on the solstice sunrise is 09:46 and sunset 17:30.
Winter start times before 10:00 are darkness.

Run it with:  python sun_on_walks.py
"""

import csv
import json
from pathlib import Path

import pandas as pd
import pvlib
import rasterio
from pyproj import Transformer

from src import weather
from src.duration import format_duration, walk_times
from src.terrain import horizon_angle, is_sunlit

PROJECTED_DEM = "data/dem/canmore_utm.tif"
ROUTES_DIR = Path("data/routes")
WALKS_CSV = Path("data/walks.csv")

LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"
CELL_SIZE_M = 30
TIMEZONE = "America/Edmonton"

# Neighbouring trail points give almost identical answers, and ray marching
# every one is slow in plain Python. Every 4th is plenty for ten walks.
SAMPLE_EVERY = 4


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
    walks = []
    with WALKS_CSV.open() as handle:
        for row in csv.DictReader(handle):
            row["distance_km"] = float(row["distance_km"])
            row["ascent_m"] = float(row["ascent_m"])
            route_file = ROUTES_DIR / f"{row['slug']}.json"
            row["points"] = (
                json.loads(route_file.read_text())["points"]
                if route_file.exists() else None
            )
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


def check_coverage(dem, grid_position, walks, max_distance_m=30_000):
    """
    Warn where the terrain model runs out before the ray march does.

    Two separate problems. Points outside the model are silently skipped,
    which quietly shrinks the sample. And a point near the edge still gets
    an answer, but its rays stop early - so a mountain beyond the edge is
    invisible and the walk reads sunnier than it is. The second is the
    dangerous one, because nothing complains.
    """
    rows, cols = dem.shape
    margin_cells = max_distance_m / CELL_SIZE_M
    warnings = []

    for walk in walks:
        if not walk["points"]:
            continue

        outside = 0
        least_margin = None
        for lat, lon in walk["points"][::SAMPLE_EVERY]:
            position = grid_position(lat, lon)
            if position is None:
                outside += 1
                continue
            row, col = position
            margin = min(row, col, rows - 1 - row, cols - 1 - col)
            if least_margin is None or margin < least_margin:
                least_margin = margin

        if outside:
            warnings.append(f"  {walk['slug']:18} {outside} sampled points "
                            f"fall outside the terrain model")
        if least_margin is not None and least_margin < margin_cells:
            reach_km = least_margin * CELL_SIZE_M / 1000
            warnings.append(f"  {walk['slug']:18} closest edge is "
                            f"{reach_km:.0f} km away, so rays stop short of "
                            f"the {max_distance_m / 1000:.0f} km design "
                            f"distance")

    if warnings:
        print("TERRAIN MODEL COVERAGE WARNINGS")
        print("  Distant mountains beyond the edge are invisible, so these")
        print("  walks may read sunnier than they are. Widen the DEM to fix.")
        print()
        for line in warnings:
            print(line)
        print()


def centre_of(points):
    return (
        sum(p[0] for p in points) / len(points),
        sum(p[1] for p in points) / len(points),
    )


def percent(value):
    return "  --" if value is None else f"{value:3.0f}%"


def number(value, suffix="", width=5):
    """Format a figure that the forecast may simply not have."""
    if value is None:
        return f"{'--':>{width}}{suffix}"
    return f"{value:{width}.1f}{suffix}"


def report(dem, grid_position, walks, start, label):
    print("=" * 92)
    print(label)
    print()

    rows = []
    for walk in walks:
        begin, middle, finish, hours = walk_times(
            start, walk["distance_km"], walk["ascent_m"]
        )
        entry = {
            "walk": walk,
            "takes": format_duration(hours),
            "at": middle,
            "start": None, "mid": None, "end": None,
            "weather": None,
        }

        if walk["points"]:
            entry["start"], _ = fraction_in_sun(
                dem, grid_position, walk["points"], begin)
            entry["mid"], _ = fraction_in_sun(
                dem, grid_position, walk["points"], middle)
            entry["end"], _ = fraction_in_sun(
                dem, grid_position, walk["points"], finish)

            lat, lon = centre_of(walk["points"])
            entry["weather"] = weather.at(lat, lon, middle)

        rows.append(entry)

    rows.sort(key=lambda e: -1 if e["mid"] is None else -e["mid"])

    have_weather = any(e["weather"] for e in rows)

    header = (f"  {'Walk':18} {'Takes':>5} {'At':>5}  "
              f"{'Start':>5} {'MID':>5} {'End':>5}")
    if have_weather:
        header += f"   {'Direct beam':<14} {'Temp':>6} {'Wind':>6}"
    print(header)
    print("  " + "-" * (88 if have_weather else 48))

    for e in rows:
        if not e["walk"]["points"]:
            print(f"  {e['walk']['slug']:18} {e['takes']:>5} "
                  f"{e['at']:%H:%M}   no trail geometry")
            continue

        line = (f"  {e['walk']['slug']:18} {e['takes']:>5} {e['at']:%H:%M}  "
                f"{percent(e['start'])} {percent(e['mid'])} "
                f"{percent(e['end'])}")

        w = e["weather"]
        if have_weather and w:
            beam = weather.describe_beam(w["dni"])
            dni = "?" if w["dni"] is None else f"{w['dni']:.0f}"
            line += (f"   {beam + ' (' + dni + ')':<16} "
                     f"{number(w['temperature'], 'C')} "
                     f"{number(w['wind'])}")
        elif have_weather:
            line += "   beyond forecast"

        print(line)

    # The short-circuit: if there is no direct beam, geometry is moot.
    #
    # This tests the MEDIAN, not any(). Direct normal irradiance is close to
    # binary - the sun's disc is either covered or it is not - so readings
    # cluster near 0 or near 500 with little between, and a single sharp
    # cloud edge over one trailhead would otherwise suppress an
    # "everywhere is overcast" verdict for the other nine.
    beams = sorted(e["weather"]["dni"] for e in rows
                   if e["weather"] and e["weather"]["dni"] is not None)
    median_beam = beams[len(beams) // 2] if beams else None

    print()
    if not beams:
        print("  No weather available - this date is beyond the forecast")
        print("  horizon. Geometry only. Cannot tell you whether the sun")
        print("  will actually be out.")
    elif not weather.shadow_matters(median_beam):
        lit = sum(1 for d in beams if weather.shadow_matters(d))
        print(f"  MOSTLY OVERCAST - median direct beam {median_beam:.0f} W/m2, "
              f"with {lit} of {len(beams)}")
        print("  trailheads seeing any sun. Terrain shadow makes little")
        print("  difference today - choose on distance or drive time instead.")
        print("  (Direct beam is close to binary and moves fast; the geometry")
        print("  above is stable, this is not.)")
    else:
        sample = next(e["weather"] for e in rows if e["weather"])
        print(f"  Median direct beam {median_beam:.0f} W/m2. "
              f"Forecast confidence: {sample['confidence']} "
              f"({weather.days_ahead(start)} days ahead, "
              f"model {sample['model']})")


if __name__ == "__main__":
    dem, grid_position = load_terrain()
    walks = load_walks()

    check_coverage(dem, grid_position, walks)

    # A real query, inside the forecast horizon - geometry plus weather.
    soon = pd.Timestamp.now(tz=TIMEZONE).normalize() + pd.Timedelta(days=3)
    report(dem, grid_position, walks,
           soon.replace(hour=11),
           f"THREE DAYS OUT - {soon:%A %d %B}, setting off at 11:00")

    # The midwinter demonstration. Beyond the forecast, so geometry only.
    report(dem, grid_position, walks,
           pd.Timestamp("2026-12-21 11:00", tz=TIMEZONE),
           "MIDWINTER - 21 December, setting off at 11:00 (geometry only)")

    print("=" * 92)
    print("\nRanked on the midpoint. Geometry and weather are shown separately")
    print("and never blended - a single score would hide which one mattered.")

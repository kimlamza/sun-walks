"""
One place where a walk is turned into a percentage.

This exists because there were two. app.py read the precomputed horizon
profiles; sun_on_walks.py ray marched the raw route files. They agreed
until they did not: trimming Lake Minnewanka from 19 km of lakeshore to the
8 km people actually walk changed the app's answer and left the command
line reporting the old one, silently.

Two implementations of the same idea will always drift. Both now call this.
"""

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

from src.terrain import horizon_towards

HORIZONS_DIR = Path("data/horizons")
WALKS_CSV = Path("data/walks.csv")
TIMEZONE = "America/Edmonton"


def load_walks():
    """
    Walk metadata with its precomputed skyline attached.

    Walks without a horizon profile are skipped - run precompute_horizons.py
    after adding a walk or changing the terrain model.
    """
    walks = []
    with WALKS_CSV.open() as handle:
        for row in csv.DictReader(handle):
            profile_file = HORIZONS_DIR / f"{row['slug']}.npz"
            if not profile_file.exists():
                continue

            stored = np.load(profile_file)
            row["distance_km"] = float(row["distance_km"])
            row["ascent_m"] = float(row["ascent_m"])
            row["drive_min"] = int(row["drive_min"])
            row["azimuths"] = stored["azimuths"]
            row["points"] = stored["points"]
            row["horizons"] = stored["horizons"]
            walks.append(row)
    return walks


def sun_position(lat, lon, when):
    """Solar elevation and bearing at one place and one moment."""
    location = pvlib.location.Location(lat, lon, tz=TIMEZONE, altitude=1400)
    position = location.get_solarposition(pd.DatetimeIndex([when]))
    return (
        float(position["apparent_elevation"].iloc[0]),
        float(position["azimuth"].iloc[0]),
    )


def evaluate(walk, when):
    """
    Which points of this walk can see the sun at this moment?

    Returns (percent, elevation, azimuth, lit) where `lit` is a boolean per
    sampled point, or (None, elevation, azimuth, None) in darkness.

    This is a lookup, not a calculation. The skyline in every direction was
    worked out once by precompute_horizons.py and does not change, so the
    only question left is whether the sun is above it.
    """
    lat, lon = walk["points"].mean(axis=0)
    elevation, azimuth = sun_position(lat, lon, when)

    if elevation <= 0:
        return None, elevation, azimuth, None

    skyline = np.array([
        horizon_towards(profile, walk["azimuths"], azimuth)
        for profile in walk["horizons"]
    ])
    lit = elevation > skyline
    return 100 * lit.mean(), elevation, azimuth, lit


def centre_of(walk):
    lat, lon = walk["points"].mean(axis=0)
    return float(lat), float(lon)

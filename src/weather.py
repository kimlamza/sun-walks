"""
Will there be any direct sunlight to be blocked?

The terrain model answers a geometric question: is there a clear line from
this spot to the sun? That is only half the answer. On an overcast day the
line is clear and it makes no difference at all.

The variable that matters is Direct Normal Irradiance - the strength of the
beam arriving straight from the sun's disc, in watts per square metre. Not
cloud cover. DNI is precisely the light that a mountain can block, so when
DNI is near zero, terrain shadow is irrelevant and the tool should say so
rather than reporting a confident geometric percentage.

The two factors are never multiplied into one score. A blended 0.4 could
mean perfect geometry under thick cloud, or a brilliant day spent entirely
behind a ridge, and those call for opposite decisions.

Source: Open-Meteo. Free, no API key, and it carries Environment Canada's
HRDPS model at 2.5 km - fine enough to resolve individual valleys, where a
25 km global model would give Canmore and the summit of Rundle identical
weather.

The hard limit: forecasts run about 16 days ahead and skill decays sharply
after 5. Beyond the horizon this returns None, and the caller must say
"I cannot tell you" rather than inventing something.
"""

import json
from datetime import date as date_type
from pathlib import Path

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_DIR = Path("data/weather")
FORECAST_HORIZON_DAYS = 16

HOURLY_VARIABLES = [
    "direct_normal_irradiance",
    "cloud_cover",
    "temperature_2m",
    "apparent_temperature",
    "wind_speed_10m",
    "precipitation_probability",
    "snowfall",
]

# Environment Canada's models, best first.
#
# gem_hrdps_continental is the 2.5 km high resolution one, and it is what
# you want for mountains - but it only runs about 48 hours ahead. Asked for
# a date beyond that it returns HTTP 200 with every value null, which looks
# like success and is not. gem_seamless blends HRDPS with the longer range
# regional and global models, so it keeps the fine detail near-term and
# still answers further out.
MODEL_PREFERENCES = ["gem_seamless", "gem_hrdps_continental", None]


def days_ahead(when):
    return (when.date() - date_type.today()).days


def within_horizon(when):
    ahead = days_ahead(when)
    return 0 <= ahead <= FORECAST_HORIZON_DAYS


def confidence(when):
    """How much to trust a forecast this far out. docs/02 section 8."""
    ahead = days_ahead(when)
    if ahead < 0:
        return "past"
    if ahead <= 2:
        return "high"
    if ahead <= 5:
        return "medium"
    if ahead <= 10:
        return "low"
    if ahead <= FORECAST_HORIZON_DAYS:
        return "very low"
    return "none"


def describe_beam(dni):
    """
    Turn watts per square metre into something a person can act on.

    Bands from docs/02 section 4. Reasoned starting points, not findings -
    they want calibrating against a season of real observation, which this
    project will not have. Flagged rather than presented as established.
    """
    if dni is None:
        return "unknown"
    if dni > 600:
        return "strong sun"
    if dni > 300:
        return "hazy sun"
    if dni > 100:
        return "broken cloud"
    return "overcast"


def shadow_matters(dni):
    """Below this, there is no beam to block and geometry is moot."""
    return dni is not None and dni > 100


def _cache_path(lat, lon, day):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{lat:.2f}_{lon:.2f}_{day}.json"


def _download(lat, lon, day):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": "America/Edmonton",
        "start_date": str(day),
        "end_date": str(day),
    }

    for models in MODEL_PREFERENCES:
        query = dict(params)
        if models:
            query["models"] = models

        response = requests.get(FORECAST_URL, params=query, timeout=60)
        if not response.ok:
            continue

        payload = response.json()
        beam = payload.get("hourly", {}).get("direct_normal_irradiance") or []

        # A model outside its forecast range answers 200 with all nulls.
        # Treat that as a miss, not a success, and try the next one.
        if all(value is None for value in beam):
            continue

        payload["_model"] = models or "best_match"
        return payload

    response.raise_for_status()


def at(lat, lon, when):
    """
    Weather at one place and one hour, or None if beyond the forecast.

    Returns a dict with dni, cloud, temperature, wind, and the model used.
    Cached to disk - never ask a free service the same question twice.
    """
    if not within_horizon(when):
        return None

    day = when.date()
    cache = _cache_path(lat, lon, day)

    if cache.exists():
        payload = json.loads(cache.read_text())
    else:
        payload = _download(lat, lon, day)
        cache.write_text(json.dumps(payload))

    hourly = payload.get("hourly", {})
    stamps = hourly.get("time", [])
    wanted = f"{day}T{when.hour:02d}:00"

    if wanted not in stamps:
        return None
    index = stamps.index(wanted)

    def value(name):
        series = hourly.get(name) or []
        return series[index] if index < len(series) else None

    return {
        "dni": value("direct_normal_irradiance"),
        "cloud": value("cloud_cover"),
        "temperature": value("temperature_2m"),
        "feels_like": value("apparent_temperature"),
        "wind": value("wind_speed_10m"),
        "rain_chance": value("precipitation_probability"),
        "snowfall": value("snowfall"),
        "model": payload.get("_model"),
        "confidence": confidence(when),
    }

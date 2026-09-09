"""
Solar position for Canmore, Alberta.

Session 1 deliverable: prove the toolchain works end to end, and check the
computed sunrise and sunset against a published table.

Note what sunrise actually is here: the moment the sun's elevation crosses
zero. The shadow engine in session 2 runs exactly the same test, but against
a non-zero horizon angle — the height of the mountains in that direction.
That is the whole idea of this project in one line of code.
"""

from datetime import date

import pandas as pd
import pvlib

# Canmore, Alberta — valley floor
LATITUDE = 51.0894
LONGITUDE = -115.3592
ELEVATION_M = 1309
TIMEZONE = "America/Edmonton"

CANMORE = pvlib.location.Location(
    latitude=LATITUDE,
    longitude=LONGITUDE,
    tz=TIMEZONE,
    altitude=ELEVATION_M,
    name="Canmore",
)


def solar_day(day):
    """Sun position for every minute of `day`, in local time."""
    times = pd.date_range(
        start=f"{day} 00:00",
        end=f"{day} 23:59",
        freq="1min",
        tz=TIMEZONE,
    )
    return CANMORE.get_solarposition(times)


def sun_events(solpos):
    """Sunrise, sunset and the daily high point, from an elevation series."""
    above = solpos["apparent_elevation"] > 0
    previous = above.shift(1, fill_value=False)

    sunrise = solpos.index[above & ~previous]
    sunset = solpos.index[~above & previous]
    peak = solpos["apparent_elevation"].idxmax()

    return sunrise, sunset, peak


if __name__ == "__main__":
    today = date.today()
    solpos = solar_day(today)
    sunrise, sunset, peak = sun_events(solpos)

    print(f"Canmore, Alberta — {today}")
    print(f"  Sunrise       {sunrise[0]:%H:%M}")
    print(f"  Sunset        {sunset[0]:%H:%M}")
    print(f"  Highest sun   {peak:%H:%M}, "
          f"{solpos['apparent_elevation'].max():.1f}° above the horizon")
    print(f"  Bearing then  {solpos.loc[peak, 'azimuth']:.0f}° from north")

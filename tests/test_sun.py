"""
Solar position, and the timezone finding that nearly went unnoticed.

These started life as check_dst.py, a one-off diagnostic written when the
model claimed the sun was 6.5 degrees below the horizon at 09:00 on the
winter solstice. A hand calculation assuming Mountain Standard Time said
it should be +1. That looked exactly like a daylight-saving bug.

It was not. Alberta passed the Official Time Act on 18 June 2026, moving to
permanent UTC-6 from November 2026 - so clocks no longer go back, and the
model was right while the hand calculation was wrong.

A diagnostic script only helps if somebody runs it. These are tests, so the
finding is pinned: if a future tzdata reverts Alberta to seasonal clocks, or
if pvlib changes how it handles localised times, this fails immediately
instead of quietly shifting every winter answer by an hour.
"""

from datetime import date

import pandas as pd

from src.sun import CANMORE, TIMEZONE, solar_day, sun_events

WINTER_SOLSTICE = date(2026, 12, 21)
SUMMER_SOLSTICE = date(2026, 6, 21)

SIX_HOURS = pd.Timedelta(hours=-6)


def test_alberta_stays_on_utc_minus_six_all_year():
    """
    No seasonal clock change, in either direction.

    Alberta ran MST (UTC-7) in winter and MDT (UTC-6) in summer until the
    Official Time Act of 18 June 2026. A -7 offset in December would mean
    the timezone database has reverted, and every winter result in this
    project would be an hour out.
    """
    for day in (WINTER_SOLSTICE, SUMMER_SOLSTICE):
        stamp = pd.Timestamp(f"{day} 09:00", tz=TIMEZONE)
        assert stamp.utcoffset() == SIX_HOURS, (
            f"{day} came back at {stamp.utcoffset()}, expected {SIX_HOURS}"
        )


def test_solstice_sunrise_is_late_by_the_clock():
    """
    Permanent UTC-6 pushes the winter day much later than intuition says.

    Solar noon at Canmore lands about 13:40, and the solstice day is 7h41m
    long, so sunrise is around 09:46 - not the 08:50 that Mountain Standard
    Time would have given. A result near 08:50 means the offset is wrong.
    """
    sunrise, sunset, _ = sun_events(solar_day(WINTER_SOLSTICE))

    assert sunrise[0].hour == 9 and 40 <= sunrise[0].minute <= 55, (
        f"sunrise came back at {sunrise[0]:%H:%M}, expected about 09:46"
    )
    assert sunset[0].hour == 17, (
        f"sunset came back at {sunset[0]:%H:%M}, expected about 17:30"
    )


def test_noon_sun_height_matches_the_geometry():
    """
    Solar noon elevation is 90 - latitude +/- 23.44 degrees, and nothing
    else. At 51.0894 N that is 15.5 in midwinter and 62.4 in midsummer.

    This is the figure the whole project rests on: a southern skyline of
    20-25 degrees against a 15.5 degree sun is why Canmore has a winter
    shade problem at all.
    """
    winter = solar_day(WINTER_SOLSTICE)["apparent_elevation"].max()
    summer = solar_day(SUMMER_SOLSTICE)["apparent_elevation"].max()

    assert 15.0 < winter < 16.5, f"midwinter noon sun {winter:.2f} deg"
    assert 61.5 < summer < 63.0, f"midsummer noon sun {summer:.2f} deg"


def test_sun_is_below_the_horizon_before_sunrise():
    """The check that started all this: 09:00 in December is still dark."""
    position = CANMORE.get_solarposition(
        pd.DatetimeIndex([pd.Timestamp(f"{WINTER_SOLSTICE} 09:00",
                                       tz=TIMEZONE)])
    )
    elevation = float(position["apparent_elevation"].iloc[0])
    assert elevation < 0, (
        f"sun at {elevation:.1f} deg at 09:00 on the solstice - expected "
        "below the horizon under permanent UTC-6"
    )

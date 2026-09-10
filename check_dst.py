"""
Diagnostic: is the winter timezone offset right?

sun.py matched published sunrise times in September, which is daylight
saving time (MDT, UTC-6). December is standard time (MST, UTC-7). If a
code path silently applies the summer offset all year, September looks
perfect and December is an hour out.

By hand, for Canmore on 21 December:
  day length  7h41m   (lat 51.09, declination -23.44)
  solar noon  ~12:40 MST
  sunrise     ~08:50 MST

So the sun should be roughly +1 degree at 09:00, not below the horizon.
"""

import pandas as pd
import pvlib

LATITUDE = 51.0894
LONGITUDE = -115.3592
ELEVATION_M = 1309
TIMEZONE = "America/Edmonton"

CANMORE = pvlib.location.Location(
    latitude=LATITUDE, longitude=LONGITUDE,
    tz=TIMEZONE, altitude=ELEVATION_M,
)

for label, day in [("Summer (expect MDT, UTC-6)", "2026-06-21"),
                   ("Winter (expect MST, UTC-7)", "2026-12-21")]:

    print("=" * 60)
    print(label, day)

    # Method A - what sun.py uses
    a = pd.date_range(f"{day} 00:00", f"{day} 23:59", freq="1min",
                      tz=TIMEZONE)
    # Method B - what check_winter_sun.py and sun_on_walks.py use
    b = pd.DatetimeIndex([f"{day} 09:00"]).tz_localize(TIMEZONE)

    print(f"  date_range offset at 09:00 : {a[540].utcoffset()}")
    print(f"  tz_localize offset at 09:00: {b[0].utcoffset()}")

    position = CANMORE.get_solarposition(a)
    elevation = position["apparent_elevation"]
    above = elevation > 0
    previous = above.shift(1, fill_value=False)
    sunrise = position.index[above & ~previous]

    print(f"  sunrise (method A)         : {sunrise[0]:%H:%M}")
    print(f"  elevation at 09:00 (A)     : {elevation.iloc[540]:6.2f} deg")

    single = CANMORE.get_solarposition(b)
    print(f"  elevation at 09:00 (B)     : "
          f"{single['apparent_elevation'].iloc[0]:6.2f} deg")

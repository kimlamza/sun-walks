"""
Which walk will actually be in the sun, if you set off at a given time?

The command line version of app.py. Both call src/evaluate.py, so they
cannot disagree - which they did once, when this script ray marched the raw
route files while the app read the trimmed horizon profiles.

For each walk:
  - read distance and ascent from data/walks.csv
  - estimate how long it takes (Naismith, src/duration.py)
  - the representative time is start plus half the duration
  - look up whether the sun clears the skyline at each trail point
  - ask Open-Meteo whether there will be any direct beam to block

Geometry and weather stay separate and are never blended. A single number
would hide which one drove the answer, and they fail in completely
different ways: perfect geometry under thick cloud means "go anywhere, it
makes no difference", while a brilliant day behind a ridge means "go
somewhere else".

Alberta is on permanent UTC-6 from November 2026 (Official Time Act,
18 June 2026), so on the solstice sunrise is 09:46 and sunset 17:30.
Winter start times before 10:00 are darkness.

Run it with:  python sun_on_walks.py
"""

import pandas as pd

from src import weather
from src.duration import format_duration, walk_times
from src.evaluate import TIMEZONE, centre_of, evaluate, load_walks

# Choosing scenarios is itself a design decision, because the answers
# saturate at both ends of the year: in December everything under a big
# skyline is shaded, in June the sun is high enough to clear almost
# anything, and walks that genuinely differ look identical at both.
#
# Mid-afternoon in February and May separates them best - the sun is low
# enough for terrain to matter and high enough that not everything is in
# shadow. Midwinter is kept because it is the headline case the project
# exists for: Grassi Lakes at 0% while Montane Traverse reads 100%.
SCENARIOS = [
    (3, "11:00", "THREE DAYS OUT"),
    ("2026-12-21", "11:00", "MIDWINTER - 21 December (geometry only)"),
    ("2027-02-15", "15:00", "FEBRUARY AFTERNOON - 15 Feb (geometry only)"),
    ("2027-05-15", "15:00", "MAY AFTERNOON - 15 May (geometry only)"),
]


def percent(value):
    return " dark" if value is None else f"{value:4.0f}%"


def number(value, suffix="", width=5):
    """Format a figure the forecast may simply not have."""
    if value is None:
        return f"{'--':>{width}}{suffix}"
    return f"{value:{width}.1f}{suffix}"


def report(walks, start, label):
    print("=" * 92)
    print(f"{label} - {start:%A %d %B}, setting off at {start:%H:%M}")
    print()

    rows = []
    for walk in walks:
        begin, middle, finish, hours = walk_times(
            start, walk["distance_km"], walk["ascent_m"]
        )
        lat, lon = centre_of(walk)
        rows.append({
            "walk": walk,
            "takes": format_duration(hours),
            "at": middle,
            "start": evaluate(walk, begin)[0],
            "mid": evaluate(walk, middle)[0],
            "end": evaluate(walk, finish)[0],
            "weather": weather.at(lat, lon, middle),
        })

    rows.sort(key=lambda r: -1 if r["mid"] is None else -r["mid"])
    have_weather = any(r["weather"] for r in rows)

    header = (f"  {'Walk':18} {'Takes':>5} {'At':>5}  "
              f"{'Start':>5} {'MID':>5} {'End':>5}")
    if have_weather:
        header += f"   {'Direct beam':<18} {'Temp':>6} {'Wind':>6}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for row in rows:
        line = (f"  {row['walk']['slug']:18} {row['takes']:>5} "
                f"{row['at']:%H:%M}  {percent(row['start'])} "
                f"{percent(row['mid'])} {percent(row['end'])}")

        forecast = row["weather"]
        if have_weather and forecast:
            beam = weather.describe_beam(forecast["dni"])
            dni = "?" if forecast["dni"] is None else f"{forecast['dni']:.0f}"
            line += (f"   {beam + ' (' + dni + ')':<18} "
                     f"{number(forecast['temperature'], 'C')} "
                     f"{number(forecast['wind'])}")
        elif have_weather:
            line += "   beyond forecast"

        print(line)

    # Direct beam is close to binary - the sun's disc is either covered or
    # it is not - so one sharp cloud edge over a single trailhead must not
    # decide the verdict for the other nine. Test the median.
    beams = sorted(r["weather"]["dni"] for r in rows
                   if r["weather"] and r["weather"]["dni"] is not None)
    median_beam = beams[len(beams) // 2] if beams else None

    print()
    if not beams:
        print("  No weather - this date is beyond the forecast horizon.")
        print("  Geometry only. Cannot tell you whether the sun will be out.")
    elif not weather.shadow_matters(median_beam):
        lit = sum(1 for d in beams if weather.shadow_matters(d))
        print(f"  MOSTLY OVERCAST - median direct beam {median_beam:.0f} W/m2, "
              f"{lit} of {len(beams)} trailheads")
        print("  seeing any sun. Terrain shadow makes little difference "
              "today - choose")
        print("  on distance or drive time instead.")
    else:
        sample = next(r["weather"] for r in rows if r["weather"])
        print(f"  Median direct beam {median_beam:.0f} W/m2. Forecast "
              f"confidence: {sample['confidence']} "
              f"({weather.days_ahead(start)} days ahead, "
              f"model {sample['model']})")


if __name__ == "__main__":
    walks = load_walks()
    if not walks:
        raise SystemExit("No horizon profiles. Run precompute_horizons.py.")

    for when, clock, label in SCENARIOS:
        if isinstance(when, int):
            day = (pd.Timestamp.now(tz=TIMEZONE).normalize()
                   + pd.Timedelta(days=when))
            start = day + pd.Timedelta(hours=int(clock.split(":")[0]))
        else:
            start = pd.Timestamp(f"{when} {clock}", tz=TIMEZONE)
        report(walks, start, label)

    print("=" * 92)
    print("\nRanked on the midpoint. Geometry and weather shown separately")
    print("and never blended - a single score would hide which mattered.")

"""
How long a walk takes, and therefore when to evaluate it.

docs/02-method-and-assumptions.md section 1a says the sun should be checked
at "start time plus half the estimated duration" - the representative time.
Not the start, because on a two-hour walk the start is systematically the
sunniest moment of an afternoon and the shadiest of a morning, which builds
a bias into every answer.

That needs a duration, which needs a rule. Naismith's is the standard one,
and it is deliberately simple:

    one hour per 5 km, plus one minute for every 10 m of climb

Naismith described a fit walker on good ground and is optimistic for most
real walks, so everything is multiplied by a pace factor. Dogs stop, people
take photographs, gates need opening.

Two known weaknesses, both recorded rather than fixed:
  - No altitude correction. These trailheads sit at 1,300-1,600 m and climb
    from there, where Naismith assumed sea level.
  - No snow correction. Packed snow is slower; unbroken snow is far slower.
"""

from datetime import timedelta

FLAT_SPEED_KMH = 5.0
ASCENT_RATE_M_PER_HOUR = 600.0
DEFAULT_PACE_FACTOR = 1.3


def naismith_hours(distance_km, ascent_m, pace_factor=DEFAULT_PACE_FACTOR):
    """Estimated walking time in hours."""
    hours = distance_km / FLAT_SPEED_KMH + ascent_m / ASCENT_RATE_M_PER_HOUR
    return hours * pace_factor


def format_duration(hours):
    """2.75 -> '2h45'."""
    whole = int(hours)
    minutes = int(round((hours - whole) * 60))
    if minutes == 60:
        whole, minutes = whole + 1, 0
    return f"{whole}h{minutes:02d}"


def walk_times(start, distance_km, ascent_m, pace_factor=DEFAULT_PACE_FACTOR):
    """
    The three moments worth checking, given a start time.

    Returns (start, midpoint, end, duration_in_hours).

    The midpoint is the headline figure. Start and end come almost free
    once the machinery exists, and the measured results argue for showing
    them: Montane Traverse runs 63% sunlit at 10:30 and 100% at 15:30, so
    a single midpoint number hides a lot on a long winter walk.

    This is still three instants, not a simulation of the whole walk.
    """
    hours = naismith_hours(distance_km, ascent_m, pace_factor)
    midpoint = start + timedelta(hours=hours / 2)
    end = start + timedelta(hours=hours)
    return start, midpoint, end, hours

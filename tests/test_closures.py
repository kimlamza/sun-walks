"""
Seasonal restrictions, and the year-end wrap that would otherwise break
them silently.

A ski-season restriction running 12-01 to 03-31 is active in January. The
obvious implementation - start <= date <= end - returns False for that,
and False is a plausible answer, so nothing complains. It just quietly
stops warning anyone about the exact months the restriction exists for.

Which is why these tests check January specifically.
"""

import pandas as pd

from src.closures import active, cautions, covers, prohibitions, restrictions

TIMEZONE = "America/Edmonton"


def day(text):
    return pd.Timestamp(f"{text} 12:00", tz=TIMEZONE)


def test_range_within_one_year():
    assert covers(day("2026-08-01"), "07-10", "09-15")
    assert not covers(day("2026-07-01"), "07-10", "09-15")
    assert not covers(day("2026-10-01"), "07-10", "09-15")


def test_range_that_wraps_the_year_end():
    """The case that fails silently if you only compare dates."""
    assert covers(day("2027-01-15"), "12-01", "03-31"), "January is mid-winter"
    assert covers(day("2026-12-15"), "12-01", "03-31")
    assert covers(day("2027-03-30"), "12-01", "03-31")
    assert not covers(day("2026-06-15"), "12-01", "03-31")


def test_boundaries_are_inclusive():
    assert covers(day("2026-07-10"), "07-10", "09-15")
    assert covers(day("2026-09-15"), "07-10", "09-15")


def test_minnewanka_bans_dogs_in_late_summer():
    """Parks Canada: no pets at all, even leashed, 10 July to 15 September."""
    assert prohibitions(day("2026-08-01"), "lake-minnewanka")
    assert not prohibitions(day("2026-11-01"), "lake-minnewanka")


def test_groomed_ski_trails_restrict_dogs_in_winter():
    assert restrictions(day("2027-01-15"), "goat-creek")
    assert restrictions(day("2027-01-15"), "grassi-lakes")
    assert not restrictions(day("2026-07-15"), "goat-creek")


def test_wildlife_cautions_apply_valley_wide():
    """Cautions are not tied to a walk - they describe the whole valley."""
    calving = cautions(day("2026-05-20"))
    assert any("calving" in entry["what"].lower() for entry in calving)

    rut = cautions(day("2026-10-01"))
    assert any("rut" in entry["what"].lower() for entry in rut)

    # Bears den over winter, so a January walk should not warn about them.
    assert not any("bear" in entry["what"].lower()
                   for entry in cautions(day("2027-01-15")))


def test_a_walk_gets_both_its_own_and_valley_wide_entries():
    found = active(day("2026-08-01"), "lake-minnewanka")
    assert any(e["slug"] == "lake-minnewanka" for e in found)
    assert any(e["slug"] == "*" for e in found)

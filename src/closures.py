"""
Seasonal restrictions that repeat every year.

The design in docs/06-dog-walk-filter.md calls for a seasonal gate, and
this is it - but with a deliberate limit worth understanding.

**Only annual, predictable restrictions are encoded here.** Alberta Parks
issues elk warnings "from May until further notice" and closes areas when a
bear starts using them. Those have no end date and no pattern, so writing
them into a table would be inventing certainty that does not exist. They
belong to the authorities, and the app links out to them instead.

So: a date range that recurs every year is data. A warning that appeared
last Tuesday is not.

Three levels:
  prohibited  the walk is off the list for that date, with a reason
  restricted  extra rules apply - shown as a warning against that walk
  caution     wildlife is active valley-wide - shown once, not per walk

A slug of "*" means the entry applies to every walk.
"""

import csv
from pathlib import Path

CLOSURES_CSV = Path("data/closures.csv")
EVERY_WALK = "*"


def _as_month_day(text):
    month, day = text.split("-")
    return int(month), int(day)


def covers(when, starts, ends):
    """
    Does this month-day range include `when`?

    Ranges that wrap the year end are the reason this is a function rather
    than a comparison. A ski-season restriction running 12-01 to 03-31 is
    active in January, which a naive start <= date <= end test gets exactly
    backwards - and silently, because it returns a plausible False.
    """
    today = (when.month, when.day)
    first = _as_month_day(starts)
    last = _as_month_day(ends)

    if first <= last:
        return first <= today <= last
    return today >= first or today <= last


def load():
    if not CLOSURES_CSV.exists():
        return []
    with CLOSURES_CSV.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def active(when, slug=None, entries=None):
    """
    Every restriction in force on `when`.

    Pass a slug for that walk's own restrictions plus the valley-wide ones;
    pass none for the valley-wide ones alone.
    """
    entries = load() if entries is None else entries
    found = []
    for entry in entries:
        if not covers(when, entry["starts"], entry["ends"]):
            continue
        if entry["slug"] == EVERY_WALK or entry["slug"] == slug:
            found.append(entry)
    return found


def prohibitions(when, slug, entries=None):
    """Restrictions that take a walk off the list entirely."""
    return [e for e in active(when, slug, entries)
            if e["severity"] == "prohibited"]


def restrictions(when, slug, entries=None):
    """Extra rules that apply to this walk but do not rule it out."""
    return [e for e in active(when, slug, entries)
            if e["severity"] == "restricted"]


def cautions(when, entries=None):
    """Valley-wide wildlife activity. Shown once, not against each walk."""
    return [e for e in active(when, None, entries)
            if e["severity"] == "caution"]

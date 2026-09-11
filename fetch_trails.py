"""
Fetch the five candidate trails from OpenStreetMap.

Rather than hand-drawing routes on a map, we ask OpenStreetMap for trails
it already has surveyed. The Bow Valley is a heavily mapped international
recreation area, so coverage here is good - see docs/01-data-sources.md.

Two things learned the hard way on the first attempt:

  1. Overpass is free, shared infrastructure and rate-limits five rapid
     requests. So we send ONE request covering all five trails and split
     the results afterwards. Fewer requests is both faster and politer.

  2. Searching for "Tunnel Mountain" returned 842 points of Tunnel
     Mountain Drive, Tunnel Mountain Road, Tunnel Mountain Campground and
     Tunnel Mountain Trailer Court. OpenStreetMap gives you a road and
     path network, not a list of walks. So we filter hard on the kind of
     way it is - paths and tracks only, never roads - and use precise
     names where we know them.

One simplification worth understanding. OpenStreetMap does not store a
trail as a single tidy line; it stores it as a scatter of "way" segments
that happen to share a name. Stitching those into one ordered path is
genuinely fiddly, and we do not need it: the question is "what fraction
of this trail is in sunlight", and a fraction does not care what order
you visit the points in. Ordering matters for distance and ascent, both
of which can wait.

Run it with:  python fetch_trails.py
"""

import json
import re
import time
from pathlib import Path

import requests

# Public Overpass instances, tried in order. The main one returns 504
# Gateway Timeout when asked for nine name patterns across this bounding
# box in one go - hence both the batching below and these fallbacks.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]
ROUTES_DIR = Path("data/routes")

# How many trail names to ask for at once. Small enough that the server
# answers comfortably, large enough not to hammer it with requests.
BATCH_SIZE = 3

# south, west, north, east - Canmore, Exshaw and Banff townsite
BBOX = (50.90, -115.80, 51.35, -115.05)

# Paths people walk. Explicitly not roads, service roads or driveways -
# that filter is what stops Tunnel Mountain Drive coming back as a trail.
WALKABLE = "^(path|footway|track|steps|bridleway)$"

# Search term, and the role each walk plays in the contrast set.
# See docs/09-candidate-walks.md.
# For each walk: the term to search for, which OpenStreetMap names to keep,
# and the role it plays in the contrast set.
#
# "keep" exists because searching by name is blunt. "Heart Creek" also
# matches "Heart Creek Bunker Trail" - a different walk that runs west along
# the Trans-Canada while the real one heads south-east into the canyon.
# Left in, it contributed a third of Heart Creek's points and its sun
# percentage. inspect_route.py is what found it.
#
# A "keep" of None means every match is wanted.
TRAILS = {
    # Grassi Lakes is two walks, not one. They share both endpoints, so
    # merging them looked safe - and at midwinter and midsummer they give
    # identical answers. But at the spring equinox at noon the lower routes
    # read 100% and the Upper reads 13%, because the Upper climbs the
    # headwall directly under the cliffs. An 87 point spread.
    # compare_variants.py found it by sweeping whole days for the hour of
    # greatest disagreement, rather than checking a few chosen moments
    # where agreement was inevitable.
    "grassi-lakes": {
        "search": "Grassi Lakes",
        "keep": ["Grassi Lakes Interpretive Trail", "Grassi Lakes Trail"],
        "role": "NE-facing under Ha Ling - the easy route",
    },
    "grassi-lakes-upper": {
        "search": "Grassi Lakes",
        "keep": ["Upper Grassi Lakes Trail"],
        "role": "Under the headwall - far shadier than the lower route",
    },
    "grotto-canyon": {
        "search": "Grotto Canyon",
        "keep": None,
        "role": "Slot canyon - azimuth gated",
    },
    "montane-traverse": {
        "search": "Montane",
        # Bare "Montane" is a different trail entirely, 19 km east near
        # Exshaw at -115.07, against the benchlands at -115.34. "Montane
        # Cutoff" is in the right area but forms its own disconnected
        # cluster - a link in the network rather than part of the loop.
        # Reversible: add it back here if it turns out to be walked.
        "keep": ["Montane Traverse"],
        "role": "SW-facing bench - the winter walk",
    },
    "tunnel-mountain": {
        "search": "Tunnel Mountain Summit",
        "keep": None,
        "role": "Small hill among giants",
    },
    # Replaced Cougar Creek, whose mapped route runs up a canyon where
    # travel past the debris retention structure is restricted after flood
    # erosion. Foot access from that trailhead is limited to this trail, so
    # this is the walk you are actually permitted to do from there.
    # "Mount Lady MacDonald Route" is the exposed upper section above the
    # teahouse ruins - the part already ruled out for a dog. It is also a
    # genuinely different walk: 100% sunlit at 17:00 on the solstice where
    # the lower trail reads 30%, because at a 2 degree sun angle the high
    # ground catches light the valley slopes cannot. Keep the trail only.
    "lady-macdonald": {
        "search": "Lady Macdonald",
        "keep": ["Lady MacDonald Trail"],
        "role": "SW-facing climb above Canmore",
    },
    "goat-creek": {
        "search": "Goat Creek",
        "keep": None,        # two spellings of the same trail
        "role": "Spray valley - different orientation",
    },
    "heart-creek": {
        "search": "Heart Creek",
        "keep": ["Heart Creek Trail"],   # excludes the Bunker Trail
        "role": "East end of the Bow Valley",
    },
    "troll-falls": {
        "search": "Troll Falls",
        "keep": ["Troll Falls"],         # excludes the Marmot Creek extension
        "role": "Kananaskis valley - runs N-S",
    },
    "lake-minnewanka": {
        "search": "Minnewanka",
        "keep": None,        # right trail, but 19 km of it - trimmed later
        "role": "E-W lakeshore - south facing",
    },
    # Quarry Lake is fetched separately, by proximity - there is no way in
    # OpenStreetMap with that name. See fetch_quarry_lake.py.
}


def build_query(terms):
    """An Overpass query covering the given trail names."""
    south, west, north, east = BBOX
    names = "|".join(terms)
    return f"""
    [out:json][timeout:180];
    way["highway"~"{WALKABLE}"]["name"~"{names}",i]
       ({south},{west},{north},{east});
    out geom;
    """


def run_query(terms, attempts=3):
    """Ask Overpass, retrying and rotating instances if one is busy."""
    last_error = None
    for attempt in range(attempts):
        for url in OVERPASS_URLS:
            try:
                response = requests.post(
                    url,
                    data={"data": build_query(terms)},
                    headers={"User-Agent": "sun-walks/0.1 (personal project)"},
                    timeout=300,
                )
                response.raise_for_status()
                return response.json().get("elements", [])
            except Exception as error:
                last_error = error
                print(f"    {url.split('/')[2]}: {type(error).__name__}")
        wait = 10 * (attempt + 1)
        print(f"    all instances busy, waiting {wait}s...")
        time.sleep(wait)
    raise RuntimeError(f"Overpass unreachable: {last_error}")


def which_trail(osm_name):
    """
    Which walk does this OpenStreetMap name belong to, if any?

    Returns (slug, kept). A name can match a walk's search term and still be
    rejected by its "keep" list - that is how the Heart Creek Bunker Trail
    is excluded while staying visible in the output, so an over-tight filter
    is as obvious as an over-loose one.
    """
    # An explicit keep list wins, because it is the specific case. Two
    # walks can share a search term - Grassi Lakes and Grassi Lakes Upper
    # both search "Grassi Lakes" - and the name decides which is which.
    for slug, trail in TRAILS.items():
        if trail["keep"] and osm_name in trail["keep"]:
            return slug, True

    # Then walks that take everything their search term matches.
    for slug, trail in TRAILS.items():
        if trail["keep"] is None and re.search(
            re.escape(trail["search"]), osm_name, re.IGNORECASE
        ):
            return slug, True

    # Matched a search term but was excluded by that walk's keep list.
    for slug, trail in TRAILS.items():
        if re.search(re.escape(trail["search"]), osm_name, re.IGNORECASE):
            return slug, False

    return None, False


if __name__ == "__main__":
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)

    terms = [trail["search"] for trail in TRAILS.values()]
    batches = [terms[i:i + BATCH_SIZE]
               for i in range(0, len(terms), BATCH_SIZE)]

    elements = []
    for number, batch in enumerate(batches, start=1):
        print(f"Batch {number} of {len(batches)}: {', '.join(batch)}")
        found = run_query(batch)
        print(f"  {len(found)} ways")
        elements.extend(found)
        if number < len(batches):
            time.sleep(5)          # be polite to free infrastructure

    print(f"\n{len(elements)} matching ways in total\n")

    collected = {slug: {"points": [], "seen": set(),
                        "names": set(), "rejected": set()}
                 for slug in TRAILS}

    for element in elements:
        osm_name = element.get("tags", {}).get("name", "")
        slug, kept = which_trail(osm_name)
        if slug is None:
            continue

        bucket = collected[slug]
        if not kept:
            bucket["rejected"].add(osm_name)
            continue

        bucket["names"].add(osm_name)
        for node in element.get("geometry", []):
            # Round to about a metre - adjacent ways share endpoints.
            key = (round(node["lat"], 5), round(node["lon"], 5))
            if key not in bucket["seen"]:
                bucket["seen"].add(key)
                bucket["points"].append([node["lat"], node["lon"]])

    for slug, trail in TRAILS.items():
        term, role = trail["search"], trail["role"]
        bucket = collected[slug]
        points = bucket["points"]
        names = sorted(bucket["names"])

        if not points:
            print(f"{slug:20} NOTHING FOUND for '{term}'")
            print(f"{'':20} either it is not in OpenStreetMap under that")
            print(f"{'':20} name, or it is not tagged as a path")
            continue

        (ROUTES_DIR / f"{slug}.json").write_text(json.dumps({
            "slug": slug,
            "search_term": term,
            "role": role,
            "osm_names": names,
            "points": points,
        }, indent=2))

        print(f"{slug:20} {len(points):4} points")
        for name in names:
            print(f"{'':20}   - {name}")
        for name in sorted(bucket["rejected"]):
            print(f"{'':20}   x {name}  (excluded by 'keep')")

    # A failed Overpass batch leaves the previous run's files untouched, and
    # everything downstream then works from stale data without complaining.
    # That has happened twice. Say so loudly.
    stale = [
        slug for slug in TRAILS
        if not collected[slug]["points"]
        and (ROUTES_DIR / f"{slug}.json").exists()
    ]
    if stale:
        print("\n" + "!" * 62)
        print("STALE DATA - these walks returned nothing this run, so the")
        print("files on disk are from a PREVIOUS fetch and may not reflect")
        print("the current filters:")
        for slug in stale:
            print(f"  - {slug}")
        print("\nRe-run fetch_trails.py before trusting precompute_horizons.")
        print("!" * 62)

    print("\nRead the names above. Every one should be something you would")
    print("actually walk. A road or a campground appearing here means the")
    print("search term is too loose.")

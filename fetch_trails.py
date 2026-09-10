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
TRAILS = {
    "grassi-lakes": ("Grassi Lakes", "NE-facing under Ha Ling"),
    "grotto-canyon": ("Grotto Canyon", "Slot canyon - azimuth gated"),
    "montane-traverse": ("Montane", "SW-facing bench - the winter walk"),
    "tunnel-mountain": ("Tunnel Mountain Summit", "Small hill among giants"),
    "cougar-creek": ("Cougar Creek", "NE drainage - steep sided"),
    "goat-creek": ("Goat Creek", "Spray valley - different orientation"),
    "heart-creek": ("Heart Creek", "East end of the Bow Valley"),
    "troll-falls": ("Troll Falls", "Kananaskis valley - runs N-S"),
    "lake-minnewanka": ("Minnewanka", "E-W lakeshore - south facing"),
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
    """Which of our five trails does this OpenStreetMap name belong to?"""
    for slug, (term, _) in TRAILS.items():
        if re.search(re.escape(term), osm_name, re.IGNORECASE):
            return slug
    return None


if __name__ == "__main__":
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)

    terms = [term for term, _ in TRAILS.values()]
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

    collected = {slug: {"points": [], "seen": set(), "names": set()}
                 for slug in TRAILS}

    for element in elements:
        osm_name = element.get("tags", {}).get("name", "")
        slug = which_trail(osm_name)
        if slug is None:
            continue

        bucket = collected[slug]
        bucket["names"].add(osm_name)
        for node in element.get("geometry", []):
            # Round to about a metre - adjacent ways share endpoints.
            key = (round(node["lat"], 5), round(node["lon"], 5))
            if key not in bucket["seen"]:
                bucket["seen"].add(key)
                bucket["points"].append([node["lat"], node["lon"]])

    for slug, (term, role) in TRAILS.items():
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

    print("\nRead the names above. Every one should be something you would")
    print("actually walk. A road or a campground appearing here means the")
    print("search term is too loose.")

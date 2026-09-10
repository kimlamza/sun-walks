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
from pathlib import Path

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ROUTES_DIR = Path("data/routes")

# south, west, north, east - Canmore, Exshaw and Banff townsite
BBOX = (50.90, -115.80, 51.35, -115.05)

# Paths people walk. Explicitly not roads, service roads or driveways -
# that filter is what stops Tunnel Mountain Drive coming back as a trail.
WALKABLE = "^(path|footway|track|steps|bridleway)$"

# Search term, and the role each walk plays in the contrast set.
# See docs/09-candidate-walks.md.
TRAILS = {
    "grassi-lakes": ("Grassi Lakes", "NE-facing - morning sun"),
    "grotto-canyon": ("Grotto Canyon", "Deep shade extreme"),
    "montane-traverse": ("Montane", "SW-facing bench - afternoon sun"),
    "tunnel-mountain": ("Tunnel Mountain Summit", "High and open - control"),
    "quarry-lake": ("Quarry Lake", "Open valley floor, high skyline"),
}


def build_query():
    """A single Overpass query covering every trail we are looking for."""
    south, west, north, east = BBOX
    names = "|".join(term for term, _ in TRAILS.values())
    return f"""
    [out:json][timeout:180];
    way["highway"~"{WALKABLE}"]["name"~"{names}",i]
       ({south},{west},{north},{east});
    out geom;
    """


def which_trail(osm_name):
    """Which of our five trails does this OpenStreetMap name belong to?"""
    for slug, (term, _) in TRAILS.items():
        if re.search(re.escape(term), osm_name, re.IGNORECASE):
            return slug
    return None


if __name__ == "__main__":
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)

    print("Querying OpenStreetMap once for all five trails...")
    response = requests.post(
        OVERPASS_URL,
        data={"data": build_query()},
        headers={"User-Agent": "sun-walks/0.1 (personal project)"},
        timeout=300,
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])
    print(f"  {len(elements)} matching ways returned\n")

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

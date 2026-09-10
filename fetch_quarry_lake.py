"""
Fetch the Quarry Lake paths from OpenStreetMap - by proximity, not by name.

fetch_trails.py finds trails by name, which works for the other four walks
and fails completely here. There is no way in OpenStreetMap called "Quarry
Lake Trail". There is a *lake* called Quarry Lake, with paths around it that
are either unnamed or named something else entirely.

That is a normal shape for OpenStreetMap data and worth knowing about. Named
long trails are well covered; the short loop round a local park usually is
not, because nobody thinks of it as having a name.

So this asks a different question: "what walkable paths lie within 250 m of
the water body called Quarry Lake?" The Overpass `around` filter does that
directly, and it can take a previously matched set as its origin - so the
whole thing is still one request.

Run it with:  python fetch_quarry_lake.py
"""

import json
from pathlib import Path

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ROUTES_DIR = Path("data/routes")

BBOX = "50.90,-115.80,51.35,-115.05"
# Measured from the shoreline, not the centre - so this reaches further than
# it sounds. At 250 m it pulled in Powerline Trail, Fun Forrest and Peaks
# Drive, which are the wider Canmore network passing nearby rather than the
# lake loop. 120 m keeps it to the water's edge.
SEARCH_RADIUS_M = 120
WALKABLE = "^(path|footway|track|steps|bridleway)$"

QUERY = f"""
[out:json][timeout:180];

// Find the lake itself first, and keep it as a named set.
(
  way["natural"="water"]["name"~"Quarry Lake",i]({BBOX});
  relation["natural"="water"]["name"~"Quarry Lake",i]({BBOX});
)->.lake;

// Then every walkable path within {SEARCH_RADIUS_M} m of it.
way["highway"~"{WALKABLE}"](around.lake:{SEARCH_RADIUS_M});
out geom;
"""

if __name__ == "__main__":
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Looking for walkable paths within {SEARCH_RADIUS_M} m of "
          "Quarry Lake...")
    response = requests.post(
        OVERPASS_URL,
        data={"data": QUERY},
        headers={"User-Agent": "sun-walks/0.1 (personal project)"},
        timeout=300,
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])

    seen = set()
    points = []
    names = set()

    for element in elements:
        tags = element.get("tags", {})
        names.add(tags.get("name") or f"(unnamed {tags.get('highway')})")
        for node in element.get("geometry", []):
            key = (round(node["lat"], 5), round(node["lon"], 5))
            if key not in seen:
                seen.add(key)
                points.append([node["lat"], node["lon"]])

    if not points:
        raise SystemExit(
            "Nothing found. Either the lake is not tagged natural=water, or "
            "there are no paths mapped within the search radius. Try widening "
            "SEARCH_RADIUS_M, or check the name on openstreetmap.org."
        )

    (ROUTES_DIR / "quarry-lake.json").write_text(json.dumps({
        "slug": "quarry-lake",
        "search_term": f"within {SEARCH_RADIUS_M} m of Quarry Lake",
        "role": "Open valley floor - high skyline",
        "osm_names": sorted(names),
        "points": points,
    }, indent=2))

    centre_lat = sum(p[0] for p in points) / len(points)
    centre_lon = sum(p[1] for p in points) / len(points)

    print(f"  {len(elements)} ways, {len(points)} points")
    print(f"  centre of the points: {centre_lat:.4f}, {centre_lon:.4f}")
    print("  matched:")
    for name in sorted(names):
        print(f"    - {name}")
    print("\nSanity check: the centre should be near 51.07, -115.37, and the")
    print("terrain model should put it around 1,400 m. Anything far off that")
    print("means the search picked up the wrong place.")

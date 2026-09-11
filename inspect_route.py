"""
Look at what OpenStreetMap actually gave us for a walk.

fetch_trails.py matches on name, which is blunt. "Heart Creek" also matches
"Heart Creek Bunker Trail", a separate walk. The result is a point cloud
that may contain two or three unrelated trails, and on the map that shows up
as disconnected clusters.

This reports the clusters, and finds the car parks nearby - because the
trailhead is the thing that actually defines which cluster is the walk.

Run it with:  python inspect_route.py heart-creek
"""

import json
import sys
from pathlib import Path

import numpy as np
import requests
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial.distance import cdist

ROUTES_DIR = Path("data/routes")
LATLON = "EPSG:4326"
UTM_11N = "EPSG:26911"

# Points closer together than this are treated as the same trail.
LINK_DISTANCE_M = 250
PARKING_SEARCH_M = 2000

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def to_metres(points):
    transformer = Transformer.from_crs(LATLON, UTM_11N, always_xy=True)
    easting, northing = transformer.transform(points[:, 1], points[:, 0])
    return np.column_stack([easting, northing])


def find_clusters(metres, link_distance=LINK_DISTANCE_M):
    """Group points into trails by whether they are within reach of each other."""
    distances = cdist(metres, metres)
    graph = csr_matrix(distances < link_distance)
    count, labels = connected_components(graph, directed=False)
    return count, labels


def find_parking(lat, lon):
    query = f"""
    [out:json][timeout:90];
    (
      way["amenity"="parking"](around:{PARKING_SEARCH_M},{lat},{lon});
      node["amenity"="parking"](around:{PARKING_SEARCH_M},{lat},{lon});
    );
    out center tags;
    """
    for url in OVERPASS_URLS:
        try:
            response = requests.post(
                url, data={"data": query},
                headers={"User-Agent": "sun-walks/0.1"}, timeout=120,
            )
            response.raise_for_status()
            return response.json().get("elements", [])
        except Exception:
            continue
    return []


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "heart-creek"
    route = json.loads((ROUTES_DIR / f"{slug}.json").read_text())

    points = np.array(route["points"])
    metres = to_metres(points)
    count, labels = find_clusters(metres)

    print(f"{slug}: {len(points)} points, matched from")
    for name in route["osm_names"]:
        print(f"   - {name}")

    print(f"\n{count} separate cluster(s), linking anything within "
          f"{LINK_DISTANCE_M} m:\n")

    order = sorted(range(count), key=lambda i: -(labels == i).sum())
    for rank, cluster in enumerate(order, start=1):
        mask = labels == cluster
        block = metres[mask]
        centre = points[mask].mean(axis=0)
        span_km = max(np.ptp(block[:, 0]), np.ptp(block[:, 1])) / 1000

        print(f"  Cluster {rank}: {mask.sum():3} points, "
              f"spans {span_km:4.1f} km, "
              f"centre {centre[0]:.4f}, {centre[1]:.4f}")

    # Search near the ENDS of the biggest cluster, not its middle. A trail
    # starts at one end, so for anything long the centroid is nowhere near
    # the car park - the middle of Lake Minnewanka, in one case.
    mask = labels == order[0]
    block = metres[mask]
    ends = {
        "west end": points[mask][block[:, 0].argmin()],
        "east end": points[mask][block[:, 0].argmax()],
    }

    for label, end in ends.items():
        print(f"\nCar parks within {PARKING_SEARCH_M / 1000:.0f} km of the "
              f"{label} ({end[0]:.4f}, {end[1]:.4f}):\n")

        found = find_parking(end[0], end[1])
        if not found:
            print("  none")
            continue

        for element in find_parking(end[0], end[1]):
            tags = element.get("tags", {})
            position = element.get("center") or element
            name = tags.get("name", "(unnamed)")
            access = tags.get("access", "")
            distance = np.hypot(
                *(to_metres(np.array([[position["lat"], position["lon"]]]))[0]
                  - to_metres(np.array([end]))[0])
            )
            print(f"  {name:38} {distance / 1000:4.1f} km  "
                  f"{position['lat']:.4f}, {position['lon']:.4f}  {access}")

    print("\nThe car park nearest a cluster is the likely trailhead. A walk")
    print("that people actually do starts there - so clusters far from any")
    print("parking are probably a different trail that shares the name.")

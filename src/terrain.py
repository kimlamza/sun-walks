"""
Terrain horizon calculations.

The one idea in this file: standing at a point and looking in a given
compass direction, how high above horizontal does the terrain rise?

If the sun is higher than that angle, you are in direct sunlight. If it is
lower, something is in the way. Sunrise on a flat plain is just the case
where that angle happens to be zero.
"""

import math

# Light bends downwards through the atmosphere, which makes the Earth
# behave as though it were about a sixth larger than it is. Standard
# approximation in surveying and radio propagation.
EARTH_RADIUS_M = 6_371_000
EFFECTIVE_RADIUS_M = EARTH_RADIUS_M * 7 / 6


def horizon_angle(dem, row, col, azimuth_deg, cell_size_m,
                  max_distance_m=30_000):
    """
    The highest angle above horizontal to the terrain, looking along a bearing.

    dem             2-D array of ground heights in metres
    row, col        where in the grid you are standing
    azimuth_deg     compass bearing, degrees clockwise from north
    cell_size_m     how much ground one grid cell covers
    max_distance_m  how far to look. 30 km, because a 1,600 m mountain
                    with the sun 5 degrees up throws an 18 km shadow

    Returns degrees. Negative means everything in that direction is
    below you.
    """
    observer_height = dem[row, col]
    n_rows, n_cols = dem.shape

    # North is decreasing row (up the array); east is increasing column.
    azimuth = math.radians(azimuth_deg)
    step_col = math.sin(azimuth)
    step_row = -math.cos(azimuth)

    highest = -90.0
    distance = cell_size_m
 
    while distance <= max_distance_m:
        cells_out = distance / cell_size_m
        r = int(round(row + step_row * cells_out))
        c = int(round(col + step_col * cells_out))

        # Walked off the edge of the terrain model — stop looking.
        if not (0 <= r < n_rows and 0 <= c < n_cols):
            break

        # Distant ground curves away below the local horizontal.
        drop = distance ** 2 / (2 * EFFECTIVE_RADIUS_M)
        rise = dem[r, c] - observer_height - drop

        angle = math.degrees(math.atan2(rise, distance))
        if angle > highest:
            highest = angle

        distance += cell_size_m

    return highest


def is_sunlit(horizon_deg, solar_elevation_deg):
    """True if the sun clears the skyline in that direction."""
    return solar_elevation_deg > horizon_deg

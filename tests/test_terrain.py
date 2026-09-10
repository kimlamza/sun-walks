"""
Tests against terrain simple enough to check by hand.

A flat plane and a single wall are not interesting landscapes, but they
are landscapes where the correct answer is known in advance. Real terrain
can hide a wrong answer behind a plausible-looking one; a flat plane
cannot.
"""

import math

import numpy as np

from src.terrain import horizon_angle, horizon_profile, is_sunlit

CELL_SIZE_M = 30
CENTRE = 100          # observer sits at row 100, col 100
WALL_DISTANCE_CELLS = 10
WALL_HEIGHT_M = 100.0

# 10 cells at 30 m each = 300 m away.
WALL_DISTANCE_M = WALL_DISTANCE_CELLS * CELL_SIZE_M
# atan(100 / 300) = 18.43 degrees. Worked out on paper, not by the code.
EXPECTED_WALL_ANGLE = math.degrees(math.atan(WALL_HEIGHT_M / WALL_DISTANCE_M))


def flat_terrain():
    return np.zeros((201, 201))


def test_flat_plane_has_no_horizon():
    """On a flat plane the skyline is at eye level in every direction."""
    dem = flat_terrain()
    for azimuth in (0, 45, 90, 135, 180, 225, 270, 315):
        angle = horizon_angle(dem, CENTRE, CENTRE, azimuth, CELL_SIZE_M)
        assert abs(angle) < 0.1, f"azimuth {azimuth} gave {angle}"


def test_wall_to_the_east():
    """A 100 m wall 300 m away should sit at atan(100/300) = 18.43 degrees."""
    dem = flat_terrain()
    dem[:, CENTRE + WALL_DISTANCE_CELLS] = WALL_HEIGHT_M

    angle = horizon_angle(dem, CENTRE, CENTRE, 90, CELL_SIZE_M)
    assert abs(angle - EXPECTED_WALL_ANGLE) < 0.1


def test_nothing_behind_you():
    """The same wall must be invisible when you look the other way."""
    dem = flat_terrain()
    dem[:, CENTRE + WALL_DISTANCE_CELLS] = WALL_HEIGHT_M

    angle = horizon_angle(dem, CENTRE, CENTRE, 270, CELL_SIZE_M)
    assert abs(angle) < 0.1


def test_north_is_not_south():
    """
    The azimuth convention test — the one that catches real bugs.

    North is decreasing row. A wall placed to the north must be found at
    bearing 0 and must NOT be found at bearing 180.
    """
    dem = flat_terrain()
    dem[CENTRE - WALL_DISTANCE_CELLS, :] = WALL_HEIGHT_M

    looking_north = horizon_angle(dem, CENTRE, CENTRE, 0, CELL_SIZE_M)
    looking_south = horizon_angle(dem, CENTRE, CENTRE, 180, CELL_SIZE_M)

    assert abs(looking_north - EXPECTED_WALL_ANGLE) < 0.1
    assert abs(looking_south) < 0.1


def test_sun_above_and_below_the_skyline():
    """The whole project, in four lines."""
    assert is_sunlit(EXPECTED_WALL_ANGLE, 20.0)      # sun clears the wall
    assert not is_sunlit(EXPECTED_WALL_ANGLE, 15.0)  # wall blocks the sun


def test_fast_path_agrees_with_slow_path():
    """
    The vectorised profile must match the readable one, bearing for bearing.

    horizon_profile exists only to be fast enough to precompute. If it ever
    disagrees with horizon_angle, every number the app shows is quietly
    wrong while the original tests stay green - so this is the test that
    keeps the optimisation honest.
    """
    dem = flat_terrain()
    dem[:, CENTRE + WALL_DISTANCE_CELLS] = WALL_HEIGHT_M
    dem[CENTRE - WALL_DISTANCE_CELLS, :] = WALL_HEIGHT_M * 0.5

    azimuths = list(range(0, 360, 15))
    fast = horizon_profile(dem, CENTRE, CENTRE, CELL_SIZE_M, azimuths)

    for index, azimuth in enumerate(azimuths):
        slow = horizon_angle(dem, CENTRE, CENTRE, azimuth, CELL_SIZE_M)
        assert abs(fast[index] - slow) < 0.01, (
            f"azimuth {azimuth}: fast {fast[index]:.3f} vs slow {slow:.3f}"
        )

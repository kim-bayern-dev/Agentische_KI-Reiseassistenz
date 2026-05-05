from typing import Tuple
from geopy import Point, distance


def make_viewbox(lat: float, lon: float, radius_m: int) -> Tuple[Point, Point]:
    """Create a viewbox around a point with a given radius in meters.
    Args:
        lat: Latitude of the center point.
        lon: Longitude of the center point.
        radius_m: Radius in meters.

    Returns:
        A tuple of two Points defining the viewbox:
        (southwest_point, northeast_point)
    """
    if radius_m < 0:
        raise ValueError("radius_m must be >= 0")

    origin = (lat, lon)

    # Bearings: 180° = south, 270° = west, 0° = north, 90° = east
    south = distance(meters=radius_m).destination(origin, bearing=180)
    west = distance(meters=radius_m).destination(origin, bearing=270)
    north = distance(meters=radius_m).destination(origin, bearing=0)
    east = distance(meters=radius_m).destination(origin, bearing=90)

    return (
        Point(south.latitude, west.longitude),
        Point(north.latitude, east.longitude),
    )

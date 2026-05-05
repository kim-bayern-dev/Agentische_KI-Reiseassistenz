from typing import Dict
from langchain.tools import tool
from pydantic import BaseModel, Field
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from mapping.map_utils import make_viewbox


class CalculateDistanceInput(BaseModel):
    origin_latitude: float = Field(
        ...,
        description="Latitude of the starting point in decimal degrees, e.g. 48.8584",
        ge=-90,
        le=90,
    )
    origin_longitude: float = Field(
        ...,
        description="Longitude of the starting point in decimal degrees, e.g. 2.2945",
        ge=-180,
        le=180,
    )
    destination_latitude: float = Field(
        ...,
        description="Latitude of the destination in decimal degrees, e.g. 51.5074",
        ge=-90,
        le=90,
    )
    destination_longitude: float = Field(
        ...,
        description="Longitude of the destination in decimal degrees, e.g. -0.1278",
        ge=-180,
        le=180,
    )


@tool(args_schema=CalculateDistanceInput)
def calculate_distance(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    """
    Calculate the geodesic distance in kilometers between two geographic points.

    Use numeric decimal degree values, not strings and not tuples.

    Example tool input:
    {
      "origin_latitude": 48.8584,
      "origin_longitude": 2.2945,
      "destination_latitude": 51.5074,
      "destination_longitude": -0.1278
    }
    """
    distance_km = geodesic(
        (origin_latitude, origin_longitude),
        (destination_latitude, destination_longitude),
    ).kilometers
    return round(distance_km, 2)


@tool
def get_coordinates(
    location: str, center: tuple = None, radius_m: int = 50_000
) -> Dict:
    """Get the coordinates for a location string.

    Args:
        location: The name of the location.
        center (tuple, optional): A tuple of (latitude, longitude) to bias the search. Defaults to None.
        radius_m (int, optional): The search radius in meters around the location. Defaults to 50,000.

    Returns:
        A dictionary containing the latitude and longitude of the location as well as a respecitve address.

    Example:
        Input: "Eiffel Tower"
        Output: {
            "latitude": 48.8584,
            "longitude": 2.2945
        }
    """
    viewbox = make_viewbox(*center, radius_m=radius_m) if center else None

    geolocator = Nominatim(user_agent="poi-search-demo", timeout=5)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=3)

    location_coords = geocode(
        location,
        addressdetails=True,
        language="en",
        country_codes="de",
        viewbox=viewbox,
        bounded=True,
    )  # bias to Germany
    if location_coords:
        return {
            "latitude": location_coords.latitude,
            "longitude": location_coords.longitude,
            "address": location_coords.address,
        }
    else:
        return {"latitude": None, "longitude": None, "address": "Location not found"}

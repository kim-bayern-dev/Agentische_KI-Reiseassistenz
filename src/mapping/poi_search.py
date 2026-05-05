import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from mapping.map_utils import make_viewbox


def resolve_poi(poi):
    """Helper to resolve a POI string to coordinates for map display."""
    marker = None
    if isinstance(poi, str):
        lat, lon, addr = poi_search(poi)
    elif isinstance(poi, tuple) and len(poi) == 2:
        lat, lon = poi
        addr = "Unnamed location"
    elif isinstance(poi, list) and len(poi) == 2:
        lat, lon = poi
        addr = "Unnamed location"
    elif isinstance(poi, list) and len(poi) == 4:
        addr, lat, lon, marker = poi
        if lat is None or lon is None:
            lat, lon, _ = poi_search(poi[0])
    elif isinstance(poi, tuple) and len(poi) == 4:
        addr, lat, lon, marker = poi
        if lat is None or lon is None:
            lat, lon, _ = poi_search(poi[0])
    elif isinstance(poi, dict):
        addr = poi.get("name") or poi.get("address") or "Unnamed location"
        lat = poi.get("lat")
        lon = poi.get("lon") or poi.get("lng")
        marker = poi.get("marker")
        if lat is None or lon is None:
            lat, lon, _ = poi_search(addr)
    else:
        raise ValueError(f"Unexpected POI type: {type(poi)}")
    return lat, lon, addr, marker


def poi_search(query: str, center: tuple = None, radius_m: int = 50_000) -> tuple:
    """Search for a point of interest (POI) and return its latitude, longitude, and address.

    Args:
        query (str): The search query for the POI.
        center (tuple, optional): A tuple of (latitude, longitude) to bias the search. Defaults to None.
        radius_m (int, optional): The search radius in meters around the location. Defaults to 50,000.

    Returns:
        tuple: A tuple containing latitude (float), longitude (float), and address (str).
    """
    viewbox = make_viewbox(*center, radius_m=radius_m) if center else None

    geolocator = Nominatim(user_agent="poi-search-demo", timeout=5)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=3)

    if os.environ.get("TABLE_NAME") == "mueller":
        country_codes = "pt"
    else:
        country_codes = "de"

    location = geocode(
        query,
        addressdetails=True,
        language="en",
        country_codes=country_codes,
        viewbox=viewbox,
        bounded=True,
    )
    if location:
        return location.latitude, location.longitude, location.address
    else:
        return None, None, "Location not found"

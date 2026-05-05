from typing import Dict
from langchain.tools import tool

from db import TOUREN_DB


@tool
def retrieve_gpx_track(tournr: str) -> Dict:
    """
    Retrieve GPX track data for a given tour number.

    Args:
        tournr: The tour number as a string.

    Returns:
        A dictionary containing the GPX filename and available named waypoints.

    Example:
        Input: "42"
        Output: {
            "gpx_filename": "tour_ba2d42.gpx",
            "pois": ["Start Point", "Scenic Overlook", "Rest Area", "End Point"]
        }
    """
    tour = next((t for t in TOUREN_DB.touren if t.tournr == tournr), None)
    if not tour:
        return f"No tour found with tournr: {tournr}"
    gpx_data = {"gpx_filename": f"{tour.gpx}", "pois": [poi for poi in tour.pois]}

    return gpx_data

import os
from loguru import logger
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List


@dataclass
class TrackPoint:
    lat: float
    lon: float
    ele: float | None = None


@dataclass
class Waypoint:
    lat: float
    lon: float
    name: str


def read_gpx(gpx_name: str) -> tuple[List[Waypoint], List[TrackPoint]]:
    """Parse GPX XML and extract waypoints and track points."""
    # Parse XML
    path = f"data/gpx/{gpx_name}"
    logger.debug(f"Reading GPX XML from {path}")
    with open(path, "rb") as gpx_xml:
        root = ET.fromstring(gpx_xml.read())

    # Define namespace
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    waypoints = []
    track_points = []

    # Extract waypoints (wpt elements)
    for wpt in root.findall(".//gpx:wpt", ns):
        lat = float(wpt.get("lat"))
        lon = float(wpt.get("lon"))
        name_elem = wpt.find("gpx:name", ns)
        name = name_elem.text if name_elem is not None else ""
        waypoints.append(Waypoint(lat=lat, lon=lon, name=name))

    # Extract track points (trkpt elements)
    for trkpt in root.findall(".//gpx:trkpt", ns):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        ele_elem = trkpt.find("gpx:ele", ns)
        ele = float(ele_elem.text) if ele_elem is not None and ele_elem.text else None
        track_points.append(TrackPoint(lat=lat, lon=lon, ele=ele))

    return waypoints, track_points

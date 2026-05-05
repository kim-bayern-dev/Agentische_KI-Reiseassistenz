"""Map rendering for the side panel (Folium)."""

from typing import Iterable, List, Optional

import folium
from loguru import logger

from mapping.poi_search import poi_search, resolve_poi
from mapping.gpx import read_gpx, TrackPoint, Waypoint


def add_poi_marker(
    m: folium.Map,
    lat: float | None,
    lon: float | None,
    address: str,
    marker: str | None = None,
) -> folium.Map:
    """Add a single marker to a Folium map and center/zoom to it."""
    if lat is None or lon is None:
        logger.warning("POI search did not return valid coordinates.")
        return m

    folium.Marker(
        location=[lat, lon],
        tooltip=address,
        popup=address,
        icon=folium.Icon(icon=marker if marker else "flag"),
    ).add_to(m)

    # center map on found location
    m.location = [lat, lon]
    m.zoom_start = 10
    m.fit_bounds([[lat - 0.05, lon - 0.05], [lat + 0.05, lon + 0.05]])
    return m


def draw_gpx_track(
    m: folium.Map,
    track_points: List[TrackPoint],
    waypoints: List[Waypoint] | None = None,
    track_color: str = "blue",
    track_weight: int = 3,
) -> folium.Map:
    """Draw GPX track and waypoints on a Folium map."""

    # Draw track polyline
    if track_points:
        track_coords = [[pt.lat, pt.lon] for pt in track_points]
        folium.PolyLine(
            track_coords,
            color=track_color,
            weight=track_weight,
            opacity=0.8,
        ).add_to(m)

    # Add waypoint markers
    if waypoints:
        for wp in waypoints:
            folium.Marker(
                location=[wp.lat, wp.lon],
                tooltip=wp.name,
                popup=wp.name,
                icon=folium.Icon(icon="flag", color="red"),
            ).add_to(m)

    # Fit map to track bounds
    if track_points:
        bounds = [[pt.lat, pt.lon] for pt in track_points]
        m.fit_bounds(bounds)

    return m


def render_map_html(
    location: str, poi_state: Iterable[str] | None, gpx_names: Optional[List[str]]
) -> str:
    """Return <div>-wrapped HTML so the map doesn't collapse height."""
    lat, lon, _addr = poi_search(location)
    if lat is None or lon is None:
        logger.warning(
            f"Could not geocode location '{location}', falling back to (0, 0)."
        )
        lat, lon = 0.0, 0.0
    m = folium.Map(location=(lat, lon))

    if gpx_names:
        for gpx_name in gpx_names:
            try:
                waypoints, track_points = read_gpx(gpx_name)
                m = draw_gpx_track(m=m, track_points=track_points, waypoints=waypoints)
            except FileNotFoundError as e:
                logger.error(f"Failed to load gpx track {gpx_name}: {e}")
    if poi_state:
        for poi in poi_state:
            lat2, lon2, address, marker = resolve_poi(poi)
            m = add_poi_marker(m, lat=lat2, lon=lon2, address=address, marker=marker)

    return f"{m.get_root()._repr_html_()}"

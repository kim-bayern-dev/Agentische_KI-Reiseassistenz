from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PoiMarker(BaseModel):
    """Point of Interest marker with coordinates"""

    name: str = Field(..., description="Name of the point of interest")
    lat: float = Field(..., description="Latitude coordinate (high precision)")
    lon: float = Field(..., description="Longitude coordinate (high precision)")
    marker: str = Field(
        ...,
        description="Bootstrap 3 glyphicons icon name for marker (e.g., 'map-marker', 'star', 'home')",
    )


class OptionsPanelItem(BaseModel):
    """Item in the options panel for travel options or recommendations"""

    title: str = Field(
        ...,
        description="Title of the option (point of interest, activity, or suggestion). Never include image filename here.",
    )
    content: str = Field(
        ...,
        description="Content with detailed information. Include citations like [[web: https://...]], [[tournr: 12]], [[file: <filename>]]. Add opening hours, prices, or links if available. Never include image filename here.",
    )
    image_file: Optional[str] = Field(
        None,
        description="Image file name from context (e.g., 'sight.jpg'). Only include if you have the actual filename. Do not fabricate.",
    )

    @field_validator("image_file")
    @classmethod
    def validate_image_file(cls, v: Optional[str]) -> Optional[str]:
        """Ensure image_file is not included in title or content"""
        return v


class DetailsPanelItem(BaseModel):
    """Item in the details panel for travel details, hints and important information"""

    title: str = Field(..., description="Title of the detail item")
    content: str = Field(
        ...,
        description="Content with general travel details, hints, and important information. Always include sources for bus, train, and general travel tips using citations like [[tournr: 01]], [[web: <url>]], [[file: <filename>]].",
    )


class StructuredResponse(BaseModel):
    """
    Main structured response schema for travel assistant vLLM

    All fields except 'message' are optional with sensible defaults.
    """

    message: str = Field(
        ...,
        description="Response to the user in the chat. Refer to details and options panels if needed but don't repeat their content. Keep the response concise. Never return lists, markdown, or HTML here. Must always be included!",
    )
    options_panel: List[OptionsPanelItem] = Field(
        default_factory=list,
        description="List of objects for the travel options or recommendations panel. Include points of interest, activities, or concrete suggestions. Return empty list if no options available.",
    )
    pois: List[PoiMarker] = Field(
        default_factory=list,
        description="Points of interest with coordinates for map marking. Keep coordinates as high precision as possible. If no coordinates are given, a name resolution service will be used. Marker should be an appropriate Bootstrap 3 glyphicon icon name.",
    )
    details_panel: List[DetailsPanelItem] = Field(
        default_factory=list,
        description="List of objects for the details panel. Include general travel details, hints, and important information. Return empty list if no details available. Always include sources for bus, train, and general travel tips.",
    )
    gpx: Optional[List[str]] = Field(
        None,
        description="List of GPX track filenames to display on the map (e.g., 'trip1.gpx'). Only include actual filenames from context. Do not fabricate. Do not tell users they can download files - they will be rendered automatically.",
    )

    @field_validator("pois")
    @classmethod
    def validate_pois(cls, v: List[PoiMarker]) -> List[PoiMarker]:
        """Validate that pois are properly formatted"""
        for poi in v:
            if not (
                isinstance(poi.lat, (int, float)) and isinstance(poi.lon, (int, float))
            ):
                raise ValueError(f"Invalid coordinates for poi '{poi.name}'")
        return v

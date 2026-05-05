from langchain_core.utils.function_calling import (
    convert_to_openai_tool,
)
from typing import Callable

from .time import time_now
from .weather import get_weather
from .local_search import (
    search_hikingtour,
    retrieve_tour_details,
    semantic_search,
)
from .gpx_tool import retrieve_gpx_track
from .distance import get_coordinates, calculate_distance
from .web_search import search_web, fetch_url
from .ddg_opening_hours import get_opening_info


def lc_tool_to_responses_tool(lc_tool: dict) -> dict:
    # LangChain ChatCompletions-shape -> Responses-shape
    if lc_tool.get("type") == "function" and "function" in lc_tool:
        f = lc_tool["function"]
        return {
            "type": "function",
            "name": f["name"],
            "description": f.get("description", ""),
            "parameters": f.get("parameters", {"type": "object", "properties": {}}),
        }
    return lc_tool


class ToolRegistry:

    def __init__(self):
        self._TOOLS = [
            get_weather,
            search_hikingtour,
            retrieve_tour_details,
            semantic_search,
            get_opening_info,
            calculate_distance,
            get_coordinates,
            retrieve_gpx_track,
            search_web,
            fetch_url,
        ]

        self.TOOLS = [
            lc_tool_to_responses_tool(convert_to_openai_tool(t)) for t in self._TOOLS
        ]
        self.tool_registry = {t.name: t for t in self._TOOLS}

    def get_tool_by_name(self, name: str) -> Callable:
        try:
            return self.tool_registry[name]
        except KeyError:
            raise ValueError(f"Unknown tool: {name}")

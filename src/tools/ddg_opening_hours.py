from ddgs import DDGS
from langchain.tools import tool


@tool
def get_opening_info(place: str) -> str:
    """Get the opening hours or schedule snippets for a POI / event

    Be as specific as possible with the location to get the right result and place, e.g. include city name.

    Examples:
        "Museum Torfbahnhof Bayern" compared to just "Torfbahnhof".
        "Biergarten am Chinesischen Turm München" compared to just "Chinesischer Turm".

    Args:
        place: natural-language name, e.g. 'Louvre Paris', 'Englischer Garten München'.

    Returns:
        Markdown string with best guess + top sources.
    """
    query = f"{place} Öffnungszeiten"
    with DDGS() as ddgs:
        hits = list(ddgs.text(query, max_results=5))

    return "\n\n".join(
        [f'URL: {hit["href"]} : {hit["body"]}' for idx, hit in enumerate(hits)]
    )

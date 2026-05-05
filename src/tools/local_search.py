from langchain.tools import tool

from db import TOUREN_DB
from db.utils import get_db, get_table


@tool
def search_hikingtour(
    n_results: int = 5,
    nahverkehr: bool = None,
    einkehr: bool = None,
    kinderfreundlich: bool = None,
    hundefreundlich: bool = None,
    kinderwagen: bool = None,
    baden: bool = None,
    schwierigkeit: str = None,
    min_dauer: float = None,
    max_dauer: float = None,
    min_hm_aufstieg: int = None,
    max_hm_aufstieg: int = None,
):
    """
    Return a list of hiking tours that match all supplied criteria.

    Only provide values for filters you want to use. Omnit 'None'.

    Args:
        n_results (Optional[int]): Maximum number of results to return.
        nahverkehr (Optional[bool]): Filter by public transport accessibility. Use it only if explicitly requested!
        einkehr (Optional[bool]): Filter by presence of eateries.
        kinderfreundlich (Optional[bool]): Filter by child-friendliness.
        hundefreundlich (Optional[bool]): Filter by dog-friendliness.
        kinderwagen (Optional[bool]): Filter by stroller accessibility.
        baden (Optional[bool]): Filter by swimming availability.
        schwierigkeit (Optional[Literal["blau", "rot", "schwarz"]]):
            Filter by difficulty level.
        min_dauer (Optional[float]): Minimum duration in hours.
        max_dauer (Optional[float]): Maximum duration in hours.
        min_hm_aufstieg (Optional[int]): Minimum ascent in meters.
        max_hm_aufstieg (Optional[int]): Maximum ascent in meters.

    Returns:
        List[Tour]: A list of tours matching the criteria.
    """
    results = TOUREN_DB.query_tours(
        n_results=n_results,
        public_transport=nahverkehr,
        einkehr=einkehr,
        kinderfreundlich=kinderfreundlich,
        hundefreundlich=hundefreundlich,
        kinderwagen=kinderwagen,
        baden=baden,
        schwierigkeit=schwierigkeit,
        min_dauer=min_dauer,
        max_dauer=max_dauer,
        min_hm_aufstieg=min_hm_aufstieg,
        max_hm_aufstieg=max_hm_aufstieg,
    )

    if not results:
        return "No tours found matching the criteria."

    response_lines = []
    for tour in results:
        line = (
            f"[tournr:{tour.tournr}] {tour.titel} | {tour.subtitle} | Duration: {tour.dauer} hours | "
            f"Difficulty: {tour.schwierigkeit} | Ascent: {tour.hm_aufstieg} m"
        )
        response_lines.append(line)

    return "\n\n".join(response_lines)


@tool
def retrieve_tour_details(tournr: str) -> str:
    """Retrieve detailed information about a specific hiking tour.

    Args:
        tournr: The unique identifier of the tour.

    Returns:
        Detailed information about the tour.
    """
    tour = next((t for t in TOUREN_DB.touren if t.tournr == tournr), None)
    if not tour:
        return f"No tour found with tournr: {tournr}"

    details = (
        f"Title: {tour.titel}\n"
        f"Subtitle: {tour.subtitle}\n"
        f"Type: {tour.tourentyp}\n"
        f"Duration: {tour.dauer} hours\n"
        f"Ascent: {tour.hm_aufstieg} meters\n"
        f"Difficulty: {tour.schwierigkeit}\n"
        f"Description: {tour.beschreibung}\n"
        f"Starting Point: {tour.ausgangspunkt}\n"
        f"Requirements: {tour.anforderungen}\n"
        f"Refreshments: {tour.refreshments}\n"
        f"Variants: {tour.varianten}\n"
        f"Summary: {tour.summary}\n"
        f"Description: {tour.beschreibung}\n"
        f"Images: {tour.bilder}\n"
        f"Points of Interest: {tour.pois}\n"
        f"GPX File: {tour.gpx}\n"
    )
    return details


@tool
def semantic_search(query: str, n_results: int = 5):
    """Perform a semantic search in the relevant text database based on a local guide book.

    Args:
        query: The semantic search query.
        n_results: The number of results to return.

    Returns:
        A list of matching text chunks from the guide books
    """
    table = get_table(get_db("lancedb"), table_name="example")
    results = table.search(query).limit(n_results).to_list()

    output = []
    for r in results:
        if "tournr" in r:
            output.append(
                {"tournr": r["tournr"], "text": r["text"], "relevance": r["_distance"]}
            )
        else:
            output.append({"text": r["text"], "relevance": r["_distance"]})

    return output


@tool
def read_file(filename: str) -> str:
    """Read the content of a file."""
    data_path = "./data/files/"
    with open(f"{data_path}{filename}", "r", encoding="utf-8") as f:
        return f.read()

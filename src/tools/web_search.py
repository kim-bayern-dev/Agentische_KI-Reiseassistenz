import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
from langchain.tools import tool


@tool
def search_web(query: str) -> str:
    """
    Return web search snippets for a German query using DuckDuckGo.

    Args:
        query: natural-language query
        Examples:
            search_web(query="Bestes italienisches Restaurant in München")
            search_web(query="Biergarten Öffnungszeiten in Freiburg")

    Returns:
        Markdown string with top search results.
    """
    with DDGS(timeout=15) as ddgs:
        results = ddgs.text(query, max_results=5, backend="duckduckgo", region="de-de")
        hits = list(results)

    return "\n\n".join(
        [f'URL: {hit["href"]} : {hit["body"]}' for idx, hit in enumerate(hits)]
    )


@tool
def fetch_url(url: str, timeout: float = 15.0) -> str:
    """
    Fetch a URL and return its contents as Markdown.

    This function downloads the resource at the given URL and converts it
    into Markdown when possible.

    Behavior:
    - HTML pages are cleaned and converted to Markdown.
    - Plain text responses are returned unchanged.
    - Unsupported binary content types (for example images or PDFs) raise
      a ValueError.

    Args:
        url: The absolute URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        The fetched content as a Markdown string.

    Raises:
        requests.RequestException:
            If the HTTP request fails, times out, or returns an invalid response.
        ValueError:
            If the response content type is not supported for Markdown conversion.

    Example:
        >>> fetch_url_as_markdown("https://example.com")
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" in content_type:
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove elements that usually do not belong in the main content.
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()

        markdown = html_to_markdown(str(soup), heading_style="ATX").strip()
        return markdown

    if "text/plain" in content_type or "text/markdown" in content_type:
        return response.text.strip()

    return f"Failed to fetch and convert website for '{url}'"


@tool
def search_image(query: str):
    """
    Find one image for the given German query using DuckDuckGo.

    Args:
        query: natural-language query
        Examples:
            search_image(query="Blick vom Großglockner")

    Returns:
        URL of the image
    """

    with DDGS() as ddgs:
        hits = list(
            ddgs.images(
                query,
                max_results=1,
                region="de-de",
                backend="duckduckgo",
                safesearch="on",
            )
        )

    return hits[0].get("image")

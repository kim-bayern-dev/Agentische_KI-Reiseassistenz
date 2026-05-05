import datetime
from langchain.tools import tool


@tool
def time_now() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return (
        datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"
    )

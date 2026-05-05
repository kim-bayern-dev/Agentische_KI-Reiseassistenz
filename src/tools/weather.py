import requests, datetime
from typing import Optional
from langchain.tools import tool

from mapping.poi_search import poi_search

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _weather_code_to_text(code: int) -> str:
    return WMO_WEATHER_CODES.get(code, f"Unknown weather code ({code})")


@tool
def get_weather(city: str, date: Optional[str] = None, days: int = 1) -> str:
    """
    Return weather forecast for a city.
    Works only in English.

    Examples:
        get_weather(city="Munich, Germany")
        get_weather(city="Munich, Germany", date="2026-04-03")
        get_weather(city="New York, USA", days=3)
        get_weather(city="Porto, Portugal", date="2026-04-05", days=2)

    Args:
        city (str): City, Country name.
        date (Optional[str]): Start date in ISO format YYYY-MM-DD.
            Defaults to today.
        days (int): Number of forecast days starting from `date`.
            Must be at least 1.

    Returns:
        str: Weather summary or forecast.
    """
    if days < 1:
        return "Parameter 'days' must be at least 1."

    # Parse date
    if date is None:
        start_date = datetime.date.today()
    else:
        try:
            start_date = datetime.date.fromisoformat(date)
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."

    # Geocode city
    lat, lon, resolved_name = poi_search(city)
    if lat is None or lon is None:
        return f"Could not geocode city: {city}"

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max,"
                    "weathercode"
                ),
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=15,
        )
        response.raise_for_status()
        w = response.json()
    except requests.RequestException as e:
        return f"Weather API request failed: {e}"

    daily = w.get("daily")
    if not daily:
        return f"No daily forecast available for {city}."

    times = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    weather_codes = daily.get("weathercode", [])

    if not times:
        return f"No forecast dates returned for {city}."

    requested_dates = [
        (start_date + datetime.timedelta(days=i)).isoformat() for i in range(days)
    ]

    available_dates = set(times)
    missing_dates = [d for d in requested_dates if d not in available_dates]
    if missing_dates:
        return (
            f"Forecast not available for all requested dates in {resolved_name or city}. "
            f"Missing: {', '.join(missing_dates)}"
        )

    lines = [f"Weather forecast for {resolved_name or city}:"]

    # Include current weather only if today is part of the request
    today = datetime.date.today().isoformat()
    if today in requested_dates and "current_weather" in w:
        current = w["current_weather"]
        current_temp = current.get("temperature")
        current_code = current.get("weathercode")
        if current_temp is not None:
            current_desc = (
                _weather_code_to_text(current_code)
                if current_code is not None
                else "Unknown"
            )
            lines.append(f"- Current ({today}): {current_temp:.1f} °C, {current_desc}")

    for d in requested_dates:
        idx = times.index(d)
        hi = max_temps[idx]
        lo = min_temps[idx]
        pop = precip_probs[idx]
        code = weather_codes[idx]
        desc = _weather_code_to_text(code)

        lines.append(
            f"- {d}: {desc}, High/Low {hi:.1f} °C / {lo:.1f} °C, "
            f"Precip chance {pop}%"
        )

    return "\n".join(lines)

import re
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

WEATHER_CODES = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Moderate drizzle 🌦️",
    55: "Dense drizzle 🌧️",
    61: "Slight rain 🌧️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Slight snow 🌨️",
    73: "Moderate snow 🌨️",
    75: "Heavy snow ❄️",
    80: "Slight rain showers 🌦️",
    81: "Moderate rain showers 🌧️",
    82: "Violent rain showers ⛈️",
    95: "Thunderstorm ⛈️",
    96: "Thunderstorm with slight hail ⛈️",
    99: "Thunderstorm with heavy hail ⛈️"
}

def extract_city_from_query(query: str) -> str:
    """
    Extracts the city name from a weather query, defaulting to Bengaluru (Gnani.ai HQ).
    """
    clean = query.strip()
    # Match patterns like "weather in [City]", "weather of [City]", "weather at [City]"
    match = re.search(r"weather\s+(?:in|of|at|for)\s+([a-zA-Z\s]+)", clean, re.IGNORECASE)
    if match:
        city = match.group(1).strip().strip("?.!,")
        # Remove trailing words like "today", "now", "currently", "tomorrow"
        city = re.sub(r"\b(today|now|currently|tomorrow|please|report|forecast)\b", "", city, flags=re.IGNORECASE).strip()
        if city:
            return city

    # Check for known prominent cities in query
    common_cities = ["bengaluru", "bangalore", "chennai", "mumbai", "delhi", "hyderabad", "pune", "kolkata", "new york", "san francisco", "london"]
    query_lower = clean.lower()
    for c in common_cities:
        if c in query_lower:
            return "Bengaluru" if c == "bangalore" else c.title()

    # Default to Gnani.ai's headquarters location
    return "Bengaluru"

def get_live_weather(city: str) -> Optional[Dict[str, Any]]:
    """
    Fetches live weather using Open-Meteo Geocoding & Weather APIs (free, keyless).
    """
    try:
        # Step 1: Geocode city name to lat/long
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        with httpx.Client(timeout=6.0) as client:
            geo_res = client.get(geo_url)
            if geo_res.status_code != 200:
                return None
            geo_data = geo_res.json()
            if not geo_data.get("results"):
                return None
            
            top_result = geo_data["results"][0]
            lat = top_result["latitude"]
            lon = top_result["longitude"]
            resolved_city = top_result.get("name", city)
            country = top_result.get("country", "")

            # Step 2: Fetch current weather
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            )
            weather_res = client.get(weather_url)
            if weather_res.status_code != 200:
                return None
            
            w_data = weather_res.json()
            current = w_data.get("current", {})
            w_code = current.get("weather_code", 0)
            condition = WEATHER_CODES.get(w_code, "Partly Cloudy ⛅")

            return {
                "city": resolved_city,
                "country": country,
                "temperature_c": current.get("temperature_2m"),
                "humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "condition": condition
            }
    except Exception as e:
        logger.warning(f"Failed to fetch live weather for {city}: {e}")
        return None


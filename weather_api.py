"""
Weather API Client using Open-Meteo (free, no API key needed)
"""
from typing import Optional, Dict
import requests
from requests.exceptions import RequestException

# WMO Weather Code → human-readable condition
WMO_CONDITIONS = {
    0: "Clear",
    1: "Mostly Clear",
    2: "Partly Cloudy",
    3: "Cloudy",
    45: "Foggy",
    48: "Foggy",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Freezing Drizzle",
    57: "Freezing Drizzle",
    61: "Rain",
    63: "Rain",
    65: "Heavy Rain",
    66: "Freezing Rain",
    67: "Freezing Rain",
    71: "Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Showers",
    81: "Showers",
    82: "Heavy Showers",
    85: "Snow Showers",
    86: "Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}


class WeatherClient:
    """Client for fetching weather data from Open-Meteo API."""

    def __init__(self, lat: float = 41.8781, lon: float = -87.6298):
        self.lat = lat
        self.lon = lon
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def get_weather(self) -> Optional[Dict]:
        """
        Fetch current weather and daily high/low for Chicago.

        Returns:
            Dict with keys: temp, high, low, condition
            Returns None if API call fails
        """
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": "temperature_2m,weather_code,is_day",
            "daily": "temperature_2m_max,temperature_2m_min",
            "temperature_unit": "fahrenheit",
            "timezone": "America/Chicago",
            "forecast_days": 1,
        }

        try:
            r = requests.get(self.base_url, params=params, timeout=10)
            r.raise_for_status()
        except RequestException as e:
            print(f"Error talking to Open-Meteo API: {e}")
            return None

        try:
            data = r.json()
            current = data["current"]
            daily = data["daily"]

            weather_code = current["weather_code"]
            condition = WMO_CONDITIONS.get(weather_code, "Unknown")

            return {
                "temp": round(current["temperature_2m"]),
                "high": round(daily["temperature_2m_max"][0]),
                "low": round(daily["temperature_2m_min"][0]),
                "condition": condition,
                "weather_code": weather_code,
                "is_day": bool(current.get("is_day", 1)),
            }
        except Exception as e:
            print(f"Error parsing Open-Meteo response: {e}")
            return None

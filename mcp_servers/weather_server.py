import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENMETEO_API_BASE = "https://api.open-meteo.com/v1"
GEOCODING_API_BASE = "https://geocoding-api.open-meteo.com/v1"
USER_AGENT = "weather-news-agent/1.0"

WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
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


class WeatherMCPServer:
    def __init__(self):
        self.headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async def _make_request(self, url: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                return None
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None

    async def _geocode_city(self, city: str) -> dict[str, Any] | None:
        url = f"{GEOCODING_API_BASE}/search?name={city}&count=1&language=en&format=json"
        data = await self._make_request(url)

        if not data or "results" not in data or len(data["results"]) == 0:
            logger.warning(f"Could not geocode city: {city}")
            return None

        result = data["results"][0]
        return {
            "name": result.get("name", city),
            "country": result.get("country", ""),
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "timezone": result.get("timezone", "auto"),
        }

    async def get_weather(self, city: str) -> str:
        logger.info(f"Getting weather for city: {city}")

        location = await self._geocode_city(city)
        if not location:
            return f"Could not find location: {city}. Please check the city name."

        url = (
            f"{OPENMETEO_API_BASE}/forecast?"
            f"latitude={location['latitude']}&longitude={location['longitude']}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m"
            f"&timezone={location['timezone']}"
        )

        data = await self._make_request(url)
        if not data or "current" not in data:
            return f"Unable to fetch weather data for {city}."

        current = data["current"]
        weather_code = current.get("weather_code", 0)
        condition = WEATHER_CODE_DESCRIPTIONS.get(weather_code, "Unknown")

        return f"""**Current Weather in {location["name"]}, {location["country"]}**

🌡️ **Temperature:** {current.get("temperature_2m", "N/A")}°C (Feels like: {current.get("apparent_temperature", "N/A")}°C)
☁️ **Condition:** {condition}
💧 **Humidity:** {current.get("relative_humidity_2m", "N/A")}%
🌧️ **Precipitation:** {current.get("precipitation", 0)} mm
💨 **Wind:** {current.get("wind_speed_10m", "N/A")} km/h
"""

    async def get_forecast(self, city: str, days: int = 3) -> str:
        logger.info(f"Getting {days}-day forecast for city: {city}")

        location = await self._geocode_city(city)
        if not location:
            return f"Could not find location: {city}. Please check the city name."

        url = (
            f"{OPENMETEO_API_BASE}/forecast?"
            f"latitude={location['latitude']}&longitude={location['longitude']}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
            f"precipitation_probability_max,weather_code"
            f"&timezone={location['timezone']}"
            f"&forecast_days={min(days, 7)}"
        )

        data = await self._make_request(url)
        if not data or "daily" not in data:
            return f"Unable to fetch forecast data for {city}."

        daily = data["daily"]
        forecast_lines = [f"**{days}-Day Forecast for {location['name']}, {location['country']}**\n"]

        for i in range(len(daily.get("time", []))):
            date = daily["time"][i]
            max_temp = daily["temperature_2m_max"][i]
            min_temp = daily["temperature_2m_min"][i]
            precip = daily["precipitation_sum"][i]
            precip_prob = daily["precipitation_probability_max"][i]
            weather_code = daily["weather_code"][i]
            condition = WEATHER_CODE_DESCRIPTIONS.get(weather_code, "Unknown")

            forecast_lines.append(
                f"📅 **{date}:** {condition}\n   🌡️ {min_temp}°C - {max_temp}°C | 🌧️ {precip}mm ({precip_prob}% chance)"
            )

        return "\n".join(forecast_lines)

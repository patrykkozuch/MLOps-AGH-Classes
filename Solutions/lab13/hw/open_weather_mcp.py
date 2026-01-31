import json
import os
import dotenv
from typing import Annotated, Optional

import requests
from fastmcp import FastMCP
from geopy import Nominatim

dotenv.load_dotenv()

mcp = FastMCP("Weather forecast tools")

def decode_city(city: str) -> Optional[int]:
    geolocator = Nominatim(user_agent="open_weather_mcp")
    location = geolocator.geocode(city)
    if location:
        return location.longitude, location.latitude
    else:
        return None

@mcp.tool(description="Get weather forecast for a city up to 16 days.")
def get_daily_forecast(
    city: Annotated[str, "City name, e.g., London"],
    days: Annotated[Optional[int], "Number of days (1-16)"] = 5
) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY", "")

    coords = decode_city(city)

    if not coords:
        return "City not found"

    lon, lat = coords

    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={days}&appid={api_key}&units=metric"
    )
    response.raise_for_status()

    return response.text

@mcp.tool(description="Get monthly average weather for a city.")
def get_monthly_average_weather(
    city: Annotated[str, "City name, e.g., London"],
    month: Annotated[int, "Number of the month (1-12)"]
) -> Annotated[str, "Monthly average weather data in JSON format. Temperature is in Kelvin."]:
    api_key = os.getenv("OPENWEATHER_API_KEY", "")

    coords = decode_city(city)

    if not coords:
        return "City not found"

    lon, lat = coords

    response = requests.get(
        f"https://history.openweathermap.org/data/2.5/aggregated/month?lat={lat}&lon={lon}&month={month}&appid={api_key}"
    )
    response.raise_for_status()

    data = response.json()

    for key, temp in data["result"]["temp"].items():
        data["result"]["temp"][key] = data["result"]["temp"][key] - 273.15

    return json.dumps(data)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Init server
mcp = FastMCP("weather")

# Consts
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weaher-app/1.0"


async def make_nws_request(url:str) -> dict[str, Any] | None:
    # Make request to NWS API
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=3.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data from NWS API: {e}")
            return None


def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f"""
            Event: {props.get('event', 'Unknown')}
            Area: {props.get('areaDesc', 'Unknown')}
            Severity: {props.get('severity', 'Unknown')}
            Description: {props.get('description', 'No description available')}
            Instructions: {props.get('instruction', 'No specific instructions provided')}
            """



# MCP tools
@mcp.tool()
async def get_alerts(state: str) -> str:
    # Get weather alerts for a specific state
    # Args: state (str): State code (e.g., "CA" for California)
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "No active alerts found or unable to fetch data."
    
    if not data["features"]:
        return "No active alerts found for the specified state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    # Get weather forecast for a specific location
    # Args: latitude (float): Latitude of the location
    #       longitude (float): Longitude of the location
    
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch forecast data."

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
                    {period['name']}:
                    Temperature: {period['temperature']}°{period['temperatureUnit']}
                    Wind: {period['windSpeed']} {period['windDirection']}
                    Forecast: {period['detailedForecast']}
                    """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)



if __name__ == "__main__":
    mcp.run(transport="stdio")

from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


@mcp.tool()
async def make_call(url: str):
    """This makes a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def format_alerts(data: dict) -> list[dict]:
    """
    Takes in NWS GeoJSON alert data and returns a simplified list of alerts
    with the most relevant information extracted.
    """
    alerts = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})  # NWS uses "properties" not "props"
        alert = {
            "id": props.get("id"),
            "event": props.get("event"),
            "area": props.get("areaDesc"),
            "sent": props.get("sent"),
            "effective": props.get("effective"),
            "onset": props.get("onset"),
            "expires": props.get("expires"),
            "ends": props.get("ends"),
            "severity": props.get("severity"),
            "certainty": props.get("certainty"),
            "urgency": props.get("urgency"),
            "headline": props.get("headline"),
            "description": props.get("description"),
            "instruction": props.get("instruction"),
            "sender": props.get("senderName"),
            "response": props.get("response"),
        }
        alerts.append(alert)

    return alerts


@mcp.tool()
async def get_alert(state: str) -> Any:
    """
    This function fetches alerts data for a particular state.
    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_call(url=url)

    if not data or "error" in data:
        return "Unable to get alert"

    if not data.get("features"):
        return "No active alerts"

    return await format_alerts(data)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")

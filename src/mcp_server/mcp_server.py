import requests
import json
from json_repair import repair_json
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("Web Tool Server")


@mcp.tool(
    name="crawl_to_markdown",
    description="Crawl a web page and convert it to markdown",
)
def crawl_to_markdown(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return text


@mcp.tool(
    name="geocode_address",
    description="Convert an address to geographic coordinates using OpenStreetMap",
)
def geocode_address(addresses: str) -> str:
    if not isinstance(addresses, str):
        addresses = str(addresses)
    addresses = repair_json(addresses)
    addresses_data = json.loads(addresses)
    default = {
        "geocoded_locations": [
            x | {"latitude": 0.0, "longitude": 0.0}
            for x in addresses_data.get("addresses", [])
        ]
    }
    try:
        output = []
        for address_object in addresses_data.get("addresses", []):
            address_string = f"{address_object.get('address', '')}, "
            address_string += f"{address_object.get('city', '')}, "
            address_string += f"{address_object.get('state', '')}, "
            address_string += f"{address_object.get('zip', '')}, "
            address_string += f"{address_object.get('country', '')}"
            output_ = {
                "address": address_object.get("address", ""),
                "city": address_object.get("city", ""),
                "state": address_object.get("state", ""),
                "zip": address_object.get("zip", ""),
                "country": address_object.get("country", ""),
            }
            endpoint = "https://nominatim.openstreetmap.org/search"
            params = {"q": address_string, "format": "json", "limit": 1}
            headers = {"User-Agent": "MCP-GeocodingService/1.0"}
            response = requests.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if not data:
                output_["latitude"] = 0.0
                output_["longitude"] = 0.0
            else:
                result = data[0]
                output_["latitude"] = str(result["lat"])
                output_["longitude"] = str(result["lon"])
            output.append(output_)
        return json.dumps({"geocoded_locations": output})
    except Exception as e:
        return json.dumps(default)


if __name__ == "__main__":
    mcp.run(transport="stdio")

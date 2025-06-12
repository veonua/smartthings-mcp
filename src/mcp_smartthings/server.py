from os import environ
from typing import List
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from api import (
    CapabilitiesMode,
    Capability,
    ComponentCategory,
    ConnectionType,
    Location,
)

load_dotenv()
token = environ.get("TOKEN")
if token is None:
    raise ValueError("TOKEN environment variable must be set")
location = Location(token)

# Create server
mcp = FastMCP("SmartThings")


@mcp.tool(description="Get rooms UUID and names")
def get_rooms() -> dict[UUID, str]:
    return location.rooms


@mcp.tool(description="Get devices")
def get_devices(
    capability: List[Capability] | None = None,
    capabilities_mode: CapabilitiesMode | None = None,
    include_restricted: bool = False,
    room_id: UUID | None = None,
    include_health: bool = True,
    include_status: bool = True,
    category: ComponentCategory | None = None,
    connection_type: ConnectionType | None = None,
):
    return location.get_devices_short(**locals())


@mcp.tool(description="Get device status")
def get_device_status(device_id: UUID):
    return location._device_status(device_id)


if __name__ == "__main__":
    """Run the FastMCP server."""
    mcp.run()


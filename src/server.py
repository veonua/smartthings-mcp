from datetime import datetime
from os import environ
from typing import List, Literal, Optional
from uuid import UUID
import logging 

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from api import (
    Attribute,
    CapabilitiesMode,
    Capability,
    Command,
    ComponentCategory,
    ConnectionType,
    Location,
)

load_dotenv()
token = environ.get("TOKEN")
if token is None:
    raise ValueError("TOKEN environment variable must be set")
location = Location(token)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create server
mcp = FastMCP("SmartThings", port=8001)


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
    """Get devices in the location"""
    return location.get_devices_short(**locals())


@mcp.tool(description="Get device status")
def get_device_status(device_id: UUID):
    logger.info(f"Getting status for device {device_id}")
    return location.device_status(device_id)


@mcp.tool(description="Execute commands on a device")
def execute_commands(device_id: UUID, commands: List[Command]):
    """Send SmartThings commands to a device.
    Hints:
        first component of a device is usually 'main', but there might be 2-3 switches.

    """
    logger.info(f"Executing commands on device {device_id}: {commands}")
    return location.device_commands(device_id, commands)


@mcp.tool(description="Answer questions about past values or trends")
def get_device_history(
    *,
    device_id: Optional[UUID] = None,
    room_id:   Optional[UUID] = None,
    attribute: Attribute,
    start: datetime,
    end: datetime,
    granularity: Literal["realtime", "5min", "hourly", "daily"] = "hourly",
    aggregate:   Literal["raw", "sum", "avg", "min", "max"]   = "raw",
) -> List[dict]:
    """
    LLM-guidance
    ------------
    • Pick **one** of `device_id` or `room_id` (not both).  
      – `device_id` → history for that device only.  
      – `room_id`   → MCP auto-aggregates across devices in the room.  
    • Use when the user asks how something has changed *over time* or wants
      an average/graph for a past period.  
    • `metric` must match a path from *Get Device Status*  
      (e.g. "powerMeter.power", "temperature.value").  
    • Cap the returned set to ≲500 points; raise `granularity` as needed.
    """
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    if (room_id is not None):
        raise NotImplementedError("Room-based history aggregation is not implemented yet.")

    return location.event_history(
        device_id=device_id,
        attribute=attribute,
        limit=500,
        paging_after_epoch=start_ms,
        paging_before_epoch=end_ms,
    )

@mcp.tool(description="Get hub time")
def get_hub_time() -> str:
    """Get the current time of the hub."""
    import datetime
    now = datetime.datetime.now(location.timezone)
    return f"{now} Timezone: {location.timezone}"

if __name__ == "__main__":
    """Run the FastMCP server."""
    mcp.run(transport="sse")


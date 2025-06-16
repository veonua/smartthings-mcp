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


@mcp.tool(description="Answer questions about past values or trends. Use ISO8601 Duration for `delta_start` and `delta_end` (e.g. P1D for 1 day, PT1H for 1 hour).")
def get_device_history(
    *,
    device_id: Optional[UUID] = None,
    room_id:   Optional[UUID] = None,
    attribute: Attribute,
    delta_start: str,
    delta_end: str | None = None,
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
    • Use ISO8601 Duration for `delta_start` and `delta_end` (e.g. "P1D" for 1 day, "PT1H" for 1 hour).
    • If `delta_end` is not provided, it defaults to now.

    """
    import time    
    import isodate

    epoch_time = int(time.time())

    start_delta = isodate.parse_duration(delta_start)
    start_s = epoch_time - int(start_delta.total_seconds())
    
    end_s = epoch_time
    if delta_end is not None:
        end_delta = isodate.parse_duration(delta_end)
        end_s = epoch_time - int(end_delta.total_seconds())

    start_ms = start_s * 1000  # Convert to milliseconds
    end_ms = end_s * 1000

    if room_id is not None:
        return location.room_history(
            room_id=room_id,
            attribute=attribute,
            start_ms=start_ms,
            end_ms=end_ms,
            granularity=granularity,
            aggregate=aggregate,
        )

    return location.event_history(
        device_id=device_id,
        attribute=attribute,
        limit=500,
        #paging_after_epoch=start_ms,
        #paging_before_epoch=end_ms,
    )

@mcp.tool(description="Get hub time")
def get_hub_time() -> str:
    """Get the current time of the hub."""
    now = datetime.now(location.timezone)
    return f"{now} Timezone: {location.timezone}"

if __name__ == "__main__":
    """Run the FastMCP server."""
    mcp.run(transport="sse")


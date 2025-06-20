from datetime import datetime
from os import environ
from typing import List, Literal, Optional
from uuid import UUID
import logging
from mcp.types  import ToolAnnotations

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


@mcp.tool(description="Get rooms UUID and names", annotations=ToolAnnotations(
    title="Get Smart Home Rooms",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False)
)
def get_rooms() -> dict[UUID, str]:
    return location.rooms


@mcp.tool(description="""
Retrieve devices based on specified filtering criteria.

Parameters:
- capability: Optional list of capabilities that devices must have (e.g., ['switch', 'temperatureMeasurement']).
- capabilities_mode: Defines how multiple capabilities are matched ('or' returns devices matching any capability, 'and' returns devices matching all specified capabilities). Default is 'or'.
- include_restricted: Include restricted devices in the results. Default is False.
- room_id: Filter devices by a specific room identifier.
- include_status: Include device status information in the response. Default is True.
- category: Filter devices by their component category.
- connection_type: Filter devices by their connection type (e.g., Wi-Fi, Zigbee).
""", annotations=ToolAnnotations(
    title="Get Smart Home Devices",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False)
)
def get_devices(
    capability: List[Capability] | None = None,
    capabilities_mode: CapabilitiesMode | None = 'or',
    include_restricted: bool = False,
    room_id: UUID | None = None,
    include_status: bool = True,
    category: ComponentCategory | None = None,
    connection_type: ConnectionType | None = None,
):
    """Get devices in the location"""
    return location.get_devices_short(**locals())


@mcp.tool(description="Get device status", annotations=ToolAnnotations(
    title="Get Device Status",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False)
)
def get_device_status(device_id: UUID):
    logger.info(f"Getting status for device {device_id}")
    return location.device_status(device_id)


@mcp.tool(description="Execute commands on a device", annotations=ToolAnnotations(
    title="Execute Device Commands",
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False)
)
def execute_commands(device_id: UUID, commands: List[Command]):
    """Send SmartThings commands to a device.
    Hints:
        first component of a device is usually 'main', but there might be 2-3 switches.

    """
    logger.info(f"Executing commands on device {device_id}: {commands}")
    return location.device_commands(device_id, commands)


@mcp.tool(description="Answer questions about past values or trends. Use ISO8601 Duration for `delta_start` and `delta_end` (e.g. P1D for 1 day, PT1H for 1 hour).",
          annotations=ToolAnnotations(
    title="Get Device History",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False)
    )
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
    return location.history(
        device_id=device_id,
        room_id=room_id,
        attribute=attribute,
        delta_start=delta_start,
        delta_end=delta_end,
        granularity=granularity,
        aggregate=aggregate,
    )

@mcp.tool(description="Get hub time")
def get_hub_time() -> str:
    """Get the current time of the hub."""
    now = datetime.now(location.timezone)
    return f"{now} Timezone: {location.timezone}"

if __name__ == "__main__":
    """Run the FastMCP server."""
    mcp.run(transport="sse")


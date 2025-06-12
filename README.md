# smartthings-mcp

This project provides a small [Model Context Protocol](https://github.com/smartthings/mcp) server exposing a few SmartThings helper tools.

```json
"mcpServers": {
  "SmartThings": {
    "type": "stdio",
    "command": "uv",
    "args": [
        "run",
        "src/mcp_smartthings/server.py"
    ],
    "env": {
        "TOKEN": "Your Personal Token"
    }
  }
}
```

## Docker

A `Dockerfile` is included for convenience. Build and run the image with:

```bash
docker build -t smartthings-mcp .
docker run -e TOKEN=<api token> smartthings-mcp
```

The container installs the production dependencies using `uv` and launches the server with `uv run src/mcp_smartthings/server.py`.

## Available tools

The server exposes the following MCP tools:

- `get_rooms` – return a mapping of room UUIDs to names.
- `get_devices` – list devices with optional filtering.
- `get_device_status` – fetch status for a device by UUID.
- `execute_commands` – send commands to a device.

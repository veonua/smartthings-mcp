# smartthings-mcp

This project provides a small [Model Context Protocol](https://github.com/smartthings/mcp) server exposing a few SmartThings helper tools.

## Installing dependencies

Use [uv](https://github.com/astral-sh/uv) to install the dependencies declared in `pyproject.toml` and `uv.lock`:

```bash
uv pip install --system --verbose
```

To run the tests:

```bash
uv pip install --system --dev --verbose
pytest -q
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

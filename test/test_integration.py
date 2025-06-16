import os
import pytest
import dotenv

from src.api import Location

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN", "")

pytestmark = pytest.mark.skipif(not TOKEN, reason="TOKEN environment variable not set")


def _get_location():
    return Location(TOKEN)


def test_fetch_devices():
    loc = _get_location()
    devices = loc.get_devices_short()
    assert isinstance(devices, list)
    assert devices, "no devices returned"
    assert "deviceId" in devices[0]


def test_event_history():
    loc = _get_location()
    devices = loc.get_devices_short()
    if not devices:
        pytest.skip("no devices available")
    first_device_id = devices[0]["deviceId"]
    history = loc.event_history(device_id=first_device_id, limit=1)
    assert len(history) == 1
    assert "deviceId" in history[0]


def test_room_history():
    loc = _get_location()
    rooms = loc.rooms
    if not rooms:
        pytest.skip("no rooms available")

    first_room_id = next(iter(rooms.keys()))
    history = loc.room_history(room_id=first_room_id)
    assert len(history) > 0
    assert "time" in history[0]


def test_device_status():
    loc = _get_location()
    devices = loc.get_devices_short()
    if not devices:
        pytest.skip("no devices available")
    for dev in devices:
        status = loc.device_status(dev["deviceId"])
        assert isinstance(status, dict)
        assert status, "no status returned"
        assert "main" in status

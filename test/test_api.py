import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from mcp_smartthings.api import Command, Location, BASE_URL

noRoomId = uuid.UUID("00000000-0000-0000-0000-000000000000")
room1Id = uuid.UUID("00000000-0000-0000-0000-000000000001")

def _make_location():
    loc = object.__new__(Location)
    loc.location_id = "loc1"
    loc.rooms = {room1Id: "Room 1"}
    loc.device_ids = set()
    return loc


def test_get_status_none():
    assert Location.get_status(None) == ("?", None, None, None)
    assert Location.get_status({}) == ("?", None, None, None)


def test_get_status_valid():
    status = {
        "supportedValues": [],
        "temperature": {"value": 20, "unit": "C", "timestamp": "t"},
    }
    assert Location.get_status(status) == ("temperature", 20, "C", "t")



def test_get_devices_url(monkeypatch):
    loc = _make_location()

    captured = {}

    def fake_get(url):
        captured["url"] = url
        return ["ok"]

    loc._get_devices = fake_get

    res = loc.get_devices(
        capability="motionSensor",
        capabilities_mode="or",
        include_restricted=True,
        room_id=room1Id,
        include_health=False,
        include_status=True,
        category="Light",
        connection_type="LAN",
    )

    assert res == ["ok"]
    expected_url = (
        f"{BASE_URL}devices?locationId=loc1"
        "&capability=motionSensor"
        "&category=Light"
        "&capabilitiesMode=or"
        "&includeRestricted=true"
        f"&roomId={room1Id}"
        "&includeStatus=true"
        "&type=LAN"
    )
    assert captured["url"] == expected_url


def test_get_devices_invalid(monkeypatch):
    loc = _make_location()
    loc._get_devices = lambda url: []
    with pytest.raises(ValueError):
        loc.get_devices(capability="unknown")
    with pytest.raises(ValueError):
        loc.get_devices(room_id=noRoomId)


def test_device_commands(monkeypatch):
    loc = _make_location()
    valid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    loc.device_ids = {valid}

    captured = {}

    def fake_post(device_id, commands):
        captured["device_id"] = device_id
        captured["commands"] = commands
        return {"status": "ok"}

    loc._device_commands = fake_post

    cmds = [Command(component="main", capability="switch", command="on", arguments=[])]
    res = loc.device_commands(valid, cmds)

    assert res == {"status": "ok"}
    assert captured["device_id"] == valid
    assert captured["commands"] == cmds


def test_validate_device_id():
    loc = _make_location()
    valid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    loc.device_ids = {valid}

    assert loc.validate_device_id(valid) == valid

    with pytest.raises(ValueError):
        loc.validate_device_id("not-a-uuid")

    with pytest.raises(ValueError):
        loc.validate_device_id(uuid.UUID("22222222-2222-2222-2222-222222222222"))


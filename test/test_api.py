import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from mcp_smartthings.api import Location, BASE_URL


def _make_location():
    loc = object.__new__(Location)
    loc.headers = {}
    loc.location_id = "loc1"
    loc.rooms = {"r1": "Room 1"}
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


def test_rooms_df(monkeypatch):
    loc = _make_location()
    loc._rooms = lambda: {"items": [{"roomId": "r1", "name": "Room 1"}]}
    df = loc.rooms_df()
    assert df.to_dict(orient="records") == [{"roomId": "r1", "name": "Room 1"}]


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
        room_id="r1",
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
        "&roomId=r1"
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
        loc.get_devices(room_id="bad")

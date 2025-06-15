import os
import sys
import uuid
import datetime
import math

import pytest

from src.st.device import DeviceItem

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.api import Command, Location, _bucket_time, _aggregate_values

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
        devices: list[DeviceItem] = []
        return devices

    loc._get_devices = fake_get

    res = loc.get_devices(
        capability="motionSensor",
        capabilities_mode="or",
        include_restricted=True,
        room_id=room1Id,
        include_status=True,
        category="Light",
        connection_type="LAN",
    )

    assert res == []
    expected_url = (
        f"devices?locationId=loc1"
        "&capability=motionSensor"
        "&category=Light"
        "&capabilitiesMode=or"
        "&includeRestricted=true"
        f"&roomId={room1Id}"
        "&includeStatus=true"
        "&type=LAN"
    )
    assert captured["url"] == expected_url

# pyright: ignore
def test_get_devices_invalid(monkeypatch):
    loc = _make_location()
    loc._get_devices = lambda url: []
    with pytest.raises(ValueError):
        loc.get_devices(capability="unknown")  # type: ignore
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
        loc.validate_device_id("not-a-uuid")  # type: ignore

    with pytest.raises(ValueError):
        loc.validate_device_id(uuid.UUID("22222222-2222-2222-2222-222222222222"))


def test_bucket_time():
    ts = datetime.datetime(2025, 6, 15, 12, 34, 56)
    assert _bucket_time(ts, "realtime") == ts
    assert _bucket_time(ts, "5min") == ts.replace(minute=30, second=0, microsecond=0)
    assert _bucket_time(ts, "hourly") == ts.replace(minute=0, second=0, microsecond=0)
    assert _bucket_time(ts, "daily") == ts.replace(hour=0, minute=0, second=0, microsecond=0)
    with pytest.raises(ValueError):
        _bucket_time(ts, "bogus") # type: ignore


def test_aggregate_values():
    values = [1.0, 2.0, 3.0]
    assert _aggregate_values(values, "sum") == 6.0
    assert _aggregate_values(values, "avg") == 2.0
    assert _aggregate_values(values, "min") == 1.0
    assert _aggregate_values(values, "max") == 3.0
    assert math.isnan(_aggregate_values([], "avg"))
    with pytest.raises(ValueError):
        _aggregate_values(values, "bogus") # type: ignore


def test_room_history_raw(monkeypatch):
    loc = _make_location()
    loc.get_devices_short = lambda **kwargs: [  # type: ignore
        {"deviceId": "dev1"},
        {"deviceId": "dev2"},
    ]
    base = datetime.datetime(2025, 1, 1, 12, 0, 0)
    events = {
        "dev1": [{"time": base, "value": 1}],
        "dev2": [{"time": base + datetime.timedelta(minutes=3), "value": 2}],
    }

    def fake_event_history(device_id, *args, **kwargs):
        return events[device_id]

    loc.event_history = fake_event_history # type: ignore

    res = loc.room_history(
        room_id=room1Id,
        attribute="temperature",
        start_ms=0,
        end_ms=0,
        granularity="realtime",
        aggregate="raw",
    )
    assert res == [
        {"time": base, "value": 1.0},
        {"time": base + datetime.timedelta(minutes=3), "value": 2.0},
    ]


def test_room_history_bucket_avg(monkeypatch):
    loc = _make_location()
    loc.get_devices_short = lambda **kwargs: [ # type: ignore
        {"deviceId": "dev1"},
        {"deviceId": "dev2"},
    ]
    base = datetime.datetime(2025, 1, 1, 12, 0, 0)
    events = {
        "dev1": [
            {"time": base + datetime.timedelta(minutes=1), "value": 10},
            {"time": base + datetime.timedelta(minutes=4), "value": 20},
        ],
        "dev2": [
            {"time": base + datetime.timedelta(minutes=3), "value": 30},
        ],
    }

    def fake_event_history(device_id, *args, **kwargs):
        return events[device_id]

    loc.event_history = fake_event_history # type: ignore

    res = loc.room_history(
        room_id=room1Id,
        attribute="temperature",
        start_ms=0,
        end_ms=0,
        granularity="5min",
        aggregate="avg",
    )
    assert res == [
        {"time": base, "value": pytest.approx(20.0)},
    ]

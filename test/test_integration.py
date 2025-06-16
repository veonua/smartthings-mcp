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


def test_history_p30d():
    loc = _get_location()
    devices = loc.get_devices_short()
    if not devices:
        pytest.skip("no devices available")
    first_device_id = devices[0]["deviceId"]
    history = loc.history(device_id=first_device_id, attribute="temperature", delta_start="P30D")
    assert history, "empty history for P30D"


missing_attributes = {
    'temperatureRange',  'heatingSetpointRange', 'coolingSetpointRange', 
    'quantity', 'type', # battery 
    'availableFanOscillationModes',
    'numberOfButtons', # button
    'levelRange', 'colorTemperatureRange', # switchLevel
    'driverVersion', 'fade', 'circadian',
    'commandResult', # lock
    
}

missing_capabilities = {'firmwareUpdate', 'bridge', 'healthCheck'}

def test_get_devices_with_status():
    loc = _get_location()
    devices = loc.get_devices(include_status=True)
    if not devices:
        pytest.skip("no devices available")
    for dev in devices:
        for component in dev.components:
            for capability in component.capabilities:
                if capability.id in missing_capabilities:
                    continue

                if capability.status is None:
                    pytest.fail(f"Capability {capability.id} has no status for device {dev.device_id}")
                
                for (attribute, status) in capability.status.items():
                    if attribute in missing_attributes or attribute.startswith("supported") or attribute.startswith("available"):
                        continue
                    if status.value is None:
                        print(f"Status value is None for capability {capability.id}/{attribute} in device {dev.device_id}")


def test_get_status_by_device_by_id():
    loc = _get_location()
    devices = loc.get_devices(include_status=True)
    if not devices:
        pytest.skip("no devices available")
    dev = devices.pop()
    status_dict = loc.device_status(dev.device_id)
    assert status_dict is not None, f"No status returned for device {dev.device_id}"
    for (comp_name, component_value) in status_dict.items():
        for (capability_id, capability_value) in component_value.items():
            if capability_value is None:
                pytest.fail(f"Capability {capability_id} has no status for device {dev.device_id}")

            for (attribute, status) in capability_value.items():
                if attribute in missing_attributes or attribute.startswith("supported") or attribute.startswith("available"):
                    continue
                assert status.value is not None, f"Status value is None for capability {capability_id}/{attribute} in device {dev.device_id}"
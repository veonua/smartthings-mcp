import logging
from functools import cached_property
from typing import List, Literal, Tuple
from uuid import UUID

import pandas as pd
from pydantic import BaseModel
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

BASE_URL = "https://api.smartthings.com/"

IGNORE_CAPABILITIES = {'mediaPresets', 'firmwareUpdate', 'healthCheck' 'threeAxis', 'momentary', 'refresh',
                       'windowShadePreset', 'configuration', 'bridge', 'alarm', 'statelessPowerToggleButton'}

Capability = Literal['button', 'motionSensor', 'dustSensor', 'carbonDioxideMeasurement',
    'illuminanceMeasurement', 'relativeHumidityMeasurement', 'temperatureMeasurement', 'atmosphericPressureMeasurement',
    'switch', 'signalStrength', 'powerMeter', 'presenceSensor', 'switchLevel', 'contactSensor', 'voltageMeasurement',
    'windowShade', 'windowShadeLevel', 'battery', 'lock']
CapabilitiesMode = Literal['and', 'or']
Attribute = Literal[
    'motion', 'battery', 'illuminance', 'temperature', 'tamper', 'atmosphericPressure', 'humidity', 'contact', 'power',
    'energy', 'level', 'voltage', 'rssi', 'lqi', 'shadeLevel', 'volume', 'water', 'presence', 'lock',
    'dustLevel', 'fineDustLevel', 'carbonDioxide', 'power', 'switch', 'atmosPressure',
    'button', 'presence', 'presenceStatus', 'level', 'windowShade', 'shadeLevel']
ConnectionType = Literal['LAN', 'ZIGBEE', 'ZWAVE', 'EDGE_CHILD', 'MOBILE']
ComponentCategory = Literal[
    'Light', 'AirConditioner', 'AirQualityDetector', 'Battery', 'Blind', 'BluetoothTracker', 'ContactSensor',
    'Dishwasher', 'Hub', 'LeakSensor', 'MobilePresence', 'MotionSensor', 'MultiFunctionalSensor', 'Others',
    'PresenceSensor', 'RemoteController', 'SmartLock', 'SmokeDetector',
    'Switch', 'Television', 'Thermostat']


class Command(BaseModel):
    component: str
    capability: Capability
    command: str
    arguments: list | None = None

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "capability": self.capability,
            "command": self.command,
            "arguments": self.arguments or []
        }

class ILocation: 
    def device_status(self, device_id: str) -> pd.DataFrame: 
        pass

    def event_history(self, device_id: str | None = None, limit: int = 500,
                      oldest_first: bool = False, paging_after_epoch: int | None = None, paging_after_hash: int | None = None,
                      paging_before_epoch: int | None = None, paging_before_hash: int | None = None) -> pd.DataFrame:
        pass

    @cached_property
    def rooms(self) -> dict[UUID, str]:
        """Get rooms UUID and names."""
        pass
   
    def get_room_name(self, room_id: UUID) -> str:
        pass

    def get_devices(self, capability: List[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                    include_restricted: bool = False,
                    room_id: UUID | None = None, include_health: bool = True, include_status: bool = True,
                    category: ComponentCategory | None = None,
                    type: ConnectionType | None = None):
        pass

    def get_devices_short(self, capability: List[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                          include_restricted: bool = False,
                          room_id: UUID | None = None, include_health: bool = True, include_status: bool = True,
                          category: ComponentCategory | None = None,
                          connection_type: ConnectionType | None = None):
        pass

    

class Location(ILocation):
    session : requests.Session
    
    def __init__(self, auth: str, location_id: UUID | None = None):
        self.session = requests.Session()
        self.session.headers = {
            'Accept': 'application/vnd.smartthings+json;v=20170916',
            'Authorization': "Bearer " + auth,
            # 'cache-control': "no-cache",
        }

        locations = self.session.get(BASE_URL + "v1/locations").json()

        self.location_id = location_id or locations['items'][0]['locationId']
        self.location = self._location()

        import pytz

        self.timezone = pytz.timezone(self.location['timeZoneId'])
        # self.timeZoneOffset = datetime.datetime.now(timezone).strftime('%z')

    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _location(self):
        return self.session.get(f"{BASE_URL}v1/locations/{self.location_id}").json()

    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _device_status(self, device_id: UUID | str) -> dict:
        return self.session.get(f"{BASE_URL}devices/{device_id}/status").json()[
            'components']

    def device_status(self, device_id: UUID | str) -> pd.DataFrame:
        device_id = self.validate_device_id(device_id)
        status = self._device_status(device_id)
        df = pd.DataFrame(status)
        return df

    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _event_history(self, limit: int | None = None, device_id: UUID | str | None = None,
                       oldest_first: bool = False,
                       paging_after_epoch: int | None = None, paging_after_hash: int | None = None,
                       paging_before_epoch: int | None = None, paging_before_hash: int | None = None):
        hub_id = self.location_id

        if limit is None:
            limit = 500

        url = f"{BASE_URL}v1/history/devices?locationId={hub_id}&limit={limit}"

        if paging_after_epoch is not None:
            url += f"&pagingAfterEpoch={paging_after_epoch}"
        if paging_after_hash is not None:
            url += f"&pagingAfterHash={paging_after_hash}"
        if paging_before_epoch is not None:
            url += f"&pagingBeforeEpoch={paging_before_epoch}"
        if paging_before_hash is not None:
            url += f"&pagingBeforeHash={paging_before_hash}"
        if oldest_first:
            url += "&oldestFirst=true"
        if device_id is not None:
            url += f"&deviceId={device_id}"

        return self.session.get(url).json()

    def event_history(self, device_id: str | None = None, limit: int = 500,
                      oldest_first: bool = False, paging_after_epoch: int | None = None, paging_after_hash: int | None = None,
                      paging_before_epoch: int | None = None, paging_before_hash: int | None = None) -> pd.DataFrame:
        kwargs = locals()
        kwargs.pop('self')
        events = self._event_history(**kwargs)
        df = pd.DataFrame(events['items']).drop(
            columns=['deviceName', 'componentLabel', 'text', 'epoch', 'data', 'translatedAttributeName',
                     'translatedAttributeValue', 'locationId', 'locationName', 'hash'])

        df['unit'] = df['unit'].map(lambda x: None if x == "" else x)
        return df

    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _rooms(self):
        return self.session.get(f"{BASE_URL}v1/locations/{self.location_id}/rooms").json()

    @cached_property
    def rooms(self) -> dict[UUID, str]:
        res = {}
        for r in self._rooms()['items']:
            res[UUID(r['roomId'])] = r['name']

        return res

    @cached_property
    def device_ids(self) -> set[UUID]:
        """Set of device UUIDs available in this location."""
        devices = self.get_devices_short(include_health=False, include_status=False)
        return {UUID(d['deviceId']) for d in devices}

    def validate_device_id(self, device_id: UUID | str) -> UUID:
        """Validate that a device ID exists in the location.

        Args:
            device_id: Device UUID or string representation.

        Returns:
            Normalised UUID if valid.

        Raises:
            ValueError: If the ID format is invalid or not known.
        """
        try:
            device_uuid = UUID(str(device_id))
        except (ValueError, AttributeError):
            raise ValueError(f"'{device_id}' is not a valid UUID") from None

        if device_uuid not in self.device_ids:
            raise ValueError(
                f"deviceId '{device_uuid}' is unknown, use get_devices to list valid ids"
            )

        return device_uuid

    def get_room_name(self, room_id: UUID) -> str:
        """Get room name by UUID."""
        if room_id not in self.rooms:
            raise ValueError(f"roomId '{room_id}' is unknown, must be one of {self.rooms.keys()}")
        return self.rooms[room_id]

    ###
    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _get_devices(self, url: str):
        try:
            return self.session.get(url).json()['items']
        except Exception:
            print(url)
            raise

    def get_devices(self, capability: List[Capability] | Capability | None = None, capabilities_mode: CapabilitiesMode | None = None,
                    include_restricted: bool = False,
                    room_id: UUID | None = None, include_health: bool = True, include_status: bool = True,
                    category: ComponentCategory | None = None,
                    connection_type: ConnectionType | None = None):
        url = f"{BASE_URL}devices?locationId={self.location_id}"
        if capability is not None:
            if isinstance(capability, str):
                capability = [capability]
            for c in capability:
                if c == 'humidity':
                    c = "relativeHumidityMeasurement"

                if c not in Capability.__args__:
                    raise ValueError(f"capability '{c}' is unknown, must be one of {Capability.__args__}")
                url += f"&capability={c}"

        if category is not None:
            url += f"&category={category}"

        if capabilities_mode is not None:
            if capabilities_mode not in CapabilitiesMode.__args__:
                raise ValueError(
                    f"capabilitiesMode '{capabilities_mode}' is unknown, must be one of {CapabilitiesMode.__args__}")
            url += f"&capabilitiesMode={capabilities_mode}"
        if include_restricted:
            url += "&includeRestricted=true"
        if room_id is not None:
            if not isinstance(room_id, UUID):
                room_id = UUID(room_id)
            if room_id not in self.rooms:
                raise ValueError(f"roomId '{room_id}' is unknown, must be one of {self.rooms.keys()}")
            url += f"&roomId={room_id}"
        if include_health:
            url += "&includeHealth=true"
        if include_status:
            url += "&includeStatus=true"
        if connection_type is not None:
            if connection_type not in ConnectionType.__args__:
                raise ValueError(f"type must be one of {ConnectionType.__args__}")
            url += f"&type={connection_type}"

        return self._get_devices(url)

    def get_devices_short(self, capability: List[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                          include_restricted: bool = False,
                          room_id: UUID | None = None, include_health: bool = True, include_status: bool = True,
                          category: ComponentCategory | None = None,
                          connection_type: ConnectionType | None = None):
        devices = self.get_devices(capability, capabilities_mode, include_restricted, room_id, include_health,
                                   include_status, category, connection_type)

        filtered_devices = []
        for device in devices:
            filtered_device = {'deviceId': device['deviceId'], 'label': device['label'],
                               'manufacturerName': device['manufacturerName']}

            if device.get('deviceModel') is not None:
                filtered_device['deviceModel'] = device.get('deviceModel')
            if device.get('roomId') is not None:
                filtered_device['roomId'] = device.get('roomId')
            filtered_device['components'] = []
            for component in device['components']:
                filtered_component = {'id': component['id'], 'label': component['label'], 'categories': []}
                for category in component['categories']:
                    filtered_category = {'name': category['name']}
                    filtered_component['categories'].append(filtered_category)

                filtered_component['capabilities'] = []
                for capability in component['capabilities']:
                    if '.' in capability['id'] or capability['id'] in IGNORE_CAPABILITIES:
                        continue
                    filtered_capability = {'id': capability['id']}
                    if 'status' in capability:
                        filtered_capability['status'] = {}
                        for (k, v) in capability['status'].items():
                            if k.startswith('supported') or k in {'numberOfButtons', ''}:
                                continue
                            filtered_capability['status'][k] = {}
                            filtered_capability['status'][k]['value'] = v['value']
                            if v.get('unit') is not None:
                                filtered_capability['status'][k]['unit'] = v.get('unit')
                            if v.get('timestamp') is not None:
                                filtered_capability['status'][k]['timestamp'] = v.get('timestamp')
                    filtered_component['capabilities'].append(filtered_capability)
                filtered_device['components'].append(filtered_component)
            filtered_device['createTime'] = device['createTime']
            filtered_device['healthState'] = device['healthState']
            if device.get('parentDeviceId') is not None:
                filtered_device['parentDeviceId'] = device['parentDeviceId']
            filtered_device['type'] = device['type']
            filtered_devices.append(filtered_device)

        return filtered_devices

    @staticmethod
    def get_status(status: dict| None):
        if status is None or status == {}:
            return "?", None, None, None

        for k, v in status.items():
            if k.startswith('supported') or k in {'numberOfButtons', ''}:
                continue
            return k, v['value'], v.get('unit'), v.get('timestamp')

    def devices_df(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        _devices = self.get_devices_short()

        d = [(device['deviceId'], device['components'][0]['categories'][-1]['name'], device['label'],
              # device['manufacturerName'],  device.get('deviceManufacturerCode'), device['locationId'], device['presentationId'],device['profile']['id'],  device.get('restrictionTier')
              device.get('roomId'), device['createTime'], device.get('parentDeviceId'), device['type']
              ) for device in _devices]

        c = [(device['deviceId'], component['id'], capability['id'], *self.get_status(capability.get('status'))) for
             device in _devices for component in device['components'] for capability in component['capabilities']]

        devices_df = pd.DataFrame(d, columns=['deviceId', 'category', 'name', 'roomId', 'createTime', 'parentDeviceId',
                                              'type'])  # .set_index('deviceId')
        rooms = self.rooms
        devices_df['room'] = devices_df['roomId'].map(lambda x: rooms.get(x, str(x)))
        devices_df.drop(columns=['roomId'], inplace=True)
        capabilities_df = pd.DataFrame(c, columns=['deviceId', 'component', 'capability', 'attribute', 'value', 'unit',
                                                   'timestamp'])
        return devices_df, capabilities_df

    @retry(wait=wait_random_exponential(2), stop=stop_after_attempt(5))
    def _device_commands(self, device_id: UUID, commands: list[Command]) -> dict:
        """Low level API call to execute commands on a device.
        {
          "results": [
            {
              "id": "36346e98-539c-4a22-9340-4e877a184a06",
              "status": "ACCEPTED"
            }
          ]
        }
        """
        url = f"{BASE_URL}v1/devices/{device_id}/commands"
        payload = {"commands": [cmd.to_dict() for cmd in commands]}
        response = self.session.post(url, json=payload)
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Failed to decode JSON from response: {response.text}")
            return {"error": "Failed to decode response", "status": response.status_code, "text": response.text}

    def device_commands(self, device_id: UUID, commands: list[Command]) -> dict:
        """Execute SmartThings commands on a device."""
        device_id = self.validate_device_id(device_id)
        return self._device_commands(device_id, commands)

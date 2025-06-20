import logging
from functools import cached_property
from typing import Any, List, Protocol, Dict, Union, Set
from uuid import UUID
from datetime import datetime


from st.device import DeviceItem, DeviceResponse, DeviceStatusResponse, StatusModel
from st.history import EventHistoryResponse
from st.command import Command
from st.literals import (
    Aggregate,
    Attribute,
    CapabilitiesMode,
    Capability,
    ComponentCategory,
    ConnectionType,
    Granularity,
)
from custom_session import CustomSession

logger = logging.getLogger(__name__)


IGNORE_CAPABILITIES = {'mediaPresets', 'firmwareUpdate', 'healthCheck', 'threeAxis', 'momentary', 'refresh',
                       'windowShadePreset', 'configuration', 'bridge', 'alarm', 'statelessPowerToggleButton'}


class ILocation(Protocol): 
    def device_status(self, device_id: UUID) -> dict[str, dict[Union[Capability, str], dict[Union[Attribute, str], StatusModel]]]:
        ...

    def event_history(self, device_id: UUID | None = None, limit: int = 500,
                      capability: Set[Capability] | None = None,
                      capability_mode: CapabilitiesMode | None = "or",
                      attribute: Attribute | None = None,
                      oldest_first: bool = False, paging_after_epoch: int | None = None, paging_after_hash: int | None = None,
                      paging_before_epoch: int | None = None, paging_before_hash: int | None = None) -> List[dict]:
        ...

    @cached_property
    def rooms(self) -> dict[UUID, str]:
        """Get room UUID and names."""
        ...

    def get_room_name(self, room_id: UUID) -> str:
        ...

    def get_devices(self, capability: Set[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                    include_restricted: bool = False,
                    room_id: UUID | None = None, include_status: bool = True,
                    category: ComponentCategory | None = None,
                    connection_type: ConnectionType | None = None) -> List[DeviceItem]:
        ...

    def get_devices_short(self, capability: Set[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                          include_restricted: bool = False,
                          room_id: UUID | None = None, include_status: bool = True,
                          category: ComponentCategory | None = None,
                          connection_type: ConnectionType | None = None) -> List[dict]:
        ...

    

class Location(ILocation):
    session : CustomSession
    
    def __init__(self, auth: str, location_id: UUID | None = None):
        self.session = CustomSession(auth=auth)
        self.session.headers = {
            'Accept': 'application/vnd.smartthings+json;v=20170916',
            'Authorization': "Bearer " + auth,
            # 'cache-control': "no-cache",
        }

        locations = self.session.get_json("v1/locations")
    
        self.location_id = location_id or locations['items'][0]['locationId']
        self.location = self._location()

        import pytz

        self.timezone = pytz.timezone(self.location['timeZoneId'])
        #self.timeZoneOffset = datetime.datetime.now(self.timezone).strftime('%z')

    def _location(self):
        return self.session.get_json(f"v1/locations/{self.location_id}")

    def _device_status(self, device_id: UUID) -> DeviceStatusResponse:
        return DeviceStatusResponse.model_validate(self.session.get_json(f"v1/devices/{device_id}/status"))

    def device_status(self, device_id: UUID) -> dict[str, dict[Union[Capability, str], dict[Union[Attribute, str], StatusModel]]]:
        device_id = self.validate_device_id(device_id)
        status = self._device_status(device_id)
        return status.components

    def event_history(self, device_id: UUID | None = None, limit: int = 500,
                      capability: Set[Capability] | None = None,
                      capability_mode: CapabilitiesMode | None = "or",
                      attribute: Attribute | None = None,
                      oldest_first: bool = False, paging_after_epoch: int | None = None, paging_after_hash: int | None = None,
                      paging_before_epoch: int | None = None, paging_before_hash: int | None = None) -> List[dict]:

        if limit is None:
            limit = 500

        url = f"v1/history/devices?locationId={self.location_id}&limit={limit}"

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

        events_data = {}
        try:
            events_data = self.session.get_json(url)
            events = EventHistoryResponse.model_validate(events_data)
        except Exception as e:
            logger.error(f"Failed to parse event history response: {e}")
            logger.debug(f"Response data: {events_data}")
            raise

        # Filter items without pandas
        filtered_items = []
        for item in events.items:
            if capability is not None and item.capability in capability:
                continue
            if attribute is not None and item.attribute != attribute:
                continue

            filtered_item = {
                'deviceId': item.device_id,
                'time': item.time,
                'component': item.component,
                'capability': item.capability,
                'attribute': item.attribute,
                'value': item.value,
                'unit': None if item.unit == "" else item.unit
            }
            filtered_items.append(filtered_item)

        return filtered_items

    def _rooms(self):
        return self.session.get_json(f"v1/locations/{self.location_id}/rooms")

    @cached_property
    def rooms(self) -> dict[UUID, str]:
        res = {}
        for r in self._rooms()['items']:
            res[UUID(r['roomId'])] = r['name']

        return res

    @cached_property
    def device_ids(self) -> set[UUID]:
        """Set of device UUIDs available in this location."""
        devices = self.get_devices_short(include_status=False)
        return {d['deviceId'] for d in devices}

    def validate_device_id(self, device_id: UUID) -> UUID:
        """Validate that a device ID exists in the location.

        Args:
            device_id: Device UUID.

        Returns:
            Normalised UUID if valid.

        Raises:
            ValueError: If the ID format is invalid or not known.
        """
        if not isinstance(device_id, UUID):
            raise ValueError(f"'{device_id}' is not a valid UUID") from None

        if device_id not in self.device_ids:
            raise ValueError(
                f"deviceId '{device_id}' is unknown, use get_devices to list valid ids"
            )

        return device_id

    def get_room_name(self, room_id: UUID) -> str:
        """Get room name by UUID."""
        if room_id not in self.rooms:
            raise ValueError(f"roomId '{room_id}' is unknown, must be one of {self.rooms.keys()}")
        return self.rooms[room_id]

    ###
    def _get_devices(self, url: str):
        return DeviceResponse.model_validate(self.session.get_json(url)).items

    def get_devices(self, capability: Set[Capability] | Capability | None = None, capabilities_mode: CapabilitiesMode | None = None,
                    include_restricted: bool = False,
                    room_id: UUID | None = None, include_status: bool = True,
                    category: ComponentCategory | None = None,
                    connection_type: ConnectionType | None = None) -> List[DeviceItem]:
        url = f"devices?locationId={self.location_id}"
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
        if include_status:
            url += "&includeStatus=true"
        if connection_type is not None:
            if connection_type not in ConnectionType.__args__:
                raise ValueError(f"type must be one of {ConnectionType.__args__}")
            url += f"&type={connection_type}"

        return self._get_devices(url)

    def get_devices_short(self, capability: Set[Capability] | None = None, capabilities_mode: CapabilitiesMode | None = None,
                          include_restricted: bool = False,
                          room_id: UUID | None = None, include_status: bool = True,
                          category: ComponentCategory | None = None,
                          connection_type: ConnectionType | None = None) -> List[dict]:
        devices = self.get_devices(capability, capabilities_mode, include_restricted, room_id, include_status, category, connection_type)

        filtered_devices = []
        for device in devices:
            filtered_device = {'deviceId': device.device_id, 'label': device.label,
                               'manufacturerName': device.manufacturer_name}

            if device.room_id is not None:
                filtered_device['roomId'] = device.room_id
            filtered_device['components'] = []
            for component in device.components:
                filtered_component = {'id': component.id, 'label': component.label, 'categories': []}
                for _category in component.categories:
                    filtered_category = {'name': _category.name}
                    filtered_component['categories'].append(filtered_category)

                filtered_component['capabilities'] = []
                for _capability in component.capabilities:
                    if '.' in _capability.id or _capability.id in IGNORE_CAPABILITIES:
                        continue
                    filtered_capability: dict[str, Any] = {'id': _capability.id}
                    if _capability.status is not None:
                        filtered_capability['status'] = {}
                        for (k, v) in _capability.status.items():
                            if k.startswith('supported') or k in {'numberOfButtons', ''}:
                                continue
                            filtered_capability['status'][k] = {}
                            filtered_capability['status'][k]['value'] = v.value
                            if v.unit is not None:
                                filtered_capability['status'][k]['unit'] = v.unit
                            #if v.timestamp is not None: timestaps are off
                            #    filtered_capability['status'][k]['timestamp'] = v.timestamp
                    filtered_component['capabilities'].append(filtered_capability)
                filtered_device['components'].append(filtered_component)
            

            if device.parent_device_id is not None:
                filtered_device['parentDeviceId'] = device.parent_device_id
            filtered_device['connection_type'] = device.connection_type
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


    def _device_commands(self, device_id: UUID, commands: list[Command]) -> dict:
        """Low-level API call to execute commands on a device.
        {
          "results": [
            {
              "id": "36346e98-539c-4a22-9340-4e877a184a06",
              "status": "ACCEPTED"
            }
          ]
        }
        """
        url = f"v1/devices/{device_id}/commands"
        payload = {"commands": [cmd.to_dict() for cmd in commands]}
        return self.session.post_json(url, json=payload)
        
    def device_commands(self, device_id: UUID, commands: list[Command]) -> dict:
        """Execute SmartThings commands on a device."""
        device_id = self.validate_device_id(device_id)
        return self._device_commands(device_id, commands)

    def room_history(
        self,
        room_id: UUID,
        attribute: Attribute | None = None,
        start_ms: int | None = None,
        end_ms: int | None = None,
    ) -> List[dict]:
        """Aggregate history across all devices in a room."""
        devices = self.get_devices_short(
            room_id=room_id,
            include_status=False,
        )

        events: List[dict] = []
        for d in devices:
            events.extend(
                self.event_history(
                    device_id=d["deviceId"],
                    attribute=attribute,
                    limit=500,
                    paging_after_epoch=start_ms,
                    paging_before_epoch=end_ms,
                )
            )

        return events

    def _calc_epoch_range(self, delta_start: str, delta_end: str | None = None) -> tuple[int, int]:
        """Calculate epoch millisecond range from ISO8601 durations."""
        import isodate

        now = datetime.now(self.timezone)
        start_delta = isodate.parse_duration(delta_start)
        start_time = now - start_delta
        if delta_end is not None:
            end_delta = isodate.parse_duration(delta_end)
            end_time = now - end_delta
        else:
            end_time = now

        return int(start_time.timestamp() * 1000), int(end_time.timestamp() * 1000)

    def history(
        self,
        delta_start: str,
        delta_end: str | None = None,
        device_id: UUID | None = None,
        room_id: UUID | None = None,
        attribute: Attribute | None = None,
        granularity: Granularity = "hourly",
        aggregate: Aggregate = "raw",
    ) -> List[dict]:
        """Fetch history for a device or room using ISO durations."""
        start_ms, end_ms = self._calc_epoch_range(delta_start, delta_end)
        if room_id is not None:
            events = self.room_history(
                room_id=room_id,
                attribute=attribute,
                start_ms=start_ms,
                end_ms=end_ms,
            )
        else:
            events = self.event_history(
                device_id=device_id,
                attribute=attribute,
                limit=500,
                paging_after_epoch=start_ms,
                paging_before_epoch=end_ms,
            )

        if aggregate == "raw" and granularity == "realtime":
            return sorted(events, key=lambda e: e["time"])

        buckets: Dict[datetime, List[float]] = {}
        for ev in events:
            bucket = _bucket_time(ev["time"], granularity)
            try:
                val = float(ev["value"])
            except (TypeError, ValueError):
                continue
            buckets.setdefault(bucket, []).append(val)

        result = []
        for ts, vals in sorted(buckets.items()):
            if aggregate == "raw":
                for v in vals:
                    result.append({"time": ts, "value": v})
            else:
                agg_value = _aggregate_values(vals, aggregate)
                result.append({"time": ts, "value": agg_value})

        return result


def _bucket_time(ts: datetime, granularity: Granularity = "realtime") -> datetime:
    """Round a timestamp down to the given granularity."""
    if granularity == "realtime":
        return ts
    if granularity == "5min":
        return ts.replace(minute=(ts.minute // 5) * 5, second=0, microsecond=0)
    if granularity == "hourly":
        return ts.replace(minute=0, second=0, microsecond=0)
    if granularity == "daily":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown granularity: {granularity}")


def _aggregate_values(values: List[float], agg: Aggregate = "raw") -> float:
    """Aggregate numeric values according to agg method."""
    if not values:
        return float("nan")
    if agg == "sum":
        return float(sum(values))
    if agg == "avg":
        return float(sum(values) / len(values))
    if agg == "min":
        return float(min(values))
    if agg == "max":
        return float(max(values))
    raise ValueError(f"Unknown aggregation: {agg}")


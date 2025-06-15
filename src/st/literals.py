
from typing import Literal


Capability = Literal['button', 'motionSensor', 'dustSensor', 'carbonDioxideMeasurement',
    'illuminanceMeasurement', 'relativeHumidityMeasurement', 'temperatureMeasurement', 'atmosphericPressureMeasurement',
    'switch', 'signalStrength', 'powerMeter', 'presenceSensor', 'switchLevel', 'contactSensor', 'voltageMeasurement',
    'windowShade', 'windowShadeLevel', 'battery', 'lock']

CapabilitiesMode = Literal['and', 'or']

Attribute = Literal[
    'motion', 'battery', 'illuminance', 'temperature', 'tamper', 'atmosphericPressure', 'humidity', 'contact',
    'power', 'energy', 'level', 'voltage', 'rssi', 'lqi', 'shadeLevel', 'volume', 'water', 'presence', 'lock',
    'dustLevel', 'fineDustLevel', 'carbonDioxide', 'switch', 'atmosPressure',
    'button', 'presenceStatus', 'windowShade']

ConnectionType = Literal['LAN', 'ZIGBEE', 'ZWAVE', 'EDGE_CHILD', 'MOBILE']

ComponentCategory = Literal[
    'Light', 'AirConditioner', 'AirQualityDetector', 'Battery', 'Blind', 'BluetoothTracker', 'ContactSensor',
    'Dishwasher', 'Hub', 'LeakSensor', 'MobilePresence', 'MotionSensor', 'MultiFunctionalSensor', 'Others',
    'PresenceSensor', 'RemoteController', 'SmartLock', 'SmokeDetector',
    'Switch', 'Television', 'Thermostat']

Granularity = Literal["realtime", "5min", "hourly", "daily"]
Aggregate = Literal["raw", "sum", "avg", "min", "max"]

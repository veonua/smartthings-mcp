# {
#             "deviceId": "854b7c13-4746-4d5b-8db9-bfc29405439f",
#             "deviceName": "Air Quality",
#             "locationId": "8db57189-6b62-4033-97d2-d2c53fdb599f",
#             "locationName": "Home",
#             "time": "2025-06-14T22:28:12.000+00:00",
#             "text": "Air Quality PM 10 was 108μg/m^3",
#             "component": "main",
#             "componentLabel": "main",
#             "capability": "dustSensor",
#             "attribute": "dustLevel",
#             "value": "108",
#             "unit": "μg/m^3",
#             "data": {},
#             "translatedAttributeName": "PM 10",
#             "translatedAttributeValue": "108",
#             "epoch": 1749940092827,
#             "hash": 2337940949
#         },

import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field
from uuid import UUID
from .literals import Attribute, Capability

class EventHistoryItem(BaseModel):
    device_id: UUID = Field(..., alias="deviceId")
    device_name: str = Field(..., alias="deviceName")
    location_id: UUID = Field(..., alias="locationId")
    location_name: str = Field(..., alias="locationName")
    time: datetime.datetime
    text: str
    component: str
    component_label: str = Field(..., alias="componentLabel")
    capability: Capability
    attribute: Attribute
    value: Union[str, int, float]
    unit: Optional[str] = None
    data: dict = {}
    translated_attribute_name: Optional[str] = Field(None, alias="translatedAttributeName")
    translated_attribute_value: Optional[str] = Field(None, alias="translatedAttributeValue")
    epoch: int
    hash: int


class Links(BaseModel):
    class Link(BaseModel):
        href: str

    next: Link
    previous: Link

class EventHistoryResponse(BaseModel):
   
    items: list[EventHistoryItem]
    links: Links = Field(alias="_links")

    def to_dict(self) -> dict:
        return {
            "items": [item.model_dump(by_alias=True) for item in self.items],
            "_links": self.links.model_dump(by_alias=True)
        }
# {
#             "deviceId": "75c2fdb1-ef20-419b-afc1-af6b34392ebb",
#             "name": "Anna's S23 Ultra",
#             "label": "Anna's S23 Ultra",
#             "manufacturerName": "SmartThings",
#             "presentationId": "SmartThings-smartthings-Mobile_Presence",
#             "locationId": "8db57189-6b62-4033-97d2-d2c53fdb599f",
#             "ownerId": "1214065d-ea75-672a-9f4a-9379e0b112c3",
#             "components": [
#                 {
#                     "id": "main",
#                     "label": "Home",
#                     "capabilities": [
#                         {
#                             "id": "presenceSensor",
#                             "version": 1
#                         }
#                     ],
#                     "categories": [
#                         {
#                             "name": "MobilePresence",
#                             "categoryType": "manufacturer"
#                         }
#                     ],
#                     "optional": false
#                 }
#             ],
#             "createTime": "2025-06-02T17:40:32.567Z",
#             "parentDeviceId": "e56e52c1-4866-43d2-978f-f2fc70c0af12",
#             "profile": {
#                 "id": "1b6b60d0-475f-3d7a-89a4-ad16a0809702"
#             },
#             "type": "MOBILE",
#             "restrictionTier": 0,
#             "allowed": [],
#             "executionContext": "CLOUD",
#             "relationships": []
#         }

from typing import Any, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from src.st.links import Links
from src.st.literals import Capability, ComponentCategory, ConnectionType, ExecutionContext

class CapabilityModel(BaseModel):
    id: Union[Capability, str]  # Capability can be a string or a specific enum type
    version: int = 1
    optional: bool = False  
    status: Optional[dict[str, Any]] = None
    
class CategoryModel(BaseModel):
    name: Union[ComponentCategory, str]  # Category can be a string or a specific enum type
    category_type: Literal["manufacturer", "user"] = Field(..., alias="categoryType")


class Component(BaseModel):
    id: str
    label: str
    capabilities: list[CapabilityModel]
    categories: list[CategoryModel]
    optional: bool = False

class DeviceProfile(BaseModel):
    id: UUID

class DeviceItem(BaseModel):
    device_id: UUID = Field(..., alias="deviceId")
    name: str
    label: str
    
    manufacturer_name: str = Field(..., alias="manufacturerName")
    presentation_id: str = Field(..., alias="presentationId")

    room_id: Optional[UUID] = Field(None, alias="roomId")
    location_id: UUID = Field(..., alias="locationId")
    owner_id: Optional[UUID] = Field(None, alias="ownerId")
    components: list[Component] = Field(..., alias="components")
    create_time: datetime = Field(..., alias="createTime")
    parent_device_id: Optional[UUID] = Field(None, alias="parentDeviceId")
    profile: DeviceProfile
    connection_type: ConnectionType = Field(..., alias="type")
    restriction_tier: int = Field(..., alias="restrictionTier")
    allowed: list[dict]
    execution_context: ExecutionContext = Field(..., alias="executionContext")
    relationships: list[dict]


class DeviceResponse(BaseModel):
    items: list[DeviceItem]
    links: Optional[Links] = Field(default=None, alias="_links")

    def to_dict(self) -> dict:
        return {
            "items": [item.model_dump(by_alias=True) for item in self.items],
            "_links": self.links if self.links else None
        }
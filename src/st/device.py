
from typing import Any, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from st.links import Links
from st.literals import Attribute, Capability, ComponentCategory, ConnectionType, ExecutionContext

class StatusModel(BaseModel):
    value: Any
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None

class CapabilityModel(BaseModel):
    id: Union[Capability, str]  # Capability can be a string or a specific enum type
    version: int = 1
    optional: bool = False
    status: Optional[dict[str, StatusModel]] = None

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
    

class DeviceStatusResponse(BaseModel):
    components: dict[str, dict[Union[Capability, str], dict[Union[Attribute, str], StatusModel]]]

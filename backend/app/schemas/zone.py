from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ZoneBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    workstation_id: int
    coordinates: Dict[str, Any] = Field(..., description="Zone coordinates as polygon points")
    is_active: bool = True
    color: str = Field("#FF0000", pattern="^#[A-Fa-f0-9]{6}$")

class ZoneCreate(ZoneBase):
    pass

class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    coordinates: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    color: Optional[str] = Field(None, pattern="^#[A-Fa-f0-9]{6}$")

class ZoneResponse(ZoneBase):
    id: int
    person_count: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class WorkstationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    video_source_type: Optional[str] = Field(None, pattern="^(rtsp|usb|ip|file)$")
    video_source_url: Optional[str] = None
    video_config: Optional[Dict[str, Any]] = None

class WorkstationCreate(WorkstationBase):
    pass

class WorkstationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    video_source_type: Optional[str] = Field(None, pattern="^(rtsp|usb|ip|file)$")
    video_source_url: Optional[str] = None
    video_config: Optional[Dict[str, Any]] = None

class WorkstationResponse(WorkstationBase):
    id: int
    current_status: str
    last_detection_at: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkstationWithZones(WorkstationResponse):
    zones: List["ZoneResponse"] = []

# Forward reference for zones
from .zone import ZoneResponse
WorkstationWithZones.model_rebuild()
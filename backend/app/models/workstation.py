from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List
from .base import BaseModel

class Workstation(BaseModel):
    __tablename__ = "workstations"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Video source configuration
    video_source_type: Mapped[Optional[str]] = mapped_column(String(50))  # rtsp, usb, ip, file
    video_source_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Current status
    current_status: Mapped[str] = mapped_column(String(50), default="idle")  # work, idle, other
    last_detection_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    zones: Mapped[List["Zone"]] = relationship("Zone", back_populates="workstation", cascade="all, delete-orphan")
    detections: Mapped[List["Detection"]] = relationship("Detection", back_populates="workstation")
    efficiency_records: Mapped[List["EfficiencyRecord"]] = relationship("EfficiencyRecord", back_populates="workstation")
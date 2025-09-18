from sqlalchemy import String, Integer, ForeignKey, Float, JSON, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BaseModel

class Detection(BaseModel):
    __tablename__ = "detections"

    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))
    zone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("zones.id"))

    # Detection metadata
    frame_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    person_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"detections": [0.95, 0.87, ...]}

    # Bounding boxes for detected persons
    bounding_boxes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"boxes": [[x1,y1,x2,y2], ...]}

    # Tracking data
    track_ids: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"track_ids": [1, 3, 5, ...]}
    tracking_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"tracks": [{"id": 1, "bbox": [...], "conf": 0.95}, ...]}

    # Zone status at time of detection
    zone_status: Mapped[str] = mapped_column(String(50))  # work, idle, other

    # Performance metrics
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    workstation: Mapped["Workstation"] = relationship("Workstation", back_populates="detections")
    zone: Mapped[Optional["Zone"]] = relationship("Zone", back_populates="detections")


class TrackingSession(BaseModel):
    """Track individual person sessions across multiple detections"""
    __tablename__ = "tracking_sessions"

    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))

    # Session metadata
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Zone movement history
    zone_history: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"movements": [{"zone_id": 1, "timestamp": "...", "duration": 30}, ...]}

    # Session stats
    total_detections: Mapped[int] = mapped_column(Integer, default=1)
    zones_visited: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # {"zone_ids": [1, 2, 3]}

    # Current status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_zone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("zones.id"))

    # Relationships
    workstation: Mapped["Workstation"] = relationship("Workstation")
    current_zone: Mapped[Optional["Zone"]] = relationship("Zone")
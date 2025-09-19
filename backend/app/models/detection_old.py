from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Detection(BaseModel):
    __tablename__ = "detections"

    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))
    zone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("zones.id"))

    # Detection metadata
    frame_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    person_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON
    )  # {"detections": [0.95, 0.87, ...]}

    # Bounding boxes for detected persons
    bounding_boxes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON
    )  # {"boxes": [[x1,y1,x2,y2], ...]}

    # Zone status at time of detection
    zone_status: Mapped[str] = mapped_column(String(50))  # work, idle, other

    # Performance metrics
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    workstation: Mapped["Workstation"] = relationship(
        "Workstation", back_populates="detections"
    )
    zone: Mapped[Optional["Zone"]] = relationship("Zone", back_populates="detections")

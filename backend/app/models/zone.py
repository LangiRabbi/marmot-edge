from sqlalchemy import String, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, List
from .base import BaseModel

class Zone(BaseModel):
    __tablename__ = "zones"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))

    # Zone coordinates (polygon points)
    coordinates: Mapped[Dict[str, Any]] = mapped_column(JSON)  # {"points": [[x1,y1], [x2,y2], ...]}

    # Zone configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(7), default="#FF0000")  # hex color

    # Current state
    person_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="idle")  # work, idle, other

    # Relationships
    workstation: Mapped["Workstation"] = relationship("Workstation", back_populates="zones")
    detections: Mapped[List["Detection"]] = relationship("Detection", back_populates="zone")
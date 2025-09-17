from sqlalchemy import String, Integer, ForeignKey, Float, DateTime, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, time
from typing import Optional
from .base import BaseModel

class EfficiencyRecord(BaseModel):
    __tablename__ = "efficiency_records"

    workstation_id: Mapped[int] = mapped_column(Integer, ForeignKey("workstations.id"))

    # Time period
    date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    shift_start: Mapped[Optional[time]] = mapped_column(Time)
    shift_end: Mapped[Optional[time]] = mapped_column(Time)

    # Time tracking (in seconds)
    total_time: Mapped[float] = mapped_column(Float, default=0.0)
    work_time: Mapped[float] = mapped_column(Float, default=0.0)
    idle_time: Mapped[float] = mapped_column(Float, default=0.0)
    other_time: Mapped[float] = mapped_column(Float, default=0.0)
    break_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Calculated efficiency
    efficiency_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Status changes count
    status_changes: Mapped[int] = mapped_column(Integer, default=0)

    # Last update
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    workstation: Mapped["Workstation"] = relationship("Workstation", back_populates="efficiency_records")
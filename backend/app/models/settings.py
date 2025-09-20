from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class SystemSettings(BaseModel):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    value: Mapped[str] = mapped_column(String(1000))
    value_type: Mapped[str] = mapped_column(
        String(50)
    )  # string, integer, float, boolean, json
    description: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(100), default="general")


class AlertSettings(BaseModel):
    __tablename__ = "alert_settings"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_type: Mapped[str] = mapped_column(
        String(100)
    )  # device_offline, no_operator, extended_break
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    threshold_unit: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # minutes, hours, percentage
    recipients: Mapped[Dict[str, Any]] = mapped_column(
        JSON
    )  # {"emails": [], "websocket": true}
    message_template: Mapped[Optional[str]] = mapped_column(String(1000))

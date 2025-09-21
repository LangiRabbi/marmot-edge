"""
Pydantic schemas for WebSocket message validation.
Defines all message types and their validation rules.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """WebSocket message types."""
    # Client to server messages
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"

    # Server to client messages
    DETECTION_UPDATE = "detection_update"
    ZONE_UPDATE = "zone_update"
    EFFICIENCY_UPDATE = "efficiency_update"
    ALERT = "alert"
    PONG = "pong"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class SubscriptionType(str, Enum):
    """Types of data subscriptions."""
    DETECTIONS = "detections"
    ZONES = "zones"
    EFFICIENCY = "efficiency"
    ALERTS = "alerts"
    ALL = "all"


# Base message classes
class BaseWSMessage(BaseModel):
    """Base WebSocket message structure."""
    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    id: Optional[str] = None  # Message ID for tracking


# Client to server messages
class SubscribeMessage(BaseWSMessage):
    """Subscribe to workstation updates."""
    type: Literal[MessageType.SUBSCRIBE] = MessageType.SUBSCRIBE
    workstation_ids: List[str] = Field(..., min_items=1, max_items=10)
    subscription_types: List[SubscriptionType] = Field(default=[SubscriptionType.ALL])

    @validator('workstation_ids')
    def validate_workstation_ids(cls, v):
        # Remove duplicates and validate format
        unique_ids = list(set(v))
        for ws_id in unique_ids:
            if not ws_id or len(ws_id) > 50:
                raise ValueError(f"Invalid workstation ID: {ws_id}")
        return unique_ids


class UnsubscribeMessage(BaseWSMessage):
    """Unsubscribe from workstation updates."""
    type: Literal[MessageType.UNSUBSCRIBE] = MessageType.UNSUBSCRIBE
    workstation_ids: Optional[List[str]] = None  # None = unsubscribe from all
    subscription_types: Optional[List[SubscriptionType]] = None  # None = all types


class PingMessage(BaseWSMessage):
    """Ping message for connection health check."""
    type: Literal[MessageType.PING] = MessageType.PING


# Server to client messages
class PersonDetection(BaseModel):
    """Individual person detection data."""
    tracking_id: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[float] = Field(..., min_items=4, max_items=4)  # [x1, y1, x2, y2]
    center: List[float] = Field(..., min_items=2, max_items=2)  # [x, y]
    zones: List[str] = []  # Zone IDs this person is in


class DetectionUpdateMessage(BaseWSMessage):
    """Real-time person detection update."""
    type: Literal[MessageType.DETECTION_UPDATE] = MessageType.DETECTION_UPDATE
    workstation_id: str
    frame_timestamp: datetime
    person_count: int = Field(..., ge=0)
    persons: List[PersonDetection] = []
    processing_fps: float = Field(..., gt=0)
    frame_number: int = Field(..., ge=0)


class ZoneOccupancy(BaseModel):
    """Zone occupancy information."""
    zone_id: str
    person_count: int = Field(..., ge=0)
    person_ids: List[int] = []  # Tracking IDs of persons in zone
    occupancy_changed: bool = False  # True if occupancy changed since last update


class ZoneUpdateMessage(BaseWSMessage):
    """Zone occupancy update."""
    type: Literal[MessageType.ZONE_UPDATE] = MessageType.ZONE_UPDATE
    workstation_id: str
    zones: List[ZoneOccupancy]
    total_persons: int = Field(..., ge=0)


class EfficiencyMetrics(BaseModel):
    """Efficiency calculation metrics."""
    work_time_seconds: float = Field(..., ge=0)
    idle_time_seconds: float = Field(..., ge=0)
    other_time_seconds: float = Field(..., ge=0)  # Multiple persons
    total_time_seconds: float = Field(..., gt=0)
    efficiency_percentage: float = Field(..., ge=0, le=100)
    current_state: Literal["work", "idle", "other"] = "idle"


class EfficiencyUpdateMessage(BaseWSMessage):
    """Efficiency metrics update."""
    type: Literal[MessageType.EFFICIENCY_UPDATE] = MessageType.EFFICIENCY_UPDATE
    workstation_id: str
    metrics: EfficiencyMetrics
    period_start: datetime
    period_end: datetime


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertMessage(BaseWSMessage):
    """System alert notification."""
    type: Literal[MessageType.ALERT] = MessageType.ALERT
    workstation_id: str
    alert_type: str  # e.g., "no_operator", "extended_break", "system_error"
    level: AlertLevel
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None  # Additional alert data


class PongMessage(BaseWSMessage):
    """Pong response to ping."""
    type: Literal[MessageType.PONG] = MessageType.PONG


class ErrorMessage(BaseWSMessage):
    """Error response message."""
    type: Literal[MessageType.ERROR] = MessageType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class ConnectedMessage(BaseWSMessage):
    """Connection established confirmation."""
    type: Literal[MessageType.CONNECTED] = MessageType.CONNECTED
    connection_id: str
    server_version: str = "1.0.0"
    features: List[str] = []  # Supported features


class DisconnectedMessage(BaseWSMessage):
    """Disconnection notification."""
    type: Literal[MessageType.DISCONNECTED] = MessageType.DISCONNECTED
    reason: str
    reconnect_allowed: bool = True


# Union type for all possible messages
ClientMessage = Union[
    SubscribeMessage,
    UnsubscribeMessage,
    PingMessage
]

ServerMessage = Union[
    DetectionUpdateMessage,
    ZoneUpdateMessage,
    EfficiencyUpdateMessage,
    AlertMessage,
    PongMessage,
    ErrorMessage,
    ConnectedMessage,
    DisconnectedMessage
]

WebSocketMessage = Union[ClientMessage, ServerMessage]


# Message parsing utilities
def parse_client_message(data: dict) -> ClientMessage:
    """
    Parse incoming client message.

    Args:
        data: Raw message data

    Returns:
        Parsed and validated client message

    Raises:
        ValueError: If message format is invalid
    """
    message_type = data.get("type")

    if message_type == MessageType.SUBSCRIBE:
        return SubscribeMessage(**data)
    elif message_type == MessageType.UNSUBSCRIBE:
        return UnsubscribeMessage(**data)
    elif message_type == MessageType.PING:
        return PingMessage(**data)
    else:
        raise ValueError(f"Unknown client message type: {message_type}")


def create_error_message(error_code: str, error_message: str, details: Optional[Dict[str, Any]] = None) -> ErrorMessage:
    """
    Create a standardized error message.

    Args:
        error_code: Error code identifier
        error_message: Human-readable error message
        details: Additional error details

    Returns:
        Error message object
    """
    return ErrorMessage(
        error_code=error_code,
        error_message=error_message,
        details=details
    )


def create_detection_update(
    workstation_id: str,
    frame_timestamp: datetime,
    persons: List[PersonDetection],
    processing_fps: float,
    frame_number: int
) -> DetectionUpdateMessage:
    """
    Create a detection update message.

    Args:
        workstation_id: Workstation identifier
        frame_timestamp: When the frame was captured
        persons: List of detected persons
        processing_fps: Current processing FPS
        frame_number: Frame sequence number

    Returns:
        Detection update message
    """
    return DetectionUpdateMessage(
        workstation_id=workstation_id,
        frame_timestamp=frame_timestamp,
        person_count=len(persons),
        persons=persons,
        processing_fps=processing_fps,
        frame_number=frame_number
    )


def create_zone_update(
    workstation_id: str,
    zones: List[ZoneOccupancy]
) -> ZoneUpdateMessage:
    """
    Create a zone update message.

    Args:
        workstation_id: Workstation identifier
        zones: List of zone occupancy data

    Returns:
        Zone update message
    """
    total_persons = sum(zone.person_count for zone in zones)

    return ZoneUpdateMessage(
        workstation_id=workstation_id,
        zones=zones,
        total_persons=total_persons
    )
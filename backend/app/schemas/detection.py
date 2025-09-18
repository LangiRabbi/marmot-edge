"""
Detection and tracking Pydantic schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x1: float
    y1: float
    x2: float
    y2: float


class PersonTracking(BaseModel):
    """Individual person tracking result"""
    bbox: BoundingBox
    confidence: float
    class_name: str = "person"
    track_id: Optional[int] = None


class ZoneStatus(BaseModel):
    """Zone status and occupancy"""
    zone_id: int
    workstation_id: int
    person_count: int
    status: str  # work, idle, other
    track_ids: List[int]
    timestamp: datetime


class ZoneAnalysis(BaseModel):
    """Complete zone analysis results"""
    analysis_timestamp: datetime
    zones: Dict[int, ZoneStatus]
    total_persons_detected: int


class DetectionResponse(BaseModel):
    """Response for detection API endpoints"""
    detection_id: int
    workstation_id: int
    timestamp: datetime
    person_count: int
    trackings: List[Dict[str, Any]]  # Raw tracking results
    zone_analysis: Dict[str, Any]    # Zone analysis results
    processing_time_ms: float


class EfficiencyData(BaseModel):
    """Zone efficiency metrics"""
    zone_id: int
    time_window_hours: int
    work_time_minutes: float
    idle_time_minutes: float
    other_time_minutes: float
    efficiency_percentage: float


class StatusChange(BaseModel):
    """Zone status change record"""
    status: str
    timestamp: datetime
    person_count: int


class TrackingAnalysisResponse(BaseModel):
    """Response for zone tracking analysis"""
    zone_id: int
    time_window_hours: int
    efficiency_data: EfficiencyData
    status_history: List[StatusChange]


class TrackingMovement(BaseModel):
    """Person movement record"""
    zone_id: int
    timestamp: datetime
    entry_type: str


class TrackingHistoryResponse(BaseModel):
    """Response for tracking history"""
    track_id: int
    workstation_id: int
    movement_history: List[TrackingMovement]
    total_movements: int


class TrackingSessionData(BaseModel):
    """Tracking session information"""
    track_id: int
    workstation_id: int
    first_seen: datetime
    last_seen: datetime
    total_detections: int
    current_zone_id: Optional[int]
    zones_visited: Optional[List[int]]
    is_active: bool
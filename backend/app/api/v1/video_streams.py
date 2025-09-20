"""
Video streams API endpoints for managing real-time video sources
Supports RTSP, USB, IP cameras with zone configuration
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ...services.video_service import (
    Rectangle,
    StreamConfig,
    StreamStatus,
    get_video_manager,
)
from ...workers.video_processor import get_video_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video-streams", tags=["video-streams"])


# Pydantic models for API
class RectangleCreate(BaseModel):
    """Rectangle zone definition for API"""

    x_min: float = Field(..., description="Left boundary")
    y_min: float = Field(..., description="Top boundary")
    x_max: float = Field(..., description="Right boundary")
    y_max: float = Field(..., description="Bottom boundary")
    zone_id: int = Field(..., description="Zone identifier")
    name: str = Field("", description="Zone name")


class StreamCreate(BaseModel):
    """Create video stream request"""

    stream_id: str = Field(
        ..., min_length=1, max_length=50, description="Unique stream identifier"
    )
    source_url: str = Field(
        ..., description="Video source (RTSP URL, USB index, file path)"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Human readable name"
    )
    stream_type: str = Field(
        ..., pattern="^(rtsp|usb|ip|file)$", description="Stream type"
    )
    target_fps: int = Field(15, ge=1, le=30, description="Target FPS")
    auto_reconnect: bool = Field(True, description="Enable auto-reconnect")
    zones: List[RectangleCreate] = Field(
        [], max_items=10, description="Rectangular zones (max 10)"
    )


class StreamUpdate(BaseModel):
    """Update video stream request"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_fps: Optional[int] = Field(None, ge=1, le=30)
    auto_reconnect: Optional[bool] = None
    zones: Optional[List[RectangleCreate]] = Field(None, max_items=10)


class StreamResponse(BaseModel):
    """Video stream response"""

    stream_id: str
    source_url: str
    name: str
    stream_type: str
    target_fps: int
    auto_reconnect: bool
    status: str
    zones_count: int
    created_at: datetime
    fps_actual: float
    frame_count: int
    error_count: int
    queue_size: int


class ProcessingResultResponse(BaseModel):
    """Processing result response"""

    stream_id: str
    timestamp: datetime
    frame_number: int
    person_count: int
    trackings: List[Dict[str, Any]]
    zone_analysis: Dict[str, Any]
    processing_time_ms: float
    fps_current: float


class EfficiencyResponse(BaseModel):
    """Zone efficiency response"""

    zone_id: int
    stream_id: str
    efficiency_percentage: float
    work_minutes: float
    idle_minutes: float
    other_minutes: float
    total_minutes: float


@router.post("/", response_model=Dict[str, Any])
async def create_stream(stream_data: StreamCreate, background_tasks: BackgroundTasks):
    """
    Create new video stream with zones

    Supports:
    - RTSP: rtsp://username:password@ip:port/stream
    - USB: "0", "1", "2" (device index)
    - IP: http://ip/mjpeg_stream
    - File: /path/to/video.mp4
    """
    video_manager = get_video_manager()

    try:
        # Validate zone count
        if len(stream_data.zones) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 zones per stream")

        # Check if stream already exists
        if stream_data.stream_id in video_manager.streams:
            raise HTTPException(
                status_code=400, detail=f"Stream {stream_data.stream_id} already exists"
            )

        # Create stream config
        config = StreamConfig(
            stream_id=stream_data.stream_id,
            source_url=stream_data.source_url,
            name=stream_data.name,
            stream_type=stream_data.stream_type,
            target_fps=stream_data.target_fps,
            auto_reconnect=stream_data.auto_reconnect,
        )

        # Create rectangle zones
        zones = []
        for zone_data in stream_data.zones:
            rectangle = Rectangle(
                x_min=zone_data.x_min,
                y_min=zone_data.y_min,
                x_max=zone_data.x_max,
                y_max=zone_data.y_max,
                zone_id=zone_data.zone_id,
                name=zone_data.name,
            )
            zones.append(rectangle)

        # Add stream to manager
        success = video_manager.add_stream(config, zones)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create stream")

        logger.info(f"Created stream {stream_data.stream_id} with {len(zones)} zones")

        return {
            "message": f"Stream {stream_data.stream_id} created successfully",
            "stream_id": stream_data.stream_id,
            "zones_count": len(zones),
            "status": "created",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[StreamResponse])
async def list_streams():
    """Get list of all video streams with status"""
    video_manager = get_video_manager()

    try:
        streams = []
        all_status = video_manager.get_all_status()

        for stream_id, worker in video_manager.streams.items():
            status_data = all_status.get(stream_id, {})

            stream_response = StreamResponse(
                stream_id=stream_id,
                source_url=worker.config.source_url,
                name=worker.config.name,
                stream_type=worker.config.stream_type,
                target_fps=worker.config.target_fps,
                auto_reconnect=worker.config.auto_reconnect,
                status=status_data.get("status", "unknown"),
                zones_count=len(worker.zones),
                created_at=datetime.utcnow(),  # TODO: Store actual creation time
                fps_actual=status_data.get("fps_actual", 0.0),
                frame_count=status_data.get("frame_count", 0),
                error_count=status_data.get("error_count", 0),
                queue_size=status_data.get("queue_size", 0),
            )
            streams.append(stream_response)

        return streams

    except Exception as e:
        logger.error(f"Failed to list streams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stream_id}", response_model=StreamResponse)
async def get_stream(stream_id: str):
    """Get specific video stream details"""
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    try:
        worker = video_manager.streams[stream_id]
        status_data = video_manager.get_stream_status(stream_id) or {}

        return StreamResponse(
            stream_id=stream_id,
            source_url=worker.config.source_url,
            name=worker.config.name,
            stream_type=worker.config.stream_type,
            target_fps=worker.config.target_fps,
            auto_reconnect=worker.config.auto_reconnect,
            status=status_data.get("status", "unknown"),
            zones_count=len(worker.zones),
            created_at=datetime.utcnow(),
            fps_actual=status_data.get("fps_actual", 0.0),
            frame_count=status_data.get("frame_count", 0),
            error_count=status_data.get("error_count", 0),
            queue_size=status_data.get("queue_size", 0),
        )

    except Exception as e:
        logger.error(f"Failed to get stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{stream_id}", response_model=Dict[str, Any])
async def update_stream(stream_id: str, update_data: StreamUpdate):
    """Update video stream configuration"""
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    try:
        worker = video_manager.streams[stream_id]

        # Update configuration
        if update_data.name is not None:
            worker.config.name = update_data.name
        if update_data.target_fps is not None:
            worker.config.target_fps = update_data.target_fps
        if update_data.auto_reconnect is not None:
            worker.config.auto_reconnect = update_data.auto_reconnect

        # Update zones if provided
        if update_data.zones is not None:
            if len(update_data.zones) > 10:
                raise HTTPException(
                    status_code=400, detail="Maximum 10 zones per stream"
                )

            new_zones = []
            for zone_data in update_data.zones:
                rectangle = Rectangle(
                    x_min=zone_data.x_min,
                    y_min=zone_data.y_min,
                    x_max=zone_data.x_max,
                    y_max=zone_data.y_max,
                    zone_id=zone_data.zone_id,
                    name=zone_data.name,
                )
                new_zones.append(rectangle)

            worker.zones = new_zones

        logger.info(f"Updated stream {stream_id}")

        return {
            "message": f"Stream {stream_id} updated successfully",
            "stream_id": stream_id,
            "zones_count": len(worker.zones),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{stream_id}", response_model=Dict[str, Any])
async def delete_stream(stream_id: str):
    """Stop and remove video stream"""
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    try:
        success = video_manager.remove_stream(stream_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove stream")

        logger.info(f"Deleted stream {stream_id}")

        return {
            "message": f"Stream {stream_id} deleted successfully",
            "stream_id": stream_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stream_id}/status", response_model=Dict[str, Any])
async def get_stream_status(stream_id: str):
    """Get detailed stream status and metrics"""
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    try:
        status = video_manager.get_stream_status(stream_id)
        return status or {"error": "Status not available"}

    except Exception as e:
        logger.error(f"Failed to get stream status {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stream_id}/results", response_model=List[ProcessingResultResponse])
async def get_stream_results(stream_id: str, limit: int = 5):
    """Get latest processing results for stream"""
    video_processor = get_video_processor()
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    try:
        results = video_processor.get_stream_results(stream_id, limit)

        responses = []
        for result in results:
            response = ProcessingResultResponse(
                stream_id=result.stream_id,
                timestamp=result.timestamp,
                frame_number=result.frame_number,
                person_count=result.person_count,
                trackings=result.trackings,
                zone_analysis=result.zone_analysis,
                processing_time_ms=result.processing_time_ms,
                fps_current=result.fps_current,
            )
            responses.append(response)

        return responses

    except Exception as e:
        logger.error(f"Failed to get stream results {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{stream_id}/zones/{zone_id}/efficiency", response_model=EfficiencyResponse
)
async def get_zone_efficiency(stream_id: str, zone_id: int, minutes: int = 60):
    """Get efficiency metrics for specific zone"""
    video_processor = get_video_processor()
    video_manager = get_video_manager()

    if stream_id not in video_manager.streams:
        raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")

    if minutes < 1 or minutes > 1440:  # Max 24 hours
        raise HTTPException(
            status_code=400, detail="Minutes must be between 1 and 1440"
        )

    try:
        efficiency = video_processor.get_zone_efficiency(stream_id, zone_id, minutes)

        return EfficiencyResponse(
            zone_id=efficiency["zone_id"],
            stream_id=efficiency["stream_id"],
            efficiency_percentage=efficiency["efficiency_percentage"],
            work_minutes=efficiency["work_minutes"],
            idle_minutes=efficiency["idle_minutes"],
            other_minutes=efficiency["other_minutes"],
            total_minutes=efficiency["total_minutes"],
        )

    except Exception as e:
        logger.error(f"Failed to get zone efficiency {stream_id}/{zone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/statistics", response_model=Dict[str, Any])
async def get_system_statistics():
    """Get overall video processing system statistics"""
    video_manager = get_video_manager()
    video_processor = get_video_processor()

    try:
        video_stats = video_manager.get_statistics()
        processing_stats = video_processor.get_statistics()

        return {
            "video_manager": video_stats,
            "video_processor": processing_stats,
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to get system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/shutdown", response_model=Dict[str, Any])
async def shutdown_system():
    """Gracefully shutdown video processing system"""
    try:
        video_processor = get_video_processor()
        video_manager = get_video_manager()

        # Shutdown in order
        video_processor.shutdown()
        video_manager.shutdown()

        logger.info("Video processing system shutdown initiated")

        return {"message": "System shutdown initiated", "timestamp": datetime.utcnow()}

    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

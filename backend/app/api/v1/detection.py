"""
Detection API endpoints with YOLOv11 tracking support
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile)
from sqlalchemy.orm import Session

from app.crud.workstation import get_workstations
from app.crud.zone import get_zones_by_workstation
from app.database import get_db
from app.models.detection import Detection, TrackingSession
from app.schemas.detection import DetectionResponse, TrackingAnalysisResponse
from app.services.yolo_service import (YOLOTrackingService,
                                       get_yolo_tracking_service)
from app.services.zone_analyzer import ZoneAnalyzer, get_zone_analyzer

router = APIRouter()


@router.post("/detect/image", response_model=DetectionResponse)
async def detect_persons_in_image(
    workstation_id: int,
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    persist_tracking: bool = True,
    db: Session = Depends(get_db),
    yolo_service: YOLOTrackingService = Depends(get_yolo_tracking_service),
    zone_analyzer: ZoneAnalyzer = Depends(get_zone_analyzer),
):
    """
    Detect and track persons in uploaded image

    Args:
        workstation_id: Target workstation ID
        file: Image file (JPEG, PNG)
        confidence_threshold: Detection confidence threshold
        persist_tracking: Maintain track IDs across detections

    Returns:
        Detection results with tracking and zone analysis
    """
    try:
        start_time = time.time()

        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read image data
        image_data = await file.read()

        # Set confidence threshold
        if confidence_threshold != yolo_service.confidence_threshold:
            yolo_service.set_confidence_threshold(confidence_threshold)

        # Perform tracking
        trackings = yolo_service.track_persons(image_data, persist=persist_tracking)

        # Get zones for this workstation
        zones = get_zones_by_workstation(db, workstation_id)
        zone_data = [
            {
                "id": zone.id,
                "workstation_id": zone.workstation_id,
                "coordinates": zone.coordinates,
            }
            for zone in zones
        ]

        # Analyze zone occupancy
        zone_analysis = zone_analyzer.analyze_detections_in_zones(trackings, zone_data)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Prepare detection data for database
        detection_data = Detection(
            workstation_id=workstation_id,
            zone_id=None,  # Will be set based on primary zone if needed
            frame_timestamp=datetime.utcnow(),
            person_count=len(trackings),
            confidence_scores={"detections": [t["confidence"] for t in trackings]},
            bounding_boxes={
                "boxes": [
                    [t["bbox"]["x1"], t["bbox"]["y1"], t["bbox"]["x2"], t["bbox"]["y2"]]
                    for t in trackings
                ]
            },
            track_ids={
                "track_ids": [
                    t["track_id"] for t in trackings if t["track_id"] is not None
                ]
            },
            tracking_data={"tracks": trackings},
            zone_status="multiple_zones",  # Since we analyze multiple zones
            processing_time_ms=processing_time,
        )

        # Save to database
        db.add(detection_data)
        db.commit()
        db.refresh(detection_data)

        # Update tracking sessions
        await _update_tracking_sessions(db, trackings, workstation_id, zone_analysis)

        return DetectionResponse(
            detection_id=detection_data.id,
            workstation_id=workstation_id,
            timestamp=detection_data.frame_timestamp,
            person_count=len(trackings),
            trackings=trackings,
            zone_analysis=zone_analysis,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect/stream")
async def start_video_stream_detection(
    workstation_id: int,
    video_source: str,  # RTSP URL, USB camera index, or file path
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Start real-time video stream detection (for Checkpoint 3)

    This endpoint will be fully implemented in video processing checkpoint
    """
    # Placeholder for video stream processing
    return {
        "message": "Video stream detection will be implemented in Checkpoint 3",
        "workstation_id": workstation_id,
        "video_source": video_source,
        "status": "placeholder",
    }


@router.get("/tracking/history/{track_id}")
async def get_tracking_history(
    track_id: int,
    workstation_id: int,
    hours: int = 1,
    zone_analyzer: ZoneAnalyzer = Depends(get_zone_analyzer),
):
    """
    Get movement history for specific track ID

    Args:
        track_id: Person tracking ID
        workstation_id: Workstation ID
        hours: Hours of history to retrieve

    Returns:
        Movement history and zone transitions
    """
    try:
        movement_history = zone_analyzer.get_track_movement_history(track_id)

        return {
            "track_id": track_id,
            "workstation_id": workstation_id,
            "movement_history": movement_history,
            "total_movements": len(movement_history),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get tracking history: {str(e)}"
        )


@router.get("/zones/{zone_id}/analysis", response_model=TrackingAnalysisResponse)
async def get_zone_analysis(
    zone_id: int,
    hours: int = 1,
    zone_analyzer: ZoneAnalyzer = Depends(get_zone_analyzer),
):
    """
    Get efficiency analysis for specific zone

    Args:
        zone_id: Zone ID
        hours: Time window for analysis

    Returns:
        Zone efficiency metrics and status history
    """
    try:
        efficiency_data = zone_analyzer.get_zone_efficiency_data(zone_id, hours)
        status_history = zone_analyzer.get_zone_status_history(zone_id)

        return TrackingAnalysisResponse(
            zone_id=zone_id,
            time_window_hours=hours,
            efficiency_data=efficiency_data,
            status_history=status_history,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zone analysis failed: {str(e)}")


@router.post("/tracking/cleanup")
async def cleanup_old_tracking_data(
    hours_to_keep: int = 24, zone_analyzer: ZoneAnalyzer = Depends(get_zone_analyzer)
):
    """
    Clean up old tracking data to prevent memory leaks

    Args:
        hours_to_keep: Hours of data to retain

    Returns:
        Cleanup summary
    """
    try:
        zone_analyzer.clear_old_tracking_data(hours_to_keep)

        return {
            "message": f"Cleaned tracking data older than {hours_to_keep} hours",
            "timestamp": datetime.utcnow(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


async def _update_tracking_sessions(
    db: Session,
    trackings: List[Dict[str, Any]],
    workstation_id: int,
    zone_analysis: Dict[str, Any],
):
    """
    Update or create tracking sessions for detected persons

    Args:
        db: Database session
        trackings: List of tracking results
        workstation_id: Workstation ID
        zone_analysis: Zone analysis results
    """
    try:
        current_time = datetime.utcnow()

        for tracking in trackings:
            track_id = tracking.get("track_id")
            if track_id is None:
                continue

            # Find existing session or create new one
            session = (
                db.query(TrackingSession)
                .filter(
                    TrackingSession.track_id == track_id,
                    TrackingSession.workstation_id == workstation_id,
                    TrackingSession.is_active == True,
                )
                .first()
            )

            if session:
                # Update existing session
                session.last_seen = current_time
                session.total_detections += 1
            else:
                # Create new session
                session = TrackingSession(
                    track_id=track_id,
                    workstation_id=workstation_id,
                    first_seen=current_time,
                    last_seen=current_time,
                    total_detections=1,
                    is_active=True,
                )
                db.add(session)

            # Update zone information if person is in a zone
            for zone_id, zone_result in zone_analysis["zones"].items():
                if track_id in zone_result["track_ids"]:
                    session.current_zone_id = zone_id
                    break

        db.commit()

    except Exception as e:
        # Log error but don't fail the main detection
        print(f"Error updating tracking sessions: {e}")
        db.rollback()

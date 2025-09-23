"""
Test endpoint for manually triggering detection data broadcasting
Helps isolate WebSocket issues from YOLOv11 processing issues
"""

import asyncio
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/trigger-mock-detection/{workstation_id}")
async def trigger_mock_detection(workstation_id: str):
    """
    Manually trigger mock detection data for testing WebSocket pipeline
    """
    try:
        from app.schemas.websocket_messages import (
            PersonDetection,
            create_detection_update,
        )
        from app.services.websocket_manager import websocket_manager

        # Create mock detection data
        mock_persons = [
            PersonDetection(
                tracking_id=1,
                bbox=[0.2, 0.3, 0.4, 0.7],
                center=[0.3, 0.5],
                confidence=0.89,
                zones=["zone_1"],
            ),
            PersonDetection(
                tracking_id=2,
                bbox=[0.6, 0.2, 0.8, 0.6],
                center=[0.7, 0.4],
                confidence=0.92,
                zones=["zone_2"],
            ),
        ]

        # Create detection message
        detection_message = create_detection_update(
            workstation_id=workstation_id,
            frame_timestamp=datetime.now(),
            persons=mock_persons,
            processing_fps=15.3,
            frame_number=1234,
        )

        # Broadcast via WebSocket
        await websocket_manager.broadcast_to_workstation(
            workstation_id=workstation_id, message=detection_message
        )

        return JSONResponse(
            {
                "success": True,
                "message": f"Mock detection data sent to workstation {workstation_id}",
                "data": {
                    "person_count": len(mock_persons),
                    "workstation_id": workstation_id,
                    "frame_number": 1234,
                },
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )

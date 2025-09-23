#!/usr/bin/env python3
"""
Send detection message via API to test bounding box rendering
"""

import asyncio
import json
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


async def send_detection_via_api():
    """Send detection message through main API instead of direct WebSocket manager"""

    try:
        from app.schemas.websocket_messages import (
            PersonDetection,
            SubscriptionType,
            create_detection_update,
        )
        from app.services.websocket_manager import websocket_manager

        print("Sending detection message via main API websocket_manager...")

        # Create mock persons with realistic bounding boxes
        mock_persons = [
            PersonDetection(
                tracking_id=1,
                bbox=[0.2, 0.3, 0.4, 0.7],  # x1, y1, x2, y2 (normalized)
                center=[0.3, 0.5],  # center x, y
                confidence=0.89,
                zones=["zone_1"],
            ),
            PersonDetection(
                tracking_id=2,
                bbox=[0.6, 0.2, 0.8, 0.6],  # x1, y1, x2, y2 (normalized)
                center=[0.7, 0.4],  # center x, y
                confidence=0.92,
                zones=["zone_2"],
            ),
        ]

        # Create detection message
        detection_message = create_detection_update(
            workstation_id="7",  # ziemniaki workstation
            frame_timestamp=datetime.now(),
            persons=mock_persons,
            processing_fps=15.3,
            frame_number=12345,
        )

        print(f"Created detection message: {detection_message}")

        # Get stats before sending
        stats_before = websocket_manager.get_stats()
        print(f"Stats before: {stats_before}")

        # Broadcast to workstation 7 with detection subscription
        await websocket_manager.broadcast_to_workstation(
            workstation_id="7",
            message=detection_message,
            subscription_type=SubscriptionType.DETECTIONS,
        )

        print("Detection message sent successfully!")

        # Get stats after sending
        stats_after = websocket_manager.get_stats()
        print(f"Stats after: {stats_after}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Sending detection message via API for testing bounding boxes...")
    asyncio.run(send_detection_via_api())

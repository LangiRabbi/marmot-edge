#!/usr/bin/env python3
"""
Single test: Send one mock detection message to debug WebSocket flow
"""

import asyncio
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


async def send_single_mock_data():
    """Send one mock detection message"""

    try:
        from app.schemas.websocket_messages import (
            PersonDetection,
            SubscriptionType,
            create_detection_update,
        )
        from app.services.websocket_manager import websocket_manager

        print("Sending single mock detection message...")

        # Create mock persons
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
            workstation_id="7",  # ziemniaki workstation
            frame_timestamp=datetime.now(),
            persons=mock_persons,
            processing_fps=15.3,
            frame_number=12345,
        )

        print(f"Created detection message: {detection_message}")

        # Broadcast to workstation 7 with specific detection subscription
        await websocket_manager.broadcast_to_workstation(
            workstation_id="7",
            message=detection_message,
            subscription_type=SubscriptionType.DETECTIONS,
        )

        print("Mock detection message sent successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Sending single mock detection message for debugging...")
    asyncio.run(send_single_mock_data())

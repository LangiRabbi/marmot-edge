#!/usr/bin/env python3
"""
Test script to verify WebSocket detection broadcasting
Creates mock detection data and sends it via WebSocket
"""

import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add the app directory to Python path
sys.path.append(".")


def test_detection_broadcast():
    """Test detection data broadcasting via WebSocket (sync wrapper)"""

    async def _inner():
        try:
            # Import after adding to path
            from app.schemas.websocket_messages import (
                DetectionUpdateMessage,
                PersonDetection,
                create_detection_update,
            )
            from app.services.websocket_manager import websocket_manager

            print("Starting WebSocket detection test...")

            # Create mock person detection data for "ziemniaki" workstation (ID: 7)
            mock_persons = [
                PersonDetection(
                    tracking_id=1,
                    bbox=[0.2, 0.3, 0.4, 0.7],  # Normalized coordinates [x1, y1, x2, y2]
                    center=[0.3, 0.5],  # Center point [x, y]
                    confidence=0.89,
                    zones=["zone_1"],
                ),
                PersonDetection(
                    tracking_id=2,
                    bbox=[0.6, 0.2, 0.8, 0.6],
                    center=[0.7, 0.4],  # Center point [x, y]
                    confidence=0.92,
                    zones=["zone_2"],
                ),
            ]

            # Create detection update message
            detection_message = create_detection_update(
                workstation_id="7",  # ziemniaki workstation
                frame_timestamp=datetime.now(),
                persons=mock_persons,
                processing_fps=15.3,
                frame_number=1234,
            )

            print(f"Created mock detection message: {detection_message}")

            # Broadcast to workstation 7 ("ziemniaki")
            await websocket_manager.broadcast_to_workstation(
                workstation_id="7", message=detection_message  # ziemniaki workstation
            )

            print("Mock detection data broadcasted successfully!")
            print("Check frontend console for detection logs")

            # Wait a bit for delivery
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(_inner())


if __name__ == "__main__":
    # The test function is a sync wrapper that runs its async body internally.
    test_detection_broadcast()

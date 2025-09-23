#!/usr/bin/env python3
"""
Quick test: Send mock detection data every 2 seconds
Open ziemniaki workstation modal and run this script
"""

import asyncio
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


async def send_continuous_mock_data():
    """Send mock detection data every 2 seconds"""

    try:
        from app.schemas.websocket_messages import (
            PersonDetection,
            SubscriptionType,
            create_detection_update,
        )
        from app.services.websocket_manager import websocket_manager

        frame_number = 1

        while True:
            print(f"Sending mock detection data (frame {frame_number})...")

            # Create mock persons with moving positions
            import random

            mock_persons = [
                PersonDetection(
                    tracking_id=1,
                    bbox=[0.1 + random.random() * 0.3, 0.2, 0.4, 0.6],
                    center=[0.25 + random.random() * 0.2, 0.4],
                    confidence=0.85 + random.random() * 0.1,
                    zones=["zone_1"],
                ),
                PersonDetection(
                    tracking_id=2,
                    bbox=[0.5 + random.random() * 0.3, 0.3, 0.8, 0.7],
                    center=[0.65 + random.random() * 0.2, 0.5],
                    confidence=0.88 + random.random() * 0.1,
                    zones=["zone_2"],
                ),
            ]

            # Create detection message
            detection_message = create_detection_update(
                workstation_id="7",  # ziemniaki
                frame_timestamp=datetime.now(),
                persons=mock_persons,
                processing_fps=15.0 + random.random() * 5,
                frame_number=frame_number,
            )

            # Broadcast to workstation 7 with specific detection subscription
            await websocket_manager.broadcast_to_workstation(
                workstation_id="7",
                message=detection_message,
                subscription_type=SubscriptionType.DETECTIONS,
            )

            frame_number += 1
            await asyncio.sleep(2)  # Wait 2 seconds

    except KeyboardInterrupt:
        print("Stopping mock detection...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting continuous mock detection for ziemniaki workstation...")
    print("Open the ziemniaki workstation modal and watch for bounding boxes!")
    print("Press Ctrl+C to stop")
    asyncio.run(send_continuous_mock_data())

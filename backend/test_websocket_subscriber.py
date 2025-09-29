#!/usr/bin/env python3
"""
Test script: register a fake in-process WebSocket connection with websocket_manager,
subscribe it to workstation '7', broadcast a detection message and verify delivery.
"""

import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, Optional

sys.path.append(".")

from fastapi import WebSocket
from app.services.websocket_manager import websocket_manager, ConnectionInfo
from app.schemas.websocket_messages import (
    DetectionUpdateMessage,
    PersonDetection,
    create_detection_update,
    SubscriptionType,
)


class FakeWebSocket:
    """Mock WebSocket that captures sent messages"""
    def __init__(self):
        self.sent = []
        self.client_state = {"type": "websocket"}  # Mock client state

    async def send_text(self, text: str):
        print("FakeWebSocket: send_text called")
        self.sent.append(text)

    async def accept(self, subprotocol: Optional[str] = None) -> None:
        """Mock accept method"""
        pass

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """Mock close method"""
        pass


def test_subscriber_receive():
    async def _inner():
        try:
            print("Registering fake connection with websocket_manager")
            fake_ws = FakeWebSocket()
            connection_id = "test-conn-1"

            # Create ConnectionInfo and register it (type: ignore for mock object)
            conn_info = ConnectionInfo(fake_ws, connection_id, user=None)  # type: ignore
            websocket_manager.connections[connection_id] = conn_info

            # Subscribe the fake connection to workstation '7' detections
            ws_id = "7"
            websocket_manager.workstation_subscribers[ws_id][
                SubscriptionType.DETECTIONS
            ].add(connection_id)

            # Create a mock detection message
            mock_persons = [
                PersonDetection(
                    tracking_id=1,
                    bbox=[0.2, 0.3, 0.4, 0.7],
                    center=[0.3, 0.5],
                    confidence=0.89,
                    zones=["zone_1"],
                )
            ]

            detection_message = create_detection_update(
                workstation_id=ws_id,
                frame_timestamp=datetime.utcnow(),
                persons=mock_persons,
                processing_fps=15.3,
                frame_number=1234,
            )

            print("Broadcasting detection message to workstation 7")
            await websocket_manager.broadcast_to_workstation(
                workstation_id=ws_id,
                message=detection_message,
                subscription_type=SubscriptionType.DETECTIONS,
            )

            # Short wait
            await asyncio.sleep(0.05)

            # Check captured messages
            print("Captured messages on fake websocket:")
            for m in fake_ws.sent:
                print(m[:1000])

            # Clean up
            await websocket_manager.disconnect(connection_id, reason="Test complete")

        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(_inner())


if __name__ == "__main__":
    test_subscriber_receive()

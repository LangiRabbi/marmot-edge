#!/usr/bin/env python3
"""
Test DetectionUpdateMessage serialization to check what JSON is produced
"""

import json
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


def test_detection_message():
    """Test DetectionUpdateMessage JSON serialization"""

    try:
        from app.schemas.websocket_messages import (
            PersonDetection,
            create_detection_update,
        )

        print("Creating test PersonDetection objects...")

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

        print("Creating DetectionUpdateMessage...")

        # Create detection message
        detection_message = create_detection_update(
            workstation_id="7",
            frame_timestamp=datetime.now(),
            persons=mock_persons,
            processing_fps=15.3,
            frame_number=12345,
        )

        print(f"Message object: {detection_message}")
        print(f"Message type: {type(detection_message)}")
        print(f"Message.type: {detection_message.type}")

        # Serialize to JSON
        message_json = detection_message.json()
        print(f"JSON output: {message_json}")

        # Parse back to see structure
        parsed = json.loads(message_json)
        print(f"Parsed type: {parsed.get('type')}")
        print(f"Parsed workstation_id: {parsed.get('workstation_id')}")
        print(f"Parsed person_count: {parsed.get('person_count')}")

        print("✅ DetectionUpdateMessage serialization test PASSED")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Testing DetectionUpdateMessage serialization...")
    test_detection_message()

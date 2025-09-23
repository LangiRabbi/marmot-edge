#!/usr/bin/env python3
"""
Test detection message creation to find the exact issue
"""

import json
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


def test_detection_creation():
    """Test each step of detection creation to find the issue"""

    print("=== TESTING DETECTION CREATION ===")

    try:
        # Step 1: Create test data
        print("1. Creating test data...")
        current_time = datetime.now().isoformat()
        detection_data = {
            "type": "detection_update",
            "timestamp": current_time,
            "workstation_id": "7",
            "frame_timestamp": current_time,
            "person_count": 2,
            "persons": [
                {
                    "tracking_id": 1,
                    "confidence": 0.89,
                    "bbox": [0.2, 0.3, 0.4, 0.7],
                    "center": [0.3, 0.5],
                    "zones": ["zone_1"],
                },
                {
                    "tracking_id": 2,
                    "confidence": 0.92,
                    "bbox": [0.6, 0.2, 0.8, 0.6],
                    "center": [0.7, 0.4],
                    "zones": ["zone_2"],
                },
            ],
            "processing_fps": 15.3,
            "frame_number": 12345,
        }
        print("OK - Test data created")

        # Step 2: Test imports
        print("2. Testing imports...")
        from app.schemas.websocket_messages import (
            PersonDetection,
            create_detection_update,
        )

        print("OK - Imports successful")

        # Step 3: Test PersonDetection creation
        print("3. Testing PersonDetection creation...")
        persons = []
        for person_data in detection_data.get("persons", []):
            person = PersonDetection(**person_data)
            persons.append(person)
        print(f"OK - Created {len(persons)} PersonDetection objects")

        # Step 4: Test datetime parsing
        print("4. Testing datetime parsing...")
        frame_timestamp_str = detection_data.get(
            "frame_timestamp", datetime.now().isoformat()
        )
        frame_timestamp = datetime.fromisoformat(frame_timestamp_str)
        print(f"OK - Parsed timestamp: {frame_timestamp}")

        # Step 5: Test DetectionUpdateMessage creation
        print("5. Testing DetectionUpdateMessage creation...")
        detection_message = create_detection_update(
            workstation_id="7",
            frame_timestamp=frame_timestamp,
            persons=persons,
            processing_fps=detection_data.get("processing_fps", 15.0),
            frame_number=detection_data.get("frame_number", 0),
        )
        print(f"OK - Created DetectionUpdateMessage")
        print(f"OK - Message type: {detection_message.type}")

        # Step 6: Test JSON serialization
        print("6. Testing JSON serialization...")
        message_json = detection_message.model_dump_json()
        print(f"OK - Serialized JSON length: {len(message_json)}")

        print("\n=== ALL TESTS PASSED ===")
        print("Detection creation should work correctly!")
        return True

    except Exception as e:
        print(f"\nERROR FOUND: {e}")
        print(f"Exception type: {type(e)}")
        import traceback

        print(f"Traceback:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    test_detection_creation()

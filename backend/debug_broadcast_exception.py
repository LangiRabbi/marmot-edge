#!/usr/bin/env python3
"""
Debug the exact exception in broadcast endpoint processing
"""

import sys
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.append('.')

def debug_broadcast_exception():
    """Test each step of the broadcast endpoint to isolate the exception"""

    print("=== DEBUGGING BROADCAST ENDPOINT EXCEPTION ===")

    try:
        # Step 1: Test JSON parsing
        print("\n1. Testing JSON parsing...")
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
                    "zones": ["zone_1"]
                },
                {
                    "tracking_id": 2,
                    "confidence": 0.92,
                    "bbox": [0.6, 0.2, 0.8, 0.6],
                    "center": [0.7, 0.4],
                    "zones": ["zone_2"]
                }
            ],
            "processing_fps": 15.3,
            "frame_number": 12345
        }
        content = json.dumps(detection_data)
        parsed_data = json.loads(content)
        print("✅ JSON parsing successful")

        # Step 2: Test imports
        print("\n2. Testing imports...")
        from app.schemas.websocket_messages import PersonDetection, create_detection_update
        print("✅ Imports successful")

        # Step 3: Test PersonDetection creation
        print("\n3. Testing PersonDetection creation...")
        persons = []
        for person_data in parsed_data.get("persons", []):
            print(f"Creating PersonDetection with data: {person_data}")
            person = PersonDetection(**person_data)
            persons.append(person)
            print(f"✅ Created PersonDetection: {person}")
        print(f"✅ Created {len(persons)} PersonDetection objects")

        # Step 4: Test datetime parsing
        print("\n4. Testing datetime parsing...")
        frame_timestamp_str = parsed_data.get("frame_timestamp", datetime.now().isoformat())
        print(f"Parsing timestamp: {frame_timestamp_str}")
        frame_timestamp = datetime.fromisoformat(frame_timestamp_str)
        print(f"✅ Parsed timestamp: {frame_timestamp}")

        # Step 5: Test DetectionUpdateMessage creation
        print("\n5. Testing DetectionUpdateMessage creation...")
        detection_message = create_detection_update(
            workstation_id="7",
            frame_timestamp=frame_timestamp,
            persons=persons,
            processing_fps=parsed_data.get("processing_fps", 15.0),
            frame_number=parsed_data.get("frame_number", 0)
        )
        print(f"✅ Created DetectionUpdateMessage: {detection_message}")
        print(f"✅ Message type: {detection_message.type}")

        # Step 6: Test JSON serialization
        print("\n6. Testing JSON serialization...")
        message_json = detection_message.model_dump_json()
        print(f"✅ Serialized JSON: {message_json[:200]}...")

        print("\n=== ALL TESTS PASSED - NO EXCEPTION FOUND ===")
        print("The broadcast endpoint should work correctly!")

    except Exception as e:
        print(f"\n❌ EXCEPTION FOUND: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    debug_broadcast_exception()
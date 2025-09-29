#!/usr/bin/env python3
"""
Wyślij test detection z bounding boxami przez WebSocket broadcast
"""

import json
import requests
from datetime import datetime

def send_test_detection():
    """Wyślij testowe detection z bounding boxami do workstation 8"""

    # Test detection data z bounding boxami
    detection_data = {
        "workstation_id": "8",
        "frame_timestamp": datetime.now().isoformat(),
        "persons": [
            {
                "tracking_id": 1,
                "confidence": 0.95,
                "bbox": [100.0, 150.0, 300.0, 400.0],  # [x1, y1, x2, y2]
                "center": [200.0, 275.0],
                "zones": []
            },
            {
                "tracking_id": 2,
                "confidence": 0.87,
                "bbox": [400.0, 200.0, 600.0, 450.0],  # [x1, y1, x2, y2]
                "center": [500.0, 325.0],
                "zones": []
            }
        ],
        "processing_fps": 15.2,
        "frame_number": 12345,
        "person_count": 2
    }

    try:
        print("Wysyłam test detection z 2 osobami i bounding boxami...")
        print(f"Detection data: {json.dumps(detection_data, indent=2)}")

        response = requests.post(
            "http://localhost:8001/api/v1/websocket/broadcast",
            params={
                "workstation_id": "8",
                "message_type": "detection_update"
            },
            data=json.dumps(detection_data),
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS: Detection wysłane przez WebSocket!")
            print("Powinieneś teraz widzieć bounding boxy w froncie na workstation 8")
        else:
            print(f"❌ ERROR: Failed to send detection: {response.status_code}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    send_test_detection()
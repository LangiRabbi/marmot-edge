#!/usr/bin/env python3
"""
Send detection message via the working broadcast endpoint with custom JSON payload
"""

import json
import requests
from datetime import datetime

def send_detection_via_broadcast():
    """Send detection message using the working broadcast endpoint"""

    try:
        # Create detection message in the correct format
        detection_data = {
            "type": "detection_update",
            "timestamp": datetime.now().isoformat(),
            "workstation_id": "7",
            "frame_timestamp": datetime.now().isoformat(),
            "person_count": 2,
            "persons": [
                {
                    "tracking_id": 1,
                    "confidence": 0.89,
                    "bbox": [0.2, 0.3, 0.4, 0.7],  # x1, y1, x2, y2 (normalized)
                    "center": [0.3, 0.5],
                    "zones": ["zone_1"]
                },
                {
                    "tracking_id": 2,
                    "confidence": 0.92,
                    "bbox": [0.6, 0.2, 0.8, 0.6],  # x1, y1, x2, y2 (normalized)
                    "center": [0.7, 0.4],
                    "zones": ["zone_2"]
                }
            ],
            "processing_fps": 15.3,
            "frame_number": 12345
        }

        # Convert to JSON string for the content parameter
        content = json.dumps(detection_data)

        # Use the working broadcast endpoint
        url = "http://localhost:8001/api/v1/websocket/broadcast"
        params = {
            "workstation_id": "7",
            "message_type": "detection_update",
            "content": content
        }

        print(f"Sending detection via broadcast endpoint...")
        print(f"URL: {url}")
        print(f"Detection data: {json.dumps(detection_data, indent=2)}")

        response = requests.post(url, params=params)

        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Response: {result}")
            print(f"Subscribers reached: {result.get('subscribers', 0)}")
        else:
            print(f"ERROR! Status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Sending detection message via broadcast endpoint...")
    send_detection_via_broadcast()
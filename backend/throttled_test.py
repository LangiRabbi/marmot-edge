#!/usr/bin/env python3
"""
Test script: Send moving bounding boxes with proper throttling (1 per second)
"""

import requests
import time
import json


def send_throttled_detections():
    """Send moving detections with 1 second intervals"""

    base_url = "http://localhost:8001"
    workstation_id = "7"

    # Moving person positions
    person1_x = 0.2
    person1_y = 0.3
    person2_x = 0.6
    person2_y = 0.4

    # Movement speed
    person1_dx = 0.02
    person1_dy = 0.01
    person2_dx = -0.015
    person2_dy = 0.02

    frame_number = 1

    print("Starting throttled detection test...")
    print("Rate limit: 500 messages/minute")
    print("Sending 1 detection per second")
    print("Open workstation 7 modal to see moving boxes!")

    try:
        for i in range(20):  # Send 20 frames
            # Update positions
            person1_x += person1_dx
            person1_y += person1_dy
            person2_x += person2_dx
            person2_y += person2_dy

            # Bounce off walls
            if person1_x <= 0.1 or person1_x >= 0.7:
                person1_dx *= -1
            if person1_y <= 0.2 or person1_y >= 0.6:
                person1_dy *= -1
            if person2_x <= 0.3 or person2_x >= 0.8:
                person2_dx *= -1
            if person2_y <= 0.1 or person2_y >= 0.7:
                person2_dy *= -1

            # Calculate bounding boxes
            bbox1_x1 = person1_x
            bbox1_y1 = person1_y
            bbox1_x2 = person1_x + 0.2
            bbox1_y2 = person1_y + 0.3

            bbox2_x1 = person2_x
            bbox2_y1 = person2_y
            bbox2_x2 = person2_x + 0.15
            bbox2_y2 = person2_y + 0.3

            # Send detection
            url = f"{base_url}/api/v1/websocket/broadcast-detection"
            params = {
                "workstation_id": workstation_id,
                "bbox1_x1": round(bbox1_x1, 2),
                "bbox1_y1": round(bbox1_y1, 2),
                "bbox1_x2": round(bbox1_x2, 2),
                "bbox1_y2": round(bbox1_y2, 2),
                "bbox2_x1": round(bbox2_x1, 2),
                "bbox2_y1": round(bbox2_y1, 2),
                "bbox2_x2": round(bbox2_x2, 2),
                "bbox2_y2": round(bbox2_y2, 2),
            }

            response = requests.post(url, params=params)

            if response.status_code == 200:
                data = response.json()
                print(
                    f"Frame {frame_number:2d}: P1({bbox1_x1:.2f},{bbox1_y1:.2f}) P2({bbox2_x1:.2f},{bbox2_y1:.2f})"
                )
                print(f"   Sent to {data.get('subscribers', 0)} subscribers")
            else:
                print(f"Error {response.status_code}: {response.text}")

            frame_number += 1
            time.sleep(1)  # 1 second intervals

    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")

    print("Test complete!")


if __name__ == "__main__":
    send_throttled_detections()

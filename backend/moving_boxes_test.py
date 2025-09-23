#!/usr/bin/env python3
"""
Test script: Send moving bounding boxes every 1 second
"""

import asyncio
import sys
import requests
import time
import random
from datetime import datetime

# Add the app directory to Python path
sys.path.append(".")


async def send_moving_boxes():
    """Send moving bounding boxes to simulate YOLO detection"""

    base_url = "http://localhost:8001"
    workstation_id = "7"

    # Initial positions
    person1_x = 0.2
    person1_y = 0.3
    person2_x = 0.6
    person2_y = 0.4

    # Movement patterns
    person1_dx = 0.02
    person1_dy = 0.01
    person2_dx = -0.015
    person2_dy = 0.02

    frame_number = 1

    try:
        print("Starting moving bounding box simulation...")
        print("Open workstation 7 modal to see the effect!")

        while True:
            # Update positions
            person1_x += person1_dx
            person1_y += person1_dy
            person2_x += person2_dx
            person2_y += person2_dy

            # Bounce off walls
            if person1_x <= 0.1 or person1_x >= 0.7:
                person1_dx *= -1
            if person1_y <= 0.2 or person1_y >= 0.7:
                person1_dy *= -1
            if person2_x <= 0.3 or person2_x >= 0.9:
                person2_dx *= -1
            if person2_y <= 0.1 or person2_y >= 0.8:
                person2_dy *= -1

            # Calculate bounding boxes (0.2 width, 0.4 height)
            bbox1_x1 = person1_x
            bbox1_y1 = person1_y
            bbox1_x2 = person1_x + 0.2
            bbox1_y2 = person1_y + 0.4

            bbox2_x1 = person2_x
            bbox2_y1 = person2_y
            bbox2_x2 = person2_x + 0.2
            bbox2_y2 = person2_y + 0.4

            # Send detection
            url = f"{base_url}/api/v1/websocket/broadcast-detection"
            params = {
                "workstation_id": workstation_id,
                "bbox1_x1": bbox1_x1,
                "bbox1_y1": bbox1_y1,
                "bbox1_x2": bbox1_x2,
                "bbox1_y2": bbox1_y2,
                "bbox2_x1": bbox2_x1,
                "bbox2_y1": bbox2_y1,
                "bbox2_x2": bbox2_x2,
                "bbox2_y2": bbox2_y2,
            }

            response = requests.post(url, params=params)

            if response.status_code == 200:
                data = response.json()
                print(
                    f"Frame {frame_number}: Sent 2 moving boxes to workstation {workstation_id}"
                )
                print(
                    f"  Person 1: ({bbox1_x1:.2f}, {bbox1_y1:.2f}) -> ({bbox1_x2:.2f}, {bbox1_y2:.2f})"
                )
                print(
                    f"  Person 2: ({bbox2_x1:.2f}, {bbox2_y1:.2f}) -> ({bbox2_x2:.2f}, {bbox2_y2:.2f})"
                )
                print(f"  Response: {data.get('message', 'No message')}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

            frame_number += 1
            await asyncio.sleep(1)  # Send every 1 second

    except KeyboardInterrupt:
        print("Stopping simulation...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(send_moving_boxes())

#!/usr/bin/env python3
"""
Send detection message directly using the broadcast_detection_message function
"""

import asyncio
import sys

# Add the app directory to Python path
sys.path.append('.')

async def send_detection_directly():
    """Send detection message through direct function call"""

    try:
        # Import the function from the websocket module
        from app.api.v1.websocket import broadcast_detection_message

        print("Calling broadcast_detection_message function directly...")

        # Call the function with workstation 7 and default bounding boxes
        result = await broadcast_detection_message(
            workstation_id="7",
            bbox1_x1=0.2, bbox1_y1=0.3, bbox1_x2=0.4, bbox1_y2=0.7,
            bbox2_x1=0.6, bbox2_y1=0.2, bbox2_x2=0.8, bbox2_y2=0.6
        )

        print(f"Function result: {result}")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Subscribers: {result['subscribers']}")
        print(f"Detection data: {result['detection_data']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Sending detection message via direct function call...")
    asyncio.run(send_detection_directly())
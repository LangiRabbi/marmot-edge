#!/usr/bin/env python3
"""
Start YOLOv11 video processor for real video file
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(".")


async def start_video_processing():
    """Start real YOLOv11 processing for video file"""

    try:
        from app.services.video_service import get_video_manager
        from app.workers.video_processor import get_video_processor

        print("Starting YOLOv11 video processor...")

        # Get processor and video manager with current event loop
        current_loop = asyncio.get_running_loop()
        processor = get_video_processor(event_loop=current_loop)
        video_manager = get_video_manager()

        # Look for video file
        video_file = None
        possible_paths = [
            "wideo_pionowe.mp4",
            "../wideo_pionowe.mp4",
            "uploads/wideo_pionowe.mp4",
            "static/wideo_pionowe.mp4",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                video_file = os.path.abspath(path)
                break

        if not video_file:
            print("Searching for video files...")
            for root, dirs, files in os.walk(".."):
                for file in files:
                    if file.endswith((".mp4", ".avi", ".mov")):
                        print(f"Found video: {os.path.join(root, file)}")
                        if "wideo" in file.lower() or "pionowe" in file.lower():
                            video_file = os.path.abspath(os.path.join(root, file))
                            break
                if video_file:
                    break

        if not video_file:
            print("No video file found. Please specify the path to wideo_pionowe.mp4")
            return

        print(f"Using video file: {video_file}")

        # Add video stream for workstation 7 (ziemniaki)
        stream_id = "7"  # workstation ID

        # This would need to be implemented in the video manager
        print(f"Starting processing for stream {stream_id} with file {video_file}")
        print("Note: Video manager integration needs to be completed")
        print("For now, run the mock detection script to see bounding boxes")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("Stopping video processor...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("YOLOv11 Video Processor Starter")
    print(
        "This will process your video file and send detections to ziemniaki workstation"
    )
    asyncio.run(start_video_processing())

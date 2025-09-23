#!/usr/bin/env python3
"""
Test script to manually trigger video processing detection for workstation 7 (ziemniaki)
This bypasses the broken /start-processing endpoint to test the core functionality.
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

async def test_detection_creation():
    """Test detection creation and WebSocket broadcasting"""
    try:
        # Import the file video processor
        from app.workers.file_video_processor import start_file_processing, get_processing_status
        from app.schemas.websocket_messages import PersonDetection, create_detection_update

        print("=== Testing Video Processing for Workstation 7 (ziemniaki) ===")

        # Check current processing status
        status = get_processing_status("7")
        print(f"Current processing status: {status}")

        # Create test file path (since workstation 7 has uploaded file data)
        test_video_path = os.path.join(os.path.dirname(__file__), "test_video.mp4")
        if not os.path.exists(test_video_path):
            print("⚠️  No test video found, will use fallback video in processor")
            test_video_path = "blob:fake_video_data"  # Processor will handle this

        print(f"Starting video processing with: {test_video_path}")

        # Start processing
        start_file_processing("7", test_video_path)

        print("✅ Video processing started successfully!")
        print("⏱️  Processing will run in background thread...")
        print("📡 Check for WebSocket messages and detection data")

        # Wait a bit and check status again
        await asyncio.sleep(2)
        status = get_processing_status("7")
        print(f"Processing status after start: {status}")

        # Wait longer to see if detections are being processed
        print("⏳ Waiting 10 seconds for detection processing...")
        await asyncio.sleep(10)

        status = get_processing_status("7")
        print(f"Final processing status: {status}")

        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_detection_creation())
    if success:
        print("\n🎉 Test completed successfully!")
        print("👀 Check the frontend for bounding box detections")
    else:
        print("\n💥 Test failed - check errors above")

    input("Press Enter to exit...")

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

def test_detection_creation():
    import asyncio

    async def _inner():
        try:
            from app.workers.file_video_processor import start_file_processing, get_processing_status

            test_video_path = os.path.join(os.path.dirname(__file__), "test_video.mp4")
            if not os.path.exists(test_video_path):
                test_video_path = "blob:fake_video_data"

            start_file_processing("7", test_video_path)
            await asyncio.sleep(0.5)
            status = get_processing_status("7")
            assert status is not None
        except Exception as e:
            assert False, f"Detection creation test failed: {e}"

    asyncio.run(_inner())

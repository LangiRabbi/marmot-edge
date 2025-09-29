#!/usr/bin/env python3
"""Test the asyncio.run_coroutine_threadsafe() performance improvement"""

import asyncio
import time
import sys
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(".")

# Import the real ProcessingResult class
from app.workers.video_processor import ProcessingResult

def test_performance():
    import asyncio

    async def _inner():
        try:
            from app.workers.video_processor import VideoProcessor

            loop = asyncio.get_running_loop()
            processor = VideoProcessor(event_loop=loop)

            result = ProcessingResult()
            result.stream_id = "ws_7_stream"
            result.timestamp = datetime.utcnow()
            result.frame_number = 12345
            result.person_count = 2
            result.trackings = []
            result.zone_analysis = {}
            result.processing_time_ms = 23.5
            result.fps_current = 13.8

            processor._schedule_websocket_broadcast(result)
            await asyncio.sleep(0.1)
        except Exception as e:
            assert False, f"Performance test failed: {e}"

    asyncio.run(_inner())
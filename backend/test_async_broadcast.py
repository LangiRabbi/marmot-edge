#!/usr/bin/env python3
"""
Test script to verify asyncio.run_coroutine_threadsafe() WebSocket broadcasting
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the app directory to Python path
sys.path.append(".")

# Import the real ProcessingResult class
from app.workers.video_processor import ProcessingResult

def test_websocket_broadcast():
    import asyncio

    async def _inner():
        try:
            from app.workers.video_processor import VideoProcessor

            # Create VideoProcessor with current event loop
            loop = asyncio.get_running_loop()
            video_processor = VideoProcessor(event_loop=loop)

            # Create mock detection data
            mock_result = ProcessingResult()  # Create instance
            # Set attributes directly
            mock_result.stream_id = "ws_7_stream"
            mock_result.timestamp = datetime.utcnow()
            mock_result.frame_number = 12345
            mock_result.person_count = 2
            mock_result.trackings = []
            mock_result.zone_analysis = {}
            mock_result.processing_time_ms = 23.5
            mock_result.fps_current = 13.8


            # Run schedule call
            video_processor._schedule_websocket_broadcast(mock_result)

            # allow short time for any background tasks
            await asyncio.sleep(0.1)

        except Exception as e:
            assert False, f"Websocket broadcast test failed: {e}"

    asyncio.run(_inner())

if __name__ == "__main__":
    print("AsyncWebSocket Broadcasting Performance Test")
    import asyncio
    # Execute the test helper when run as a script
    test_websocket_broadcast()
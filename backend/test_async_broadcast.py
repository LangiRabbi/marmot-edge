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

def test_websocket_broadcast():
    import asyncio

    async def _inner():
        try:
            from app.workers.video_processor import VideoProcessor, ProcessingResult

            # Create VideoProcessor with current event loop
            loop = asyncio.get_running_loop()
            video_processor = VideoProcessor(event_loop=loop)

            # Create mock detection data using the actual ProcessingResult class
            mock_result = ProcessingResult(
                stream_id="ws_7_stream",
                timestamp=datetime.utcnow(),
                frame_number=12345,
                person_count=2,
                trackings=[],
                zone_analysis={},
                processing_time_ms=23.5,
                fps_current=13.8,
            )

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
#!/usr/bin/env python3
"""
Test script to verify database persistence in VideoProcessor
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(".")

# Import the real ProcessingResult class
from app.workers.video_processor import ProcessingResult

def test_database_persistence():
    import asyncio

    async def _inner():
        try:
            from app.workers.video_processor import VideoProcessor

            loop = asyncio.get_running_loop()
            processor = VideoProcessor(event_loop=loop)

            # Create a ProcessingResult with all required arguments
            mock = ProcessingResult(
                stream_id="ws_7_stream",
                timestamp=datetime.utcnow(),
                frame_number=1,
                person_count=1,
                trackings=[],
                zone_analysis={},
                processing_time_ms=23.5,
                fps_current=13.8
            )


            processor._schedule_database_persistence(mock)
            await asyncio.sleep(0.1)
        except Exception as e:
            assert False, f"Database persistence test failed: {e}"

    asyncio.run(_inner())
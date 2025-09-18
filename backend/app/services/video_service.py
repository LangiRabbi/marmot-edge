"""
Video source management service for real-time streaming
Handles RTSP, USB, IP cameras with auto-reconnect and resource management
"""
import cv2
import time
import logging
import threading
import signal
import sys
from typing import Dict, List, Optional, Tuple, Any
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Stream connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class StreamConfig:
    """Configuration for video stream"""
    stream_id: str
    source_url: str
    name: str
    stream_type: str  # "rtsp", "usb", "ip", "file"
    target_fps: int = 15
    max_zones: int = 10
    auto_reconnect: bool = True
    reconnect_delay: int = 1


@dataclass
class Rectangle:
    """Simple rectangle zone definition"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    zone_id: int
    name: str = ""


class VideoStreamWorker(threading.Thread):
    """Worker thread for individual video stream processing"""

    def __init__(self, config: StreamConfig, zones: List[Rectangle]):
        super().__init__(daemon=True)
        self.config = config
        self.zones = zones[:10]  # Max 10 zones per stream
        self.frame_queue = Queue(maxsize=100)
        self.stop_event = threading.Event()
        self.status = StreamStatus.DISCONNECTED
        self.cap = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.error_count = 0

        # Performance tracking
        self.fps_actual = 0.0
        self.last_fps_update = time.time()

    def run(self):
        """Main worker loop with auto-reconnect"""
        logger.info(f"Starting video worker for stream {self.config.stream_id}")

        while not self.stop_event.is_set():
            try:
                if self._connect():
                    self._process_frames()
                else:
                    if self.config.auto_reconnect:
                        self._reconnect_with_backoff()
                    else:
                        break

            except Exception as e:
                logger.error(f"Stream {self.config.stream_id} error: {e}")
                self.status = StreamStatus.ERROR
                self.error_count += 1

                if self.config.auto_reconnect and self.error_count < 10:
                    time.sleep(2)
                else:
                    break

        self._cleanup()
        logger.info(f"Video worker stopped for stream {self.config.stream_id}")

    def _connect(self) -> bool:
        """Establish connection to video source"""
        try:
            self.status = StreamStatus.CONNECTING
            logger.info(f"Connecting to {self.config.source_url}")

            # Handle different source types
            if self.config.stream_type == "usb":
                # USB camera (e.g., source_url = "0", "1", "2")
                device_id = int(self.config.source_url)
                self.cap = cv2.VideoCapture(device_id)
            else:
                # RTSP, IP, file sources
                self.cap = cv2.VideoCapture(self.config.source_url)

            if not self.cap.isOpened():
                logger.error(f"Failed to open video source: {self.config.source_url}")
                return False

            # Configure capture properties
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
            if self.config.target_fps > 0:
                self.cap.set(cv2.CAP_PROP_FPS, self.config.target_fps)

            self.status = StreamStatus.CONNECTED
            self.error_count = 0
            logger.info(f"Connected successfully to {self.config.stream_id}")
            return True

        except Exception as e:
            logger.error(f"Connection failed for {self.config.stream_id}: {e}")
            self.status = StreamStatus.ERROR
            return False

    def _process_frames(self):
        """Process video frames with FPS control"""
        frame_interval = 1.0 / self.config.target_fps if self.config.target_fps > 0 else 0

        while not self.stop_event.is_set() and self.cap.isOpened():
            ret, frame = self.cap.read()

            if not ret:
                logger.warning(f"Failed to read frame from {self.config.stream_id}")
                break

            current_time = time.time()

            # FPS control - skip frames if processing too fast
            if frame_interval > 0:
                time_since_last = current_time - self.last_frame_time
                if time_since_last < frame_interval:
                    continue

            self.last_frame_time = current_time
            self.frame_count += 1

            # Update FPS tracking
            self._update_fps_tracking(current_time)

            # Add frame to queue (drop oldest if full)
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()  # Remove oldest frame
                except Empty:
                    pass

            self.frame_queue.put({
                'frame': frame,
                'timestamp': current_time,
                'frame_number': self.frame_count,
                'stream_id': self.config.stream_id,
                'zones': self.zones
            })

    def _update_fps_tracking(self, current_time: float):
        """Update actual FPS calculation"""
        if current_time - self.last_fps_update >= 1.0:  # Update every second
            self.fps_actual = self.frame_count / (current_time - self.last_fps_update)
            self.last_fps_update = current_time
            self.frame_count = 0

    def _reconnect_with_backoff(self):
        """Exponential backoff reconnection strategy"""
        delays = [1, 2, 4, 8, 16, 32, 60]  # seconds

        for attempt, delay in enumerate(delays):
            if self.stop_event.is_set():
                return

            logger.info(f"Reconnecting {self.config.stream_id} in {delay}s (attempt {attempt + 1})")
            time.sleep(delay)

            if self._connect():
                logger.info(f"Reconnected {self.config.stream_id} successfully")
                return

        logger.error(f"Failed to reconnect {self.config.stream_id} after {len(delays)} attempts")
        self.status = StreamStatus.ERROR

    def _cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
            self.cap = None

        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break

        self.status = StreamStatus.STOPPED

    def get_frame(self) -> Optional[Dict[str, Any]]:
        """Get latest frame from queue"""
        try:
            return self.frame_queue.get_nowait()
        except Empty:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get current stream status and metrics"""
        return {
            'stream_id': self.config.stream_id,
            'status': self.status.value,
            'fps_actual': round(self.fps_actual, 2),
            'fps_target': self.config.target_fps,
            'frame_count': self.frame_count,
            'error_count': self.error_count,
            'queue_size': self.frame_queue.qsize(),
            'zones_count': len(self.zones)
        }

    def stop(self):
        """Stop the worker thread"""
        self.stop_event.set()


class VideoManager:
    """Main video stream manager with graceful shutdown"""

    MAX_STREAMS = 4
    MAX_ZONES_PER_STREAM = 10
    MAX_TOTAL_ZONES = 40

    def __init__(self):
        self.streams: Dict[str, VideoStreamWorker] = {}
        self.running = threading.Event()
        self.running.set()

        # Setup graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Docker stop

    def add_stream(self, config: StreamConfig, zones: List[Rectangle]) -> bool:
        """
        Add new video stream with zones

        Args:
            config: Stream configuration
            zones: List of rectangular zones (max 10)

        Returns:
            True if stream added successfully
        """
        if not self.running.is_set():
            logger.error("VideoManager is shutting down, cannot add streams")
            return False

        if len(self.streams) >= self.MAX_STREAMS:
            logger.error(f"Maximum streams limit reached ({self.MAX_STREAMS})")
            return False

        if len(zones) > self.MAX_ZONES_PER_STREAM:
            logger.error(f"Too many zones ({len(zones)}), max {self.MAX_ZONES_PER_STREAM}")
            return False

        total_zones = sum(len(worker.zones) for worker in self.streams.values())
        if total_zones + len(zones) > self.MAX_TOTAL_ZONES:
            logger.error(f"Total zones limit exceeded, max {self.MAX_TOTAL_ZONES}")
            return False

        if config.stream_id in self.streams:
            logger.error(f"Stream {config.stream_id} already exists")
            return False

        try:
            worker = VideoStreamWorker(config, zones)
            worker.start()
            self.streams[config.stream_id] = worker

            logger.info(f"Added stream {config.stream_id} with {len(zones)} zones")
            return True

        except Exception as e:
            logger.error(f"Failed to add stream {config.stream_id}: {e}")
            return False

    def remove_stream(self, stream_id: str) -> bool:
        """Remove video stream"""
        if stream_id not in self.streams:
            logger.warning(f"Stream {stream_id} not found")
            return False

        try:
            worker = self.streams[stream_id]
            worker.stop()
            worker.join(timeout=5.0)  # Wait up to 5 seconds

            del self.streams[stream_id]
            logger.info(f"Removed stream {stream_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove stream {stream_id}: {e}")
            return False

    def get_frame(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get latest frame from specific stream"""
        if stream_id not in self.streams:
            return None

        return self.streams[stream_id].get_frame()

    def get_all_frames(self) -> Dict[str, Dict[str, Any]]:
        """Get latest frames from all streams"""
        frames = {}
        for stream_id, worker in self.streams.items():
            frame_data = worker.get_frame()
            if frame_data:
                frames[stream_id] = frame_data
        return frames

    def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get status for specific stream"""
        if stream_id not in self.streams:
            return None

        return self.streams[stream_id].get_status()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all streams"""
        status = {}
        for stream_id, worker in self.streams.items():
            status[stream_id] = worker.get_status()
        return status

    def shutdown(self):
        """Graceful shutdown of all streams"""
        logger.info("Initiating VideoManager shutdown...")
        self.running.clear()

        # Stop all workers
        for stream_id, worker in self.streams.items():
            logger.info(f"Stopping stream {stream_id}")
            worker.stop()

        # Wait for workers to finish (with timeout)
        for stream_id, worker in self.streams.items():
            worker.join(timeout=5.0)
            if worker.is_alive():
                logger.warning(f"Stream {stream_id} did not stop gracefully")

        self.streams.clear()
        logger.info("VideoManager shutdown complete")

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        total_zones = sum(len(worker.zones) for worker in self.streams.values())

        return {
            'active_streams': len(self.streams),
            'max_streams': self.MAX_STREAMS,
            'total_zones': total_zones,
            'max_total_zones': self.MAX_TOTAL_ZONES,
            'running': self.running.is_set(),
            'stream_details': self.get_all_status()
        }


# Global video manager instance
_video_manager = None


def get_video_manager() -> VideoManager:
    """Get global video manager instance"""
    global _video_manager
    if _video_manager is None:
        _video_manager = VideoManager()
    return _video_manager
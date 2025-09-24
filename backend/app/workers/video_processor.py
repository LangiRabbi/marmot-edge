"""
Video processing pipeline with YOLOv11 tracking and zone analysis
Handles real-time frame processing from multiple video streams
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import Empty, Queue
from typing import Any, Dict, List, Optional

from ..services.video_service import Rectangle, get_video_manager
from ..services.yolo_service import get_yolo_tracking_service

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of video frame processing"""

    stream_id: str
    timestamp: datetime
    frame_number: int
    person_count: int
    trackings: List[Dict[str, Any]]
    zone_analysis: Dict[str, Any]
    processing_time_ms: float
    fps_current: float


class RectangleZoneAnalyzer:
    """Optimized zone analyzer for rectangular zones only"""

    def __init__(self):
        self.zone_status_history = {}  # stream_id -> zone_id -> status history
        self.track_history = {}  # stream_id -> track_id -> movement history

    def analyze_trackings_in_rectangles(
        self,
        trackings: List[Dict[str, Any]],
        rectangles: List[Rectangle],
        stream_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze tracked persons in rectangular zones (max 10 per stream)

        Args:
            trackings: List of YOLO tracking results
            rectangles: List of Rectangle zones (max 10)
            stream_id: Stream identifier

        Returns:
            Zone analysis results
        """
        analysis_timestamp = datetime.utcnow()
        zone_results = {}

        # Initialize zone occupancy
        zone_occupancy = {rect.zone_id: [] for rect in rectangles}

        # Check each tracking against each rectangle
        for tracking in trackings:
            if tracking.get("track_id") is None:
                continue

            person_center = self._get_person_center(tracking)

            # Check all rectangles (max 10)
            for rect in rectangles:
                if self._is_point_in_rectangle(person_center, rect):
                    zone_occupancy[rect.zone_id].append(tracking["track_id"])

                    # Update track movement history
                    self._update_track_history(
                        stream_id,
                        tracking["track_id"],
                        rect.zone_id,
                        analysis_timestamp,
                    )

        # Calculate zone statuses
        for rect in rectangles:
            person_count = len(zone_occupancy[rect.zone_id])

            # Determine status: 0=idle, 1=work, >1=other
            if person_count == 0:
                status = "idle"
            elif person_count == 1:
                status = "work"
            else:
                status = "other"

            # Update zone status history
            self._update_zone_status_history(
                stream_id, rect.zone_id, status, analysis_timestamp
            )

            zone_results[rect.zone_id] = {
                "zone_id": rect.zone_id,
                "zone_name": rect.name,
                "person_count": person_count,
                "status": status,
                "track_ids": zone_occupancy[rect.zone_id],
                "timestamp": analysis_timestamp,
                "rectangle": {
                    "x_min": rect.x_min,
                    "y_min": rect.y_min,
                    "x_max": rect.x_max,
                    "y_max": rect.y_max,
                },
            }

        return {
            "stream_id": stream_id,
            "analysis_timestamp": analysis_timestamp,
            "zones": zone_results,
            "total_persons_detected": len(
                [t for t in trackings if t.get("track_id") is not None]
            ),
        }

    def _get_person_center(self, tracking: Dict[str, Any]) -> tuple:
        """Get center point of person bounding box"""
        bbox = tracking["bbox"]
        center_x = (bbox["x1"] + bbox["x2"]) / 2
        center_y = (bbox["y1"] + bbox["y2"]) / 2
        return (center_x, center_y)

    def _is_point_in_rectangle(self, point: tuple, rect: Rectangle) -> bool:
        """
        O(1) check if point is inside rectangle

        Args:
            point: (x, y) coordinates
            rect: Rectangle zone definition

        Returns:
            True if point is inside rectangle
        """
        x, y = point
        return rect.x_min <= x <= rect.x_max and rect.y_min <= y <= rect.y_max

    def _update_track_history(
        self, stream_id: str, track_id: int, zone_id: int, timestamp: datetime
    ):
        """Update tracking movement history"""
        if stream_id not in self.track_history:
            self.track_history[stream_id] = {}

        if track_id not in self.track_history[stream_id]:
            self.track_history[stream_id][track_id] = []

        # Add zone entry
        self.track_history[stream_id][track_id].append(
            {"zone_id": zone_id, "timestamp": timestamp, "entry_type": "zone_presence"}
        )

        # Keep only recent history (last 100 entries per track)
        if len(self.track_history[stream_id][track_id]) > 100:
            self.track_history[stream_id][track_id] = self.track_history[stream_id][
                track_id
            ][-100:]

    def _update_zone_status_history(
        self, stream_id: str, zone_id: int, status: str, timestamp: datetime
    ):
        """Update zone status change history"""
        if stream_id not in self.zone_status_history:
            self.zone_status_history[stream_id] = {}

        if zone_id not in self.zone_status_history[stream_id]:
            self.zone_status_history[stream_id][zone_id] = []

        # Only record status changes
        history = self.zone_status_history[stream_id][zone_id]
        if not history or history[-1]["status"] != status:
            history.append({"status": status, "timestamp": timestamp})

            # Keep only recent history (last 1000 status changes per zone)
            if len(history) > 1000:
                self.zone_status_history[stream_id][zone_id] = history[-1000:]

    def get_zone_efficiency(
        self, stream_id: str, zone_id: int, minutes: int = 60
    ) -> Dict[str, Any]:
        """Calculate efficiency for specific zone over time period"""
        if (
            stream_id not in self.zone_status_history
            or zone_id not in self.zone_status_history[stream_id]
        ):
            return {
                "zone_id": zone_id,
                "stream_id": stream_id,
                "efficiency_percentage": 0.0,
                "work_minutes": 0,
                "idle_minutes": 0,
                "other_minutes": 0,
            }

        history = self.zone_status_history[stream_id][zone_id]
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        # Filter recent history
        recent_history = [h for h in history if h["timestamp"] > cutoff_time]

        if not recent_history:
            return {
                "zone_id": zone_id,
                "stream_id": stream_id,
                "efficiency_percentage": 0.0,
                "work_minutes": 0,
                "idle_minutes": 0,
                "other_minutes": 0,
            }

        # Calculate time in each status
        work_time = idle_time = other_time = 0.0

        for i in range(len(recent_history)):
            current = recent_history[i]

            # Duration until next status change or now
            if i < len(recent_history) - 1:
                duration = (
                    recent_history[i + 1]["timestamp"] - current["timestamp"]
                ).total_seconds() / 60
            else:
                duration = (
                    datetime.utcnow() - current["timestamp"]
                ).total_seconds() / 60

            if current["status"] == "work":
                work_time += duration
            elif current["status"] == "idle":
                idle_time += duration
            elif current["status"] == "other":
                other_time += duration

        total_time = work_time + idle_time + other_time
        efficiency = (work_time / total_time * 100) if total_time > 0 else 0.0

        return {
            "zone_id": zone_id,
            "stream_id": stream_id,
            "efficiency_percentage": round(efficiency, 2),
            "work_minutes": round(work_time, 2),
            "idle_minutes": round(idle_time, 2),
            "other_minutes": round(other_time, 2),
            "total_minutes": round(total_time, 2),
        }


class VideoProcessor:
    """Main video processing pipeline coordinator"""

    def __init__(self):
        self.yolo_service = get_yolo_tracking_service()
        self.video_manager = get_video_manager()
        self.zone_analyzer = RectangleZoneAnalyzer()

        self.processing_queue = Queue(maxsize=1000)
        self.results_queue = Queue(maxsize=1000)

        self.running = threading.Event()
        self.running.set()

        self.workers = []
        self.stats = {
            "frames_processed": 0,
            "total_processing_time": 0.0,
            "average_fps": 0.0,
            "last_update": time.time(),
        }

        # Start processing workers
        self._start_workers()

    def _start_workers(self):
        """Start background processing workers"""
        # Frame collector worker
        collector_worker = threading.Thread(
            target=self._frame_collector_worker, daemon=True, name="FrameCollector"
        )
        collector_worker.start()
        self.workers.append(collector_worker)

        # Processing workers (2 threads for parallel processing)
        for i in range(2):
            processor_worker = threading.Thread(
                target=self._processing_worker, daemon=True, name=f"Processor-{i+1}"
            )
            processor_worker.start()
            self.workers.append(processor_worker)

        logger.info(f"Started {len(self.workers)} video processing workers")

    def _frame_collector_worker(self):
        """Worker that collects frames from all video streams"""
        while self.running.is_set():
            try:
                # Get frames from all active streams
                all_frames = self.video_manager.get_all_frames()

                for stream_id, frame_data in all_frames.items():
                    if self.processing_queue.full():
                        # Drop oldest frame if queue is full
                        try:
                            self.processing_queue.get_nowait()
                        except Empty:
                            pass

                    self.processing_queue.put(frame_data)

                # Small delay to prevent CPU spinning
                time.sleep(0.001)  # 1ms

            except Exception as e:
                logger.error(f"Frame collector error: {e}")
                time.sleep(0.1)

    def _processing_worker(self):
        """Worker that processes frames with YOLO and zone analysis"""
        while self.running.is_set():
            try:
                # Get frame from queue
                try:
                    frame_data = self.processing_queue.get(timeout=0.1)
                except Empty:
                    continue

                # Process frame
                result = self._process_frame(frame_data)

                if result:
                    # Add to results queue
                    if self.results_queue.full():
                        try:
                            self.results_queue.get_nowait()  # Drop oldest result
                        except Empty:
                            pass

                    self.results_queue.put(result)

                    # Update statistics
                    self._update_stats(result)

                    # Broadcast WebSocket updates (async)
                    self._schedule_websocket_broadcast(result)

            except Exception as e:
                logger.error(f"Processing worker error: {e}")

    def _process_frame(self, frame_data: Dict[str, Any]) -> Optional[ProcessingResult]:
        """Process single frame with YOLO tracking and zone analysis"""
        start_time = time.time()

        try:
            frame = frame_data["frame"]
            stream_id = frame_data["stream_id"]
            zones = frame_data["zones"]
            timestamp = datetime.fromtimestamp(frame_data["timestamp"])

            # Convert frame to bytes for YOLO
            import cv2

            _, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            # Run YOLO tracking
            trackings = self.yolo_service.track_persons(frame_bytes, persist=True)

            # Run zone analysis with rectangles
            zone_analysis = self.zone_analyzer.analyze_trackings_in_rectangles(
                trackings, zones, stream_id
            )

            processing_time = (time.time() - start_time) * 1000  # milliseconds

            return ProcessingResult(
                stream_id=stream_id,
                timestamp=timestamp,
                frame_number=frame_data["frame_number"],
                person_count=len(trackings),
                trackings=trackings,
                zone_analysis=zone_analysis,
                processing_time_ms=processing_time,
                fps_current=1000.0 / processing_time if processing_time > 0 else 1.0,
            )

        except Exception as e:
            logger.error(f"Frame processing failed: {e}")
            return None

    def _update_stats(self, result: ProcessingResult):
        """Update processing statistics"""
        self.stats["frames_processed"] += 1
        self.stats["total_processing_time"] += result.processing_time_ms

        # Update average FPS every 100 frames
        if self.stats["frames_processed"] % 100 == 0:
            avg_time = (
                self.stats["total_processing_time"] / self.stats["frames_processed"]
            )
            self.stats["average_fps"] = 1000.0 / avg_time if avg_time > 0 else 0.0
            self.stats["last_update"] = time.time()

    def _schedule_websocket_broadcast(self, result: ProcessingResult):
        """
        Schedule WebSocket broadcast in the main event loop.

        Args:
            result: Processing result to broadcast
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread, try to get the main loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Schedule the coroutine
            if loop.is_running():
                # Use call_soon_threadsafe if loop is running
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_websocket_updates(result), loop
                )
            else:
                # Run the coroutine
                loop.run_until_complete(self._broadcast_websocket_updates(result))

        except Exception as e:
            logger.error(f"Failed to schedule WebSocket broadcast: {e}")

    def get_latest_results(self, max_results: int = 10) -> List[ProcessingResult]:
        """Get latest processing results"""
        results = []
        count = 0

        while count < max_results and not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                results.append(result)
                count += 1
            except Empty:
                break

        return results

    def get_stream_results(
        self, stream_id: str, max_results: int = 5
    ) -> List[ProcessingResult]:
        """Get latest results for specific stream"""
        all_results = self.get_latest_results(max_results * 5)  # Get more to filter
        stream_results = [r for r in all_results if r.stream_id == stream_id]
        return stream_results[:max_results]

    def get_zone_efficiency(
        self, stream_id: str, zone_id: int, minutes: int = 60
    ) -> Dict[str, Any]:
        """Get efficiency metrics for specific zone"""
        return self.zone_analyzer.get_zone_efficiency(stream_id, zone_id, minutes)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "active_streams": len(self.video_manager.streams),
            "processing_queue_size": self.processing_queue.qsize(),
            "results_queue_size": self.results_queue.qsize(),
            "workers_count": len(self.workers),
            "running": self.running.is_set(),
        }

    async def _broadcast_websocket_updates(self, result: ProcessingResult):
        """
        Broadcast processing results via WebSocket to subscribers.

        Args:
            result: Processing result to broadcast
        """
        try:
            from ..schemas.websocket_messages import (
                PersonDetection,
                SubscriptionType,
                ZoneOccupancy,
                create_detection_update,
                create_zone_update,
            )
            from ..services.websocket_manager import websocket_manager

            # Create person detection data
            persons = []
            for tracking in result.trackings:
                if (
                    "bbox" in tracking
                    and "track_id" in tracking
                    and tracking["track_id"] is not None
                ):
                    bbox = tracking["bbox"]

                    # Calculate center point
                    center_x = (bbox[0] + bbox[2]) / 2
                    center_y = (bbox[1] + bbox[3]) / 2

                    # Find zones this person is in
                    person_zones = []
                    zone_analysis = result.zone_analysis.get("zones", {})
                    for zone_id, zone_data in zone_analysis.items():
                        if tracking["track_id"] in zone_data.get("person_ids", []):
                            person_zones.append(zone_id)

                    person = PersonDetection(
                        tracking_id=tracking["track_id"],
                        confidence=tracking.get("confidence", 0.0),
                        bbox=[
                            float(bbox[0]),
                            float(bbox[1]),
                            float(bbox[2]),
                            float(bbox[3]),
                        ],
                        center=[float(center_x), float(center_y)],
                        zones=person_zones,
                    )
                    persons.append(person)

            # Create detection update message
            detection_message = create_detection_update(
                workstation_id=result.stream_id,
                frame_timestamp=result.timestamp,
                persons=persons,
                processing_fps=result.fps_current,
                frame_number=result.frame_number,
            )

            # Broadcast detection update
            await websocket_manager.broadcast_to_workstation(
                workstation_id=result.stream_id,
                message=detection_message,
                subscription_type=SubscriptionType.DETECTIONS,
            )

            # Create zone update data
            zones = []
            zone_analysis = result.zone_analysis.get("zones", {})
            for zone_id, zone_data in zone_analysis.items():
                person_ids = zone_data.get("person_ids", [])
                zone_occupancy = ZoneOccupancy(
                    zone_id=zone_id,
                    person_count=len(person_ids),
                    person_ids=person_ids,
                    occupancy_changed=zone_data.get("status_changed", False),
                )
                zones.append(zone_occupancy)

            # Create zone update message
            zone_message = create_zone_update(
                workstation_id=result.stream_id, zones=zones
            )

            # Broadcast zone update
            await websocket_manager.broadcast_to_workstation(
                workstation_id=result.stream_id,
                message=zone_message,
                subscription_type=SubscriptionType.ZONES,
            )

            # Create efficiency update if available
            efficiency_data = result.zone_analysis.get("efficiency")
            if efficiency_data:
                from ..schemas.websocket_messages import (
                    EfficiencyMetrics,
                    EfficiencyUpdateMessage,
                )

                # Determine current state based on person count
                current_state = "idle"
                if result.person_count == 1:
                    current_state = "work"
                elif result.person_count > 1:
                    current_state = "other"

                efficiency_metrics = EfficiencyMetrics(
                    work_time_seconds=efficiency_data.get("work_minutes", 0) * 60,
                    idle_time_seconds=efficiency_data.get("idle_minutes", 0) * 60,
                    other_time_seconds=efficiency_data.get("other_minutes", 0) * 60,
                    total_time_seconds=efficiency_data.get("total_minutes", 0) * 60,
                    efficiency_percentage=efficiency_data.get(
                        "efficiency_percentage", 0
                    ),
                    current_state=current_state,
                )

                efficiency_message = EfficiencyUpdateMessage(
                    workstation_id=result.stream_id,
                    metrics=efficiency_metrics,
                    period_start=result.timestamp
                    - timedelta(minutes=efficiency_data.get("total_minutes", 0)),
                    period_end=result.timestamp,
                )

                # Broadcast efficiency update
                await websocket_manager.broadcast_to_workstation(
                    workstation_id=result.stream_id,
                    message=efficiency_message,
                    subscription_type=SubscriptionType.EFFICIENCY,
                )

        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")
            # Don't propagate the error to avoid affecting video processing

    def shutdown(self):
        """Graceful shutdown of video processor"""
        logger.info("Shutting down video processor...")
        self.running.clear()

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} did not stop gracefully")

        # Clear queues
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except Empty:
                break

        while not self.results_queue.empty():
            try:
                self.results_queue.get_nowait()
            except Empty:
                break

        logger.info("Video processor shutdown complete")


# Global processor instance
_video_processor = None


def get_video_processor() -> VideoProcessor:
    """Get global video processor instance"""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor

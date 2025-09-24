"""
File Video Processor - Processes uploaded video files with YOLOv11 and broadcasts detections
"""

import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict

import cv2

from ..schemas.websocket_messages import (
    PersonDetection,
    SubscriptionType,
    create_detection_update,
)
from ..services.websocket_manager import websocket_manager
from ..services.yolo_service import get_yolo_tracking_service

logger = logging.getLogger(__name__)

# Global dictionary to track running processors
_running_processors: Dict[str, threading.Thread] = {}
_processor_stop_flags: Dict[str, bool] = {}


class FileVideoProcessor:
    """Processes video files with YOLOv11 detection and WebSocket broadcasting"""

    def __init__(self, workstation_id: str, file_path: str):
        self.workstation_id = workstation_id
        self.file_path = file_path
        self.yolo_service = get_yolo_tracking_service()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.last_fps_count = 0
        self.current_fps = 0.0

    def process_video(self):
        """Main video processing loop"""
        logger.info(f"Starting video processing for workstation {self.workstation_id}")
        logger.info(f"Video file: {self.file_path}")

        # Handle different file path scenarios
        actual_file_path = self.file_path

        # For blob URLs or non-existent files, use test video
        if self.file_path.startswith("blob:") or not os.path.exists(self.file_path):
            test_video_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "test_video.mp4"
            )
            if os.path.exists(test_video_path):
                actual_file_path = test_video_path
                logger.info(f"Using test video instead: {actual_file_path}")
            else:
                logger.error(
                    f"No accessible video file found. Original: {self.file_path}"
                )
                return

        logger.info(f"Processing video file: {actual_file_path}")

        try:
            # Open video file
            cap = cv2.VideoCapture(actual_file_path)

            if not cap.isOpened():
                logger.error(f"Cannot open video file: {actual_file_path}")
                return

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            logger.info(
                f"Video properties: {width}x{height}, {fps} FPS, {total_frames} frames"
            )

            # Calculate frame delay to maintain original FPS
            frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30.0  # Default to 30 FPS

            frame_number = 0
            while cap.isOpened():
                # Check stop flag
                if _processor_stop_flags.get(self.workstation_id, False):
                    logger.info(
                        f"Stop flag detected for workstation {self.workstation_id}"
                    )
                    break

                ret, frame = cap.read()
                if not ret:
                    logger.info("End of video reached, looping...")
                    # Reset to beginning for continuous loop
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_number = 0
                    continue

                frame_number += 1
                self.frame_count += 1

                try:
                    # Convert frame to bytes for YOLO processing
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_bytes = buffer.tobytes()

                    # Run YOLO detection
                    trackings = self.yolo_service.track_persons(
                        frame_bytes, persist=True
                    )

                    # Convert trackings to PersonDetection format
                    persons = []
                    for tracking in trackings:
                        # Convert absolute coordinates to normalized (0-1)
                        bbox = tracking["bbox"]
                        norm_bbox = [
                            bbox["x1"] / width,  # x1 normalized
                            bbox["y1"] / height,  # y1 normalized
                            bbox["x2"] / width,  # x2 normalized
                            bbox["y2"] / height,  # y2 normalized
                        ]

                        # Calculate center point
                        center_x = (bbox["x1"] + bbox["x2"]) / 2 / width
                        center_y = (bbox["y1"] + bbox["y2"]) / 2 / height

                        person = PersonDetection(
                            tracking_id=tracking.get("track_id") or 0,
                            bbox=norm_bbox,
                            center=[center_x, center_y],
                            confidence=tracking["confidence"],
                            zones=[],  # Zone assignment would be handled by frontend
                        )
                        persons.append(person)

                    # Update FPS calculation
                    self._update_fps()

                    # Create detection message
                    detection_message = create_detection_update(
                        workstation_id=self.workstation_id,
                        frame_timestamp=datetime.now(),
                        persons=persons,
                        processing_fps=max(self.current_fps, 0.1),  # Ensure FPS is > 0
                        frame_number=frame_number,
                    )

                    # Broadcast to WebSocket
                    asyncio.run(self._broadcast_detection(detection_message))

                    logger.debug(
                        f"Frame {frame_number}: Detected {len(persons)} persons"
                    )

                except Exception as e:
                    logger.error(f"Error processing frame {frame_number}: {e}")

                # Wait to maintain original video FPS
                time.sleep(frame_delay)

        except Exception as e:
            logger.error(f"Video processing error: {e}")
        finally:
            if "cap" in locals():
                cap.release()
            logger.info(
                f"Video processing stopped for workstation {self.workstation_id}"
            )

    def _update_fps(self):
        """Update FPS calculation"""
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:  # Update every second
            frames_processed = self.frame_count - self.last_fps_count
            self.current_fps = frames_processed / (current_time - self.last_fps_time)
            self.last_fps_time = current_time
            self.last_fps_count = self.frame_count

    async def _broadcast_detection(self, detection_message):
        """Broadcast detection message to WebSocket subscribers"""
        try:
            await websocket_manager.broadcast_to_workstation(
                workstation_id=self.workstation_id,
                message=detection_message,
                subscription_type=SubscriptionType.DETECTIONS,
            )
        except Exception as e:
            logger.error(f"Error broadcasting detection: {e}")


def start_file_processing(workstation_id: str, file_path: str):
    """Start video processing in a background thread"""
    global _running_processors, _processor_stop_flags

    # Stop existing processor if running
    if workstation_id in _running_processors:
        logger.info(f"Stopping existing processor for workstation {workstation_id}")
        _processor_stop_flags[workstation_id] = True
        _running_processors[workstation_id].join(timeout=5.0)

    # Reset stop flag
    _processor_stop_flags[workstation_id] = False

    # Create and start new processor
    processor = FileVideoProcessor(workstation_id, file_path)

    def run_processor():
        try:
            processor.process_video()
        except Exception as e:
            logger.error(f"Processor thread error: {e}")
        finally:
            # Clean up
            if workstation_id in _running_processors:
                del _running_processors[workstation_id]
            if workstation_id in _processor_stop_flags:
                del _processor_stop_flags[workstation_id]

    thread = threading.Thread(target=run_processor, daemon=True)
    thread.start()

    _running_processors[workstation_id] = thread

    logger.info(f"Video processing started for workstation {workstation_id}")


async def stop_file_processing(workstation_id: str) -> bool:
    """Stop video processing for a workstation"""
    global _running_processors, _processor_stop_flags

    if workstation_id not in _running_processors:
        logger.info(f"No processor running for workstation {workstation_id}")
        return False

    logger.info(f"Stopping video processing for workstation {workstation_id}")

    # Set stop flag
    _processor_stop_flags[workstation_id] = True

    # Wait for thread to finish
    thread = _running_processors[workstation_id]
    thread.join(timeout=10.0)

    # Clean up
    if workstation_id in _running_processors:
        del _running_processors[workstation_id]
    if workstation_id in _processor_stop_flags:
        del _processor_stop_flags[workstation_id]

    logger.info(f"Video processing stopped for workstation {workstation_id}")
    return True


def get_processing_status(workstation_id: str) -> Dict[str, any]:
    """Get processing status for a workstation"""
    is_running = workstation_id in _running_processors
    thread_alive = False

    if is_running:
        thread = _running_processors[workstation_id]
        thread_alive = thread.is_alive()

    return {
        "workstation_id": workstation_id,
        "is_processing": is_running and thread_alive,
        "thread_exists": is_running,
        "thread_alive": thread_alive,
    }


def stop_all_processing():
    """Stop all running processors (for cleanup)"""
    global _running_processors, _processor_stop_flags

    logger.info("Stopping all video processors...")

    # Set stop flags for all processors
    for workstation_id in list(_running_processors.keys()):
        _processor_stop_flags[workstation_id] = True

    # Wait for all threads to finish
    for workstation_id, thread in list(_running_processors.items()):
        thread.join(timeout=5.0)

    # Clear all dictionaries
    _running_processors.clear()
    _processor_stop_flags.clear()

    logger.info("All video processors stopped")

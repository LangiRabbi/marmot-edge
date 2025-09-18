"""
YOLOv11 person detection and tracking service with BoT-SORT
"""
import io
import os
import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image
from ultralytics import YOLO
import cv2

logger = logging.getLogger(__name__)


class YOLOTrackingService:
    """Service for YOLOv11 person detection and tracking with BoT-SORT"""

    def __init__(self, confidence_threshold: float = 0.5, tracker: str = "botsort.yaml"):
        """
        Initialize YOLO tracking service

        Args:
            confidence_threshold: Minimum confidence for detections
            tracker: Tracker configuration file (botsort.yaml or bytetrack.yaml)
        """
        self.confidence_threshold = confidence_threshold
        self.tracker = tracker
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize YOLOv11 model"""
        try:
            # Load YOLOv11 nano model for faster inference
            # Will download model if not cached
            self.model = YOLO('yolo11n.pt')
            logger.info(f"YOLOv11 model loaded successfully with {self.tracker} tracker")
        except Exception as e:
            logger.error(f"Failed to load YOLOv11 model: {e}")
            raise

    def track_persons(self, image_data: bytes, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Track persons in image with persistent IDs

        Args:
            image_data: Image data as bytes
            persist: Maintain track IDs across frames

        Returns:
            List of tracking dictionaries with bbox, confidence, and track_id
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert PIL to numpy for YOLO tracking
            image_np = np.array(image)

            # Run tracking with BoT-SORT
            results = self.model.track(
                image_np,
                conf=self.confidence_threshold,
                classes=[0],  # class 0 = person
                tracker=self.tracker,
                persist=persist
            )

            trackings = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())

                        # Get track ID if available
                        track_id = None
                        if box.id is not None:
                            track_id = int(box.id[0].cpu().numpy())

                        tracking = {
                            'bbox': {
                                'x1': float(x1),
                                'y1': float(y1),
                                'x2': float(x2),
                                'y2': float(y2)
                            },
                            'confidence': confidence,
                            'class': 'person',
                            'track_id': track_id
                        }
                        trackings.append(tracking)

            logger.info(f"Tracked {len(trackings)} persons with confidence >= {self.confidence_threshold}")
            return trackings

        except Exception as e:
            logger.error(f"Person tracking failed: {e}")
            raise

    def track_persons_from_file(self, image_path: str, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Track persons from image file

        Args:
            image_path: Path to image file
            persist: Maintain track IDs across frames

        Returns:
            List of tracking dictionaries
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return self.track_persons(image_data, persist=persist)
        except Exception as e:
            logger.error(f"Failed to track persons from file {image_path}: {e}")
            raise

    def track_video_stream(self, video_source: str, persist: bool = True) -> None:
        """
        Track persons in video stream (for real-time monitoring)

        Args:
            video_source: Video source (RTSP, USB camera, file path)
            persist: Maintain track IDs across frames
        """
        try:
            # This will be used for real-time video processing
            # Returns generator of tracking results per frame
            results = self.model.track(
                source=video_source,
                conf=self.confidence_threshold,
                classes=[0],  # person only
                tracker=self.tracker,
                persist=persist,
                stream=True  # Use streaming for real-time
            )

            for result in results:
                yield self._process_tracking_result(result)

        except Exception as e:
            logger.error(f"Video stream tracking failed: {e}")
            raise

    def _process_tracking_result(self, result) -> List[Dict[str, Any]]:
        """Process single tracking result"""
        trackings = []
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())

                track_id = None
                if box.id is not None:
                    track_id = int(box.id[0].cpu().numpy())

                tracking = {
                    'bbox': {
                        'x1': float(x1),
                        'y1': float(y1),
                        'x2': float(x2),
                        'y2': float(y2)
                    },
                    'confidence': confidence,
                    'class': 'person',
                    'track_id': track_id
                }
                trackings.append(tracking)

        return trackings

    def get_person_centers_with_ids(self, trackings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get center points of tracked persons with their IDs

        Args:
            trackings: List of tracking dictionaries

        Returns:
            List of dictionaries with center coordinates and track_id
        """
        centers = []
        for tracking in trackings:
            bbox = tracking['bbox']
            center_x = (bbox['x1'] + bbox['x2']) / 2
            center_y = (bbox['y1'] + bbox['y2']) / 2

            centers.append({
                'center_x': center_x,
                'center_y': center_y,
                'track_id': tracking['track_id'],
                'confidence': tracking['confidence']
            })

        return centers

    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Confidence threshold updated to {threshold}")
        else:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")

    def set_tracker(self, tracker: str):
        """
        Switch tracking algorithm

        Args:
            tracker: 'botsort.yaml' or 'bytetrack.yaml'
        """
        if tracker in ['botsort.yaml', 'bytetrack.yaml']:
            self.tracker = tracker
            logger.info(f"Tracker switched to {tracker}")
        else:
            raise ValueError("Tracker must be 'botsort.yaml' or 'bytetrack.yaml'")


# Backward compatibility - keep old detection service
class YOLODetectionService(YOLOTrackingService):
    """Legacy detection service - redirects to tracking service"""

    def detect_persons(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Legacy detection method"""
        return self.track_persons(image_data, persist=False)

    def detect_persons_from_file(self, image_path: str) -> List[Dict[str, Any]]:
        """Legacy detection method"""
        return self.track_persons_from_file(image_path, persist=False)

    def get_person_centers(self, detections: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """Legacy center calculation"""
        centers = []
        for detection in detections:
            bbox = detection['bbox']
            center_x = (bbox['x1'] + bbox['x2']) / 2
            center_y = (bbox['y1'] + bbox['y2']) / 2
            centers.append((center_x, center_y))
        return centers


# Global service instances
_yolo_tracking_service = None
_yolo_detection_service = None


def get_yolo_tracking_service() -> YOLOTrackingService:
    """Get global YOLO tracking service instance"""
    global _yolo_tracking_service
    if _yolo_tracking_service is None:
        _yolo_tracking_service = YOLOTrackingService()
    return _yolo_tracking_service


def get_yolo_service() -> YOLODetectionService:
    """Get global YOLO service instance (backward compatibility)"""
    global _yolo_detection_service
    if _yolo_detection_service is None:
        _yolo_detection_service = YOLODetectionService()
    return _yolo_detection_service
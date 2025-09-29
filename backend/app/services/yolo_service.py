"""
YOLOv11 person detection and tracking service with BoT-SORT
"""

import io
import logging
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from PIL import Image
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class YOLOTrackingService:
    """Service for YOLOv11 person detection and tracking with BoT-SORT"""

    def __init__(self, confidence_threshold: float = 0.6, tracker: str | None = "botsort.yaml"):
        """
        Initialize YOLO tracking service

        Args:
            confidence_threshold: Minimum confidence for detections (default: 0.6 for industrial use)
            tracker: Tracker configuration file (default: botsort.yaml for better tracking)
        """
        self.confidence_threshold = confidence_threshold
        self.tracker = tracker  # Default to BoT-SORT for better multi-person tracking
        self.model: Optional[Any] = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize YOLOv11 model with warmup.

        Uses `YOLO_MODEL_PATH` environment variable when provided. Falls back to
        the default 'yolo11n.pt' model. If CUDA is requested but unavailable,
        falls back to CPU and logs a warning.
        """
        import os

        model_path = os.environ.get("YOLO_MODEL_PATH", "yolo11n.pt")
        try:
            logger.info(f"Loading YOLO model from: {model_path}")
            self.model = YOLO(model_path)
            # Narrow type for static checkers
            model = self.model
            assert model is not None

            # Explicit device selection: prefer CUDA when available
            try:
                import torch

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                # Move model to device if supported
                try:
                    model.to(device)
                    logger.info(f"Moved model to device: {device}")
                except Exception:
                    logger.debug("Model .to(device) not supported or failed; continuing with default device")
            except Exception:
                logger.debug("Torch not available to check CUDA; proceeding without explicit device selection")
            logger.info(f"YOLOv11 model loaded successfully with {self.tracker} tracker")

            # Warmup: first inference is often slower due to model compilation
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            try:
                _ = model.track(dummy_frame, persist=False, verbose=False)
                logger.info("Model warmup completed")
            except Exception as warmup_exc:
                # If warmup fails due to CUDA issues, attempt CPU-only run
                logger.warning(f"Model warmup failed: {warmup_exc}. Trying CPU fallback.")
                try:
                    # Force CPU by setting device
                    try:
                        model.to("cpu")
                    except Exception:
                        logger.debug("Model .to('cpu') not supported; continuing and retrying track() on CPU if possible")
                    _ = model.track(dummy_frame, persist=False, verbose=False)
                    logger.info("Model warmup completed on CPU")
                except Exception as cpu_exc:
                    logger.error(f"Model warmup failed on CPU as well: {cpu_exc}")
                    raise

        except Exception as e:
            logger.error(f"Failed to load YOLOv11 model from {model_path}: {e}")
            raise

    def track_persons(
        self, image_data, persist: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Track persons in image with persistent IDs

        Args:
            image_data: Image data as bytes or numpy array
            persist: Maintain track IDs across frames

        Returns:
            List of tracking dictionaries with bbox, confidence, and track_id
        """
        try:
            # Handle both bytes and numpy array inputs for zero-copy optimization
            if isinstance(image_data, bytes):
                # Legacy path: Convert bytes to PIL Image
                image = Image.open(io.BytesIO(image_data))
                # Convert to RGB if needed
                if image.mode != "RGB":
                    image = image.convert("RGB")
                # Convert PIL to numpy for YOLO tracking
                image_np = np.array(image)
            else:
                # Optimized path: Direct numpy array (zero-copy)
                image_np = image_data

            # Smart BGR/RGB detection and conversion
            # Only convert if we detect BGR format (OpenCV typically uses BGR)
            if isinstance(image_np, np.ndarray) and image_np.ndim == 3 and image_np.shape[2] == 3:
                # Check if image is likely BGR by analyzing color distribution
                # Skip conversion for now - YOLO handles both formats
                # TODO: Implement smart detection based on blue channel dominance
                pass  # Let YOLO handle the format automatically

            # Prepare kwargs for tracker: only pass tracker if configured
            track_kwargs: Dict[str, Any] = {
                "conf": self.confidence_threshold,
                "classes": [0],  # class 0 = person
                "persist": persist,
            }
            if self.tracker:
                # if tracker looks like a path, optionally check existence
                try:
                    import os as _os

                    if _os.path.exists(self.tracker):
                        track_kwargs["tracker"] = self.tracker
                    else:
                        # Pass tracker name as-is (some ultralytics builds accept named trackers)
                        track_kwargs["tracker"] = self.tracker
                except Exception:
                    track_kwargs["tracker"] = self.tracker

            # Ensure model is loaded and narrow type for static checkers
            if self.model is None:
                raise RuntimeError("YOLO model is not initialized")
            model = self.model
            assert model is not None

            # Run tracking with configured kwargs
            results = model.track(image_np, **track_kwargs)

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
                            "bbox": {
                                "x1": float(x1),
                                "y1": float(y1),
                                "x2": float(x2),
                                "y2": float(y2),
                            },
                            "confidence": confidence,
                            "class": "person",
                            "track_id": track_id,
                        }
                        trackings.append(tracking)

            # Enhanced logging with bbox format details
            if trackings:
                sample_bbox = trackings[0]["bbox"] if trackings else None
                logger.info(
                    f"Tracked {len(trackings)} persons (conf>={self.confidence_threshold}), "
                    f"bbox format: {type(sample_bbox).__name__ if sample_bbox else 'None'}"
                )
            else:
                logger.debug(f"No persons detected (conf>={self.confidence_threshold})")
            return trackings

        except Exception as e:
            logger.error(f"Person tracking failed: {e}")
            raise

    def track_persons_from_file(
        self, image_path: str, persist: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Track persons from image file

        Args:
            image_path: Path to image file
            persist: Maintain track IDs across frames

        Returns:
            List of tracking dictionaries
        """
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            return self.track_persons(image_data, persist=persist)
        except Exception as e:
            logger.error(f"Failed to track persons from file {image_path}: {e}")
            raise

    from typing import Generator

    def track_video_stream(self, video_source: str, persist: bool = True) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Track persons in video stream (for real-time monitoring)

        Args:
            video_source: Video source (RTSP, USB camera, file path)
            persist: Maintain track IDs across frames
        """
        try:
            # This will be used for real-time video processing
            # Returns generator of tracking results per frame
            if self.model is None:
                raise RuntimeError("YOLO model is not initialized")
            model = self.model
            assert model is not None

            results = model.track(
                source=video_source,
                conf=self.confidence_threshold,
                classes=[0],  # person only
                tracker=self.tracker,
                persist=persist,
                stream=True,  # Use streaming for real-time
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
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                    },
                    "confidence": confidence,
                    "class": "person",
                    "track_id": track_id,
                }
                trackings.append(tracking)

        return trackings

    def get_person_centers_with_ids(
        self, trackings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get center points of tracked persons with their IDs

        Args:
            trackings: List of tracking dictionaries

        Returns:
            List of dictionaries with center coordinates and track_id
        """
        centers = []
        for tracking in trackings:
            bbox = tracking["bbox"]
            center_x = (bbox["x1"] + bbox["x2"]) / 2
            center_y = (bbox["y1"] + bbox["y2"]) / 2

            centers.append(
                {
                    "center_x": center_x,
                    "center_y": center_y,
                    "track_id": tracking["track_id"],
                    "confidence": tracking["confidence"],
                }
            )

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
        if tracker in ["botsort.yaml", "bytetrack.yaml"]:
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

    def get_person_centers(
        self, detections: List[Dict[str, Any]]
    ) -> List[Tuple[float, float]]:
        """Legacy center calculation"""
        centers = []
        for detection in detections:
            bbox = detection["bbox"]
            center_x = (bbox["x1"] + bbox["x2"]) / 2
            center_y = (bbox["y1"] + bbox["y2"]) / 2
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

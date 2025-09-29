import os
import pytest

# Ensure we import the service from the app
from backend.app.services.yolo_service import YOLOTrackingService


def test_yolo_service_instantiation():
    """Smoke test: instantiate YOLOTrackingService and ensure model is loaded or raises a clear error."""
    # Allow tests to run in environments where model file may not exist by
    # honoring YOLO_MODEL_PATH env var; the test will surface import/load errors.
    svc = None
    try:
        svc = YOLOTrackingService()
    except Exception as e:
        # If model loading fails due to missing dependencies (torch/ultralytics) or missing weights,
        # fail the test with the original exception message to make diagnosis easier.
        pytest.fail(f"YOLOTrackingService failed to initialize: {e}")

    # Basic post-conditions
    assert svc is not None
    assert getattr(svc, "model", None) is not None, "YOLO model should be initialized and not None"

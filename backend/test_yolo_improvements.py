#!/usr/bin/env python3
"""
Test improved YOLO service with BoT-SORT tracking
"""

import sys
import time
import numpy as np
from datetime import datetime

sys.path.append(".")

def test_improved_yolo():
    """Test the improved YOLO service with proper bbox handling"""
    from app.services.yolo_service import get_yolo_tracking_service

    print("="*60)
    print("Testing Improved YOLO Service")
    print("="*60)

    # Get the YOLO service (should now use BoT-SORT by default)
    yolo_service = get_yolo_tracking_service()

    # Check configuration
    print(f"✓ Confidence threshold: {yolo_service.confidence_threshold}")
    print(f"✓ Tracker configured: {yolo_service.tracker}")
    print(f"✓ Model loaded: {yolo_service.model is not None}")
    print()

    # Create a test image (black with white rectangles to simulate people)
    test_image = np.zeros((640, 640, 3), dtype=np.uint8)
    # Add some white rectangles as "people"
    test_image[100:300, 100:200] = 255  # Person 1
    test_image[200:400, 400:500] = 255  # Person 2

    print("Testing detection on synthetic image...")
    start_time = time.time()

    try:
        # Run detection
        trackings = yolo_service.track_persons(test_image, persist=True)

        elapsed = (time.time() - start_time) * 1000
        print(f"✓ Detection completed in {elapsed:.2f}ms")
        print(f"✓ Detected {len(trackings)} persons")

        # Check bbox format
        if trackings:
            sample_tracking = trackings[0]
            bbox = sample_tracking.get("bbox", {})
            print(f"\nBbox format verification:")
            print(f"  - Type: {type(bbox).__name__}")
            print(f"  - Keys: {list(bbox.keys()) if isinstance(bbox, dict) else 'N/A'}")
            print(f"  - Track ID: {sample_tracking.get('track_id', 'None')}")
            print(f"  - Confidence: {sample_tracking.get('confidence', 0):.2%}")

            # Verify bbox structure
            if isinstance(bbox, dict):
                print("✓ Bbox is correctly formatted as dictionary")
                has_all_keys = all(k in bbox for k in ["x1", "y1", "x2", "y2"])
                if has_all_keys:
                    print("✓ All required bbox keys present (x1, y1, x2, y2)")
                else:
                    print("✗ Missing bbox keys!")
            else:
                print("✗ Bbox is not a dictionary - needs fixing!")
        else:
            print("\nNo detections on synthetic image (expected for simple test)")

    except Exception as e:
        print(f"✗ Error during detection: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_improved_yolo()
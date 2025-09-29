#!/usr/bin/env python3
"""
Test YOLO detection on real video file
"""

import sys
import cv2
import time
from datetime import datetime

sys.path.append(".")

def test_video_detection():
    """Test YOLO detection on actual video file"""
    from app.services.yolo_service import get_yolo_tracking_service

    print("="*60)
    print("Testing YOLO on Real Video")
    print("="*60)

    # Video path from user's Downloads
    video_path = r"C:\Users\uzytkownik\Downloads\wideo_pionowe.mp4"

    # Get YOLO service
    yolo_service = get_yolo_tracking_service()
    print(f"✓ YOLO Service initialized")
    print(f"  - Confidence: {yolo_service.confidence_threshold}")
    print(f"  - Tracker: {yolo_service.tracker}")
    print()

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"✗ Failed to open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"✓ Video loaded: {total_frames} frames @ {fps:.2f} FPS")
    print()

    # Test on first 5 frames
    test_frames = 5
    frame_results = []

    for i in range(test_frames):
        ret, frame = cap.read()
        if not ret:
            break

        start_time = time.time()

        # Run detection (frame is already numpy array in BGR from OpenCV)
        trackings = yolo_service.track_persons(frame, persist=True)

        elapsed_ms = (time.time() - start_time) * 1000

        # Store results
        frame_results.append({
            'frame': i + 1,
            'detections': len(trackings),
            'time_ms': elapsed_ms,
            'trackings': trackings
        })

        print(f"Frame {i+1}: {len(trackings)} persons detected in {elapsed_ms:.2f}ms")

        # Show details for first detection
        if trackings and i == 0:
            first = trackings[0]
            bbox = first.get('bbox', {})
            print(f"  Sample detection:")
            print(f"    - Bbox type: {type(bbox).__name__}")
            print(f"    - Track ID: {first.get('track_id', 'None')}")
            print(f"    - Confidence: {first.get('confidence', 0):.2%}")
            if isinstance(bbox, dict):
                print(f"    - Bbox keys: {list(bbox.keys())}")
                print(f"    - Position: x1={bbox.get('x1', 0):.0f}, y1={bbox.get('y1', 0):.0f}")

    cap.release()

    # Summary
    print()
    print("Summary:")
    print("-" * 40)
    avg_detections = sum(r['detections'] for r in frame_results) / len(frame_results)
    avg_time = sum(r['time_ms'] for r in frame_results) / len(frame_results)
    print(f"✓ Average detections: {avg_detections:.1f} persons/frame")
    print(f"✓ Average processing: {avg_time:.2f}ms/frame")
    print(f"✓ Effective FPS: {1000/avg_time:.1f}")

    # Check if tracking IDs are consistent
    if len(frame_results) > 1:
        track_ids_present = all(
            any(t.get('track_id') is not None for t in r['trackings'])
            for r in frame_results if r['trackings']
        )
        if track_ids_present:
            print(f"✓ Tracking IDs are being generated")
        else:
            print(f"✗ No tracking IDs found - tracker may not be working")

    print()
    print("="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_video_detection()
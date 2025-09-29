#!/usr/bin/env python3
"""
Test YOLOv11 detection directly on wideo_pionowe.mp4 with various confidence levels
"""
import sys
import cv2
import time
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))

from app.services.yolo_service import get_yolo_tracking_service

def test_yolo_on_video():
    """Test YOLOv11 on local video with different confidence thresholds"""
    video_path = "C:/Users/uzytkownik/Downloads/wideo_pionowe.mp4"

    print(f"🎬 Testing YOLOv11 on: {video_path}")

    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return

    # Test different confidence levels
    confidence_levels = [0.1, 0.3, 0.5, 0.7]

    for conf_level in confidence_levels:
        print(f"\n🔍 Testing with confidence threshold: {conf_level}")

        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Get YOLOv11 service
        yolo_service = get_yolo_tracking_service()
        yolo_service.set_confidence_threshold(conf_level)

        people_found = 0
        frames_tested = 0

        # Test first 10 frames
        for frame_num in range(10):
            ret, frame = cap.read()
            if not ret:
                break

            # Convert frame to bytes
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Run detection
            start_time = time.time()
            trackings = yolo_service.track_persons(frame_bytes, persist=False)
            detection_time = (time.time() - start_time) * 1000

            if trackings:
                people_found += len(trackings)
                print(f"  📸 Frame {frame_num}: {len(trackings)} people detected ({detection_time:.1f}ms)")
                for i, track in enumerate(trackings):
                    bbox = track['bbox']
                    conf = track['confidence']
                    print(f"    Person {i+1}: confidence={conf:.3f}, bbox=({bbox['x1']:.0f}, {bbox['y1']:.0f}, {bbox['x2']:.0f}, {bbox['y2']:.0f})")
            else:
                print(f"  📸 Frame {frame_num}: 0 people detected ({detection_time:.1f}ms)")

            frames_tested += 1

        print(f"  📊 Results: {people_found} people found in {frames_tested} frames")

    cap.release()
    print("\n✅ YOLOv11 test completed")

if __name__ == "__main__":
    test_yolo_on_video()
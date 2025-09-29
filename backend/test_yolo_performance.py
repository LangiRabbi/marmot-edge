import time
import numpy as np
from app.services.yolo_service import get_yolo_tracking_service

def test_performance():
    print("=== YOLOv11 Performance Test ===\n")

    yolo_service = get_yolo_tracking_service()

    dummy_frames = [np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8) for _ in range(50)]

    print("Testing with numpy arrays (zero-copy optimized)...")
    start_time = time.time()

    latencies = []
    for i, frame in enumerate(dummy_frames):
        frame_start = time.time()
        trackings = yolo_service.track_persons(frame, persist=True)
        frame_end = time.time()

        latency_ms = (frame_end - frame_start) * 1000
        latencies.append(latency_ms)

        if i % 10 == 0:
            print(f"Frame {i}: {latency_ms:.2f}ms, detections: {len(trackings)}")

    total_time = time.time() - start_time
    fps = len(dummy_frames) / total_time
    avg_latency = np.mean(latencies)
    min_latency = np.min(latencies)
    max_latency = np.max(latencies)

    print(f"\n=== Results ===")
    print(f"Total frames: {len(dummy_frames)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average FPS: {fps:.2f}")
    print(f"Average latency: {avg_latency:.2f}ms")
    print(f"Min latency: {min_latency:.2f}ms")
    print(f"Max latency: {max_latency:.2f}ms")

    print(f"\n=== Expected vs Actual ===")
    print(f"Previous FPS: 14.65")
    print(f"Current FPS: {fps:.2f}")
    print(f"Improvement: {((fps - 14.65) / 14.65 * 100):.1f}%")
    print(f"\nPrevious latency: 208ms")
    print(f"Current latency: {avg_latency:.2f}ms")
    print(f"Reduction: {((208 - avg_latency) / 208 * 100):.1f}%")

if __name__ == "__main__":
    test_performance()
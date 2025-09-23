import asyncio
import time
from app.workers.file_video_processor import FileVideoProcessor
import cv2
import os

def analyze_full_video():
    """Analyze the entire test video and report detections per frame"""
    
    test_video_path = "test_video.mp4"
    if not os.path.exists(test_video_path):
        print(f"ERROR: Test video not found at {test_video_path}")
        return
        
    # Open video to get properties
    cap = cv2.VideoCapture(test_video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration_seconds = total_frames / fps if fps > 0 else 0
    cap.release()
    
    print(f"=== FULL VIDEO ANALYSIS FOR WORKSTATION 7 (ziemniaki) ===")
    print(f"Video: {test_video_path}")
    print(f"Total Frames: {total_frames}")
    print(f"FPS: {fps}")
    print(f"Duration: {duration_seconds:.2f} seconds")
    print("=" * 60)
    
    # Create processor to analyze
    processor = FileVideoProcessor("7", test_video_path)
    
    # Process video and count detections per second
    cap = cv2.VideoCapture(test_video_path)
    frame_number = 0
    second_detections = {}
    current_second = 0
    
    while cap.isOpened() and frame_number < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Calculate current second
        current_second = int(frame_number / fps)
        
        # Get detection count for this frame
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        
        try:
            trackings = processor.yolo_service.track_persons(frame_bytes, persist=True)
            person_count = len(trackings)
            
            # Store detection count
            if current_second not in second_detections:
                second_detections[current_second] = []
            second_detections[current_second].append(person_count)
            
            frame_number += 1
            
            # Print progress every second
            if frame_number % int(fps) == 0:
                print(f"Processed second {current_second}: {len(second_detections.get(current_second, []))} frames")
                
        except Exception as e:
            print(f"Error processing frame {frame_number}: {e}")
            break
    
    cap.release()
    
    # Print results
    print("\n=== DETECTION RESULTS PER SECOND ===")
    for second in sorted(second_detections.keys()):
        detections = second_detections[second]
        avg_persons = sum(detections) / len(detections) if detections else 0
        max_persons = max(detections) if detections else 0
        min_persons = min(detections) if detections else 0
        
        print(f"Second {second:3d}: "
              f"Avg: {avg_persons:.1f} persons, "
              f"Max: {max_persons} persons, "
              f"Min: {min_persons} persons, "
              f"Frames: {len(detections)}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total seconds analyzed: {len(second_detections)}")
    print(f"Total frames analyzed: {frame_number}")
    all_detections = []
    for dets in second_detections.values():
        all_detections.extend(dets)
    if all_detections:
        print(f"Average persons per frame: {sum(all_detections)/len(all_detections):.2f}")
        print(f"Max persons detected: {max(all_detections)}")
        print(f"Min persons detected: {min(all_detections)}")

if __name__ == "__main__":
    analyze_full_video()


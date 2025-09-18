#!/usr/bin/env python3
"""
Test script for video streaming and processing system
Tests multiple streams with rectangular zones
"""
import asyncio
import time
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8001/api/v1"

def test_api_connection():
    """Test basic API connection"""
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"[OK] API Status: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] API Connection failed: {e}")
        return False

def test_create_file_stream():
    """Test creating a video stream from file"""
    stream_config = {
        "stream_id": "test_file_stream",
        "source_url": "test_video.mp4",
        "name": "Test Video Stream",
        "stream_type": "file",
        "target_fps": 15,
        "auto_reconnect": False,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 720,
                "y_max": 640,
                "zone_id": 1,
                "name": "Top Zone"
            },
            {
                "x_min": 0,
                "y_min": 640,
                "x_max": 720,
                "y_max": 1280,
                "zone_id": 2,
                "name": "Bottom Zone"
            }
        ]
    }

    try:
        response = requests.post(f"{BASE_URL}/video-streams/", json=stream_config)
        print(f"[OK] Stream created: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] Stream creation failed: {e}")
        return False

def test_create_usb_stream():
    """Test creating USB camera stream"""
    stream_config = {
        "stream_id": "usb_camera_test",
        "source_url": "0",  # First USB camera
        "name": "USB Test Camera",
        "stream_type": "usb",
        "target_fps": 10,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 320,
                "y_max": 240,
                "zone_id": 3,
                "name": "Left Station"
            },
            {
                "x_min": 320,
                "y_min": 0,
                "x_max": 640,
                "y_max": 240,
                "zone_id": 4,
                "name": "Right Station"
            }
        ]
    }

    try:
        response = requests.post(f"{BASE_URL}/video-streams/", json=stream_config)
        print(f"[OK] USB Stream created: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] USB Stream creation failed: {e}")
        return False

def test_list_streams():
    """Test listing all streams"""
    try:
        response = requests.get(f"{BASE_URL}/video-streams/")
        streams = response.json()
        print(f"[OK] Active streams ({len(streams)}):")
        for stream in streams:
            print(f"   - {stream['stream_id']}: {stream['name']} ({stream['status']})")
        return streams
    except Exception as e:
        print(f"[ERROR] List streams failed: {e}")
        return []

def test_stream_status(stream_id: str):
    """Test getting stream status"""
    try:
        response = requests.get(f"{BASE_URL}/video-streams/{stream_id}/status")
        status = response.json()
        print(f"[OK] Stream {stream_id} status:")
        print(f"   Status: {status.get('status', 'unknown')}")
        print(f"   FPS: {status.get('fps_actual', 0):.1f}/{status.get('fps_target', 0)}")
        print(f"   Frames: {status.get('frame_count', 0)}")
        print(f"   Queue: {status.get('queue_size', 0)}")
        return status
    except Exception as e:
        print(f"[ERROR] Stream status failed: {e}")
        return {}

def test_processing_results(stream_id: str, limit: int = 3):
    """Test getting processing results"""
    try:
        response = requests.get(f"{BASE_URL}/video-streams/{stream_id}/results?limit={limit}")
        results = response.json()
        print(f"[OK] Processing results for {stream_id} ({len(results)} results):")

        for result in results:
            print(f"   Frame {result['frame_number']}: {result['person_count']} persons")
            print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
            print(f"   Zones analyzed: {len(result['zone_analysis']['zones'])}")

            # Show zone statuses
            for zone_id, zone_data in result['zone_analysis']['zones'].items():
                print(f"     Zone {zone_id}: {zone_data['status']} ({zone_data['person_count']} persons)")

        return results
    except Exception as e:
        print(f"[ERROR] Processing results failed: {e}")
        return []

def test_zone_efficiency(stream_id: str, zone_id: int, minutes: int = 5):
    """Test zone efficiency calculation"""
    try:
        response = requests.get(f"{BASE_URL}/video-streams/{stream_id}/zones/{zone_id}/efficiency?minutes={minutes}")
        efficiency = response.json()
        print(f"[OK] Zone {zone_id} efficiency (last {minutes} minutes):")
        print(f"   Efficiency: {efficiency['efficiency_percentage']:.1f}%")
        print(f"   Work time: {efficiency['work_minutes']:.1f} min")
        print(f"   Idle time: {efficiency['idle_minutes']:.1f} min")
        print(f"   Other time: {efficiency['other_minutes']:.1f} min")
        return efficiency
    except Exception as e:
        print(f"[ERROR] Zone efficiency failed: {e}")
        return {}

def test_system_statistics():
    """Test system statistics"""
    try:
        response = requests.get(f"{BASE_URL}/video-streams/system/statistics")
        stats = response.json()
        print(f"[OK] System statistics:")

        video_stats = stats.get('video_manager', {})
        processing_stats = stats.get('video_processor', {})

        print(f"   Active streams: {video_stats.get('active_streams', 0)}")
        print(f"   Total zones: {video_stats.get('total_zones', 0)}")
        print(f"   Frames processed: {processing_stats.get('frames_processed', 0)}")
        print(f"   Average FPS: {processing_stats.get('average_fps', 0):.1f}")
        print(f"   Processing queue: {processing_stats.get('processing_queue_size', 0)}")

        return stats
    except Exception as e:
        print(f"[ERROR] System statistics failed: {e}")
        return {}

def test_update_stream(stream_id: str):
    """Test updating stream configuration"""
    update_data = {
        "name": "Updated Test Stream",
        "target_fps": 20,
        "zones": [
            {
                "x_min": 50,
                "y_min": 50,
                "x_max": 670,
                "y_max": 590,
                "zone_id": 1,
                "name": "Updated Top Zone"
            },
            {
                "x_min": 50,
                "y_min": 690,
                "x_max": 670,
                "y_max": 1230,
                "zone_id": 2,
                "name": "Updated Bottom Zone"
            }
        ]
    }

    try:
        response = requests.put(f"{BASE_URL}/video-streams/{stream_id}", json=update_data)
        print(f"[OK] Stream updated: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] Stream update failed: {e}")
        return False

def test_delete_stream(stream_id: str):
    """Test deleting stream"""
    try:
        response = requests.delete(f"{BASE_URL}/video-streams/{stream_id}")
        print(f"[OK] Stream deleted: {response.json()}")
        return True
    except Exception as e:
        print(f"[ERROR] Stream deletion failed: {e}")
        return False

def main():
    """Run comprehensive video streaming tests"""
    print("Starting Video Streaming System Tests")
    print("=" * 50)

    # Test 1: API Connection
    print("\n1. Testing API Connection")
    if not test_api_connection():
        print("[ERROR] Cannot proceed without API connection")
        return

    # Test 2: Create File Stream
    print("\n2. Creating File-based Stream")
    file_stream_created = test_create_file_stream()

    # Test 3: Create USB Stream (optional - may fail if no camera)
    print("\n3. Creating USB Camera Stream")
    usb_stream_created = test_create_usb_stream()

    # Test 4: List Streams
    print("\n4. Listing All Streams")
    streams = test_list_streams()

    if not streams:
        print("[ERROR] No streams available for testing")
        return

    # Get first available stream for testing
    test_stream_id = streams[0]['stream_id']

    # Wait for stream to start processing
    print(f"\n5. Waiting for stream {test_stream_id} to start...")
    time.sleep(5)

    # Test 6: Stream Status
    print(f"\n6. Getting Stream Status")
    test_stream_status(test_stream_id)

    # Test 7: Processing Results
    print(f"\n7. Getting Processing Results")
    test_processing_results(test_stream_id)

    # Test 8: Zone Efficiency
    print(f"\n8. Testing Zone Efficiency")
    test_zone_efficiency(test_stream_id, 1, 5)  # Zone 1, last 5 minutes

    # Test 9: System Statistics
    print(f"\n9. System Statistics")
    test_system_statistics()

    # Test 10: Update Stream
    print(f"\n10. Updating Stream Configuration")
    test_update_stream(test_stream_id)

    # Wait a bit more for processing
    print(f"\n11. Processing for 10 seconds...")
    time.sleep(10)

    # Test 12: Final Results
    print(f"\n12. Final Processing Results")
    test_processing_results(test_stream_id, 5)

    # Test 13: Cleanup
    print(f"\n13. Cleaning Up Streams")
    for stream in streams:
        test_delete_stream(stream['stream_id'])

    print("\nVideo Streaming Tests Completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
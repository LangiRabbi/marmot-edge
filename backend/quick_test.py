#!/usr/bin/env python3
"""
Quick test for video streaming imports and basic functionality
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test all video streaming imports"""
    print("Testing imports...")

    try:
        from app.services.video_service import VideoManager, StreamConfig, Rectangle
        print("[OK] Video service imports")
    except Exception as e:
        print(f"[ERROR] Video service imports: {e}")
        return False

    try:
        from app.workers.video_processor import VideoProcessor, RectangleZoneAnalyzer
        print("[OK] Video processor imports")
    except Exception as e:
        print(f"[ERROR] Video processor imports: {e}")
        return False

    try:
        from app.services.zone_analyzer import ZoneAnalyzer
        print("[OK] Zone analyzer imports")
    except Exception as e:
        print(f"[ERROR] Zone analyzer imports: {e}")
        return False

    try:
        from app.services.yolo_service import get_yolo_tracking_service
        print("[OK] YOLO service imports")
    except Exception as e:
        print(f"[ERROR] YOLO service imports: {e}")
        return False

    return True

def test_basic_functionality():
    """Test basic video manager functionality"""
    print("\nTesting basic functionality...")

    try:
        from app.services.video_service import VideoManager, StreamConfig, Rectangle

        # Create video manager
        manager = VideoManager()
        print("[OK] Video manager created")

        # Create test rectangle
        rect = Rectangle(
            x_min=0, y_min=0, x_max=100, y_max=100,
            zone_id=1, name="Test Zone"
        )
        print("[OK] Rectangle created")

        # Create stream config
        config = StreamConfig(
            stream_id="test",
            source_url="test.mp4",
            name="Test Stream",
            stream_type="file"
        )
        print("[OK] Stream config created")

        # Test statistics
        stats = manager.get_statistics()
        print(f"[OK] Statistics: {stats}")

        return True

    except Exception as e:
        print(f"[ERROR] Basic functionality test: {e}")
        return False

def test_zone_analyzer():
    """Test rectangle zone analyzer"""
    print("\nTesting zone analyzer...")

    try:
        from app.workers.video_processor import RectangleZoneAnalyzer
        from app.services.video_service import Rectangle

        analyzer = RectangleZoneAnalyzer()
        print("[OK] Zone analyzer created")

        # Test rectangle zones
        rectangles = [
            Rectangle(0, 0, 100, 100, 1, "Zone 1"),
            Rectangle(100, 0, 200, 100, 2, "Zone 2")
        ]

        # Mock tracking data
        trackings = [
            {
                'track_id': 1,
                'bbox': {'x1': 50, 'y1': 50, 'x2': 60, 'y2': 60},
                'confidence': 0.9
            }
        ]

        # Test analysis
        result = analyzer.analyze_trackings_in_rectangles(trackings, rectangles, "test_stream")
        print(f"[OK] Zone analysis: {len(result['zones'])} zones analyzed")

        return True

    except Exception as e:
        print(f"[ERROR] Zone analyzer test: {e}")
        return False

def main():
    """Run quick tests"""
    print("Quick Video Streaming System Test")
    print("=" * 40)

    success = True

    # Test imports
    if not test_imports():
        success = False

    # Test basic functionality
    if not test_basic_functionality():
        success = False

    # Test zone analyzer
    if not test_zone_analyzer():
        success = False

    print("\n" + "=" * 40)
    if success:
        print("[OK] All tests passed!")
    else:
        print("[ERROR] Some tests failed!")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
import os
import sys

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_imports():
    try:
        from app.services.video_service import Rectangle, StreamConfig, VideoManager
        from app.workers.video_processor import RectangleZoneAnalyzer, VideoProcessor
        from app.services.zone_analyzer import ZoneAnalyzer
        from app.services.yolo_service import get_yolo_tracking_service
    except Exception as e:
        assert False, f"Import failed: {e}"


def test_basic_functionality():
    try:
        from app.services.video_service import Rectangle, StreamConfig, VideoManager

        manager = VideoManager()
        rect = Rectangle(x_min=0, y_min=0, x_max=100, y_max=100, zone_id=1, name="Test Zone")
        config = StreamConfig(stream_id="test", source_url="test.mp4", name="Test Stream", stream_type="file")

        stats = manager.get_statistics()

        assert manager is not None
        assert isinstance(rect, Rectangle)
        assert isinstance(config, StreamConfig)
        assert isinstance(stats, dict)
    except Exception as e:
        assert False, f"Basic functionality smoke failed: {e}"


def test_zone_analyzer():
    try:
        from app.services.video_service import Rectangle
        from app.workers.video_processor import RectangleZoneAnalyzer

        analyzer = RectangleZoneAnalyzer()
        rectangles = [Rectangle(0, 0, 100, 100, 1, "Zone 1"), Rectangle(100, 0, 200, 100, 2, "Zone 2")]
        trackings = [{"track_id": 1, "bbox": {"x1": 50, "y1": 50, "x2": 60, "y2": 60}, "confidence": 0.9}]

        result = analyzer.analyze_trackings_in_rectangles(trackings, rectangles, "test_stream")
        assert isinstance(result, dict)
    except Exception as e:
        assert False, f"Zone analyzer smoke failed: {e}"

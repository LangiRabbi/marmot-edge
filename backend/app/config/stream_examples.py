"""
Example stream configurations for testing video processing system
"""

from typing import Any, Dict, List

# USB Camera Examples
USB_CAMERA_EXAMPLES = [
    {
        "stream_id": "usb_cam_01",
        "source_url": "0",  # First USB camera
        "name": "Production Line Camera 1",
        "stream_type": "usb",
        "target_fps": 15,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 320,
                "y_max": 240,
                "zone_id": 1,
                "name": "Assembly Station 1",
            },
            {
                "x_min": 320,
                "y_min": 0,
                "x_max": 640,
                "y_max": 240,
                "zone_id": 2,
                "name": "Assembly Station 2",
            },
        ],
    },
    {
        "stream_id": "usb_cam_02",
        "source_url": "1",  # Second USB camera
        "name": "Quality Control Camera",
        "stream_type": "usb",
        "target_fps": 20,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 100,
                "y_min": 100,
                "x_max": 540,
                "y_max": 380,
                "zone_id": 3,
                "name": "QC Station",
            }
        ],
    },
]

# RTSP Stream Examples
RTSP_STREAM_EXAMPLES = [
    {
        "stream_id": "rtsp_warehouse_01",
        "source_url": "rtsp://admin:password@192.168.1.100:554/stream1",
        "name": "Warehouse Overview",
        "stream_type": "rtsp",
        "target_fps": 15,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 400,
                "y_max": 300,
                "zone_id": 4,
                "name": "Loading Dock",
            },
            {
                "x_min": 400,
                "y_min": 0,
                "x_max": 800,
                "y_max": 300,
                "zone_id": 5,
                "name": "Storage Area",
            },
            {
                "x_min": 0,
                "y_min": 300,
                "x_max": 800,
                "y_max": 600,
                "zone_id": 6,
                "name": "Packaging Area",
            },
        ],
    },
    {
        "stream_id": "rtsp_production_line",
        "source_url": "rtsp://192.168.1.101:8554/live/stream",
        "name": "Production Line Monitor",
        "stream_type": "rtsp",
        "target_fps": 25,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 200,
                "y_max": 400,
                "zone_id": 7,
                "name": "Station 1",
            },
            {
                "x_min": 200,
                "y_min": 0,
                "x_max": 400,
                "y_max": 400,
                "zone_id": 8,
                "name": "Station 2",
            },
            {
                "x_min": 400,
                "y_min": 0,
                "x_max": 600,
                "y_max": 400,
                "zone_id": 9,
                "name": "Station 3",
            },
            {
                "x_min": 600,
                "y_min": 0,
                "x_max": 800,
                "y_max": 400,
                "zone_id": 10,
                "name": "Final Assembly",
            },
        ],
    },
]

# File-based Examples (for testing)
FILE_STREAM_EXAMPLES = [
    {
        "stream_id": "test_video_vertical",
        "source_url": "/app/test_video.mp4",  # Path to test video
        "name": "Test Video - Vertical Format",
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
                "name": "Top Zone",
            },
            {
                "x_min": 0,
                "y_min": 640,
                "x_max": 720,
                "y_max": 1280,
                "zone_id": 2,
                "name": "Bottom Zone",
            },
        ],
    }
]

# IP Camera Examples
IP_CAMERA_EXAMPLES = [
    {
        "stream_id": "ip_cam_entrance",
        "source_url": "http://192.168.1.50/mjpeg/1/video.mjpg",
        "name": "Entrance Monitor",
        "stream_type": "ip",
        "target_fps": 10,
        "auto_reconnect": True,
        "zones": [
            {
                "x_min": 200,
                "y_min": 100,
                "x_max": 600,
                "y_max": 400,
                "zone_id": 11,
                "name": "Entry Zone",
            }
        ],
    }
]

# Combined example for multi-stream setup
MULTI_STREAM_SETUP = {
    "streams": [
        USB_CAMERA_EXAMPLES[0],  # USB camera for close monitoring
        RTSP_STREAM_EXAMPLES[0],  # RTSP for warehouse overview
        FILE_STREAM_EXAMPLES[0],  # File for testing
    ],
    "total_streams": 3,
    "total_zones": 9,
    "description": "Example multi-stream industrial monitoring setup",
}


def get_example_by_type(stream_type: str) -> List[Dict[str, Any]]:
    """Get example configurations by stream type"""
    examples = {
        "usb": USB_CAMERA_EXAMPLES,
        "rtsp": RTSP_STREAM_EXAMPLES,
        "file": FILE_STREAM_EXAMPLES,
        "ip": IP_CAMERA_EXAMPLES,
    }
    return examples.get(stream_type, [])


def get_test_setup() -> Dict[str, Any]:
    """Get a simple test setup for development"""
    return {
        "stream_id": "test_development",
        "source_url": "test_video.mp4",
        "name": "Development Test Stream",
        "stream_type": "file",
        "target_fps": 15,
        "auto_reconnect": False,
        "zones": [
            {
                "x_min": 0,
                "y_min": 0,
                "x_max": 360,
                "y_max": 640,
                "zone_id": 1,
                "name": "Left Zone",
            },
            {
                "x_min": 360,
                "y_min": 0,
                "x_max": 720,
                "y_max": 640,
                "zone_id": 2,
                "name": "Right Zone",
            },
        ],
    }


def validate_stream_config(config: Dict[str, Any]) -> bool:
    """Validate stream configuration"""
    required_fields = ["stream_id", "source_url", "name", "stream_type"]

    # Check required fields
    for field in required_fields:
        if field not in config:
            return False

    # Validate stream type
    if config["stream_type"] not in ["usb", "rtsp", "ip", "file"]:
        return False

    # Validate zones (max 10)
    zones = config.get("zones", [])
    if len(zones) > 10:
        return False

    # Validate zone format
    for zone in zones:
        required_zone_fields = ["x_min", "y_min", "x_max", "y_max", "zone_id"]
        for field in required_zone_fields:
            if field not in zone:
                return False

    return True

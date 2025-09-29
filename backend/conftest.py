import pytest


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


# Shared in-memory streams for tests
_STREAMS = [
    {"stream_id": "test_stream_1", "name": "Test Stream", "status": "running"}
]


def _make_status(stream_id=None):
    return {
        "status": "running" if stream_id else "ok",
        "fps_actual": 15.0,
        "fps_target": 15,
        "frame_count": 100,
        "queue_size": 0,
    }


def _make_results(limit=3):
    results = []
    for i in range(limit):
        results.append(
            {
                "frame_number": i,
                "person_count": 1,
                "processing_time_ms": 10.0,
                "zone_analysis": {"zones": {"1": {"status": "occupied", "person_count": 1}}},
            }
        )
    return results


def _mock_get(url, *args, **kwargs):
    # Simple heuristics based on URL to return DummyResponse objects
    if url.endswith("/status"):
        return DummyResponse(_make_status())

    if url.endswith("/video-streams/") or url.endswith("/video-streams"):
        return DummyResponse(_STREAMS)

    if "/video-streams/" in url and url.endswith("/status"):
        return DummyResponse(_make_status(stream_id=True))

    if "/results" in url:
        # parse limit if provided
        limit = 3
        if "limit=" in url:
            try:
                limit = int(url.split("limit=")[-1])
            except Exception:
                limit = 3
        return DummyResponse(_make_results(limit))

    if "/zones/" in url and "/efficiency" in url:
        return DummyResponse(
            {"efficiency_percentage": 75.0, "work_minutes": 3.0, "idle_minutes": 1.0, "other_minutes": 1.0}
        )

    if url.endswith("/video-streams/system/statistics"):
        return DummyResponse(
            {
                "video_manager": {"active_streams": len(_STREAMS), "total_zones": 2},
                "video_processor": {"frames_processed": 1000, "average_fps": 15.0, "processing_queue_size": 0},
            }
        )

    # Default
    return DummyResponse({})


def _mock_post(url, *args, **kwargs):
    if url.endswith("/video-streams/"):
        body = kwargs.get("json", {})
        # ensure stream_id exists
        if "stream_id" not in body:
            body["stream_id"] = f"stream_{len(_STREAMS) + 1}"
        body.setdefault("status", "created")
        _STREAMS.append(body)
        return DummyResponse(body, status_code=201)
    return DummyResponse({}, status_code=404)


def _mock_put(url, *args, **kwargs):
    # Echo the update for simplicity
    return DummyResponse(kwargs.get("json", {}))


def _mock_delete(url, *args, **kwargs):
    # Remove stream if exists
    for s in list(_STREAMS):
        if s["stream_id"] in url:
            _STREAMS.remove(s)
            return DummyResponse({"ok": True})
    return DummyResponse({"ok": False}, status_code=404)


@pytest.fixture(autouse=True)
def stub_requests(monkeypatch):
    """Monkeypatch requests.* methods so tests don't require a running API."""
    import requests

    monkeypatch.setattr(requests, "get", _mock_get)
    monkeypatch.setattr(requests, "post", _mock_post)
    monkeypatch.setattr(requests, "put", _mock_put)
    monkeypatch.setattr(requests, "delete", _mock_delete)


@pytest.fixture()
def stream_id():
    return _STREAMS[0]["stream_id"]


@pytest.fixture()
def zone_id():
    return 1

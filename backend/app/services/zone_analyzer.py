"""
Zone analysis service with tracking ID support
Optimized for rectangular zones only (max 10 zones per stream)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ZoneAnalyzer:
    """Service for analyzing persons in rectangular zones with tracking support (max 10 zones)"""

    MAX_ZONES_PER_ANALYSIS = 10

    def __init__(self):
        """Initialize zone analyzer"""
        self.track_history = {}  # track_id -> list of zone entries with timestamps
        self.zone_status_history = {}  # zone_id -> list of status changes
        self.current_zone_occupancy = {}  # zone_id -> set of track_ids

    def analyze_detections_in_zones(
        self, trackings: List[Dict[str, Any]], zones: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze which tracked persons are in which rectangular zones (max 10)

        Args:
            trackings: List of tracking results with track_id, bbox, confidence
            zones: List of zone definitions with id, coordinates, workstation_id (max 10)

        Returns:
            Dictionary with zone analysis results
        """
        try:
            analysis_timestamp = datetime.utcnow()
            zone_results = {}

            # Limit zones to maximum allowed
            limited_zones = zones[: self.MAX_ZONES_PER_ANALYSIS]
            if len(zones) > self.MAX_ZONES_PER_ANALYSIS:
                logger.warning(
                    f"Too many zones ({len(zones)}), using first {self.MAX_ZONES_PER_ANALYSIS}"
                )

            # Initialize zone occupancy for this frame
            current_occupancy = {zone["id"]: set() for zone in limited_zones}

            # Check each tracking against each zone (optimized for rectangles)
            for tracking in trackings:
                if tracking["track_id"] is None:
                    continue

                person_center = self._get_person_center(tracking)

                # Check all zones (max 10) - O(10) complexity
                for zone in limited_zones:
                    if self._is_point_in_zone(person_center, zone["coordinates"]):
                        current_occupancy[zone["id"]].add(tracking["track_id"])

                        # Update tracking history
                        self._update_track_history(
                            tracking["track_id"], zone["id"], analysis_timestamp
                        )

            # Calculate zone statuses and update occupancy tracking
            for zone in limited_zones:
                zone_id = zone["id"]
                person_count = len(current_occupancy[zone_id])

                # Determine zone status based on person count
                if person_count == 0:
                    status = "idle"
                elif person_count == 1:
                    status = "work"
                else:
                    status = "other"

                # Update zone status history
                self._update_zone_status_history(zone_id, status, analysis_timestamp)

                zone_results[zone_id] = {
                    "zone_id": zone_id,
                    "workstation_id": zone.get("workstation_id"),
                    "person_count": person_count,
                    "status": status,
                    "track_ids": list(current_occupancy[zone_id]),
                    "timestamp": analysis_timestamp,
                    "zone_name": zone.get("name", f"Zone {zone_id}"),
                }

            # Update global occupancy tracking
            self.current_zone_occupancy = current_occupancy

            return {
                "analysis_timestamp": analysis_timestamp,
                "zones": zone_results,
                "total_persons_detected": len(
                    [t for t in trackings if t["track_id"] is not None]
                ),
                "zones_analyzed": len(limited_zones),
            }

        except Exception as e:
            logger.error(f"Zone analysis failed: {e}")
            raise

    def _get_person_center(self, tracking: Dict[str, Any]) -> Tuple[float, float]:
        """Get center point of person bounding box"""
        bbox = tracking["bbox"]
        center_x = (bbox["x1"] + bbox["x2"]) / 2
        center_y = (bbox["y1"] + bbox["y2"]) / 2
        return (center_x, center_y)

    def _is_point_in_zone(
        self, point: Tuple[float, float], zone_coordinates: Dict[str, Any]
    ) -> bool:
        """
        Check if point is inside rectangular zone (O(1) operation)

        Args:
            point: (x, y) coordinates
            zone_coordinates: Zone coordinates dict with rectangle bounds
                             {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100}
                             OR legacy format {"points": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]}

        Returns:
            True if point is inside rectangle
        """
        try:
            x, y = point

            # New rectangle format (preferred)
            if all(
                key in zone_coordinates for key in ["x_min", "y_min", "x_max", "y_max"]
            ):
                return (
                    zone_coordinates["x_min"] <= x <= zone_coordinates["x_max"]
                    and zone_coordinates["y_min"] <= y <= zone_coordinates["y_max"]
                )

            # Legacy points format - convert to rectangle
            elif "points" in zone_coordinates and len(zone_coordinates["points"]) >= 2:
                points = zone_coordinates["points"]

                # Extract min/max coordinates from points (assuming rectangle)
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]

                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                return x_min <= x <= x_max and y_min <= y <= y_max

            else:
                logger.warning("Invalid zone coordinates format")
                return False

        except Exception as e:
            logger.warning(f"Error checking point in zone: {e}")
            return False

    def _update_track_history(self, track_id: int, zone_id: int, timestamp: datetime):
        """Update tracking history for person movement"""
        if track_id not in self.track_history:
            self.track_history[track_id] = []

        # Add zone entry with timestamp
        self.track_history[track_id].append(
            {"zone_id": zone_id, "timestamp": timestamp, "entry_type": "zone_presence"}
        )

        # Keep only recent history (last hour)
        cutoff_time = timestamp - timedelta(hours=1)
        self.track_history[track_id] = [
            entry
            for entry in self.track_history[track_id]
            if entry["timestamp"] > cutoff_time
        ]

    def _update_zone_status_history(
        self, zone_id: int, status: str, timestamp: datetime
    ):
        """Update zone status change history"""
        if zone_id not in self.zone_status_history:
            self.zone_status_history[zone_id] = []

        # Only record status changes
        if (
            not self.zone_status_history[zone_id]
            or self.zone_status_history[zone_id][-1]["status"] != status
        ):

            self.zone_status_history[zone_id].append(
                {
                    "status": status,
                    "timestamp": timestamp,
                    "person_count": len(
                        self.current_zone_occupancy.get(zone_id, set())
                    ),
                }
            )

            # Keep only recent history (last 24 hours)
            cutoff_time = timestamp - timedelta(hours=24)
            self.zone_status_history[zone_id] = [
                entry
                for entry in self.zone_status_history[zone_id]
                if entry["timestamp"] > cutoff_time
            ]

    def get_track_movement_history(self, track_id: int) -> List[Dict[str, Any]]:
        """
        Get movement history for specific track ID

        Args:
            track_id: Person tracking ID

        Returns:
            List of zone entries with timestamps
        """
        return self.track_history.get(track_id, [])

    def get_zone_status_history(self, zone_id: int) -> List[Dict[str, Any]]:
        """
        Get status change history for specific zone

        Args:
            zone_id: Zone ID

        Returns:
            List of status changes with timestamps
        """
        return self.zone_status_history.get(zone_id, [])

    def get_zone_efficiency_data(
        self, zone_id: int, time_window_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for zone

        Args:
            zone_id: Zone ID
            time_window_hours: Time window for calculation

        Returns:
            Efficiency metrics dictionary
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            zone_history = [
                entry
                for entry in self.zone_status_history.get(zone_id, [])
                if entry["timestamp"] > cutoff_time
            ]

            if not zone_history:
                return {
                    "zone_id": zone_id,
                    "time_window_hours": time_window_hours,
                    "work_time_minutes": 0,
                    "idle_time_minutes": 0,
                    "other_time_minutes": 0,
                    "efficiency_percentage": 0.0,
                }

            # Calculate time spent in each status
            work_time = timedelta()
            idle_time = timedelta()
            other_time = timedelta()

            for i in range(len(zone_history)):
                current_entry = zone_history[i]

                # Calculate duration until next status change or now
                if i < len(zone_history) - 1:
                    duration = (
                        zone_history[i + 1]["timestamp"] - current_entry["timestamp"]
                    )
                else:
                    duration = datetime.utcnow() - current_entry["timestamp"]

                # Add to appropriate status time
                if current_entry["status"] == "work":
                    work_time += duration
                elif current_entry["status"] == "idle":
                    idle_time += duration
                elif current_entry["status"] == "other":
                    other_time += duration

            total_time = work_time + idle_time + other_time

            # Calculate efficiency (work_time / (total_time - break_time))
            # For now, assuming no explicit break time tracking
            efficiency = (
                (work_time.total_seconds() / total_time.total_seconds() * 100)
                if total_time.total_seconds() > 0
                else 0.0
            )

            return {
                "zone_id": zone_id,
                "time_window_hours": time_window_hours,
                "work_time_minutes": work_time.total_seconds() / 60,
                "idle_time_minutes": idle_time.total_seconds() / 60,
                "other_time_minutes": other_time.total_seconds() / 60,
                "efficiency_percentage": round(efficiency, 2),
            }

        except Exception as e:
            logger.error(f"Error calculating zone efficiency: {e}")
            return {
                "zone_id": zone_id,
                "time_window_hours": time_window_hours,
                "work_time_minutes": 0,
                "idle_time_minutes": 0,
                "other_time_minutes": 0,
                "efficiency_percentage": 0.0,
                "error": str(e),
            }

    def clear_old_tracking_data(self, hours_to_keep: int = 24):
        """Clear old tracking data to prevent memory leaks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_to_keep)

        # Clear old track history
        for track_id in list(self.track_history.keys()):
            self.track_history[track_id] = [
                entry
                for entry in self.track_history[track_id]
                if entry["timestamp"] > cutoff_time
            ]

            # Remove empty track histories
            if not self.track_history[track_id]:
                del self.track_history[track_id]

        # Clear old zone status history
        for zone_id in list(self.zone_status_history.keys()):
            self.zone_status_history[zone_id] = [
                entry
                for entry in self.zone_status_history[zone_id]
                if entry["timestamp"] > cutoff_time
            ]


# Global analyzer instance
_zone_analyzer = None


def get_zone_analyzer() -> ZoneAnalyzer:
    """Get global zone analyzer instance"""
    global _zone_analyzer
    if _zone_analyzer is None:
        _zone_analyzer = ZoneAnalyzer()
    return _zone_analyzer

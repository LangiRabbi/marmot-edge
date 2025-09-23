from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workstation import Workstation
from app.models.zone import Zone
from app.models.detection import Detection
from app.schemas.workstation import WorkstationCreate, WorkstationUpdate
from app.schemas.zone import ZoneCreate, ZoneUpdate


class WorkstationRepository(Protocol):
    """Protocol for workstation data operations."""

    async def get_workstations(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Workstation]:
        """Get all workstations with pagination."""
        ...

    async def get_workstation(
        self, db: AsyncSession, workstation_id: int
    ) -> Optional[Workstation]:
        """Get a workstation by ID."""
        ...

    async def create_workstation(
        self, db: AsyncSession, workstation: WorkstationCreate
    ) -> Workstation:
        """Create a new workstation."""
        ...

    async def update_workstation(
        self, db: AsyncSession, workstation_id: int, workstation: WorkstationUpdate
    ) -> Optional[Workstation]:
        """Update an existing workstation."""
        ...

    async def delete_workstation(self, db: AsyncSession, workstation_id: int) -> bool:
        """Delete a workstation."""
        ...


class ZoneRepository(Protocol):
    """Protocol for zone data operations."""

    async def get_zones(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Zone]:
        """Get all zones with pagination."""
        ...

    async def get_zones_by_workstation(
        self, db: AsyncSession, workstation_id: int
    ) -> List[Zone]:
        """Get all zones for a specific workstation."""
        ...

    async def get_zone(self, db: AsyncSession, zone_id: int) -> Optional[Zone]:
        """Get a zone by ID."""
        ...

    async def create_zone(self, db: AsyncSession, zone: ZoneCreate) -> Zone:
        """Create a new zone."""
        ...

    async def update_zone(
        self, db: AsyncSession, zone_id: int, zone: ZoneUpdate
    ) -> Optional[Zone]:
        """Update an existing zone."""
        ...

    async def delete_zone(self, db: AsyncSession, zone_id: int) -> bool:
        """Delete a zone."""
        ...


class DetectionRepository(Protocol):
    """Protocol for detection data operations."""

    async def get_detections(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Detection]:
        """Get all detections with pagination."""
        ...

    async def get_detections_by_workstation(
        self, db: AsyncSession, workstation_id: int, skip: int = 0, limit: int = 100
    ) -> List[Detection]:
        """Get detections for a specific workstation."""
        ...

    async def create_detection(
        self, db: AsyncSession, detection_data: dict
    ) -> Detection:
        """Create a new detection."""
        ...


class VideoStreamRepository(Protocol):
    """Protocol for video stream data operations."""

    async def get_active_streams(self, db: AsyncSession) -> List[dict]:
        """Get all active video streams."""
        ...

    async def update_stream_status(
        self, db: AsyncSession, stream_id: str, status: str
    ) -> bool:
        """Update video stream status."""
        ...


class DatabaseService(ABC):
    """Abstract base class for database service implementations."""

    @property
    @abstractmethod
    def workstations(self) -> WorkstationRepository:
        """Get workstation repository."""
        ...

    @property
    @abstractmethod
    def zones(self) -> ZoneRepository:
        """Get zone repository."""
        ...

    @property
    @abstractmethod
    def detections(self) -> DetectionRepository:
        """Get detection repository."""
        ...

    @property
    @abstractmethod
    def video_streams(self) -> VideoStreamRepository:
        """Get video stream repository."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database service is healthy."""
        ...

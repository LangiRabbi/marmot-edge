from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_service import (
    DatabaseService,
    WorkstationRepository,
    ZoneRepository,
    DetectionRepository,
    VideoStreamRepository,
)
from app.models.workstation import Workstation
from app.models.zone import Zone
from app.models.detection import Detection
from app.schemas.workstation import WorkstationCreate, WorkstationUpdate
from app.schemas.zone import ZoneCreate, ZoneUpdate
from app.crud import workstation as workstation_crud
from app.crud import zone as zone_crud


class PostgreSQLWorkstationRepository:
    """PostgreSQL implementation of WorkstationRepository."""

    async def get_workstations(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Workstation]:
        return await workstation_crud.get_workstations(db, skip, limit)

    async def get_workstation(
        self, db: AsyncSession, workstation_id: int
    ) -> Optional[Workstation]:
        return await workstation_crud.get_workstation(db, workstation_id)

    async def create_workstation(
        self, db: AsyncSession, workstation: WorkstationCreate
    ) -> Workstation:
        return await workstation_crud.create_workstation(db, workstation)

    async def update_workstation(
        self, db: AsyncSession, workstation_id: int, workstation: WorkstationUpdate
    ) -> Optional[Workstation]:
        return await workstation_crud.update_workstation(
            db, workstation_id, workstation
        )

    async def delete_workstation(self, db: AsyncSession, workstation_id: int) -> bool:
        return await workstation_crud.delete_workstation(db, workstation_id)


class PostgreSQLZoneRepository:
    """PostgreSQL implementation of ZoneRepository."""

    async def get_zones(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Zone]:
        return await zone_crud.get_zones(db, skip, limit)

    async def get_zones_by_workstation(
        self, db: AsyncSession, workstation_id: int
    ) -> List[Zone]:
        return await zone_crud.get_zones_by_workstation(db, workstation_id)

    async def get_zone(self, db: AsyncSession, zone_id: int) -> Optional[Zone]:
        return await zone_crud.get_zone(db, zone_id)

    async def create_zone(self, db: AsyncSession, zone: ZoneCreate) -> Zone:
        return await zone_crud.create_zone(db, zone)

    async def update_zone(
        self, db: AsyncSession, zone_id: int, zone: ZoneUpdate
    ) -> Optional[Zone]:
        return await zone_crud.update_zone(db, zone_id, zone)

    async def delete_zone(self, db: AsyncSession, zone_id: int) -> bool:
        return await zone_crud.delete_zone(db, zone_id)


class PostgreSQLDetectionRepository:
    """PostgreSQL implementation of DetectionRepository."""

    async def get_detections(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Detection]:
        from sqlalchemy import select

        result = await db.execute(
            select(Detection)
            .offset(skip)
            .limit(limit)
            .order_by(Detection.timestamp.desc())
        )
        return list(result.scalars().all())

    async def get_detections_by_workstation(
        self, db: AsyncSession, workstation_id: int, skip: int = 0, limit: int = 100
    ) -> List[Detection]:
        from sqlalchemy import select

        result = await db.execute(
            select(Detection)
            .where(Detection.workstation_id == workstation_id)
            .offset(skip)
            .limit(limit)
            .order_by(Detection.timestamp.desc())
        )
        return list(result.scalars().all())

    async def create_detection(
        self, db: AsyncSession, detection_data: dict
    ) -> Detection:
        db_detection = Detection(**detection_data)
        db.add(db_detection)
        await db.commit()
        await db.refresh(db_detection)
        return db_detection


class PostgreSQLVideoStreamRepository:
    """PostgreSQL implementation of VideoStreamRepository."""

    async def get_active_streams(self, db: AsyncSession) -> List[dict]:
        return []

    async def update_stream_status(
        self, db: AsyncSession, stream_id: str, status: str
    ) -> bool:
        return True


class PostgreSQLService(DatabaseService):
    """PostgreSQL implementation of DatabaseService."""

    def __init__(self):
        self._workstations = PostgreSQLWorkstationRepository()
        self._zones = PostgreSQLZoneRepository()
        self._detections = PostgreSQLDetectionRepository()
        self._video_streams = PostgreSQLVideoStreamRepository()

    @property
    def workstations(self) -> WorkstationRepository:
        return self._workstations

    @property
    def zones(self) -> ZoneRepository:
        return self._zones

    @property
    def detections(self) -> DetectionRepository:
        return self._detections

    @property
    def video_streams(self) -> VideoStreamRepository:
        return self._video_streams

    async def health_check(self) -> bool:
        try:
            from app.database import get_db_session

            async with get_db_session() as db:
                await db.execute("SELECT 1")
                return True
        except Exception:
            return False

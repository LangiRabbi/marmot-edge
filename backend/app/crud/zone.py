from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from typing import List, Optional

from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneUpdate

async def get_zone(db: AsyncSession, zone_id: int) -> Optional[Zone]:
    """Get a single zone by ID"""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalar_one_or_none()

async def get_zones(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Zone]:
    """Get list of zones with pagination"""
    result = await db.execute(
        select(Zone)
        .offset(skip)
        .limit(limit)
        .order_by(Zone.created_at.desc())
    )
    return list(result.scalars().all())

async def get_zones_by_workstation(
    db: AsyncSession, workstation_id: int, skip: int = 0, limit: int = 100
) -> List[Zone]:
    """Get zones for a specific workstation"""
    result = await db.execute(
        select(Zone)
        .where(Zone.workstation_id == workstation_id)
        .offset(skip)
        .limit(limit)
        .order_by(Zone.created_at.desc())
    )
    return list(result.scalars().all())

async def create_zone(db: AsyncSession, zone: ZoneCreate) -> Zone:
    """Create a new zone"""
    db_zone = Zone(**zone.model_dump())
    db.add(db_zone)
    await db.commit()
    await db.refresh(db_zone)
    return db_zone

async def update_zone(
    db: AsyncSession,
    zone_id: int,
    zone_update: ZoneUpdate
) -> Optional[Zone]:
    """Update an existing zone"""
    # Get existing zone
    db_zone = await get_zone(db, zone_id)
    if not db_zone:
        return None

    # Update only provided fields
    update_data = zone_update.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Zone)
            .where(Zone.id == zone_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(db_zone)

    return db_zone

async def delete_zone(db: AsyncSession, zone_id: int) -> bool:
    """Delete a zone"""
    result = await db.execute(
        delete(Zone).where(Zone.id == zone_id)
    )
    await db.commit()
    return result.rowcount > 0

async def get_zones_count(db: AsyncSession, workstation_id: Optional[int] = None) -> int:
    """Get total count of zones, optionally filtered by workstation"""
    query = select(Zone.id)
    if workstation_id:
        query = query.where(Zone.workstation_id == workstation_id)

    result = await db.execute(query)
    return len(list(result.scalars().all()))
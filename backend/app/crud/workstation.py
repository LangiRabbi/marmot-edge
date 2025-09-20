from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workstation import Workstation
from app.models.zone import Zone
from app.schemas.workstation import WorkstationCreate, WorkstationUpdate


async def get_workstation(
    db: AsyncSession, workstation_id: int
) -> Optional[Workstation]:
    """Get a single workstation by ID"""
    result = await db.execute(
        select(Workstation)
        .options(selectinload(Workstation.zones))
        .where(Workstation.id == workstation_id)
    )
    return result.scalar_one_or_none()


async def get_workstations(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Workstation]:
    """Get list of workstations with pagination"""
    result = await db.execute(
        select(Workstation)
        .options(selectinload(Workstation.zones))
        .offset(skip)
        .limit(limit)
        .order_by(Workstation.created_at.desc())
    )
    return list(result.scalars().all())


async def create_workstation(
    db: AsyncSession, workstation: WorkstationCreate
) -> Workstation:
    """Create a new workstation"""
    db_workstation = Workstation(**workstation.model_dump())
    db.add(db_workstation)
    await db.commit()
    await db.refresh(db_workstation)
    return db_workstation


async def update_workstation(
    db: AsyncSession, workstation_id: int, workstation_update: WorkstationUpdate
) -> Optional[Workstation]:
    """Update an existing workstation"""
    # Get existing workstation
    db_workstation = await get_workstation(db, workstation_id)
    if not db_workstation:
        return None

    # Update only provided fields
    update_data = workstation_update.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Workstation)
            .where(Workstation.id == workstation_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(db_workstation)

    return db_workstation


async def delete_workstation(db: AsyncSession, workstation_id: int) -> bool:
    """Delete a workstation"""
    result = await db.execute(
        delete(Workstation).where(Workstation.id == workstation_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_workstations_count(db: AsyncSession) -> int:
    """Get total count of workstations"""
    result = await db.execute(select(Workstation.id))
    return len(list(result.scalars().all()))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from app.crud import zone as zone_crud
from app.crud import workstation as workstation_crud

router = APIRouter()

@router.get("/", response_model=List[ZoneResponse])
async def read_zones(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    workstation_id: Optional[int] = Query(None, description="Filter zones by workstation ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve zones, optionally filtered by workstation.
    """
    if workstation_id:
        zones = await zone_crud.get_zones_by_workstation(
            db, workstation_id=workstation_id, skip=skip, limit=limit
        )
    else:
        zones = await zone_crud.get_zones(db, skip=skip, limit=limit)
    return zones

@router.get("/{zone_id}", response_model=ZoneResponse)
async def read_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific zone by ID.
    """
    zone = await zone_crud.get_zone(db, zone_id=zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@router.post("/", response_model=ZoneResponse, status_code=201)
async def create_zone(
    zone: ZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new zone.
    """
    # Verify workstation exists
    workstation = await workstation_crud.get_workstation(db, workstation_id=zone.workstation_id)
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")

    return await zone_crud.create_zone(db=db, zone=zone)

@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    zone_update: ZoneUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing zone.
    """
    zone = await zone_crud.update_zone(
        db=db, zone_id=zone_id, zone_update=zone_update
    )
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@router.delete("/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a zone.
    """
    success = await zone_crud.delete_zone(db=db, zone_id=zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")

@router.get("/{zone_id}/status", response_model=dict)
async def get_zone_status(
    zone_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current status and detection info for a zone.
    """
    zone = await zone_crud.get_zone(db, zone_id=zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")

    return {
        "id": zone.id,
        "name": zone.name,
        "status": zone.status,
        "person_count": zone.person_count,
        "is_active": zone.is_active,
        "workstation_id": zone.workstation_id,
        "coordinates": zone.coordinates,
        "color": zone.color
    }
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import workstation as workstation_crud
from app.database import get_db
from app.schemas.workstation import (WorkstationCreate, WorkstationResponse,
                                     WorkstationUpdate, WorkstationWithZones)

router = APIRouter()


@router.get("/", response_model=List[WorkstationWithZones])
async def read_workstations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all workstations with their zones.
    """
    workstations = await workstation_crud.get_workstations(db, skip=skip, limit=limit)
    return workstations


@router.get("/{workstation_id}", response_model=WorkstationWithZones)
async def read_workstation(workstation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific workstation by ID with its zones.
    """
    workstation = await workstation_crud.get_workstation(
        db, workstation_id=workstation_id
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return workstation


@router.post("/", response_model=WorkstationResponse, status_code=201)
async def create_workstation(
    workstation: WorkstationCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new workstation.
    """
    return await workstation_crud.create_workstation(db=db, workstation=workstation)


@router.put("/{workstation_id}", response_model=WorkstationResponse)
async def update_workstation(
    workstation_id: int,
    workstation_update: WorkstationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing workstation.
    """
    workstation = await workstation_crud.update_workstation(
        db=db, workstation_id=workstation_id, workstation_update=workstation_update
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return workstation


@router.delete("/{workstation_id}", status_code=204)
async def delete_workstation(workstation_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a workstation.
    """
    success = await workstation_crud.delete_workstation(
        db=db, workstation_id=workstation_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Workstation not found")


@router.get("/{workstation_id}/status", response_model=dict)
async def get_workstation_status(
    workstation_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Get current status and statistics for a workstation.
    """
    workstation = await workstation_crud.get_workstation(
        db, workstation_id=workstation_id
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")

    return {
        "id": workstation.id,
        "name": workstation.name,
        "status": workstation.current_status,
        "is_active": workstation.is_active,
        "zones_count": len(workstation.zones),
        "active_zones": len([z for z in workstation.zones if z.is_active]),
        "last_detection": workstation.last_detection_at,
    }

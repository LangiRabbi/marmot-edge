from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_factory import get_db_service
from app.core.database_service import DatabaseService
from app.database import get_db
from app.schemas.workstation import (
    WorkstationCreate,
    WorkstationResponse,
    WorkstationUpdate,
    WorkstationWithZones,
)

router = APIRouter()


@router.get("/", response_model=List[WorkstationWithZones])
async def read_workstations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Retrieve all workstations with their zones.
    """
    workstations = await db_service.workstations.get_workstations(
        db, skip=skip, limit=limit
    )
    print(f"🔍 API Debug: Found {len(workstations)} workstations")
    for ws in workstations:
        print(f"🔍 Workstation: ID={ws.id}, Name={ws.name}")
    return workstations


@router.get("/{workstation_id}", response_model=WorkstationWithZones)
async def read_workstation(
    workstation_id: int,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Get a specific workstation by ID with its zones.
    """
    workstation = await db_service.workstations.get_workstation(
        db, workstation_id=workstation_id
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return workstation


@router.post("/", response_model=WorkstationResponse, status_code=201)
async def create_workstation(
    workstation: WorkstationCreate,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Create a new workstation.
    """
    return await db_service.workstations.create_workstation(
        db=db, workstation=workstation
    )


@router.put("/{workstation_id}", response_model=WorkstationResponse)
async def update_workstation(
    workstation_id: int,
    workstation_update: WorkstationUpdate,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Update an existing workstation.
    """
    workstation = await db_service.workstations.update_workstation(
        db=db, workstation_id=workstation_id, workstation=workstation_update
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")
    return workstation


@router.delete("/{workstation_id}", status_code=204)
async def delete_workstation(
    workstation_id: int,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Delete a workstation.
    """
    success = await db_service.workstations.delete_workstation(
        db=db, workstation_id=workstation_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Workstation not found")


@router.get("/{workstation_id}/status", response_model=dict)
async def get_workstation_status(
    workstation_id: int,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Get current status and statistics for a workstation.
    """
    workstation = await db_service.workstations.get_workstation(
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


@router.post("/{workstation_id}/start-processing", response_model=dict)
async def start_video_processing(
    workstation_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Start video processing for a workstation with file video source.
    Will begin YOLOv11 analysis and WebSocket broadcasting of detections.
    """
    workstation = await db_service.workstations.get_workstation(
        db, workstation_id=workstation_id
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")

    # Check if workstation has video configuration
    if not workstation.video_config:
        raise HTTPException(
            status_code=400, detail="Workstation has no video source configuration"
        )

    video_config = workstation.video_config

    # Only support file type for now
    if video_config.get("type") != "file":
        raise HTTPException(
            status_code=400,
            detail="Only file video sources are supported for processing",
        )

    file_path = video_config.get("filePath")
    if not file_path:
        raise HTTPException(
            status_code=400, detail="No file path found in video configuration"
        )

    # Import and start the video processor
    from app.workers.file_video_processor import start_file_processing

    # Start processing in background
    background_tasks.add_task(
        start_file_processing, workstation_id=str(workstation_id), file_path=file_path
    )

    return {
        "status": "started",
        "workstation_id": workstation_id,
        "file_path": file_path,
        "message": "Video processing started in background",
    }


@router.post("/{workstation_id}/stop-processing", response_model=dict)
async def stop_video_processing(
    workstation_id: int,
    db: AsyncSession = Depends(get_db),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    Stop video processing for a workstation.
    """
    workstation = await db_service.workstations.get_workstation(
        db, workstation_id=workstation_id
    )
    if workstation is None:
        raise HTTPException(status_code=404, detail="Workstation not found")

    # Import and stop the video processor
    from app.workers.file_video_processor import stop_file_processing

    success = await stop_file_processing(str(workstation_id))

    return {
        "status": "stopped" if success else "not_running",
        "workstation_id": workstation_id,
        "message": (
            "Video processing stopped" if success else "No processing was running"
        ),
    }

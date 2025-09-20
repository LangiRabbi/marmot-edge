from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workstation import Workstation
from app.models.zone import Zone

router = APIRouter()

# Sample workstations data matching frontend
SAMPLE_WORKSTATIONS = [
    {
        "name": "Assembly Line 1",
        "description": "Main assembly line for product manufacturing",
        "is_active": True,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.101/stream1",
        "current_status": "work",
    },
    {
        "name": "QC Station 3",
        "description": "Quality control and inspection station",
        "is_active": True,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.102/stream1",
        "current_status": "idle",
    },
    {
        "name": "Packaging Unit A",
        "description": "Product packaging and labeling unit",
        "is_active": True,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.103/stream1",
        "current_status": "work",
    },
    {
        "name": "Welding Station 2",
        "description": "Automated welding and joining station",
        "is_active": False,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.104/stream1",
        "current_status": "offline",
    },
    {
        "name": "Paint Booth 1",
        "description": "Paint application and finishing booth",
        "is_active": True,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.105/stream1",
        "current_status": "work",
    },
    {
        "name": "Final Inspection",
        "description": "Final quality inspection before shipping",
        "is_active": True,
        "video_source_type": "ip",
        "video_source_url": "rtsp://192.168.1.106/stream1",
        "current_status": "other",
    },
]

# Sample zones for each workstation
SAMPLE_ZONES = [
    # Zones for Assembly Line 1
    {
        "name": "Work Area",
        "coordinates": {"points": [[100, 100], [300, 100], [300, 200], [100, 200]]},
        "color": "#00FF00",
        "person_count": 2,
        "status": "work",
    },
    {
        "name": "Tool Storage",
        "coordinates": {"points": [[320, 100], [450, 100], [450, 180], [320, 180]]},
        "color": "#0000FF",
        "person_count": 0,
        "status": "idle",
    },
    # Zones for QC Station 3
    {
        "name": "Inspection Table",
        "coordinates": {"points": [[50, 150], [250, 150], [250, 250], [50, 250]]},
        "color": "#FF0000",
        "person_count": 0,
        "status": "idle",
    },
    # Zones for Packaging Unit A
    {
        "name": "Packing Area",
        "coordinates": {"points": [[80, 80], [280, 80], [280, 220], [80, 220]]},
        "color": "#00FF00",
        "person_count": 3,
        "status": "work",
    },
    {
        "name": "Storage Zone",
        "coordinates": {"points": [[300, 80], [400, 80], [400, 160], [300, 160]]},
        "color": "#FFFF00",
        "person_count": 0,
        "status": "idle",
    },
    # Zones for Welding Station 2 (offline)
    {
        "name": "Welding Bay",
        "coordinates": {"points": [[120, 120], [320, 120], [320, 240], [120, 240]]},
        "color": "#808080",
        "person_count": 0,
        "status": "offline",
    },
    # Zones for Paint Booth 1
    {
        "name": "Spray Area",
        "coordinates": {"points": [[90, 90], [290, 90], [290, 210], [90, 210]]},
        "color": "#00FF00",
        "person_count": 2,
        "status": "work",
    },
    # Zones for Final Inspection
    {
        "name": "Inspection Line",
        "coordinates": {"points": [[60, 110], [260, 110], [260, 230], [60, 230]]},
        "color": "#FFA500",
        "person_count": 2,
        "status": "other",
    },
]


@router.post("/", response_model=Dict[str, Any])
async def seed_database(db: AsyncSession = Depends(get_db), force: bool = False):
    """
    Seed the database with sample workstations and zones data.
    Use force=True to clear existing data first.
    """
    try:
        # Check if data already exists
        from sqlalchemy import delete, select

        existing_workstations = await db.execute(select(Workstation.id))
        workstation_count = len(list(existing_workstations.scalars().all()))

        if workstation_count > 0 and not force:
            raise HTTPException(
                status_code=400,
                detail=f"Database already has {workstation_count} workstations. Use force=True to clear and reseed.",
            )

        # Clear existing data if force=True
        if force:
            await db.execute(delete(Zone))
            await db.execute(delete(Workstation))
            await db.commit()

        # Create workstations
        created_workstations = []
        for ws_data in SAMPLE_WORKSTATIONS:
            workstation = Workstation(**ws_data)
            db.add(workstation)
            created_workstations.append(workstation)

        await db.commit()

        # Refresh workstations to get IDs
        for ws in created_workstations:
            await db.refresh(ws)

        # Create zones - distribute them across workstations
        zone_idx = 0
        zones_per_workstation = [2, 1, 2, 1, 1, 1]  # Distribution of zones

        created_zones = []
        for i, workstation in enumerate(created_workstations):
            zones_count = zones_per_workstation[i]
            for j in range(zones_count):
                if zone_idx < len(SAMPLE_ZONES):
                    zone_data = SAMPLE_ZONES[zone_idx].copy()
                    zone_data["workstation_id"] = workstation.id
                    zone = Zone(**zone_data)
                    db.add(zone)
                    created_zones.append(zone)
                    zone_idx += 1

        await db.commit()

        return {
            "message": "Database seeded successfully",
            "workstations_created": len(created_workstations),
            "zones_created": len(created_zones),
            "workstations": [
                {"id": ws.id, "name": ws.name, "status": ws.current_status}
                for ws in created_workstations
            ],
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")


@router.delete("/", response_model=Dict[str, str])
async def clear_database(db: AsyncSession = Depends(get_db)):
    """
    Clear all workstations and zones from the database.
    """
    try:
        from sqlalchemy import delete

        # Delete in correct order (zones first due to foreign key)
        zones_result = await db.execute(delete(Zone))
        workstations_result = await db.execute(delete(Workstation))

        await db.commit()

        return {
            "message": "Database cleared successfully",
            "zones_deleted": str(zones_result.rowcount),
            "workstations_deleted": str(workstations_result.rowcount),
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error clearing database: {str(e)}"
        )

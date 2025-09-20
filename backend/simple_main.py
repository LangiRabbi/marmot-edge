import asyncio
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Simple FastAPI app for testing frontend connection
app = FastAPI(title="Marmot API - Simple Test", version="1.0.0")

# CORS configuration to allow frontend on different ports
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mock workstation data
mock_workstations = [
    {
        "id": 1,
        "name": "Assembly Line 1",
        "location": "Production Floor A",
        "status": "online",
        "people_count": 2,
        "efficiency": 86,
        "last_activity": "2 min ago",
        "created_at": "2025-09-17T10:00:00Z",
        "updated_at": "2025-09-18T20:49:00Z",
    },
    {
        "id": 2,
        "name": "QC Station 3",
        "location": "Quality Control",
        "status": "alert",
        "people_count": 0,
        "efficiency": 45,
        "last_activity": "35 min ago",
        "created_at": "2025-09-17T10:00:00Z",
        "updated_at": "2025-09-18T20:14:00Z",
    },
    {
        "id": 3,
        "name": "Packaging Unit A",
        "location": "Packaging Department",
        "status": "online",
        "people_count": 3,
        "efficiency": 94,
        "last_activity": "1 min ago",
        "created_at": "2025-09-17T10:00:00Z",
        "updated_at": "2025-09-18T20:48:00Z",
    },
]


@app.get("/")
async def root():
    return {"message": "Marmot Industrial Monitoring System API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-09-19T13:45:00Z"}


@app.get("/api/v1/workstations/")
async def get_workstations():
    return mock_workstations


@app.post("/api/v1/workstations/")
async def create_workstation(workstation_data: dict):
    new_id = max([w["id"] for w in mock_workstations]) + 1
    new_workstation = {
        "id": new_id,
        "name": workstation_data.get("name", f"Workstation {new_id}"),
        "location": workstation_data.get("location", "Unknown"),
        "status": workstation_data.get("status", "offline"),
        "people_count": 0,
        "efficiency": 0,
        "last_activity": "just now",
        "created_at": "2025-09-19T13:45:00Z",
        "updated_at": "2025-09-19T13:45:00Z",
    }
    mock_workstations.append(new_workstation)
    return new_workstation


@app.put("/api/v1/workstations/{workstation_id}")
async def update_workstation(workstation_id: int, workstation_data: dict):
    for workstation in mock_workstations:
        if workstation["id"] == workstation_id:
            workstation.update(workstation_data)
            workstation["updated_at"] = "2025-09-19T13:45:00Z"
            return workstation
    return {"error": "Workstation not found"}


@app.delete("/api/v1/workstations/{workstation_id}")
async def delete_workstation(workstation_id: int):
    global mock_workstations
    mock_workstations = [w for w in mock_workstations if w["id"] != workstation_id]
    return {"message": "Workstation deleted successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

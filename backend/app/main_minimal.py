import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api.v1 import workstations, zones

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app without lifespan for CI testing
app = FastAPI(
    title="Marmot Industrial Monitoring System",
    description="Real-time person detection and efficiency monitoring for industrial workstations",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:8080"),
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only basic API routers (no video processing)
app.include_router(
    workstations.router, prefix="/api/v1/workstations", tags=["workstations"]
)
app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])


@app.get("/")
async def root():
    return {
        "message": "Marmot Industrial Monitoring System API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "marmot-backend",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
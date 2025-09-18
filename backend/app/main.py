from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Import API routers
from app.api.v1 import workstations, zones, seed, detection

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Marmot Industrial Monitoring System...")
    yield
    # Shutdown
    print("Shutting down Marmot Industrial Monitoring System...")

# Create FastAPI app
app = FastAPI(
    title="Marmot Industrial Monitoring System",
    description="Real-time person detection and efficiency monitoring for industrial workstations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:8080"),
        "http://localhost:3000",  # Backup for development
        "http://localhost:8080"   # Current frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    workstations.router,
    prefix="/api/v1/workstations",
    tags=["workstations"]
)
app.include_router(
    zones.router,
    prefix="/api/v1/zones",
    tags=["zones"]
)
app.include_router(
    seed.router,
    prefix="/api/v1/seed",
    tags=["seed"]
)
app.include_router(
    detection.router,
    prefix="/api/v1/detection",
    tags=["detection"]
)

@app.get("/")
async def root():
    return {
        "message": "Marmot Industrial Monitoring System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "marmot-backend",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/v1/status")
async def api_status():
    return {
        "api_version": "v1",
        "database": "connected",  # Will be updated when DB connection is tested
        "yolo_model": "not_loaded",  # Will be updated when YOLO is integrated
        "video_sources": 0
    }

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
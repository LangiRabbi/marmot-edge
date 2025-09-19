import os
import signal
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api.v1 import detection, seed, video_streams, workstations, zones
# Import services for graceful shutdown
from app.services.video_service import get_video_manager
from app.workers.video_processor import get_video_processor

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Marmot Industrial Monitoring System...")

    # Setup graceful shutdown handlers
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, initiating graceful shutdown...")

        try:
            # Shutdown video processing system
            video_processor = get_video_processor()
            video_manager = get_video_manager()

            print("Shutting down video processor...")
            video_processor.shutdown()

            print("Shutting down video manager...")
            video_manager.shutdown()

            print("Graceful shutdown completed")
        except Exception as e:
            print(f"Error during shutdown: {e}")

        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Docker stop

    yield

    # Shutdown
    print("Shutting down Marmot Industrial Monitoring System...")
    try:
        video_processor = get_video_processor()
        video_manager = get_video_manager()
        video_processor.shutdown()
        video_manager.shutdown()
    except Exception as e:
        print(f"Error during lifespan shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Marmot Industrial Monitoring System",
    description="Real-time person detection and efficiency monitoring for industrial workstations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:8080"),
        "http://localhost:3000",  # Backup for development
        "http://localhost:8080",  # Original port
        "http://localhost:8081",  # Alternative port 1
        "http://localhost:8082",  # Alternative port 2
        "http://localhost:8083",  # Current frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    workstations.router, prefix="/api/v1/workstations", tags=["workstations"]
)
app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])
app.include_router(seed.router, prefix="/api/v1/seed", tags=["seed"])
app.include_router(detection.router, prefix="/api/v1/detection", tags=["detection"])
app.include_router(video_streams.router, prefix="/api/v1", tags=["video-streams"])


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


@app.get("/api/v1/status")
async def api_status():
    try:
        # Get video system status
        video_manager = get_video_manager()
        video_processor = get_video_processor()

        video_stats = video_manager.get_statistics()
        processing_stats = video_processor.get_statistics()

        return {
            "api_version": "v1",
            "database": "connected",
            "yolo_model": "loaded",
            "video_sources": video_stats.get("active_streams", 0),
            "total_zones": video_stats.get("total_zones", 0),
            "processing_fps": processing_stats.get("average_fps", 0.0),
            "frames_processed": processing_stats.get("frames_processed", 0),
            "system_running": video_stats.get("running", False),
        }
    except Exception as e:
        return {
            "api_version": "v1",
            "database": "connected",
            "yolo_model": "not_loaded",
            "video_sources": 0,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")

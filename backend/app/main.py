import asyncio
import os
import signal
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api.v1 import (
    detection,
    seed,
    test_detection,
    video_streams,
    websocket,
    workstations,
    zones,
)
from app.core.rate_limiting import rate_limiter

# Import services for graceful shutdown
from app.services.video_service import get_video_manager
from app.workers.video_processor import get_video_processor
from app.workers.file_video_processor import start_file_processing
from app.database import get_db
from app.core.database_factory import get_db_service

# Load environment variables
load_dotenv()

# Shared shutdown flag
_shutdown_requested = False


async def shutdown_services():
    """Centralized shutdown logic for all services"""
    global _shutdown_requested
    if _shutdown_requested:
        return  # Prevent duplicate shutdown
    _shutdown_requested = True

    print("Shutting down Marmot Industrial Monitoring System...")
    success = True

    try:
        # Get current event loop for VideoProcessor
        current_loop = asyncio.get_running_loop()

        # Shutdown video processing system
        video_processor = get_video_processor(event_loop=current_loop)
        video_manager = get_video_manager()

        print("Shutting down video processor...")
        video_processor.shutdown()

        print("Shutting down video manager...")
        video_manager.shutdown()

        print("Shutting down rate limiter...")
        await rate_limiter.stop()
        print("Rate limiter stopped")

        print("Graceful shutdown completed")
    except Exception as e:
        print(f"Error during shutdown: {e}")
        success = False

    return success


def signal_handler(signum, frame):
    """Signal handler that triggers async shutdown"""
    print(f"Received signal {signum}, initiating graceful shutdown...")

    # Create new event loop for shutdown in signal context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        success = loop.run_until_complete(shutdown_services())
        exit_code = 0 if success else 1
    except Exception as e:
        print(f"Critical error during signal shutdown: {e}")
        exit_code = 1
    finally:
        loop.close()

    sys.exit(exit_code)


async def auto_start_video_processing():
    """Auto-start video processing for workstations with video configuration"""
    print("Auto-starting video processing for configured workstations...")

    try:
        from app.database import AsyncSessionLocal

        db_service = get_db_service()
        async with AsyncSessionLocal() as db:
            workstations = await db_service.workstations.get_workstations(db, skip=0, limit=100)

            started_count = 0
            for ws in workstations:
                if ws.video_config and ws.video_config.get("type") == "file":
                    file_path = ws.video_config.get("filePath")
                    if file_path:
                        print(f"Auto-starting processing for workstation {ws.id}: {ws.name}")
                        start_file_processing(workstation_id=str(ws.id), file_path=file_path)
                        started_count += 1

            print(f"Auto-started {started_count} video processing streams")
    except Exception as e:
        print(f"Error during auto-start: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Marmot Industrial Monitoring System...")

    # Start rate limiter
    await rate_limiter.start()
    print("Rate limiter started")

    # Initialize video processor with current event loop
    current_loop = asyncio.get_running_loop()
    get_video_processor(event_loop=current_loop)
    print("Video processor initialized with event loop")

    # Auto-start video processing for workstations with video config
    await auto_start_video_processing()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Docker stop

    yield

    # Shutdown - use centralized shutdown logic
    await shutdown_services()


# Create FastAPI app
app = FastAPI(
    title="Marmot Industrial Monitoring System",
    description=(
        "Real-time person detection and efficiency monitoring "
        "for industrial workstations"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS origins from environment
cors_origins = [
    os.getenv("FRONTEND_URL", "http://localhost:8083"),  # Primary frontend URL
]

# Add development ports if in development mode
if os.getenv("ENVIRONMENT", "development") == "development":
    dev_ports = os.getenv("DEV_CORS_PORTS", "3000,8080,8081,8082,8083").split(",")
    cors_origins.extend([f"http://localhost:{port.strip()}" for port in dev_ports])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
app.include_router(test_detection.router, prefix="/api/v1/test", tags=["test"])
app.include_router(video_streams.router, prefix="/api/v1", tags=["video-streams"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])


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
        # Get current event loop and video system status
        current_loop = asyncio.get_running_loop()
        video_manager = get_video_manager()
        video_processor = get_video_processor(event_loop=current_loop)

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

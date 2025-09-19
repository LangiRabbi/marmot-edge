import os

# Load environment variables
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Create FastAPI app for testing only
app = FastAPI(
    title="Marmot Industrial Monitoring System - Test",
    description="Test version for CI without heavy dependencies",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Marmot Industrial Monitoring System API - Test Mode",
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


@app.get("/api/v1/workstations/")
async def read_workstations():
    """Test endpoint that returns empty list without database dependency"""
    return []


@app.get("/api/v1/zones/")
async def read_zones():
    """Test endpoint that returns empty list without database dependency"""
    return []

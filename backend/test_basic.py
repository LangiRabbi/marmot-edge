#!/usr/bin/env python3
"""
Basic test script to check if we can import our models and FastAPI app
without requiring database connection.
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

try:
    print("Testing basic Python imports...")

    print("Testing app.models import...")
    from app.models import Base, Detection, Workstation, Zone

    print("Models imported successfully")

    print("Testing FastAPI app import...")
    from app.main import app

    print("FastAPI app imported successfully")

    print("All basic imports successful!")
    print("\nNext step: Install dependencies and test database connection")

except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)

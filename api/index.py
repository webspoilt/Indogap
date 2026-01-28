"""
Vercel Serverless Function Entrypoint for FastAPI

This file exports the FastAPI app for Vercel deployment.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the FastAPI app from api_server
from api_server import app

# Export app for Vercel - this is required for ASGI detection
# Vercel will use this as the handler

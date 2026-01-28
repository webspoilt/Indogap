"""
Vercel Serverless Entrypoint - Main App

This file exposes the FastAPI app as 'app' to be detected by Vercel.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
# This ensures imports from 'mini_services' work correctly
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the FastAPI app from api_server
try:
    from api_server import app
except Exception as e:
    # Fallback to prevent build failure if import crashes
    # This allows checking logs in Vercel
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/")
    def error():
        return {"error": str(e), "status": "Import Failed"}

# Expose app for Vercel
# Vercel looks for 'app' variable in app.py

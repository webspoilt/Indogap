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
# We do NOT use a try/except block here.
# If the app fails to import, Vercel build/deployment should fail loudly.
from api_server import app

# Expose app for Vercel
# Vercel looks for 'app' variable in app.py


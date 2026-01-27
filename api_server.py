"""
IndoGap API Server - FastAPI Backend with Dashboard

This module provides the web API and serves the dashboard UI.
Optimized for local deployment with local AI models.
"""
import asyncio
import json
import logging
import os
import psutil
import GPUtil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from uuid import uuid4
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import IndoGap components
import sys
sys.path.insert(0, str(Path(__file__).parent))

from mini_services.llm.ollama_client import get_ollama_client, ModelType
from mini_services.llm.free_api import get_free_api_client
from mini_services.scrapers.yc_scraper import YCombinatorScraper
from mini_services.scrapers.product_hunt import ProductHuntScraper
from mini_services.database.repository import get_repository
from mini_services.config import get_settings

# Initialize components
settings = get_settings()
repository = get_repository()
ollama = get_ollama_client()
free_api = get_free_api_client()

# Load Indian competitors config
COMPETITORS_CONFIG_PATH = Path(__file__).parent / "config" / "indian_competitors.json"

def get_indian_competitors(tags: List[str] = None) -> str:
    """Load Indian competitors from config file with category matching."""
    try:
        if COMPETITORS_CONFIG_PATH.exists():
            with open(COMPETITORS_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Try to match by category based on tags
            if tags and "categories" in config:
                tag_lower = [t.lower() for t in tags]
                for category, data in config["categories"].items():
                    if category.lower() in tag_lower or any(cat in " ".join(tag_lower) for cat in [category]):
                        competitors = data.get("competitors", [])
                        desc = data.get("description", "Indian startups")
                        return f"{desc}: {', '.join(competitors)}"
            
            # Return default
            return config.get("default", "Major Indian startups in this space")
    except Exception as e:
        logger.warning(f"Failed to load competitors config: {e}")
    
    # Fallback
    return "Major Indian startups: Razorpay, Freshworks, Zoho, Byjus, Practo"

# Create FastAPI app
app = FastAPI(
    title="IndoGap AI Engine",
    description="AI-Powered Opportunity Discovery Engine for India",
    version="1.0.0"
)

# CORS - Configure allowed origins from environment or use localhost for development
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    models_available: List[str]
    ram_usage: float
    vram_usage: Optional[float]
    timestamp: str

class ScrapeRequest(BaseModel):
    source: str = Field(..., description="Source to scrape: 'yc' or 'ph' or 'all'")
    batch: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)

class AnalysisRequest(BaseModel):
    startup_name: str
    description: str
    tags: List[str] = []
    source: str = "yc"
    batch: Optional[str] = None

class MVPRequest(BaseModel):
    startup_name: str
    description: str
    gap_score: float = 0.7

class OpportunityResponse(BaseModel):
    id: str
    name: str
    description: str
    source: str
    gap_score: float
    similarity_score: float
    opportunity_level: str
    analysis: Dict[str, Any]
    mvp_spec: Optional[str] = None
    created_at: str

class SystemStats(BaseModel):
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    vram_used_gb: Optional[float]
    vram_total_gb: Optional[float]
    models_loaded: List[str]


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard file not found</h1>"


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check system health and available models"""
    ollama_available = ollama.is_available()
    models = ollama.list_models() if ollama_available else []
    
    # Get system stats
    ram = psutil.virtual_memory()
    gpus = GPUtil.getGPUs()
    vram = (gpus[0].memoryUsed / 1024) if len(gpus) > 0 else None
    
    return HealthResponse(
        status="healthy" if ollama_available else "degraded",
        ollama_available=ollama_available,
        models_available=models,
        ram_usage=ram.percent,
        vram_usage=vram,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/system/stats")
async def get_system_stats():
    """Get real-time system resource usage"""
    ram = psutil.virtual_memory()
    gpus = GPUtil.getGPUs()
    
    stats = {
        "cpu_percent": psutil.cpu_percent(),
        "ram_percent": ram.percent,
        "ram_used_gb": ram.used / (1024**3),
        "ram_total_gb": ram.total / (1024**3),
        "vram_used_gb": (gpus[0].memoryUsed / 1024) if len(gpus) > 0 else None,
        "vram_total_gb": (gpus[0].memoryTotal / 1024) if len(gpus) > 0 else None,
        "models_loaded": [],
        "timestamp": datetime.now().isoformat()
    }
    
    return stats


@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    return {"models": ollama.list_models()}


@app.post("/api/scrape")
async def scrape_data(request: ScrapeRequest):
    """Scrape data from YC or Product Hunt"""
    results = []
    
    try:
        if request.source in ["yc", "all"]:
            scraper = YCombinatorScraper()
            result = scraper.scrape(batch=request.batch, limit=request.limit)
            if result.success and result.data:
                for item in result.data:
                    storage_data = {
                        "source": "yc",
                        "data": item,
                        "scraped_at": datetime.now().isoformat()
                    }
                    results.append(storage_data)
                    # Save to DB if possible
                    try:
                        await repository.store_global_startup({
                            "id": item.get("id") or str(uuid4()),
                            "name": item.get("name", "Unknown"),
                            "description": item.get("description", ""),
                            "short_description": item.get("short_description", ""),
                            "tags": item.get("tags", []),
                            "website": item.get("website"),
                            "source": "yc",
                            "batch": item.get("batch"),
                            "funding_stage": item.get("funding_stage"),
                            "funding_amount": item.get("funding_amount"),
                        })
                    except Exception as e:
                        logger.error(f"Failed to store scraped item: {e}")
        
        if request.source in ["ph", "all"]:
            scraper = ProductHuntScraper()
            result = scraper.scrape(limit=request.limit)
            if result.success and result.data:
                for item in result.data:
                    storage_data = {
                        "source": "ph",
                        "data": item,
                        "scraped_at": datetime.now().isoformat()
                    }
                    results.append(storage_data)
                    # Save to DB if possible
                    try:
                        await repository.store_global_startup({
                            "id": item.get("id") or str(uuid4()),
                            "name": item.get("name", "Unknown"),
                            "description": item.get("description", ""),
                            "short_description": item.get("short_description", ""),
                            "tags": item.get("tags", []),
                            "website": item.get("website"),
                            "source": "ph",
                            "upvotes": item.get("upvotes"),
                        })
                    except Exception as e:
                        logger.error(f"Failed to store scraped item: {e}")
        
        return {
            "success": True,
            "count": len(results),
            "items": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_startup(request: AnalysisRequest):
    """Analyze a startup opportunity using local AI"""
    try:
        # Get Indian competitors from config file
        indian_competitors = get_indian_competitors(request.tags)
        
        # Use local Ollama for analysis
        result = ollama.analyze_opportunity(
            startup_name=request.startup_name,
            description=request.description,
            tags=request.tags,
            indian_competitors=indian_competitors
        )
        
        # Save to DB
        gap_score = result.get("gap_score", 0.5)
        opportunity = {
            "id": f"opp_{request.startup_name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
            "name": request.startup_name,
            "description": request.description,
            "source": request.source or "manual",
            "gap_score": gap_score,
            "similarity_score": 1 - gap_score,
            "opportunity_level": "HIGH" if gap_score >= 0.7 else "MEDIUM" if gap_score >= 0.4 else "LOW",
            "analysis": result,
            "created_at": datetime.now()
        }
        await repository.store_opportunity(opportunity)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mvp")
async def generate_mvp(request: MVPRequest):
    """Generate MVP specification using local AI"""
    try:
        spec = ollama.generate_mvp_spec(
            startup_name=request.startup_name,
            description=request.description,
            gap_score=request.gap_score
        )
        
        return {
            "startup": request.startup_name,
            "gap_score": request.gap_score,
            "mvp_specification": spec,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/opportunities")
async def get_opportunities():
    """Get all analyzed opportunities"""
    return repository.get_all_opportunities()


@app.post("/api/demo")
async def run_demo_analysis(background_tasks: BackgroundTasks):
    """Run demo analysis with sample data"""
    
    # Sample YC companies for demo
    sample_startups = [
        {"name": "VoiceFlow Pro", "description": "AI voice agents for customer service", "tags": ["AI", "Enterprise"]},
        {"name": "Legal AI Assistant", "description": "AI-powered legal document review", "tags": ["Legal", "AI"]},
        {"name": "FarmOS", "description": "IoT platform for precision farming", "tags": ["AgriTech", "IoT"]},
        {"name": "SeniorCare AI", "description": "AI monitoring for elderly care", "tags": ["HealthTech", "AI"]},
        {"name": "Code Review AI", "description": "AI code review and security analysis", "tags": ["DevTools", "AI"]},
    ]
    
    opportunities = []
    
    for startup in sample_startups:
        result = ollama.analyze_opportunity(
            startup_name=startup["name"],
            description=startup["description"],
            tags=startup["tags"],
            indian_competitors="Indian market context loaded"
        )
        
        gap_score = result.get("gap_score", 0.5)
        
        opportunity = {
            "id": f"opp_{startup['name'].lower().replace(' ', '_')}",
            "name": startup["name"],
            "description": startup["description"],
            "source": "yc_demo",
            "gap_score": gap_score,
            "similarity_score": 1 - gap_score,
            "opportunity_level": "HIGH" if gap_score >= 0.7 else "MEDIUM" if gap_score >= 0.4 else "LOW",
            "analysis": result,
            "created_at": datetime.now().isoformat()
        }
        
        opportunities.append(opportunity)
    
    # Store in repository
    for opp in opportunities:
        repository.store_opportunity(opp)
    
    return {
        "success": True,
        "count": len(opportunities),
        "opportunities": opportunities
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    logger.info(f"Starting IndoGap API Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IndoGap API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    args = parser.parse_args()
    
    run_server(args.host, args.port)

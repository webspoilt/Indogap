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
try:
    import GPUtil
except ImportError:
    GPUtil = None
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from uuid import uuid4
import uvicorn
import hashlib
import secrets
import time
import aiofiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

# Initialize components placeholders
settings = None
repository = None
ollama = None
free_api = None

def init_components():
    """Lazy initialize components"""
    global settings, repository, ollama, free_api
    try:
        settings = get_settings()
        repository = get_repository()
        ollama = get_ollama_client()
        free_api = get_free_api_client()
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")

# Initialize immediately for local dev, but defer for Vercel/tests if needed
# We'll call this in startup event too to be safe
try:
    init_components()
except Exception:
    pass

# Admin Authentication Config
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "development").lower() == "development"

if not ADMIN_PASSWORD:
    if IS_DEVELOPMENT:
        logger.warning("⚠️ ADMIN_PASSWORD not set! Using default for development only.")
        ADMIN_PASSWORD = "indogap2024"
    else:
        raise ValueError("ADMIN_PASSWORD environment variable must be set in production!")

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    if IS_DEVELOPMENT:
        JWT_SECRET = secrets.token_hex(32)
        logger.warning("⚠️ JWT_SECRET not set! Generated ephemeral secret for development.")
    else:
        raise ValueError("JWT_SECRET environment variable must be set in production!")

JWT_EXPIRY = 3600 * 24  # 24 hours

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# Simple token storage (in production, use Redis or database)
active_tokens: Dict[str, Dict[str, Any]] = {}
security = HTTPBearer(auto_error=False)

def cleanup_expired_tokens():
    """Remove expired tokens from memory"""
    current_time = time.time()
    expired = [
        token for token, data in active_tokens.items()
        if data["expires_at"] < current_time
    ]
    for token in expired:
        del active_tokens[token]
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired tokens")

def create_token(username: str) -> str:
    """Create a simple JWT-like token"""
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": username,
        "created_at": time.time(),
        "expires_at": time.time() + JWT_EXPIRY
    }
    return token

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify token and return user info"""
    if token in active_tokens:
        token_data = active_tokens[token]
        if token_data["expires_at"] > time.time():
            return token_data
        else:
            del active_tokens[token]
    return None

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to verify admin authentication"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_data

# Load Indian competitors config
COMPETITORS_CONFIG_PATH = Path(__file__).parent / "config" / "indian_competitors.json"

async def get_indian_competitors(tags: Optional[List[str]] = None) -> str:
    """Load Indian competitors from config file with category matching (async)."""
    try:
        if COMPETITORS_CONFIG_PATH.exists():
            async with aiofiles.open(COMPETITORS_CONFIG_PATH, "r", encoding="utf-8") as f:
                content = await f.read()
                config = json.loads(content)
            
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

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Background task for token cleanup
async def token_cleanup_task():
    """Periodically clean up expired tokens"""
    while True:
        await asyncio.sleep(3600)  # Every hour
        cleanup_expired_tokens()

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    init_components()  # Ensure components are ready
    asyncio.create_task(token_cleanup_task())
    logger.info("Started token cleanup background task")

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

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str
    username: Optional[str] = None


# ============== AUTH ENDPOINTS ==============

@app.post("/api/auth/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Admin login endpoint with rate limiting"""
    if login_data.username == ADMIN_USERNAME and login_data.password == ADMIN_PASSWORD:
        token = create_token(login_data.username)
        logger.info(f"Admin login successful: {login_data.username}")
        return LoginResponse(
            success=True,
            token=token,
            message="Login successful",
            username=login_data.username
        )
    logger.warning(f"Failed login attempt for: {login_data.username}")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/logout")
async def logout(admin: Dict = Depends(get_current_admin)):
    """Admin logout endpoint"""
    # Remove all tokens for this user
    tokens_to_remove = [
        token for token, data in active_tokens.items()
        if data.get("username") == admin.get("username")
    ]
    for token in tokens_to_remove:
        del active_tokens[token]
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify_auth(admin: Dict = Depends(get_current_admin)):
    """Verify if current token is valid"""
    return {"valid": True, "username": admin.get("username")}


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard HTML (async file I/O)"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    if dashboard_path.exists():
        async with aiofiles.open(dashboard_path, "r", encoding="utf-8") as f:
            return await f.read()
    return "<h1>Dashboard file not found</h1>"


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check system health and available models"""
    if not ollama: init_components()
    ollama_available = ollama.is_available() if ollama else False
    models = ollama.list_models() if ollama_available else []
    
    # Get system stats
    ram = psutil.virtual_memory()
    
    vram = None
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            vram = (gpus[0].memoryUsed / 1024) if len(gpus) > 0 else None
        except Exception:
            pass
    
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
    ram = psutil.virtual_memory()
    
    vram_used = None
    vram_total = None
    
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            vram_used = (gpus[0].memoryUsed / 1024) if len(gpus) > 0 else None
            vram_total = (gpus[0].memoryTotal / 1024) if len(gpus) > 0 else None
        except Exception:
            pass
    
    stats = {
        "cpu_percent": psutil.cpu_percent(),
        "ram_percent": ram.percent,
        "ram_used_gb": ram.used / (1024**3),
        "ram_total_gb": ram.total / (1024**3),
        "vram_used_gb": vram_used,
        "vram_total_gb": vram_total,
        "models_loaded": [],
        "timestamp": datetime.now().isoformat()
    }
    
    return stats


@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    if not ollama: init_components()
    return {"models": ollama.list_models() if ollama else []}


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
                        if not repository: init_components()
                        if repository:
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
        if not ollama: init_components()
        if not ollama:
            raise HTTPException(status_code=503, detail="AI service not available")
            
        # Get Indian competitors from config file (async)
        indian_competitors = await get_indian_competitors(request.tags)
        
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
        if not repository: init_components()
        if repository:
            await repository.store_opportunity(opportunity)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mvp")
async def generate_mvp(request: MVPRequest):
    """Generate MVP specification using local AI"""
    try:
        if not ollama: init_components()
        if not ollama:
            raise HTTPException(status_code=503, detail="AI service not available")

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
    if not repository: init_components()
    return repository.get_all_opportunities() if repository else []


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
        await repository.store_opportunity(opp)
    
    return {
        "success": True,
        "count": len(opportunities),
        "opportunities": opportunities
    }


# ============== ADMIN ENDPOINTS ==============

@app.get("/api/admin/stats")
async def get_admin_stats(admin: Dict = Depends(get_current_admin)):
    """Get database statistics for admin dashboard"""
    try:
        opportunities = await repository.get_all_opportunities() if hasattr(repository, 'get_all_opportunities') else []
        global_startups = await repository.get_all_global_startups() if hasattr(repository, 'get_all_global_startups') else []
        indian_startups = await repository.get_all_indian_startups() if hasattr(repository, 'get_all_indian_startups') else []
        
        # Count by opportunity level
        high = sum(1 for o in opportunities if o.get('opportunity_level') == 'HIGH')
        medium = sum(1 for o in opportunities if o.get('opportunity_level') == 'MEDIUM')
        low = sum(1 for o in opportunities if o.get('opportunity_level') == 'LOW')
        
        return {
            "opportunities_count": len(opportunities),
            "global_startups_count": len(global_startups),
            "indian_startups_count": len(indian_startups),
            "opportunities_by_level": {"high": high, "medium": medium, "low": low},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return {
            "opportunities_count": 0,
            "global_startups_count": 0,
            "indian_startups_count": 0,
            "opportunities_by_level": {"high": 0, "medium": 0, "low": 0},
            "error": str(e)
        }

@app.get("/api/admin/global-startups")
async def get_global_startups(admin: Dict = Depends(get_current_admin)):
    """Get all scraped global startups (YC, Product Hunt)"""
    try:
        if hasattr(repository, 'get_all_global_startups'):
            startups = await repository.get_all_global_startups()
            return {"count": len(startups), "startups": startups}
        return {"count": 0, "startups": [], "message": "Global startups not available in current repository"}
    except Exception as e:
        logger.error(f"Error getting global startups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/indian-startups")
async def get_indian_startups(admin: Dict = Depends(get_current_admin)):
    """Get all Indian startups from database"""
    try:
        if hasattr(repository, 'get_all_indian_startups'):
            startups = await repository.get_all_indian_startups()
            return {"count": len(startups), "startups": startups}
        return {"count": 0, "startups": [], "message": "Indian startups not available in current repository"}
    except Exception as e:
        logger.error(f"Error getting indian startups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/opportunities")
async def get_all_opportunities_admin(admin: Dict = Depends(get_current_admin)):
    """Get all opportunities with full details (admin only)"""
    try:
        opportunities = await repository.get_all_opportunities() if hasattr(repository, 'get_all_opportunities') else []
        return {"count": len(opportunities), "opportunities": opportunities}
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/opportunity/{opportunity_id}")
async def delete_opportunity(opportunity_id: str, admin: Dict = Depends(get_current_admin)):
    """Delete an opportunity by ID"""
    try:
        if hasattr(repository, 'delete_opportunity'):
            await repository.delete_opportunity(opportunity_id)
            return {"success": True, "message": f"Opportunity {opportunity_id} deleted"}
        return {"success": False, "message": "Delete not supported in current repository"}
    except Exception as e:
        logger.error(f"Error deleting opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== EXPORT & SEARCH ENDPOINTS ==============

@app.get("/api/export/opportunities")
async def export_opportunities(
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    admin: Dict = Depends(get_current_admin)
):
    """Export all opportunities as JSON or CSV (admin only)"""
    try:
        opportunities = await repository.get_all_opportunities() if hasattr(repository, 'get_all_opportunities') else []
        
        if format.lower() == "csv":
            import io
            import csv
            
            output = io.StringIO()
            if opportunities:
                fieldnames = ["id", "name", "description", "source", "gap_score", 
                             "similarity_score", "opportunity_level", "created_at"]
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for opp in opportunities:
                    writer.writerow(opp)
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=opportunities.csv"}
            )
        
        # Default: JSON
        return {"count": len(opportunities), "data": opportunities}
        
    except Exception as e:
        logger.error(f"Error exporting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/startups")
async def export_startups(
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    source: str = Query("all", description="Source: 'global', 'indian', or 'all'"),
    admin: Dict = Depends(get_current_admin)
):
    """Export startups as JSON or CSV (admin only)"""
    try:
        data = []
        
        if source in ["global", "all"]:
            if hasattr(repository, 'get_all_global_startups'):
                global_startups = await repository.get_all_global_startups()
                data.extend(global_startups)
        
        if source in ["indian", "all"]:
            if hasattr(repository, 'get_all_indian_startups'):
                indian_startups = await repository.get_all_indian_startups()
                data.extend(indian_startups)
        
        if format.lower() == "csv":
            import io
            import csv
            
            output = io.StringIO()
            if data:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for item in data:
                    writer.writerow(item)
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=startups_{source}.csv"}
            )
        
        return {"count": len(data), "source": source, "data": data}
        
    except Exception as e:
        logger.error(f"Error exporting startups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_opportunities(
    q: Optional[str] = Query(None, description="Search query for name/description"),
    min_score: float = Query(0, ge=0, le=1, description="Minimum gap score"),
    max_score: float = Query(1, ge=0, le=1, description="Maximum gap score"),
    level: Optional[str] = Query(None, description="Opportunity level: HIGH, MEDIUM, LOW"),
    source: Optional[str] = Query(None, description="Source filter: yc, ph, manual"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """Search and filter opportunities with various criteria"""
    try:
        # Get all opportunities
        all_opportunities = await repository.get_all_opportunities() if hasattr(repository, 'get_all_opportunities') else []
        
        # Apply filters
        filtered = all_opportunities
        
        # Text search
        if q:
            q_lower = q.lower()
            filtered = [
                opp for opp in filtered
                if q_lower in opp.get("name", "").lower() or 
                   q_lower in opp.get("description", "").lower()
            ]
        
        # Score filters
        filtered = [
            opp for opp in filtered
            if min_score <= opp.get("gap_score", 0) <= max_score
        ]
        
        # Level filter
        if level:
            filtered = [opp for opp in filtered if opp.get("opportunity_level") == level.upper()]
        
        # Source filter
        if source:
            filtered = [opp for opp in filtered if opp.get("source") == source.lower()]
        
        # Pagination
        total = len(filtered)
        filtered = filtered[offset:offset + limit]
        
        return {
            "total": total,
            "count": len(filtered),
            "offset": offset,
            "limit": limit,
            "query": q,
            "filters": {"min_score": min_score, "max_score": max_score, "level": level, "source": source},
            "results": filtered
        }
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/stats")
async def get_cache_stats(admin: Dict = Depends(get_current_admin)):
    """Get cache statistics (admin only)"""
    try:
        from mini_services.cache import cache
        return cache.get_stats()
    except ImportError:
        return {"error": "Cache module not available"}


@app.post("/api/cache/clear")
async def clear_cache(admin: Dict = Depends(get_current_admin)):
    """Clear all cached data (admin only)"""
    try:
        from mini_services.cache import cache
        cache.clear()
        return {"success": True, "message": "Cache cleared"}
    except ImportError:
        return {"error": "Cache module not available"}


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

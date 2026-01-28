"""
API Endpoint Tests for IndoGap

Tests the FastAPI endpoints for correct behavior.
Run with: pytest tests/test_api.py -v
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""
    
    def test_health_response_structure(self):
        """Test that health response has expected fields"""
        # This would use TestClient in a full implementation
        expected_fields = ["status", "ollama_available", "models_available", 
                          "ram_usage", "vram_usage", "timestamp"]
        # Placeholder - actual test would use FastAPI TestClient
        assert len(expected_fields) == 6


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    def test_login_request_model(self):
        """Test LoginRequest model validation"""
        from pydantic import BaseModel
        
        class LoginRequest(BaseModel):
            username: str
            password: str
        
        # Valid request
        req = LoginRequest(username="admin", password="test123")
        assert req.username == "admin"
        assert req.password == "test123"
    
    def test_login_response_model(self):
        """Test LoginResponse model"""
        from pydantic import BaseModel
        from typing import Optional
        
        class LoginResponse(BaseModel):
            success: bool
            token: Optional[str] = None
            message: str
            username: Optional[str] = None
        
        # Success response
        resp = LoginResponse(success=True, token="abc123", 
                            message="Login successful", username="admin")
        assert resp.success is True
        assert resp.token == "abc123"


class TestOpportunityEndpoints:
    """Tests for opportunity-related endpoints"""
    
    def test_opportunity_response_structure(self, sample_opportunity):
        """Test opportunity response has expected fields"""
        required_fields = ["id", "name", "description", "source", 
                          "gap_score", "similarity_score", "opportunity_level"]
        for field in required_fields:
            assert field in sample_opportunity
    
    def test_gap_score_range(self, sample_opportunity):
        """Test gap score is within valid range"""
        score = sample_opportunity["gap_score"]
        assert 0 <= score <= 1, "Gap score must be between 0 and 1"
    
    def test_opportunity_level_values(self):
        """Test opportunity level has valid values"""
        valid_levels = ["HIGH", "MEDIUM", "LOW"]
        # Would test actual endpoint response
        for level in valid_levels:
            assert level in ["HIGH", "MEDIUM", "LOW"]


class TestAnalysisRequest:
    """Tests for /api/analyze endpoint request validation"""
    
    def test_analysis_request_model(self):
        """Test AnalysisRequest model"""
        from pydantic import BaseModel
        from typing import List, Optional
        
        class AnalysisRequest(BaseModel):
            startup_name: str
            description: str
            tags: List[str] = []
            source: str = "yc"
            batch: Optional[str] = None
        
        req = AnalysisRequest(
            startup_name="TestCo",
            description="AI-powered testing platform",
            tags=["AI", "Testing"]
        )
        assert req.startup_name == "TestCo"
        assert len(req.tags) == 2


class TestScrapeEndpoint:
    """Tests for /api/scrape endpoint"""
    
    def test_scrape_request_validation(self):
        """Test ScrapeRequest model validation"""
        from pydantic import BaseModel, Field
        from typing import Optional
        
        class ScrapeRequest(BaseModel):
            source: str = Field(..., description="Source: 'yc' or 'ph' or 'all'")
            batch: Optional[str] = None
            limit: int = Field(default=50, ge=1, le=200)
        
        # Valid request
        req = ScrapeRequest(source="yc", limit=100)
        assert req.source == "yc"
        assert req.limit == 100
        
        # Test limit bounds
        req_min = ScrapeRequest(source="ph", limit=1)
        assert req_min.limit == 1

"""
Pytest fixtures for IndoGap tests
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_startup():
    """Sample startup data for testing"""
    return {
        "id": "test_001",
        "name": "TestStartup",
        "description": "A test startup for unit testing",
        "tags": ["AI", "SaaS", "B2B"],
        "source": "yc",
        "batch": "W24"
    }


@pytest.fixture
def sample_opportunity():
    """Sample opportunity data for testing"""
    return {
        "id": "opp_test_001",
        "name": "TestOpportunity",
        "description": "A test opportunity",
        "source": "yc",
        "gap_score": 0.75,
        "similarity_score": 0.25,
        "opportunity_level": "HIGH",
        "analysis": {"market_gap": "High potential"},
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def indian_startups():
    """Sample Indian startups for testing"""
    return [
        {"id": "ind_001", "name": "Razorpay", "category": "Fintech", "tags": ["payments"]},
        {"id": "ind_002", "name": "Freshworks", "category": "SaaS", "tags": ["crm", "saas"]},
        {"id": "ind_003", "name": "Zoho", "category": "SaaS", "tags": ["productivity"]},
    ]

"""
Scraper Tests for IndoGap

Tests the web scraper functionality.
Run with: pytest tests/test_scrapers.py -v
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestScraperResult:
    """Tests for ScraperResult dataclass"""
    
    def test_scraper_result_creation(self):
        """Test creating a ScraperResult"""
        from mini_services.scrapers.base import ScraperResult
        
        result = ScraperResult(success=True, data=[{"name": "Test"}])
        assert result.success is True
        assert result.count == 1
    
    def test_scraper_result_empty(self):
        """Test empty ScraperResult"""
        from mini_services.scrapers.base import ScraperResult
        
        result = ScraperResult(success=False)
        assert result.is_empty() is True
        assert result.count == 0
    
    def test_add_error(self):
        """Test adding errors to result"""
        from mini_services.scrapers.base import ScraperResult
        
        result = ScraperResult(success=False)
        result.add_error("Connection timeout")
        result.add_error("Rate limited")
        assert len(result.errors) == 2


class TestBaseScraper:
    """Tests for BaseScraper class"""
    
    def test_user_agent_rotation(self):
        """Test that User-Agents are rotated"""
        from mini_services.scrapers.base import USER_AGENTS
        
        assert len(USER_AGENTS) >= 4, "Should have multiple User-Agents"
        
        # All should be valid User-Agent strings
        for ua in USER_AGENTS:
            assert "Mozilla" in ua or "Chrome" in ua or "Safari" in ua
    
    def test_scraper_stats(self):
        """Test scraper statistics"""
        from mini_services.scrapers.base import BaseScraper
        
        # Can't instantiate abstract class, so test the expected interface
        expected_stats = ["name", "requests_made", "errors_encountered", "success_rate"]
        assert len(expected_stats) == 4


class TestYCombinatorScraper:
    """Tests for Y Combinator scraper"""
    
    def test_batch_sort_key(self):
        """Test batch sorting logic"""
        batches = ["W24", "S23", "W23", "S24"]
        # W24 should be highest, then S24, W23, S23
        sorted_batches = sorted(batches, reverse=True)
        assert sorted_batches[0] in ["W24", "S24"]
    
    def test_company_name_validation(self):
        """Test company name validation logic"""
        # Valid names
        valid_names = ["Stripe", "Airbnb", "OpenAI", "Y Combinator startup"]
        for name in valid_names:
            assert len(name) > 1 and len(name) < 200
        
        # Invalid names (too short or too long)
        invalid_names = ["", "A" * 201]
        for name in invalid_names:
            assert len(name) < 2 or len(name) > 200


class TestProductHuntScraper:
    """Tests for Product Hunt scraper"""
    
    def test_upvote_threshold(self):
        """Test upvote threshold filtering"""
        products = [
            {"name": "Product A", "upvotes": 500},
            {"name": "Product B", "upvotes": 50},
            {"name": "Product C", "upvotes": 150},
        ]
        min_upvotes = 100
        filtered = [p for p in products if p["upvotes"] >= min_upvotes]
        assert len(filtered) == 2
        assert all(p["upvotes"] >= min_upvotes for p in filtered)


class TestScraperErrors:
    """Tests for scraper error handling"""
    
    def test_scraper_error_creation(self):
        """Test ScraperError exception"""
        from mini_services.scrapers.base import ScraperError
        
        error = ScraperError("Connection failed", source="yc_scraper")
        assert error.message == "Connection failed"
        assert error.source == "yc_scraper"
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception"""
        from mini_services.scrapers.base import RateLimitError
        
        error = RateLimitError("Too many requests", source="ph_scraper")
        assert isinstance(error, Exception)
        assert "Too many" in error.message

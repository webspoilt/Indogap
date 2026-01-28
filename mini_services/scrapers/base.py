"""
Base scraper class for IndoGap - AI-Powered Opportunity Discovery Engine

This module defines the abstract base class that all scrapers must implement,
providing common functionality for web scraping, rate limiting, and error handling.
"""
import time
import logging
import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from mini_services.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=dict)

# User-Agent rotation pool to avoid being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


@dataclass
class ScraperResult(Generic[T]):
    """Generic result container for scraper outputs"""
    success: bool
    data: Optional[List[T]] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.now)
    
    @property
    def count(self) -> int:
        """Number of items scraped"""
        return len(self.data) if self.data else 0
    
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def is_empty(self) -> bool:
        """Check if result contains no data"""
        return self.count == 0


class ScraperError(Exception):
    """Base exception for scraper errors"""
    def __init__(self, message: str, source: str = "Unknown", details: Dict = None):
        self.message = message
        self.source = source
        self.details = details or {}
        super().__init__(message)


class RateLimitError(ScraperError):
    """Exception raised when rate limit is encountered"""
    pass


class ValidationError(ScraperError):
    """Exception raised when validation fails"""
    pass


class BaseScraper(ABC):
    """
    Abstract base class for all web scrapers.
    
    Provides common functionality:
    - HTTP client management with proper headers
    - Rate limiting and delay between requests
    - Retry logic with exponential backoff
    - Error handling and logging
    - Result caching and persistence
    
    Subclasses must implement:
    - scrape(): Main scraping logic
    - parse_response(): Parse raw response into structured data
    - validate_data(): Validate parsed data
    """
    
    def __init__(
        self,
        name: str,
        base_url: str = "",
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the scraper.
        
        Args:
            name: Scraper name for logging
            base_url: Base URL for requests
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            user_agent: Custom User-Agent string
        """
        self.name = name
        self.base_url = base_url
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        
        settings = get_settings()
        self.user_agent = user_agent or settings.user_agent
        
        self.client: Optional[httpx.Client] = None
        self._request_count = 0
        self._error_count = 0
        self._last_request_time: Optional[float] = None
        
    def _create_client(self) -> httpx.Client:
        """Create HTTP client with proper configuration and random User-Agent"""
        settings = get_settings()
        
        # Use random User-Agent for anti-detection (rotate on each client creation)
        selected_ua = self.user_agent if self.user_agent else random.choice(USER_AGENTS)
        
        headers = {
            "User-Agent": selected_ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        timeout = httpx.Timeout(settings.request_timeout)
        
        return httpx.Client(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
    
    def __enter__(self) -> "BaseScraper":
        """Context manager entry"""
        self.client = self._create_client()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        if self.client:
            self.client.close()
            self.client = None
    
    async def __aenter__(self) -> "BaseScraper":
        """Async context manager entry"""
        self.client = self._create_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        if self.client:
            self.client.close()  # Use sync close for sync httpx.Client
            self.client = None
    
    def _ensure_client(self) -> None:
        """Ensure HTTP client is created"""
        if self.client is None:
            self.client = self._create_client()
    
    def _respect_delay(self) -> None:
        """Wait to respect rate limiting delay"""
        if self.delay > 0 and self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
    )
    def _make_request(self, url: str, **kwargs) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
            
        Raises:
            ScraperError: On request failure after retries
        """
        self._ensure_client()
        self._respect_delay()
        
        try:
            response = self.client.get(url, **kwargs)
            response.raise_for_status()
            self._request_count += 1
            return response
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    source=self.name,
                    details={"url": url, "status": e.response.status_code}
                )
            raise ScraperError(
                f"HTTP error: {e.response.status_code}",
                source=self.name,
                details={"url": url, "status": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise ScraperError(
                f"Request failed: {str(e)}",
                source=self.name,
                details={"url": url}
            )
    
    def _make_sync_request(self, url: str, **kwargs) -> httpx.Response:
        """
        Synchronous request wrapper.
        
        For use outside async context.
        """
        return self._make_request(url, **kwargs)
    
    async def _make_async_request(self, url: str, **kwargs) -> httpx.Response:
        """
        Async request wrapper.
        
        For use in async context with httpx.AsyncClient.
        """
        self._ensure_client()
        self._respect_delay()
        
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            self._request_count += 1
            return response
        except httpx.RequestError as e:
            raise ScraperError(f"Async request failed: {str(e)}", source=self.name)
    
    @abstractmethod
    def scrape(self, **kwargs) -> ScraperResult:
        """
        Main scraping method to be implemented by subclasses.
        
        Args:
            **kwargs: Scraping parameters
            
        Returns:
            ScraperResult containing scraped data
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: httpx.Response) -> List[Dict[str, Any]]:
        """
        Parse raw HTTP response into structured data.
        
        Args:
            response: HTTP response object
            
        Returns:
            List of parsed data dictionaries
        """
        pass
    
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean scraped data.
        
        Override in subclasses for specific validation.
        
        Args:
            data: List of data dictionaries
            
        Returns:
            Validated and cleaned data
        """
        # Basic validation: remove empty entries
        return [item for item in data if item and len(item) > 0]
    
    def save_results(
        self,
        result: ScraperResult,
        output_dir: Optional[Path] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Save scraping results to file.
        
        Args:
            result: ScraperResult to save
            output_dir: Output directory (default: from config)
            filename: Custom filename
            
        Returns:
            Path to saved file
        """
        import json
        
        settings = get_settings()
        output_dir = output_dir or settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{timestamp}.json"
        
        filepath = output_dir / filename
        
        output_data = {
            "scraper": self.name,
            "scraped_at": result.scraped_at.isoformat(),
            "success": result.success,
            "count": result.count,
            "errors": result.errors,
            "metadata": result.metadata,
            "data": result.data,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {result.count} items to {filepath}")
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        return {
            "name": self.name,
            "requests_made": self._request_count,
            "errors_encountered": self._error_count,
            "success_rate": (
                self._request_count / (self._request_count + self._error_count)
                if (self._request_count + self._error_count) > 0 else 1.0
            ),
        }


def create_scraper(scraper_type: str, **kwargs):
    """
    Factory function to create scraper instances.
    
    Args:
        scraper_type: Type of scraper to create
        **kwargs: Additional scraper configuration
        
    Returns:
        BaseScraper instance
        
    Raises:
        ValueError: If scraper type is not recognized
    """
    scrapers = {
        "yc": ("mini_services.scrapers.yc_scraper", "YCombinatorScraper"),
        "ycombinator": ("mini_services.scrapers.yc_scraper", "YCombinatorScraper"),
        "product_hunt": ("mini_services.scrapers.product_hunt", "ProductHuntScraper"),
        "producthunt": ("mini_services.scrapers.product_hunt", "ProductHuntScraper"),
    }
    
    if scraper_type.lower() not in scrapers:
        raise ValueError(f"Unknown scraper type: {scraper_type}")
    
    module_path, class_name = scrapers[scraper_type.lower()]
    
    import importlib
    module = importlib.import_module(module_path)
    scraper_class = getattr(module, class_name)
    
    return scraper_class(**kwargs)

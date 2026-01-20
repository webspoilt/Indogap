"""
Scrapers package for IndoGap - AI-Powered Opportunity Discovery Engine

This package contains modules for scraping data from various sources
including Y Combinator, Product Hunt, and other startup databases.
"""
from .base import BaseScraper, ScraperResult, create_scraper
from .yc_scraper import YCombinatorScraper
from .product_hunt import ProductHuntScraper

__all__ = [
    "BaseScraper",
    "ScraperResult",
    "create_scraper",
    "YCombinatorScraper",
    "ProductHuntScraper",
]

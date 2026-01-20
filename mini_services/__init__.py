"""
Mini Services - AI-Powered Opportunity Discovery Engine for India
"""
__version__ = "0.1.0"
__author__ = "IndoGap Team"

from .config import get_settings, Settings
from .database.repository import create_repository
from .scrapers.yc_scraper import create_scraper
from .processors.text_processor import create_text_processor
from .processors.similarity import create_similarity_engine
from .scoring.seven_dimensions import create_scorer
from .mvp_generator.generator import create_generator

__all__ = [
    "get_settings",
    "Settings",
    "create_repository",
    "create_scraper",
    "create_text_processor",
    "create_similarity_engine",
    "create_scorer",
    "create_generator",
]

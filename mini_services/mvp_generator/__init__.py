"""
MVP Generator package for IndoGap - AI-Powered Opportunity Discovery Engine

This package contains modules for generating localized MVP roadmaps for
opportunities identified in the Indian market.
"""
from .generator import MVPGenerator, create_generator
from .india_localizer import IndiaLocalizer

__all__ = [
    "MVPGenerator",
    "create_generator",
    "IndiaLocalizer",
]

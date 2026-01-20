"""
Database Repository - Package exports for IndoGap

This module re-exports all database functionality from repository.py
for clean imports throughout the application.
"""
from .repository import (
    InMemoryRepository,
    OpportunityRepository,
    get_repository,
    create_repository,
    init_database,
    close_database,
)

__all__ = [
    "InMemoryRepository",
    "OpportunityRepository",
    "get_repository",
    "create_repository",
    "init_database",
    "close_database",
]

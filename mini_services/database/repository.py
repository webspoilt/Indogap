"""
Database Repository - Placeholder for future database implementation.

This module provides a simple in-memory repository for the MVP/trial version.
In production, this would be replaced with PostgreSQL + pgvector implementation.
"""
from typing import List, Optional, Any, Dict
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from mini_services.models.startup import GlobalStartup, IndianStartup
from mini_services.models.opportunity import Opportunity
from mini_services.config import get_settings

logger = logging.getLogger(__name__)
Base = declarative_base()

class GlobalStartupModel(Base):
    __tablename__ = "global_startups"
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    short_description = Column(String, nullable=True)
    tags = Column(JSON)
    website = Column(String, nullable=True)
    source = Column(String)
    source_id = Column(String, nullable=True)
    batch = Column(String, nullable=True)
    funding_stage = Column(String, nullable=True)
    funding_amount = Column(String, nullable=True)
    analyzed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class IndianStartupModel(Base):
    __tablename__ = "indian_startups"
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    category = Column(String)
    tags = Column(JSON)
    website = Column(String, nullable=True)
    headquarters = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class OpportunityModel(Base):
    __tablename__ = "opportunities"
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    source = Column(String)
    gap_score = Column(Float)
    similarity_score = Column(Float)
    opportunity_level = Column(String)
    analysis = Column(JSON)
    mvp_spec = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PostgreSQLRepository:
    """
    PostgreSQL implementation of the repository using SQLAlchemy.
    Includes connection pooling for better performance under load.
    """
    def __init__(self, database_url: str):
        # Configure connection pooling to prevent connection exhaustion
        self.engine = create_engine(
            database_url,
            pool_size=10,           # Number of connections to maintain
            max_overflow=20,        # Additional connections when pool is full
            pool_pre_ping=True,     # Test connections before use
            pool_recycle=300        # Recycle connections after 5 minutes
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    async def store_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """Store an analyzed opportunity"""
        session = self.Session()
        try:
            opp_id = opportunity.get("id")
            existing = session.query(OpportunityModel).filter_by(id=opp_id).first()
            if existing:
                for key, value in opportunity.items():
                    if hasattr(existing, key): setattr(existing, key, value)
            else:
                new_opp = OpportunityModel(**opportunity)
                session.add(new_opp)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing opportunity: {e}")
            raise
        finally:
            session.close()

    async def store_global_startup(self, startup: Dict[str, Any]) -> None:
        """Store a global startup"""
        session = self.Session()
        try:
            sid = startup.get("id")
            existing = session.query(GlobalStartupModel).filter_by(id=sid).first()
            if existing:
                for key, value in startup.items():
                    if hasattr(existing, key): setattr(existing, key, value)
            else:
                new_item = GlobalStartupModel(**startup)
                session.add(new_item)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing global startup: {e}")
            raise
        finally:
            session.close()

    async def store_indian_startup(self, startup: Dict[str, Any]) -> None:
        """Store an Indian startup"""
        session = self.Session()
        try:
            sid = startup.get("id")
            existing = session.query(IndianStartupModel).filter_by(id=sid).first()
            if existing:
                for key, value in startup.items():
                    if hasattr(existing, key): setattr(existing, key, value)
            else:
                new_item = IndianStartupModel(**startup)
                session.add(new_item)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing indian startup: {e}")
            raise
        finally:
            session.close()

    async def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all stored opportunities"""
        session = self.Session()
        try:
            opportunities = session.query(OpportunityModel).order_by(OpportunityModel.created_at.desc()).all()
            return [
                {
                    "id": opp.id,
                    "name": opp.name,
                    "description": opp.description,
                    "source": opp.source,
                    "gap_score": opp.gap_score,
                    "similarity_score": opp.similarity_score,
                    "opportunity_level": opp.opportunity_level,
                    "analysis": opp.analysis,
                    "mvp_spec": opp.mvp_spec,
                    "created_at": opp.created_at.isoformat()
                }
                for opp in opportunities
            ]
        finally:
            session.close()

    async def get_all_global_startups(self) -> List[Dict[str, Any]]:
        """Get all global startups (YC, Product Hunt)"""
        session = self.Session()
        try:
            startups = session.query(GlobalStartupModel).order_by(GlobalStartupModel.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "short_description": s.short_description,
                    "tags": s.tags,
                    "website": s.website,
                    "source": s.source,
                    "batch": s.batch,
                    "funding_stage": s.funding_stage,
                    "analyzed": s.analyzed,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in startups
            ]
        finally:
            session.close()

    async def get_all_indian_startups(self) -> List[Dict[str, Any]]:
        """Get all Indian startups"""
        session = self.Session()
        try:
            startups = session.query(IndianStartupModel).order_by(IndianStartupModel.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "category": s.category,
                    "tags": s.tags,
                    "website": s.website,
                    "headquarters": s.headquarters,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in startups
            ]
        finally:
            session.close()

    async def delete_opportunity(self, opportunity_id: str) -> bool:
        """Delete an opportunity by ID"""
        session = self.Session()
        try:
            opp = session.query(OpportunityModel).filter_by(id=opportunity_id).first()
            if opp:
                session.delete(opp)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting opportunity: {e}")
            raise
        finally:
            session.close()


class InMemoryRepository:
    """
    Simple in-memory repository for testing and fallback.
    """
    def __init__(self):
        self.opportunities: List[Dict[str, Any]] = []
        self.global_startups: List[Dict[str, Any]] = []
        self.indian_startups: List[Dict[str, Any]] = []
    
    async def store_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """Store an opportunity in memory"""
        self.opportunities.append(opportunity)
    
    async def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all stored opportunities"""
        return self.opportunities

    async def get_all_global_startups(self) -> List[Dict[str, Any]]:
        """Get all global startups"""
        return self.global_startups

    async def get_all_indian_startups(self) -> List[Dict[str, Any]]:
        """Get all Indian startups"""
        return self.indian_startups

    async def delete_opportunity(self, opportunity_id: str) -> bool:
        """Delete an opportunity by ID"""
        for i, opp in enumerate(self.opportunities):
            if opp.get("id") == opportunity_id:
                del self.opportunities[i]
                return True
        return False


# Singleton instance for the application
_repository_instance = None


def get_repository():
    """Get or create the repository singleton based on configuration"""
    global _repository_instance
    if _repository_instance is None:
        settings = get_settings()
        # Check if database_url is provided and not a default placeholder
        if settings.database_url and "postgres" in settings.database_url:
            try:
                logger.info(f"Initializing PostgreSQL repository...")
                _repository_instance = PostgreSQLRepository(settings.database_url)
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL: {e}. Falling back to InMemory.")
                _repository_instance = InMemoryRepository()
        else:
            logger.info("Using InMemory repository (No DATABASE_URL found)")
            _repository_instance = InMemoryRepository()
    return _repository_instance

# Aliases and Compatibility
OpportunityRepository = PostgreSQLRepository
create_repository = get_repository

def init_database():
    """Initialize database connection"""
    get_repository()

def close_database():
    """Close database connection"""
    pass

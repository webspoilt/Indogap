"""
Startup data models for IndoGap - AI-Powered Opportunity Discovery Engine

This module defines data models for tracking both global startups (from YC, Product Hunt, etc.)
and Indian startups (the knowledge graph for comparison).
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, HttpUrl


class StartupType(str, Enum):
    """Classification of startup types based on business model"""
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    C2C = "c2c"
    PLATFORM = "platform"
    SAAS = "saas"
    MARKETPLACE = "marketplace"
    D2C = "d2c"


class StartupSource(str, Enum):
    """Source of startup data"""
    Y_COMBINATOR = "yc"
    PRODUCT_HUNT = "product_hunt"
    CRUNCHBASE = "crunchbase"
    MANUAL = "manual"
    API = "api"
    OTHER = "other"


class StartupStatus(str, Enum):
    """Status of startup in the system"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ACQUIRED = "acquired"
    SHUT_DOWN = "shut_down"
    IPO = "ipo"
    UNKNOWN = "unknown"


class FundingStage(str, Enum):
    """Startup funding stages"""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D = "series_d"
    LATE_STAGE = "late_stage"
    PUBLIC = "public"
    BOOTSTRAPPED = "bootstrapped"
    UNKNOWN = "unknown"


class IndianStartupCategory(str, Enum):
    """Categories for Indian startups"""
    FINTECH = "fintech"
    E_COMMERCE = "e_commerce"
    SAAS = "saas"
    HEALTHTECH = "healthtech"
    EDTECH = "edtech"
    FOOD_DELIVERY = "food_delivery"
    LOGISTICS = "logistics"
    B2B = "b2b"
    CONSUMER = "consumer"
    AI_ML = "ai_ml"
    CRYPTO = "crypto"
    REAL_ESTATE = "real_estate"
    HR_TECH = "hr_tech"
    LEGAL_TECH = "legal_tech"
    INSURTECH = "insurtech"
    PROP_TECH = "prop_tech"
    AGRITECH = "agritech"
    CLIMATE_TECH = "climate_tech"
    DEEPTECH = "deeptech"
    MOBILITY = "mobility"
    TRAVEL = "travel"
    SOCIAL = "social"
    CONTENT = "content"
    DEVOPS = "devops"
    CYBERSECURITY = "cybersecurity"
    OTHER = "other"


class BaseStartup(BaseModel):
    """Base model with common startup fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Startup name")
    description: str = Field(..., min_length=10, description="Startup description")
    short_description: Optional[str] = Field(None, max_length=200, description="Brief one-line description")
    tags: List[str] = Field(default_factory=list, description="Tags/categories")
    website: Optional[str] = Field(None, description="Website URL")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format"""
        if v is None:
            return v
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v
    
    def to_text(self) -> str:
        """Combine all text fields for embedding"""
        parts = [
            self.name,
            self.short_description or "",
            self.description,
            " ".join(self.tags)
        ]
        return " ".join(filter(None, parts))


class GlobalStartup(BaseStartup):
    """
    Model for tracking global startups from YC, Product Hunt, etc.
    
    This represents startups that could potentially be adapted for the Indian market.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    source: StartupSource = Field(..., description="Data source")
    source_id: Optional[str] = Field(None, description="ID in source system")
    
    # YC-specific fields
    batch: Optional[str] = Field(None, description="YC batch (e.g., W24, S25)")
    yc_url: Optional[str] = Field(None, description="YC company page URL")
    
    # Product Hunt specific
    product_hunt_url: Optional[str] = Field(None, description="Product Hunt URL")
    launch_date: Optional[datetime] = Field(None, description="Product launch date")
    upvotes: Optional[int] = Field(None, description="Product Hunt upvotes")
    
    # Funding information
    funding_stage: Optional[FundingStage] = Field(None, description="Funding stage")
    funding_amount: Optional[str] = Field(None, description="Funding amount raised")
    last_funding_date: Optional[datetime] = Field(None, description="Last funding date")
    
    # Analysis fields
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    analyzed: bool = Field(default=False, description="Whether analyzed for India")
    analysis_date: Optional[datetime] = Field(None, description="Last analysis date")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation date")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update date")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "short_description": self.short_description,
            "tags": self.tags,
            "website": self.website,
            "source": self.source.value if self.source else None,
            "source_id": self.source_id,
            "batch": self.batch,
            "funding_stage": self.funding_stage.value if self.funding_stage else None,
            "funding_amount": self.funding_amount,
            "analyzed": self.analyzed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IndianStartup(BaseStartup):
    """
    Model for Indian startups in the knowledge graph.
    
    This represents the competitive landscape for gap detection.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    
    # Category classification
    category: IndianStartupCategory = Field(..., description="Primary category")
    sub_categories: List[str] = Field(default_factory=list, description="Secondary categories")
    
    # Company details
    headquarters: Optional[str] = Field(None, description="City/state headquarters")
    founded_date: Optional[str] = Field(None, description="Founded date")
    team_size: Optional[str] = Field(None, description="Team size description")
    
    # Funding
    funding_stage: Optional[FundingStage] = Field(None, description="Funding stage")
    funding_amount: Optional[str] = Field(None, description="Total funding raised")
    last_funding_date: Optional[datetime] = Field(None, description="Last funding date")
    investors: List[str] = Field(default_factory=list, description="Key investors")
    
    # Market position
    market_position: Optional[str] = Field(None, description="Market position description")
    target_segment: Optional[str] = Field(None, description="Target customer segment")
    geographic_focus: List[str] = Field(default_factory=list, description="Geographic focus areas")
    
    # Business metrics (where available)
    gmv: Optional[str] = Field(None, description="Gross Merchandise Value")
    revenue: Optional[str] = Field(None, description="Annual revenue")
    customers: Optional[str] = Field(None, description="Number of customers")
    
    # Analysis fields
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    
    # Status
    status: StartupStatus = Field(default=StartupStatus.ACTIVE, description="Startup status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation date")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "funding_stage": self.funding_stage.value if self.funding_stage else None,
            "funding_amount": self.funding_amount,
            "headquarters": self.headquarters,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def create_global_startup(
    name: str,
    description: str,
    source: StartupSource,
    short_description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    website: Optional[str] = None,
    batch: Optional[str] = None,
    **kwargs
) -> GlobalStartup:
    """
    Factory function to create a GlobalStartup instance.
    
    Args:
        name: Startup name
        description: Full description
        source: Data source (YC, Product Hunt, etc.)
        short_description: Brief description
        tags: List of tags
        website: Website URL
        batch: YC batch (if applicable)
        **kwargs: Additional fields
        
    Returns:
        GlobalStartup instance
    """
    return GlobalStartup(
        name=name,
        description=description,
        short_description=short_description or description[:200],
        tags=tags or [],
        website=website,
        source=source,
        batch=batch,
        **kwargs
    )


def create_indian_startup(
    name: str,
    description: str,
    category: IndianStartupCategory,
    short_description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    website: Optional[str] = None,
    headquarters: Optional[str] = None,
    funding_stage: Optional[FundingStage] = None,
    funding_amount: Optional[str] = None,
    **kwargs
) -> IndianStartup:
    """
    Factory function to create an IndianStartup instance.
    
    Args:
        name: Startup name
        description: Full description
        category: Primary category
        short_description: Brief description
        tags: List of tags
        website: Website URL
        headquarters: City/state
        funding_stage: Funding stage
        funding_amount: Amount raised
        **kwargs: Additional fields
        
    Returns:
        IndianStartup instance
    """
    return IndianStartup(
        name=name,
        description=description,
        short_description=short_description or description[:200],
        tags=tags or [],
        website=website,
        category=category,
        headquarters=headquarters,
        funding_stage=funding_stage,
        funding_amount=funding_amount,
        **kwargs
    )

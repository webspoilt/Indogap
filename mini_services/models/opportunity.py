"""
Opportunity data models for IndoGap - AI-Powered Opportunity Discovery Engine

This module defines data models for tracking market opportunities discovered
by comparing global startups against the Indian market landscape.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class OpportunityLevel(str, Enum):
    """Classification of opportunity levels based on gap score"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class OpportunityStatus(str, Enum):
    """Status of opportunity in the pipeline"""
    NEW = "new"
    VALIDATING = "validating"
    PRIORITIZED = "prioritized"
    BUILDING = "building"
    LAUNCHED = "launched"
    SOLD = "sold"
    DECLINED = "declined"
    ARCHIVED = "archived"


class OpportunityPriority(str, Enum):
    """Priority levels for opportunity handling"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SimilarityMatch(BaseModel):
    """Model for storing similarity match results"""
    matched_startup_id: str = Field(..., description="ID of matched Indian startup")
    matched_startup_name: str = Field(..., description="Name of matched startup")
    matched_startup_category: str = Field(..., description="Category of matched startup")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1)")
    gap_score: float = Field(..., ge=0, le=1, description="Gap score (1 - similarity)")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords that matched")
    missing_keywords: List[str] = Field(default_factory=list, description="Keywords not found in India")


class Opportunity(BaseModel):
    """
    Model for tracking discovered market opportunities.
    
    An opportunity represents a gap in the Indian market where a global
    startup's model could potentially succeed.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    
    # Source startup information
    source_startup_id: str = Field(..., description="ID of source global startup")
    source_startup_name: str = Field(..., description="Name of source startup")
    source_startup_description: str = Field(..., description="Description from source")
    source_batch: Optional[str] = Field(None, description="YC batch if applicable")
    source_tags: List[str] = Field(default_factory=list, description="Tags from source")
    source_url: Optional[str] = Field(None, description="URL to source")
    
    # Comparison results
    best_match: Optional[SimilarityMatch] = Field(None, description="Best matching Indian startup")
    other_matches: List[SimilarityMatch] = Field(default_factory=list, description="Other similar startups")
    comparison_summary: str = Field("", description="Summary of comparison analysis")
    
    # Scoring
    overall_score: Optional[float] = Field(None, ge=0, le=1, description="Overall opportunity score")
    cultural_fit_score: Optional[int] = Field(None, ge=1, le=10, description="Cultural fit score (1-10)")
    logistics_score: Optional[int] = Field(None, ge=1, le=10, description="Logistics feasibility score")
    payment_readiness_score: Optional[int] = Field(None, ge=1, le=10, description="Payment readiness score")
    timing_score: Optional[int] = Field(None, ge=1, le=10, description="Timing alignment score")
    monopoly_score: Optional[int] = Field(None, ge=1, le=10, description="Monopoly potential score")
    regulatory_score: Optional[int] = Field(None, ge=1, le=10, description="Regulatory risk score")
    execution_score: Optional[int] = Field(None, ge=1, le=10, description="Execution feasibility score")
    scoring_reasoning: Optional[str] = Field(None, description="AI reasoning for scores")
    
    # Classification
    opportunity_level: OpportunityLevel = Field(
        default=OpportunityLevel.UNKNOWN, 
        description="Opportunity level classification"
    )
    inferred_categories: List[str] = Field(default_factory=list, description="Inferred categories for India")
    
    # MVP Roadmap (if generated)
    mvp_roadmap_id: Optional[str] = Field(None, description="ID of generated MVP roadmap")
    mvp_timeline: Optional[str] = Field(None, description="Estimated MVP timeline")
    mvp_complexity: Optional[str] = Field(None, description="MVP complexity level")
    
    # Status tracking
    status: OpportunityStatus = Field(default=OpportunityStatus.NEW, description="Opportunity status")
    priority: OpportunityPriority = Field(default=OpportunityPriority.MEDIUM, description="Priority level")
    
    # Actions
    recommendation: Optional[str] = Field(None, description="System recommendation")
    notes: List[str] = Field(default_factory=list, description="Additional notes")
    action_items: List[str] = Field(default_factory=list, description="Suggested action items")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation date")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update date")
    analyzed_at: Optional[datetime] = Field(None, description="When analysis was completed")
    last_action_at: Optional[datetime] = Field(None, description="When status was last changed")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        from_attributes = True
    
    @property
    def is_high_opportunity(self) -> bool:
        """Check if this is a high-priority opportunity"""
        return self.opportunity_level == OpportunityLevel.HIGH
    
    @property
    def has_mvp(self) -> bool:
        """Check if MVP roadmap has been generated"""
        return self.mvp_roadmap_id is not None
    
    @property
    def requires_attention(self) -> bool:
        """Check if opportunity needs attention"""
        return self.status in [
            OpportunityStatus.NEW,
            OpportunityStatus.VALIDATING,
            OpportunityStatus.PRIORITIZED
        ]
    
    def update_status(self, new_status: OpportunityStatus) -> None:
        """Update opportunity status with timestamp"""
        self.status = new_status
        self.last_action_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_note(self, note: str) -> None:
        """Add a note to the opportunity"""
        self.notes.append(note)
        self.updated_at = datetime.now()
    
    def add_action_item(self, action: str) -> None:
        """Add an action item"""
        self.action_items.append(action)
        self.updated_at = datetime.now()
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Create a summary dictionary for display"""
        return {
            "id": self.id,
            "name": self.source_startup_name,
            "level": self.opportunity_level.value if self.opportunity_level else "unknown",
            "score": self.overall_score,
            "best_match": self.best_match.matched_startup_name if self.best_match else "None",
            "status": self.status.value if self.status else "unknown",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "source_startup_id": self.source_startup_id,
            "source_startup_name": self.source_startup_name,
            "source_startup_description": self.source_startup_description,
            "source_batch": self.source_batch,
            "source_tags": self.source_tags,
            "best_match": self.best_match.model_dump() if self.best_match else None,
            "other_matches": [m.model_dump() for m in self.other_matches],
            "overall_score": self.overall_score,
            "opportunity_level": self.opportunity_level.value if self.opportunity_level else None,
            "scoring_reasoning": self.scoring_reasoning,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "recommendation": self.recommendation,
            "notes": self.notes,
            "action_items": self.action_items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


def create_opportunity(
    source_startup_id: str,
    source_startup_name: str,
    source_startup_description: str,
    source_tags: Optional[List[str]] = None,
    source_batch: Optional[str] = None,
    source_url: Optional[str] = None,
    best_match: Optional[SimilarityMatch] = None,
    overall_score: Optional[float] = None,
    opportunity_level: Optional[OpportunityLevel] = None,
    **kwargs
) -> Opportunity:
    """
    Factory function to create an Opportunity instance.
    
    Args:
        source_startup_id: ID of source global startup
        source_startup_name: Name of source startup
        source_startup_description: Description from source
        source_tags: Tags from source
        source_batch: YC batch if applicable
        source_url: URL to source
        best_match: Best matching Indian startup
        overall_score: Overall opportunity score
        opportunity_level: Opportunity level classification
        **kwargs: Additional fields
        
    Returns:
        Opportunity instance
    """
    # Calculate opportunity level if not provided
    if opportunity_level is None and overall_score is not None:
        gap_score = 1.0 - (best_match.similarity_score if best_match else 0)
        if gap_score >= 0.7:
            opportunity_level = OpportunityLevel.HIGH
        elif gap_score >= 0.4:
            opportunity_level = OpportunityLevel.MEDIUM
        else:
            opportunity_level = OpportunityLevel.LOW
    
    return Opportunity(
        source_startup_id=source_startup_id,
        source_startup_name=source_startup_name,
        source_startup_description=source_startup_description,
        source_tags=source_tags or [],
        source_batch=source_batch,
        source_url=source_url,
        best_match=best_match,
        overall_score=overall_score,
        opportunity_level=opportunity_level or OpportunityLevel.UNKNOWN,
        **kwargs
    )

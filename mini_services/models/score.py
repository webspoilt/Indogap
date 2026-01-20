"""
Scoring models for IndoGap - AI-Powered Opportunity Discovery Engine

This module defines data models for the 7-dimension scoring system
and MVP roadmap generation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ScoringDimension(str, Enum):
    """The 7 dimensions for opportunity scoring"""
    CULTURAL_FIT = "cultural_fit"
    LOGISTICS = "logistics"
    PAYMENT_READINESS = "payment_readiness"
    TIMING = "timing"
    MONOPOLY_POTENTIAL = "monopoly_potential"
    REGULATORY_RISK = "regulatory_risk"
    EXECUTION_FEASIBILITY = "execution_feasibility"


class ScoringStatus(str, Enum):
    """Status of scoring process"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class MVPTimeline(str, Enum):
    """MVP development timeline estimates"""
    TWO_WEEKS = "2 weeks"
    ONE_MONTH = "1 month"
    TWO_MONTHS = "2 months"
    THREE_MONTHS = "3 months"
    SIX_MONTHS = "6 months"
    MORE = "6+ months"


class MVPComplexity(str, Enum):
    """MVP complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class DimensionScore(BaseModel):
    """Score for a single dimension"""
    dimension: str = Field(..., description="Dimension name")
    score: int = Field(..., ge=1, le=10, description="Score (1-10)")
    weight: float = Field(default=0.15, ge=0, le=1, description="Weight in overall score")
    reasoning: str = Field("", description="Explanation for the score")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in scoring")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted contribution to overall score"""
        return self.score * self.weight
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dimension": self.dimension,
            "score": self.score,
            "weight": self.weight,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "weighted_score": self.weighted_score,
        }


class SevenDimensionScores(BaseModel):
    """
    Complete 7-dimension scoring for an opportunity.
    
    Dimensions:
    1. Cultural Fit: Does the behavior/habit exist in India?
    2. Logistics: Is physical infrastructure available?
    3. Payment Readiness: Are Indian consumers ready to pay?
    4. Timing: Is the market timing right?
    5. Monopoly Potential: Does it tend toward winner-take-all?
    6. Regulatory Risk: Government intervention probability
    7. Execution Feasibility: Can a small team build this?
    """
    # Individual dimension scores
    cultural_fit: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="cultural_fit", score=5)
    )
    logistics: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="logistics", score=5)
    )
    payment_readiness: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="payment_readiness", score=5)
    )
    timing: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="timing", score=5)
    )
    monopoly_potential: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="monopoly_potential", score=5)
    )
    regulatory_risk: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="regulatory_risk", score=5)
    )
    execution_feasibility: DimensionScore = Field(
        default_factory=lambda: DimensionScore(dimension="execution_feasibility", score=5)
    )
    
    # Overall calculation
    overall_score: float = Field(default=0.0, ge=0, le=1, description="Weighted overall score")
    overall_reasoning: str = Field("", description="Overall reasoning summary")
    
    # Metadata
    model_used: str = Field(default="rule-based", description="Scoring model used")
    model_version: str = Field(default="1.0", description="Model version")
    calculated_at: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted overall score from dimensions"""
        total = sum(d.weighted_score for d in self.get_all_dimensions())
        self.overall_score = total / 10.0  # Normalize to 0-1
        return self.overall_score
    
    def get_all_dimensions(self) -> List[DimensionScore]:
        """Get all dimension scores as a list"""
        return [
            self.cultural_fit,
            self.logistics,
            self.payment_readiness,
            self.timing,
            self.monopoly_potential,
            self.regulatory_risk,
            self.execution_feasibility,
        ]
    
    def get_dimension(self, name: str) -> Optional[DimensionScore]:
        """Get a specific dimension by name"""
        name = name.lower().replace(" ", "_")
        for dim in self.get_all_dimensions():
            if dim.dimension == name:
                return dim
        return None
    
    def get_top_strengths(self, count: int = 3) -> List[DimensionScore]:
        """Get top scoring dimensions (strengths)"""
        return sorted(self.get_all_dimensions(), key=lambda x: x.score, reverse=True)[:count]
    
    def get_top_weaknesses(self, count: int = 3) -> List[DimensionScore]:
        """Get lowest scoring dimensions (weaknesses)"""
        return sorted(self.get_all_dimensions(), key=lambda x: x.score)[:count]
    
    def is_recommended(self, threshold: float = 0.6) -> bool:
        """Check if opportunity is recommended based on score"""
        return self.overall_score >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cultural_fit": self.cultural_fit.to_dict(),
            "logistics": self.logistics.to_dict(),
            "payment_readiness": self.payment_readiness.to_dict(),
            "timing": self.timing.to_dict(),
            "monopoly_potential": self.monopoly_potential.to_dict(),
            "regulatory_risk": self.regulatory_risk.to_dict(),
            "execution_feasibility": self.execution_feasibility.to_dict(),
            "overall_score": self.overall_score,
            "overall_reasoning": self.overall_reasoning,
            "model_used": self.model_used,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }


class MVPMilestone(BaseModel):
    """Individual MVP development milestone"""
    week: int = Field(..., ge=1, le=12, description="Week number")
    title: str = Field(..., description="Milestone title")
    description: str = Field("", description="Detailed description")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")
    complexity: str = Field(default="medium", description="Complexity level")


class MVPTechStack(BaseModel):
    """Technology stack recommendation for MVP"""
    frontend: List[str] = Field(default_factory=list, description="Frontend technologies")
    backend: List[str] = Field(default_factory=list, description="Backend technologies")
    database: List[str] = Field(default_factory=list, description="Database technologies")
    cloud: List[str] = Field(default_factory=list, description="Cloud platforms")
    payments: List[str] = Field(default_factory=list, description="Payment gateways (India-specific)")
    messaging: List[str] = Field(default_factory=list, description="Communication channels")
    ai_ml: List[str] = Field(default_factory=list, description="AI/ML services")


class MVPMarketStrategy(BaseModel):
    """Market strategy for MVP launch"""
    target_cities: List[str] = Field(default_factory=list, description="Initial target cities")
    target_segment: str = Field("", description="Target customer segment")
    pricing_strategy: str = Field("", description="Pricing approach for India")
    pricing_tiers: List[str] = Field(default_factory=list, description="Pricing tier suggestions")
    go_to_market: List[str] = Field(default_factory=list, description="GTM channels")
    customer_acquisition: List[str] = Field(default_factory=list, description="Acquisition strategies")


class MVPRoadmap(BaseModel):
    """
    Complete MVP roadmap for an opportunity.
    
    Generated by the MVP Generator component based on opportunity scoring.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    opportunity_id: str = Field(..., description="Associated opportunity ID")
    
    # Summary
    startup_name: str = Field(..., description="Startup name")
    one_liner: str = Field("", description="One-line value proposition for India")
    
    # Timeline and complexity
    timeline: str = Field(default="3 months", description="Estimated development timeline")
    complexity: str = Field(default="moderate", description="Complexity level")
    estimated_cost: Optional[str] = Field(None, description="Estimated development cost")
    
    # Key features
    core_features: List[str] = Field(default_factory=list, description="Core features for v1")
    future_features: List[str] = Field(default_factory=list, description="Future feature ideas")
    
    # India-specific recommendations
    india_localization: List[str] = Field(default_factory=list, description="India-specific adaptations")
    payment_gateways: List[str] = Field(default_factory=list, description="Recommended payment methods")
    communication_channels: List[str] = Field(default_factory=list, description="Communication channels")
    regulatory_considerations: List[str] = Field(default_factory=list, description="Regulatory notes")
    
    # Technical stack
    tech_stack: MVPTechStack = Field(default_factory=MVPTechStack, description="Recommended tech stack")
    
    # Market strategy
    market_strategy: MVPMarketStrategy = Field(
        default_factory=MVPMarketStrategy, 
        description="Market entry strategy"
    )
    
    # Milestones
    milestones: List[MVPMilestone] = Field(default_factory=list, description="Development milestones")
    
    # Risk factors
    key_risks: List[str] = Field(default_factory=list, description="Key risk factors")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Risk mitigation")
    
    # Success metrics
    success_metrics: List[str] = Field(default_factory=list, description="KPIs to track")
    
    # Full content
    full_roadmap: str = Field("", description="Full markdown roadmap content")
    
    # Metadata
    model_used: str = Field(default="gpt-4", description="Generation model")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    version: str = Field(default="1.0", description="Roadmap version")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "startup_name": self.startup_name,
            "one_liner": self.one_liner,
            "timeline": self.timeline,
            "complexity": self.complexity,
            "estimated_cost": self.estimated_cost,
            "core_features": self.core_features,
            "future_features": self.future_features,
            "india_localization": self.india_localization,
            "payment_gateways": self.payment_gateways,
            "tech_stack": self.tech_stack.model_dump(),
            "market_strategy": self.market_strategy.model_dump(),
            "milestones": [m.model_dump() for m in self.milestones],
            "key_risks": self.key_risks,
            "success_metrics": self.success_metrics,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }


class ScoringResult(BaseModel):
    """
    Complete scoring result for an opportunity.
    
    Contains both the dimension scores and the MVP roadmap.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    opportunity_id: str = Field(..., description="Associated opportunity ID")
    
    # Scoring
    scores: SevenDimensionScores = Field(
        default_factory=SevenDimensionScores, 
        description="Dimension scores"
    )
    status: ScoringStatus = Field(default=ScoringStatus.PENDING, description="Scoring status")
    
    # Reasoning
    summary_reasoning: str = Field("", description="Summary of scoring reasoning")
    detailed_reasoning: str = Field("", description="Detailed reasoning for each dimension")
    
    # MVP Roadmap
    mvp_roadmap: Optional[MVPRoadmap] = Field(None, description="Generated MVP roadmap")
    mvp_status: ScoringStatus = Field(default=ScoringStatus.PENDING, description="MVP generation status")
    
    # Recommendations
    recommendation: str = Field("", description="Final recommendation")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    
    # Metadata
    model_used: str = Field(default="gpt-4o", description="LLM model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    cost_usd: Optional[float] = Field(None, description="API cost in USD")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "scores": self.scores.to_dict(),
            "status": self.status.value if self.status else None,
            "summary_reasoning": self.summary_reasoning,
            "detailed_reasoning": self.detailed_reasoning,
            "mvp_roadmap": self.mvp_roadmap.to_dict() if self.mvp_roadmap else None,
            "recommendation": self.recommendation,
            "next_steps": self.next_steps,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


def create_dimension_score(
    dimension: str,
    score: int,
    weight: float = 0.15,
    reasoning: str = "",
    confidence: float = 0.8,
    evidence: Optional[List[str]] = None,
) -> DimensionScore:
    """
    Factory function to create a DimensionScore.
    
    Args:
        dimension: Dimension name
        score: Score (1-10)
        weight: Weight in overall calculation
        reasoning: Explanation for the score
        confidence: Confidence level (0-1)
        evidence: Supporting evidence list
        
    Returns:
        DimensionScore instance
    """
    return DimensionScore(
        dimension=dimension,
        score=score,
        weight=weight,
        reasoning=reasoning,
        confidence=confidence,
        evidence=evidence or [],
    )


def create_scoring_result(
    opportunity_id: str,
    scores: Optional[SevenDimensionScores] = None,
    status: ScoringStatus = ScoringStatus.COMPLETED,
    recommendation: str = "",
    **kwargs
) -> ScoringResult:
    """
    Factory function to create a ScoringResult.
    
    Args:
        opportunity_id: Associated opportunity ID
        scores: Pre-calculated dimension scores
        status: Scoring status
        recommendation: Final recommendation
        **kwargs: Additional fields
        
    Returns:
        ScoringResult instance
    """
    if scores:
        scores.calculate_overall_score()
    
    return ScoringResult(
        opportunity_id=opportunity_id,
        scores=scores or SevenDimensionScores(),
        status=status,
        recommendation=recommendation,
        **kwargs
    )

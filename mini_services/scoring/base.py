"""
Base Scorer for IndoGap - AI-Powered Opportunity Discovery Engine

This module defines the abstract base class for all scoring implementations
and common data structures for scoring requests and responses.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from mini_services.config import get_settings

logger = logging.getLogger(__name__)


class ScoringDimension(str, Enum):
    """Enumeration of scoring dimensions"""
    CULTURAL_FIT = "cultural_fit"
    LOGISTICS = "logistics"
    PAYMENT_READINESS = "payment_readiness"
    TIMING = "timing"
    MONOPOLY_POTENTIAL = "monopoly_potential"
    REGULATORY_RISK = "regulatory_risk"
    EXECUTION_FEASIBILITY = "execution_feasibility"


class ScoringMethod(str, Enum):
    """Enumeration of scoring methods"""
    RULE_BASED = "rule_based"
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"


@dataclass
class ScoringRequest:
    """Request structure for scoring an opportunity"""
    opportunity_id: str
    startup_name: str
    startup_description: str
    source_market: str = "global"
    source_batch: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    best_match: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    include_reasoning: bool = True
    include_recommendations: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "opportunity_id": self.opportunity_id,
            "startup_name": self.startup_name,
            "startup_description": self.startup_description,
            "source_market": self.source_market,
            "source_batch": self.source_batch,
            "tags": self.tags,
            "best_match": self.best_match,
            "context": self.context,
            "include_reasoning": self.include_reasoning,
            "include_recommendations": self.include_recommendations,
        }


@dataclass
class DimensionScore:
    """Score for a single dimension"""
    dimension: str
    score: int = 5  # 1-10 scale
    weight: float = 0.15
    reasoning: str = ""
    confidence: float = 0.8
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dimension": self.dimension,
            "score": self.score,
            "weight": self.weight,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "weighted_score": self.score * self.weight / 10,
        }


@dataclass
class ScoringResponse:
    """Response structure for scoring results"""
    opportunity_id: str
    overall_score: float = 0.0  # 0-1 scale
    overall_reasoning: str = ""
    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)
    recommendation: str = ""
    next_steps: List[str] = field(default_factory=list)
    opportunity_level: str = "unknown"
    
    # Metadata
    method: str = "rule_based"
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: float = 0.0
    scored_at: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "opportunity_id": self.opportunity_id,
            "overall_score": self.overall_score,
            "overall_reasoning": self.overall_reasoning,
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "recommendation": self.recommendation,
            "next_steps": self.next_steps,
            "opportunity_level": self.opportunity_level,
            "method": self.method,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "scored_at": self.scored_at.isoformat() if self.scored_at else None,
            "errors": self.errors,
        }
    
    def get_dimension(self, name: str) -> Optional[DimensionScore]:
        """Get a specific dimension score"""
        return self.dimensions.get(name)
    
    def get_top_strengths(self, count: int = 3) -> List[DimensionScore]:
        """Get top scoring dimensions"""
        return sorted(
            self.dimensions.values(),
            key=lambda x: x.score,
            reverse=True
        )[:count]
    
    def get_top_weaknesses(self, count: int = 3) -> List[DimensionScore]:
        """Get lowest scoring dimensions"""
        return sorted(
            self.dimensions.values(),
            key=lambda x: x.score
        )[:count]
    
    def is_recommended(self, threshold: float = 0.6) -> bool:
        """Check if opportunity is recommended"""
        return self.overall_score >= threshold
    
    def get_warnings(self) -> List[str]:
        """Get all warnings from dimensions"""
        warnings = []
        for dim in self.dimensions.values():
            warnings.extend(dim.warnings)
        return warnings


class BaseScorer(ABC):
    """
    Abstract base class for scoring implementations.
    
    Subclasses must implement:
    - score(): Main scoring logic
    - get_dimensions(): Return list of dimensions scored
    
    Common functionality:
    - Request validation
    - Response formatting
    - Error handling
    - Statistics tracking
    """
    
    def __init__(self, method: str = "rule_based"):
        """
        Initialize base scorer.
        
        Args:
            method: Scoring method identifier
        """
        self.method = method
        self.settings = get_settings()
        self._scoring_stats = {
            "total_scored": 0,
            "total_time_ms": 0,
            "errors": 0,
        }
    
    @abstractmethod
    def score(self, request: ScoringRequest) -> ScoringResponse:
        """
        Score an opportunity.
        
        Args:
            request: ScoringRequest with opportunity details
            
        Returns:
            ScoringResponse with scores and reasoning
        """
        pass
    
    @abstractmethod
    def get_dimensions(self) -> List[str]:
        """Return list of dimension names this scorer evaluates"""
        pass
    
    def validate_request(self, request: ScoringRequest) -> tuple:
        """
        Validate scoring request.
        
        Args:
            request: Request to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not request.opportunity_id:
            return False, "Missing opportunity_id"
        if not request.startup_name:
            return False, "Missing startup_name"
        if not request.startup_description:
            return False, "Missing startup_description"
        return True, ""
    
    def create_response(
        self,
        request: ScoringRequest,
        **kwargs
    ) -> ScoringResponse:
        """Create a ScoringResponse with common defaults"""
        return ScoringResponse(
            opportunity_id=request.opportunity_id,
            method=self.method,
            **kwargs
        )
    
    def calculate_overall_score(
        self,
        dimensions: Dict[str, DimensionScore],
        weights: Dict[str, float],
    ) -> float:
        """Calculate weighted overall score from dimensions"""
        if not dimensions:
            return 0.0
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for dim_name, dim_score in dimensions.items():
            weight = dim_score.weight or weights.get(dim_name, 0.15)
            total_weighted += dim_score.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize to 0-1 scale (score is 1-10, so divide by 10)
        return (total_weighted / total_weight) / 10.0
    
    def determine_opportunity_level(self, overall_score: float) -> str:
        """Determine opportunity level from overall score"""
        if overall_score >= 0.7:
            return "high"
        elif overall_score >= 0.5:
            return "medium"
        elif overall_score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def generate_recommendation(
        self,
        response: ScoringResponse,
    ) -> str:
        """Generate recommendation based on scoring results"""
        level = response.opportunity_level
        
        if level == "high":
            return (
                "Strong opportunity. Consider building or investing. "
                "The concept shows good alignment with Indian market conditions."
            )
        elif level == "medium":
            return (
                "Moderate opportunity. Proceed with caution. "
                "Some dimensions show promise while others need attention."
            )
        elif level == "low":
            return (
                "Limited opportunity. Significant challenges identified. "
                "Consider pivoting or substantial adaptation before proceeding."
            )
        else:
            return (
                "Not recommended at this time. Multiple barriers to success identified."
            )
    
    def generate_next_steps(
        self,
        response: ScoringResponse,
    ) -> List[str]:
        """Generate suggested next steps based on scoring"""
        steps = []
        weaknesses = response.get_top_weaknesses(3)
        
        for dim in weaknesses:
            if dim.dimension == "cultural_fit":
                steps.append("Conduct user research to validate cultural assumptions")
            elif dim.dimension == "logistics":
                steps.append("Investigate local infrastructure partnerships")
            elif dim.dimension == "payment_readiness":
                steps.append("Research Indian pricing sensitivity and willingness to pay")
            elif dim.dimension == "timing":
                steps.append("Reassess market timing and readiness indicators")
            elif dim.dimension == "regulatory_risk":
                steps.append("Consult with legal experts on regulatory requirements")
            elif dim.dimension == "execution_feasibility":
                steps.append("Evaluate team capabilities and resource requirements")
        
        if response.overall_score >= 0.6:
            steps.insert(0, "Proceed with MVP development")
            steps.append("Set up pilot in Tier 1 city")
        else:
            steps.insert(0, "Conduct deeper market research")
            steps.append("Consider strategic partnership")
        
        return steps[:5]  # Limit to 5 steps
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scorer statistics"""
        return {
            "method": self.method,
            "dimensions": self.get_dimensions(),
            "total_scored": self._scoring_stats["total_scored"],
            "total_time_ms": self._scoring_stats["total_time_ms"],
            "avg_time_ms": (
                self._scoring_stats["total_time_ms"] / max(1, self._scoring_stats["total_scored"])
            ),
            "errors": self._scoring_stats["errors"],
        }
    
    def _record_stat(self, time_ms: float, error: bool = False) -> None:
        """Record scoring statistic"""
        self._scoring_stats["total_scored"] += 1
        self._scoring_stats["total_time_ms"] += time_ms
        if error:
            self._scoring_stats["errors"] += 1


def create_scorer(method: str = "rule_based", **kwargs) -> BaseScorer:
    """
    Factory function to create scorer based on method.
    
    Args:
        method: Scoring method ('rule_based', 'llm_based')
        **kwargs: Additional scorer configuration
        
    Returns:
        BaseScorer instance
    """
    if method == "llm_based":
        from .seven_dimensions import SevenDimensionScorer
        return SevenDimensionScorer(**kwargs)
    else:
        from .seven_dimensions import SevenDimensionScorer
        return SevenDimensionScorer(**kwargs)

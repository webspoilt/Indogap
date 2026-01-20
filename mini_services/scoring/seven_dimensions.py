"""
Seven Dimension Scorer for IndoGap - AI-Powered Opportunity Discovery Engine

This module implements the comprehensive 7-dimension scoring system for
evaluating opportunities in the Indian market.

Dimensions:
1. Cultural Fit: Does the behavior/habit exist in India?
2. Logistics: Is physical infrastructure available?
3. Payment Readiness: Are Indian consumers ready to pay?
4. Timing: Is the market timing right?
5. Monopoly Potential: Does it tend toward winner-take-all?
6. Regulatory Risk: Government intervention probability
7. Execution Feasibility: Can a small team build this?
"""
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from openai import OpenAI

from .base import (
    BaseScorer,
    ScoringRequest,
    ScoringResponse,
    DimensionScore,
    ScoringDimension,
)
from mini_services.config import get_settings

logger = logging.getLogger(__name__)


# India-specific knowledge for rule-based scoring
INDIA_MARKET_KNOWLEDGE = {
    "high_payment_readiness_categories": [
        "b2b software", "enterprise software", "saas", "productivity tools",
        "fintech", "financial services", "investment", "insurance",
    ],
    "low_payment_readiness_categories": [
        "b2c consumer", "social media", "entertainment", "gaming",
        "consumer apps", "lifestyle", "dating", "dating apps",
    ],
    "high_logistics_categories": [
        "food delivery", "grocery delivery", "logistics", "supply chain",
        "e-commerce fulfillment", "last mile delivery", "physical products",
    ],
    "low_logistics_categories": [
        "software", "saas", "ai tools", "api services", "digital products",
        "online courses", "content platforms",
    ],
    "high_regulatory_risk_categories": [
        "fintech", "lending", "crypto", "blockchain", "healthcare",
        "education", "gaming", "gambling", "adult", "insurance",
        "financial services", "telecom",
    ],
    "high_cultural_fit_categories": [
        "payments", "shopping", "food", "education", "healthcare",
        "mobility", "communication", "social",
    ],
    "timing_indicators": {
        "ripe": ["ai", "automation", "saas", "b2b software", "fintech"],
        "saturated": ["food delivery", "ride sharing", "edtech", "ecommerce"],
        "early": ["climate tech", "space tech", "synthetic biology"],
    },
}


@dataclass
class ScoringPrompt:
    """Prompt templates for LLM-based scoring"""
    system_prompt = """You are an expert analyst evaluating business opportunities for the Indian market.
Your task is to score each dimension on a scale of 1-10 based on the opportunity details and provide clear reasoning.
Consider India's unique market characteristics including:
- Large population with diverse languages and income levels
- Growing smartphone and internet penetration
- Strong preference for mobile-first solutions
- Price sensitivity in consumer markets
- Trust and reliability concerns
- Regulatory environment
- Infrastructure limitations in some areas

Provide scores and reasoning for each dimension.
"""
    
    cultural_fit_prompt = """
Evaluate CULTURAL FIT: Does the behavior/habit exist in India?

Consider:
- Do Indians already engage in this behavior?
- Is there cultural acceptance of this product/service?
- Are there religious, social, or traditional barriers?
- Is this a Western concept that needs adaptation?

Startup: {name}
Description: {description}
Tags: {tags}

Score (1-10) and explain your reasoning.
"""
    
    logistics_prompt = """
Evaluate LOGISTICS: Is Indian infrastructure ready for this?

Consider:
- Does this require physical infrastructure (delivery, storage, etc.)?
- Is Indian logistics and supply chain adequate?
- Are there last-mile delivery challenges?
- Dependency on reliable electricity, internet, or transportation?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""
    
    payment_prompt = """
Evaluate PAYMENT READINESS: Are Indians ready to pay for this?

Consider:
- Is this a B2B (usually pays) or B2C (price sensitive)?
- What's the pricing expectation vs Indian purchasing power?
- Are there free alternatives available?
- Is there willingness to pay for convenience/quality?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""
    
    timing_prompt = """
Evaluate TIMING: Is this the right time for this opportunity?

Consider:
- Is the market too early, right, or too late?
- Are enabling factors (internet, smartphones, etc.) in place?
- Is there growing or declining demand?
- Are macro trends favorable?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""
    
    monopoly_prompt = """
Evaluate MONOPOLY POTENTIAL: Does this tend toward winner-take-all?

Consider:
- Network effects potential?
- Data advantages?
- Brand loyalty in this category?
- Switching costs for users?
- Economies of scale?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""
    
    regulatory_prompt = """
Evaluate REGULATORY RISK: What's the government intervention risk?

Consider:
- Is this a regulated sector (fintech, healthcare, education)?
- Are there licensing requirements?
- Data localization requirements?
- Recent regulatory changes or upcoming legislation?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""
    
    execution_prompt = """
Evaluate EXECUTION FEASIBILITY: Can a small team build this?

Consider:
- Technical complexity?
- Capital requirements?
- Talent availability in India?
- Time to MVP?
- Scaling challenges?

Startup: {name}
Description: {description}
Category: {category}

Score (1-10) and explain your reasoning.
"""


class SevenDimensionScorer(BaseScorer):
    """
    Scoring engine for the 7-dimension opportunity analysis.
    
    Supports both rule-based scoring (fast, no API required)
    and LLM-based scoring (more accurate, requires OpenAI API).
    """
    
    def __init__(
        self,
        use_llm: bool = False,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        include_llm_reasoning: bool = True,
    ):
        """
        Initialize the 7-dimension scorer.
        
        Args:
            use_llm: Use LLM for scoring (requires OpenAI API key)
            model: OpenAI model to use
            temperature: Temperature for LLM calls
            include_llm_reasoning: Include detailed LLM reasoning
        """
        super().__init__(method="llm_based" if use_llm else "rule_based")
        
        self.use_llm = use_llm
        self.model = model
        self.temperature = temperature
        self.include_reasoning = include_llm_reasoning
        
        settings = get_settings()
        
        if use_llm and settings.has_openai_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
            if use_llm:
                logger.warning("OpenAI API key not found, falling back to rule-based scoring")
                self.use_llm = False
        
        # Scoring weights (configurable)
        self.weights = {
            "cultural_fit": 0.15,
            "logistics": 0.15,
            "payment_readiness": 0.15,
            "timing": 0.15,
            "monopoly_potential": 0.10,
            "regulatory_risk": 0.15,
            "execution_feasibility": 0.15,
        }
    
    def get_dimensions(self) -> List[str]:
        """Return list of dimensions this scorer evaluates"""
        return [
            ScoringDimension.CULTURAL_FIT.value,
            ScoringDimension.LOGISTICS.value,
            ScoringDimension.PAYMENT_READINESS.value,
            ScoringDimension.TIMING.value,
            ScoringDimension.MONOPOLY_POTENTIAL.value,
            ScoringDimension.REGULATORY_RISK.value,
            ScoringDimension.EXECUTION_FEASIBILITY.value,
        ]
    
    def score(self, request: ScoringRequest) -> ScoringResponse:
        """
        Score an opportunity across all 7 dimensions.
        
        Args:
            request: ScoringRequest with opportunity details
            
        Returns:
            ScoringResponse with all dimension scores
        """
        start_time = time.time()
        
        # Validate request
        is_valid, error = self.validate_request(request)
        if not is_valid:
            return ScoringResponse(
                opportunity_id=request.opportunity_id,
                errors=[error],
                method=self.method,
            )
        
        try:
            # Score each dimension
            dimensions = {}
            
            # 1. Cultural Fit
            dimensions["cultural_fit"] = self._score_cultural_fit(request)
            
            # 2. Logistics
            dimensions["logistics"] = self._score_logistics(request)
            
            # 3. Payment Readiness
            dimensions["payment_readiness"] = self._score_payment_readiness(request)
            
            # 4. Timing
            dimensions["timing"] = self._score_timing(request)
            
            # 5. Monopoly Potential
            dimensions["monopoly_potential"] = self._score_monopoly_potential(request)
            
            # 6. Regulatory Risk
            dimensions["regulatory_risk"] = self._score_regulatory_risk(request)
            
            # 7. Execution Feasibility
            dimensions["execution_feasibility"] = self._score_execution_feasibility(request)
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(dimensions, self.weights)
            
            # Create response
            response = self.create_response(
                request,
                dimensions=dimensions,
                overall_score=overall_score,
            )
            
            # Determine opportunity level
            response.opportunity_level = self.determine_opportunity_level(overall_score)
            
            # Generate reasoning and recommendations
            if request.include_reasoning:
                response.overall_reasoning = self._generate_overall_reasoning(dimensions)
            
            if request.include_recommendations:
                response.recommendation = self.generate_recommendation(response)
                response.next_steps = self.generate_next_steps(response)
            
            # Record stats
            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms
            self._record_stat(latency_ms)
            
            return response
            
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            self._record_stat((time.time() - start_time) * 1000, error=True)
            return ScoringResponse(
                opportunity_id=request.opportunity_id,
                errors=[str(e)],
                method=self.method,
            )
    
    def _score_cultural_fit(self, request: ScoringRequest) -> DimensionScore:
        """Score cultural fit dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "cultural_fit")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        tags = [t.lower() for t in request.tags]
        combined = " ".join(tags + [description])
        
        score = 5  # Default middle score
        reasoning = []
        evidence = []
        warnings = []
        
        # Check for high cultural fit categories
        for category in INDIA_MARKET_KNOWLEDGE["high_cultural_fit_categories"]:
            if category in combined:
                score = min(9, score + 2)
                evidence.append(f"Category '{category}' has strong cultural precedent in India")
        
        # Check for cultural barriers
        cultural_barriers = [
            ("dating", "Dating apps face social stigma in some segments"),
            ("pet", "Pet culture is emerging but not mainstream"),
            ("subscription", "Subscription models face resistance"),
            ("premium", "Premium pricing requires strong value proposition"),
        ]
        
        for barrier, warning in cultural_barriers:
            if barrier in combined:
                score = max(3, score - 2)
                warnings.append(warning)
                reasoning.append(f"Potential cultural barrier: {barrier}")
        
        # Check for Western concepts needing adaptation
        western_concepts = [
            "gym membership",
            "meal kit",
            "home security",
            "elderly care",
        ]
        
        for concept in western_concepts:
            if concept in description:
                score = min(7, score + 1)
                reasoning.append(f"Concept '{concept}' may need Indian adaptation")
        
        return DimensionScore(
            dimension="cultural_fit",
            score=min(10, max(1, score)),
            weight=self.weights["cultural_fit"],
            reasoning="; ".join(reasoning) if reasoning else "Standard cultural assessment",
            confidence=0.75,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _score_logistics(self, request: ScoringRequest) -> DimensionScore:
        """Score logistics dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "logistics")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        tags = [t.lower() for t in request.tags]
        combined = " ".join(tags + [description])
        
        score = 5
        reasoning = []
        evidence = []
        warnings = []
        
        # High logistics requirements
        high_logistics = INDIA_MARKET_KNOWLEDGE["high_logistics_categories"]
        for category in high_logistics:
            if category in combined:
                score = max(3, score - 3)
                reasoning.append(f"Category '{category}' requires complex logistics")
                warnings.append("Logistics complexity may be challenging in India")
        
        # Low logistics requirements
        low_logistics = INDIA_MARKET_KNOWLEDGE["low_logistics_categories"]
        for category in low_logistics:
            if category in combined:
                score = min(9, score + 2)
                evidence.append(f"Category '{category}' is primarily digital")
        
        # Infrastructure dependencies
        if any(word in combined for word in ["offline", "physical store", "warehouse"]):
            score = max(4, score - 2)
            warnings.append("Physical infrastructure requirements may be limiting")
        
        if "iot" in combined or "smart home" in combined:
            score = max(4, score - 1)
            reasoning.append("IoT devices require reliable connectivity")
        
        return DimensionScore(
            dimension="logistics",
            score=min(10, max(1, score)),
            weight=self.weights["logistics"],
            reasoning="; ".join(reasoning) if reasoning else "Standard logistics assessment",
            confidence=0.80,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _score_payment_readiness(self, request: ScoringRequest) -> DimensionScore:
        """Score payment readiness dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "payment_readiness")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        tags = [t.lower() for t in request.tags]
        combined = " ".join(tags + [description])
        
        score = 5
        reasoning = []
        evidence = []
        warnings = []
        
        # B2B vs B2C
        if any(word in combined for word in ["b2b", "enterprise", "business", "sme"]):
            score = min(9, score + 2)
            evidence.append("B2B category - companies are willing to pay for value")
        elif any(word in combined for word in ["b2c", "consumer", "individual"]):
            score = max(4, score - 2)
            reasoning.append("B2C category - consumer price sensitivity is high")
        
        # High payment readiness categories
        for category in INDIA_MARKET_KNOWLEDGE["high_payment_readiness_categories"]:
            if category in combined:
                score = min(9, score + 1)
                evidence.append(f"Category '{category}' has good payment readiness")
        
        # Low payment readiness categories
        for category in INDIA_MARKET_KNOWLEDGE["low_payment_readiness_categories"]:
            if category in combined:
                score = max(3, score - 2)
                warnings.append(f"Category '{category}' has low payment willingness")
        
        # Freemium indicators
        if "freemium" in combined or "free" in combined:
            score = max(4, score - 1)
            reasoning.append("Freemium model common, conversion to paid is challenging")
        
        return DimensionScore(
            dimension="payment_readiness",
            score=min(10, max(1, score)),
            weight=self.weights["payment_readiness"],
            reasoning="; ".join(reasoning) if reasoning else "Standard payment assessment",
            confidence=0.75,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _score_timing(self, request: ScoringRequest) -> DimensionScore:
        """Score timing dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "timing")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        tags = [t.lower() for t in request.tags]
        combined = " ".join(tags + [description])
        
        score = 5
        reasoning = []
        evidence = []
        warnings = []
        
        # Ripe categories
        for category in INDIA_MARKET_KNOWLEDGE["timing_indicators"]["ripe"]:
            if category in combined:
                score = min(8, score + 2)
                evidence.append(f"Category '{category}' timing is favorable")
        
        # Saturated categories
        for category in INDIA_MARKET_KNOWLEDGE["timing_indicators"]["saturated"]:
            if category in combined:
                score = max(3, score - 3)
                reasoning.append(f"Category '{category}' may be saturated")
                warnings.append("Market may be crowded with established players")
        
        # Early categories
        for category in INDIA_MARKET_KNOWLEDGE["timing_indicators"]["early"]:
            if category in combined:
                score = max(3, score - 1)
                reasoning.append(f"Category '{category}' may be early")
                warnings.append("Market may not be ready")
        
        return DimensionScore(
            dimension="timing",
            score=min(10, max(1, score)),
            weight=self.weights["timing"],
            reasoning="; ".join(reasoning) if reasoning else "Standard timing assessment",
            confidence=0.70,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _score_monopoly_potential(self, request: ScoringRequest) -> DimensionScore:
        """Score monopoly potential dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "monopoly_potential")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        
        score = 5
        reasoning = []
        evidence = []
        
        # Network effects
        if any(word in description for word in ["marketplace", "network", "platform"]):
            score = min(9, score + 2)
            evidence.append("Platform business model with network effects potential")
        
        # Data advantages
        if any(word in description for word in ["ai", "ml", "algorithm", "data"]):
            score = min(8, score + 1)
            evidence.append("AI/ML creates data moats")
        
        # Switching costs
        if any(word in description for word in ["workflow", "integration", "embedded"]):
            score = min(8, score + 1)
            evidence.append("Integration creates switching costs")
        
        # Commoditized categories
        if any(word in description for word in ["generic", "simple", "basic tool"]):
            score = max(4, score - 2)
            reasoning.append("Category may have low differentiation")
        
        return DimensionScore(
            dimension="monopoly_potential",
            score=min(10, max(1, score)),
            weight=self.weights["monopoly_potential"],
            reasoning="; ".join(reasoning) if reasoning else "Standard monopoly assessment",
            confidence=0.70,
            evidence=evidence,
        )
    
    def _score_regulatory_risk(self, request: ScoringRequest) -> DimensionScore:
        """Score regulatory risk dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "regulatory_risk")
        
        # Rule-based scoring (inverted - higher score = lower risk)
        description = request.startup_description.lower()
        tags = [t.lower() for t in request.tags]
        combined = " ".join(tags + [description])
        
        score = 5  # Start middle (medium risk)
        reasoning = []
        evidence = []
        warnings = []
        
        # High regulatory risk categories
        for category in INDIA_MARKET_KNOWLEDGE["high_regulatory_risk_categories"]:
            if category in combined:
                score = max(2, score - 3)
                reasoning.append(f"Category '{category}' has regulatory considerations")
                warnings.append(f"Regulatory risk in {category} sector")
        
        # Lower risk categories
        if any(word in combined for word in ["saas", "software", "tool", "productivity"]):
            score = min(8, score + 2)
            evidence.append("Software categories typically have lower regulatory burden")
        
        # Data considerations
        if any(word in combined for word in ["data", "user data", "personal"]):
            score = max(4, score - 1)
            reasoning.append("Data protection compliance required")
        
        return DimensionScore(
            dimension="regulatory_risk",
            score=min(10, max(1, score)),
            weight=self.weights["regulatory_risk"],
            reasoning="; ".join(reasoning) if reasoning else "Standard regulatory assessment",
            confidence=0.75,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _score_execution_feasibility(self, request: ScoringRequest) -> DimensionScore:
        """Score execution feasibility dimension"""
        if self.use_llm and self.client:
            return self._llm_score_dimension(request, "execution_feasibility")
        
        # Rule-based scoring
        description = request.startup_description.lower()
        
        score = 6  # Slightly optimistic for Indian tech talent
        reasoning = []
        evidence = []
        warnings = []
        
        # Technical complexity
        if any(word in description for word in ["blockchain", "crypto", "quantum"]):
            score = max(4, score - 2)
            reasoning.append("Specialized technical expertise required")
        elif any(word in description for word in ["simple", "basic", "straightforward"]):
            score = min(9, score + 1)
            evidence.append("Relatively simple to execute")
        
        # Capital requirements
        if any(word in description for word in ["hardware", "physical", "manufacturing"]):
            score = max(4, score - 2)
            reasoning.append("Hardware/physical products require significant capital")
        
        # Indian advantages
        if any(word in description for word in ["ai", "ml", "software", "mobile", "app"]):
            score = min(9, score + 1)
            evidence.append("Strong software/Mobile development talent in India")
        
        # Talent availability
        if any(word in description for word in ["design", "ux", "creative"]):
            score = max(5, score - 1)
            reasoning.append("Design talent may require urban focus")
        
        return DimensionScore(
            dimension="execution_feasibility",
            score=min(10, max(1, score)),
            weight=self.weights["execution_feasibility"],
            reasoning="; ".join(reasoning) if reasoning else "Standard execution assessment",
            confidence=0.75,
            evidence=evidence,
            warnings=warnings,
        )
    
    def _llm_score_dimension(
        self,
        request: ScoringRequest,
        dimension: str,
    ) -> DimensionScore:
        """Use LLM to score a dimension"""
        if not self.client:
            raise ValueError("OpenAI client not available")
        
        # Get prompt template
        prompt_attr = f"{dimension}_prompt"
        prompt_template = getattr(ScoringPrompt, prompt_attr, None)
        
        if not prompt_template:
            raise ValueError(f"Unknown dimension: {dimension}")
        
        # Format prompt
        prompt = prompt_template.format(
            name=request.startup_name,
            description=request.startup_description,
            tags=", ".join(request.tags),
            category=", ".join(request.tags[:2]),
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ScoringPrompt.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=500,
            )
            
            content = response.choices[0].message.content
            
            # Extract score (look for number in text)
            import re
            score_match = re.search(r'(\d+)', content)
            score = int(score_match.group(1)) if score_match else 5
            
            return DimensionScore(
                dimension=dimension,
                score=min(10, max(1, score)),
                weight=self.weights.get(dimension, 0.15),
                reasoning=content[:500],
                confidence=0.85,
            )
            
        except Exception as e:
            logger.warning(f"LLM scoring failed for {dimension}: {str(e)}")
            # Fall back to rule-based
            return self._fallback_score(request, dimension)
    
    def _fallback_score(
        self,
        request: ScoringRequest,
        dimension: str,
    ) -> DimensionScore:
        """Fallback to rule-based scoring"""
        # Temporarily disable LLM to prevent recursion
        original_use_llm = self.use_llm
        self.use_llm = False
        
        try:
            # Map dimension to appropriate rule-based method
            dimension_methods = {
                "cultural_fit": self._score_cultural_fit,
                "logistics": self._score_logistics,
                "payment_readiness": self._score_payment_readiness,
                "timing": self._score_timing,
                "monopoly_potential": self._score_monopoly_potential,
                "regulatory_risk": self._score_regulatory_risk,
                "execution_feasibility": self._score_execution_feasibility,
            }
            
            method = dimension_methods.get(dimension)
            if method:
                return method(request)
            
            return DimensionScore(
                dimension=dimension,
                score=5,
                weight=self.weights.get(dimension, 0.15),
                reasoning="Default score (LLM unavailable)",
                confidence=0.5,
            )
        finally:
            self.use_llm = original_use_llm
    
    def _generate_overall_reasoning(self, dimensions: Dict[str, DimensionScore]) -> str:
        """Generate overall reasoning summary"""
        strengths = [d for d in dimensions.values() if d.score >= 7]
        weaknesses = [d for d in dimensions.values() if d.score <= 4]
        
        reasoning_parts = []
        
        if strengths:
            top_strength = max(strengths, key=lambda x: x.score)
            reasoning_parts.append(
                f"Strength: {top_strength.dimension.replace('_', ' ').title()} "
                f"(score: {top_strength.score}/10)"
            )
        
        if weaknesses:
            top_weakness = min(weaknesses, key=lambda x: x.score)
            reasoning_parts.append(
                f"Challenge: {top_weakness.dimension.replace('_', ' ').title()} "
                f"(score: {top_weakness.score}/10)"
            )
        
        return "; ".join(reasoning_parts)


def create_scorer(**kwargs) -> SevenDimensionScorer:
    """
    Factory function to create SevenDimensionScorer.
    
    Args:
        **kwargs: Scorer configuration
        
    Returns:
        SevenDimensionScorer instance
    """
    return SevenDimensionScorer(**kwargs)

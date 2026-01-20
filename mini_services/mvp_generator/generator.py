"""
MVP Generator for IndoGap - AI-Powered Opportunity Discovery Engine

This module generates comprehensive MVP roadmaps for opportunities,
including India-specific localization, tech stack, and execution plans.
"""
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import OpenAI

from .india_localizer import IndiaLocalizer, create_india_localizer
from ..models.score import MVPRoadmap, MVPMilestone, MVPTechStack, MVPMarketStrategy
from ..scoring.base import ScoringResponse
from ..config import get_settings

logger = logging.getLogger(__name__)


class MVPComplexity(str, Enum):
    """MVP complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class MVPTimeline(str, Enum):
    """MVP development timeline estimates"""
    TWO_WEEKS = "2 weeks"
    ONE_MONTH = "1 month"
    TWO_MONTHS = "2 months"
    THREE_MONTHS = "3 months"
    SIX_MONTHS = "6 months"


@dataclass
class RoadmapConfig:
    """Configuration for roadmap generation"""
    timeline: MVPTimeline = MVPTimeline.THREE_MONTHS
    complexity: MVPComplexity = MVPComplexity.MODERATE
    include_milestones: bool = True
    include_tech_stack: bool = True
    include_pricing: bool = True
    include_regulatory: bool = True
    target_cities: List[str] = field(default_factory=lambda: ["Bangalore", "Mumbai", "Delhi"])


class MVPGenerator:
    """
    Generator for India-specific MVP roadmaps.
    
    Creates comprehensive plans including:
    - Core features for v1
    - India-specific tech stack
    - Localization recommendations
    - Payment and communication integration
    - Go-to-market strategy
    - Development milestones
    - Risk factors and mitigation
    """
    
    def __init__(
        self,
        use_llm: bool = False,
        model: str = "gpt-4o",
        temperature: float = 0.7,
    ):
        """
        Initialize MVP generator.
        
        Args:
            use_llm: Use LLM for generation (requires API key)
            model: OpenAI model to use
            temperature: Temperature for LLM calls
        """
        settings = get_settings()
        
        self.use_llm = use_llm and settings.has_openai_key
        self.model = model
        self.temperature = temperature
        
        if self.use_llm and settings.has_openai_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
            if use_llm:
                logger.warning("OpenAI API key not found, falling back to template-based generation")
        
        self.localizer = create_india_localizer()
    
    def generate_roadmap(
        self,
        startup_name: str,
        description: str,
        scores: Optional[ScoringResponse] = None,
        config: Optional[RoadmapConfig] = None,
    ) -> MVPRoadmap:
        """
        Generate a complete MVP roadmap.
        
        Args:
            startup_name: Name of the startup
            description: Description of the startup/product
            scores: Optional scoring results
            config: Roadmap configuration
            
        Returns:
            MVPRoadmap with full execution plan
        """
        if config is None:
            config = RoadmapConfig()
        
        start_time = time.time()
        
        try:
            # Determine complexity from scores if available
            complexity = self._determine_complexity(scores)
            timeline = self._estimate_timeline(complexity, description)
            
            # Generate core features
            core_features = self._generate_core_features(startup_name, description, scores)
            future_features = self._generate_future_features(description)
            
            # Generate India-specific localization
            india_localization = self._generate_india_localization(description, scores)
            
            # Generate tech stack
            tech_stack = self._generate_tech_stack(description)
            
            # Generate market strategy
            market_strategy = self._generate_market_strategy(
                description, config.target_cities, scores
            )
            
            # Generate milestones
            milestones = []
            if config.include_milestones:
                milestones = self._generate_milestones(timeline, core_features)
            
            # Identify risks
            key_risks = self._identify_risks(description, scores)
            mitigation_strategies = self._generate_mitigations(key_risks)
            
            # Define success metrics
            success_metrics = self._define_success_metrics()
            
            # Generate one-liner
            one_liner = self._generate_one_liner(startup_name, description)
            
            # Create roadmap
            roadmap = MVPRoadmap(
                opportunity_id=f"roadmap_{startup_name.lower().replace(' ', '_')}",
                startup_name=startup_name,
                one_liner=one_liner,
                timeline=timeline.value,
                complexity=complexity.value,
                core_features=core_features,
                future_features=future_features,
                india_localization=india_localization,
                payment_gateways=self._get_payment_gateways(),
                communication_channels=self._get_communication_channels(),
                tech_stack=tech_stack,
                market_strategy=market_strategy,
                milestones=milestones,
                key_risks=key_risks,
                mitigation_strategies=mitigation_strategies,
                success_metrics=success_metrics,
                model_used=self.model if self.use_llm else "template",
                generated_at=datetime.now(),
            )
            
            # Generate full markdown if LLM available
            if self.use_llm:
                roadmap.full_roadmap = self._generate_full_markdown(roadmap)
            else:
                roadmap.full_roadmap = self._generate_template_markdown(roadmap)
            
            logger.info(f"Generated roadmap for {startup_name} in {time.time() - start_time:.2f}s")
            
            return roadmap
            
        except Exception as e:
            logger.error(f"Roadmap generation failed: {str(e)}")
            return self._create_fallback_roadmap(startup_name, description)
    
    def _determine_complexity(
        self,
        scores: Optional[ScoringResponse] = None,
    ) -> MVPComplexity:
        """Determine MVP complexity from scoring"""
        if not scores:
            return MVPComplexity.MODERATE
        
        # Look at execution feasibility score
        exec_score = scores.get_dimension("execution_feasibility")
        if exec_score:
            if exec_score.score >= 8:
                return MVPComplexity.SIMPLE
            elif exec_score.score >= 6:
                return MVPComplexity.MODERATE
            elif exec_score.score >= 4:
                return MVPComplexity.COMPLEX
            else:
                return MVPComplexity.VERY_COMPLEX
        
        return MVPComplexity.MODERATE
    
    def _estimate_timeline(
        self,
        complexity: MVPComplexity,
        description: str,
    ) -> MVPTimeline:
        """Estimate development timeline"""
        base_timelines = {
            MVPComplexity.SIMPLE: MVPTimeline.ONE_MONTH,
            MVPComplexity.MODERATE: MVPTimeline.TWO_MONTHS,
            MVPComplexity.COMPLEX: MVPTimeline.THREE_MONTHS,
            MVPComplexity.VERY_COMPLEX: MVPTimeline.SIX_MONTHS,
        }
        
        # Check for complexity indicators
        description_lower = description.lower()
        
        # Add time for hardware/integration
        if any(word in description_lower for word in ["hardware", "iot", "device"]):
            return MVPTimeline.THREE_MONTHS
        
        # Add time for AI/ML
        if any(word in description_lower for word in ["ai", "ml", "machine learning", "model"]):
            return MVPTimeline.TWO_MONTHS
        
        return base_timelines.get(complexity, MVPTimeline.THREE_MONTHS)
    
    def _generate_core_features(
        self,
        name: str,
        description: str,
        scores: Optional[ScoringResponse] = None,
    ) -> List[str]:
        """Generate core features for MVP"""
        features = []
        
        # Essential features for any app
        features.append("User authentication (phone/email)")
        features.append("Core functionality based on description")
        features.append("Dashboard/admin panel")
        features.append("Basic analytics")
        features.append("Customer support integration")
        
        # India-specific essentials
        features.append("Hindi language support")
        features.append("UPI payment integration")
        features.append("WhatsApp notification integration")
        
        # Scoring-based features
        if scores:
            # Add features based on strengths
            cultural_fit = scores.get_dimension("cultural_fit")
            if cultural_fit and cultural_fit.score >= 7:
                features.append("Social/community features")
            
            # Add features to address weaknesses
            payment_readiness = scores.get_dimension("payment_readiness")
            if payment_readiness and payment_readiness.score < 6:
                features.append("Freemium tier")
                features.append("Cash payment option")
        
        # Remove duplicates and limit
        return list(dict.fromkeys(features))[:8]
    
    def _generate_future_features(self, description: str) -> List[str]:
        """Generate features for future versions"""
        return [
            "Advanced AI/ML recommendations",
            "Multi-language support expansion",
            "Premium subscription tier",
            "Enterprise/saas features",
            "API for third-party integrations",
            "White-label solution",
        ]
    
    def _generate_india_localization(
        self,
        description: str,
        scores: Optional[ScoringResponse] = None,
    ) -> List[str]:
        """Generate India-specific localization recommendations"""
        localization = []
        
        description_lower = description.lower()
        
        # Language localization
        localization.append("Hindi language support (70%+ of users)")
        localization.append("Regional language options based on target market")
        
        # Payment localization
        localization.append("UPI integration (primary payment method)")
        localization.append("Cash on delivery option if physical product")
        localization.append("EMI options for high-value services")
        
        # Communication localization
        localization.append("WhatsApp Business for customer communication")
        localization.append("SMS fallback for critical notifications")
        
        # Cultural localization
        if any(word in description_lower for word in ["social", "community"]):
            localization.append("Community features (groups, forums)")
        
        if any(word in description_lower for word in ["food", "restaurant"]):
            localization.append("Zomato/Swiggy integration options")
        
        # Infrastructure considerations
        localization.append("Offline-first functionality for low-connectivity areas")
        localization.append("Lightweight app design (<50MB)")
        
        return localization
    
    def _generate_tech_stack(
        self,
        description: str,
    ) -> MVPTechStack:
        """Generate technology stack recommendations"""
        description_lower = description.lower()
        
        # Determine stack based on product type
        if any(word in description_lower for word in ["mobile", "app", "ios", "android"]):
            frontend = ["React Native", "Flutter"]
        else:
            frontend = ["React.js", "Next.js"]
        
        backend = ["Node.js", "Python FastAPI"]
        database = ["PostgreSQL", "MongoDB"]
        cloud = ["AWS Mumbai", "Google Cloud India"]
        
        # India-specific additions
        payments = ["Razorpay", "UPI", "Paytm"]
        messaging = ["WhatsApp Business API", "Twilio", "Firebase"]
        
        # AI/ML specific
        if any(word in description_lower for word in ["ai", "ml", "chatbot"]):
            backend.append("OpenAI API")
            backend.append("LangChain")
        
        return MVPTechStack(
            frontend=frontend,
            backend=backend,
            database=database,
            cloud=cloud,
            payments=payments,
            messaging=messaging,
            ai_ml=["OpenAI", "HuggingFace"] if any(word in description_lower for word in ["ai", "ml"]) else [],
        )
    
    def _generate_market_strategy(
        self,
        description: str,
        target_cities: List[str],
        scores: Optional[ScoringResponse] = None,
    ) -> MVPMarketStrategy:
        """Generate go-to-market strategy"""
        description_lower = description.lower()
        
        # Determine target segment
        if any(word in description_lower for word in ["b2b", "enterprise", "business"]):
            target_segment = "SMBs and mid-market companies in metro cities"
            pricing_strategy = "Annual contracts with monthly options"
            gtm_channels = ["LinkedIn", "Partner networks", "Industry events"]
        else:
            target_segment = "Urban millennials and Gen Z in tier 1 cities"
            pricing_strategy = "Freemium model with premium tiers"
            gtm_channels = ["WhatsApp marketing", "Instagram", "Influencer partnerships"]
        
        # Tier 1 cities for launch
        if not target_cities:
            target_cities = ["Bangalore", "Mumbai", "Delhi-NCR"]
        
        return MVPMarketStrategy(
            target_cities=target_cities,
            target_segment=target_segment,
            pricing_strategy=pricing_strategy,
            pricing_tiers=[
                "Free tier (limited features)",
                "Pro - ₹199-499/month",
                "Enterprise - Custom pricing",
            ],
            go_to_market=gtm_channels,
            customer_acquisition=[
                "Content marketing (SEO)",
                "Paid social advertising",
                "Community building",
                "Referral programs",
            ],
        )
    
    def _generate_milestones(
        self,
        timeline: MVPTimeline,
        core_features: List[str],
    ) -> List[MVPMilestone]:
        """Generate development milestones"""
        milestones = []
        
        # Parse timeline to weeks
        week_map = {
            MVPTimeline.TWO_WEEKS: 2,
            MVPTimeline.ONE_MONTH: 4,
            MVPTimeline.TWO_MONTHS: 8,
            MVPTimeline.THREE_MONTHS: 12,
            MVPTimeline.SIX_MONTHS: 24,
        }
        
        total_weeks = week_map.get(timeline, 12)
        features_per_phase = len(core_features) // 3
        
        # Week 1-4: Foundation
        milestones.append(MVPMilestone(
            week=1,
            title="Setup & Authentication",
            description="Initialize project, set up CI/CD, implement auth",
            deliverables=["Project setup", "User auth", "Database schema"],
            dependencies=[],
            complexity="medium",
        ))
        
        milestones.append(MVPMilestone(
            week=2,
            title="Core Feature 1",
            description="Build first core feature",
            deliverables=[core_features[0] if core_features else "Core feature"],
            dependencies=["Week 1"],
            complexity="medium",
        ))
        
        # Week 5-8: Development
        milestones.append(MVPMilestone(
            week=5,
            title="Core Feature 2 & Payments",
            description="Build second feature and integrate payments",
            deliverables=[core_features[1] if len(core_features) > 1 else "Feature 2", "UPI/Razorpay integration"],
            dependencies=["Week 2"],
            complexity="high",
        ))
        
        milestones.append(MVPMilestone(
            week=8,
            title="India Features & Testing",
            description="Add India-specific features and testing",
            deliverables=["Hindi support", "WhatsApp integration", "QA testing"],
            dependencies=["Week 5"],
            complexity="medium",
        ))
        
        # Week 9+: Launch
        if total_weeks >= 10:
            milestones.append(MVPMilestone(
                week=10,
                title="Beta Launch",
                description="Launch beta with limited users",
                deliverables=["Beta release", "User onboarding", "Feedback collection"],
                dependencies=["Week 8"],
                complexity="medium",
            ))
        
        milestones.append(MVPMilestone(
            week=min(total_weeks, 12),
            title="Public Launch",
            description="Full public launch with marketing",
            deliverables=["Public release", "Marketing campaign", "Support setup"],
            dependencies=["Beta launch"],
            complexity="high",
        ))
        
        return milestones
    
    def _identify_risks(
        self,
        description: str,
        scores: Optional[ScoringResponse] = None,
    ) -> List[str]:
        """Identify key risks for the opportunity"""
        risks = []
        
        description_lower = description.lower()
        
        # Common India-specific risks
        risks.append("Cash-on-delivery expectations may impact unit economics")
        risks.append("User acquisition costs may be higher than expected")
        risks.append("Payment gateway failures may affect conversions")
        
        # Scoring-based risks
        if scores:
            cultural_fit = scores.get_dimension("cultural_fit")
            if cultural_fit and cultural_fit.score < 5:
                risks.append("Cultural fit concerns may require significant product changes")
            
            regulatory_risk = scores.get_dimension("regulatory_risk")
            if regulatory_risk and regulatory_risk.score < 5:
                risks.append("Regulatory uncertainty in the category")
            
            timing = scores.get_dimension("timing")
            if timing and timing.score < 5:
                risks.append("Market timing may not be optimal")
        
        # Category-specific risks
        if any(word in description_lower for word in ["fintech", "payments"]):
            risks.append("RBI regulatory compliance requirements")
            risks.append("Partnership requirements with banks")
        
        if any(word in description_lower for word in ["health", "medical"]):
            risks.append("Healthcare regulations and data privacy")
            risks.append("Doctor/health professional availability")
        
        if any(word in description_lower for word in ["education", "learning"]):
            risks.append("Edtech market saturation")
            risks.append("User engagement and completion rates")
        
        return risks[:5]
    
    def _generate_mitigations(self, risks: List[str]) -> List[str]:
        """Generate risk mitigation strategies"""
        mitigations = []
        
        for risk in risks:
            if "cash" in risk.lower():
                mitigations.append("Offer COD with prepaid discount incentive")
            elif "acquisition" in risk.lower():
                mitigations.append("Focus on organic growth and referrals initially")
            elif "regulatory" in risk.lower():
                mitigations.append("Engage legal counsel early, build compliance from start")
            elif "cultural" in risk.lower():
                mitigations.append("Conduct user research, iterate based on feedback")
            elif "timing" in risk.lower():
                mitigations.append("Start with niche segment, expand later")
            elif "payment" in risk.lower():
                mitigations.append("Have backup payment options, monitor failures")
            else:
                mitigations.append("Monitor closely, have contingency plans")
        
        return mitigations
    
    def _define_success_metrics(self) -> List[str]:
        """Define success metrics for MVP"""
        return [
            "Daily Active Users (DAU) > 1000 in first month",
            "User retention rate > 30% at Day 7",
            "Payment success rate > 95%",
            "Customer Support tickets < 10% of users",
            "NPS score > 30",
            "Organic traffic > 50% of total",
        ]
    
    def _generate_one_liner(self, name: str, description: str) -> str:
        """Generate one-line value proposition"""
        return f"{name}: {description[:100]}..."
    
    def _get_payment_gateways(self) -> List[str]:
        """Get recommended payment gateways"""
        return ["UPI", "Razorpay", "Paytm", "PhonePe"]
    
    def _get_communication_channels(self) -> List[str]:
        """Get recommended communication channels"""
        return ["WhatsApp Business", "SMS", "Email", "Push Notifications"]
    
    def _generate_full_markdown(self, roadmap: MVPRoadmap) -> str:
        """Generate detailed markdown roadmap using LLM"""
        if not self.client:
            return self._generate_template_markdown(roadmap)
        
        prompt = f"""
Generate a detailed MVP roadmap in markdown format for:

Startup: {roadmap.startup_name}
One-liner: {roadmap.one_liner}
Timeline: {roadmap.timeline}
Complexity: {roadmap.complexity}

Core Features:
{chr(10).join(f'- {f}' for f in roadmap.core_features[:6])}

India Localization:
{chr(10).join(f'- {l}' for l in roadmap.india_localization[:5])}

Tech Stack:
Frontend: {', '.join(roadmap.tech_stack.frontend)}
Backend: {', '.join(roadmap.tech_stack.backend)}
Payments: {', '.join(roadmap.tech_stack.payments)}

Target Cities: {', '.join(roadmap.market_strategy.target_cities)}
Target Segment: {roadmap.market_strategy.target_segment}

Generate a comprehensive markdown document with:
1. Executive Summary
2. Product Overview
3. Technical Architecture
4. India Market Strategy
5. Development Plan with milestones
6. Risk Assessment
7. Success Metrics
8. Next Steps
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=3000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM markdown generation failed: {str(e)}")
            return self._generate_template_markdown(roadmap)
    
    def _generate_template_markdown(self, roadmap: MVPRoadmap) -> str:
        """Generate markdown roadmap using templates"""
        lines = []
        
        lines.append(f"# MVP Roadmap: {roadmap.startup_name}")
        lines.append("")
        lines.append(f"**Timeline:** {roadmap.timeline} | **Complexity:** {roadmap.complexity}")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(roadmap.one_liner)
        lines.append("")
        lines.append("## Core Features (v1.0)")
        lines.append("")
        for i, feature in enumerate(roadmap.core_features, 1):
            lines.append(f"{i}. {feature}")
        lines.append("")
        lines.append("## India-Specific Localization")
        lines.append("")
        for loc in roadmap.india_localization:
            lines.append(f"- {loc}")
        lines.append("")
        lines.append("## Technology Stack")
        lines.append("")
        lines.append(f"**Frontend:** {', '.join(roadmap.tech_stack.frontend)}")
        lines.append(f"**Backend:** {', '.join(roadmap.tech_stack.backend)}")
        lines.append(f"**Database:** {', '.join(roadmap.tech_stack.database)}")
        lines.append(f"**Cloud:** {', '.join(roadmap.tech_stack.cloud)}")
        lines.append(f"**Payments:** {', '.join(roadmap.tech_stack.payments)}")
        lines.append(f"**Messaging:** {', '.join(roadmap.tech_stack.messaging)}")
        lines.append("")
        lines.append("## Market Strategy")
        lines.append("")
        lines.append(f"**Target Cities:** {', '.join(roadmap.market_strategy.target_cities)}")
        lines.append(f"**Target Segment:** {roadmap.market_strategy.target_segment}")
        lines.append(f"**Pricing Strategy:** {roadmap.market_strategy.pricing_strategy}")
        lines.append("")
        lines.append("## Development Milestones")
        lines.append("")
        for milestone in roadmap.milestones:
            lines.append(f"### Week {milestone.week}: {milestone.title}")
            lines.append(f"**Description:** {milestone.description}")
            lines.append(f"**Deliverables:** {', '.join(milestone.deliverables)}")
            lines.append("")
        lines.append("## Risk Assessment")
        lines.append("")
        for i, risk in enumerate(roadmap.key_risks, 1):
            lines.append(f"{i}. {risk}")
        lines.append("")
        lines.append("## Mitigation Strategies")
        lines.append("")
        for i, mitigation in enumerate(roadmap.mitigation_strategies, 1):
            lines.append(f"{i}. {mitigation}")
        lines.append("")
        lines.append("## Success Metrics")
        lines.append("")
        for metric in roadmap.success_metrics:
            lines.append(f"- {metric}")
        
        return "\n".join(lines)
    
    def _create_fallback_roadmap(
        self,
        name: str,
        description: str,
    ) -> MVPRoadmap:
        """Create a basic roadmap when generation fails"""
        return MVPRoadmap(
            opportunity_id=f"roadmap_{name.lower().replace(' ', '_')}",
            startup_name=name,
            one_liner=f"{name}: {description[:100]}",
            timeline="3 months",
            complexity="moderate",
            core_features=["Core feature 1", "Core feature 2", "User auth", "Payments"],
            india_localization=["Hindi support", "UPI integration"],
            tech_stack=MVPTechStack(
                frontend=["React Native"],
                backend=["Node.js"],
                database=["PostgreSQL"],
                cloud=["AWS Mumbai"],
                payments=["Razorpay"],
                messaging=["WhatsApp"],
            ),
            market_strategy=MVPMarketStrategy(
                target_cities=["Bangalore", "Mumbai", "Delhi"],
                target_segment="Urban professionals",
            ),
            full_roadmap=f"# {name}\n\n{description}\n\n## MVP Plan\n\nComing soon...",
        )


def create_generator(**kwargs) -> MVPGenerator:
    """
    Factory function to create MVPGenerator.
    
    Args:
        **kwargs: Generator configuration
        
    Returns:
        MVPGenerator instance
    """
    return MVPGenerator(**kwargs)

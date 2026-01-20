"""
India Localizer for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides India-specific knowledge and recommendations for localizing
startups and MVPs for the Indian market.
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PaymentOption:
    """Indian payment option"""
    name: str
    description: str
    adoption_rate: str  # high, medium, low
    integration_ease: str  # easy, medium, hard
    fees: str


@dataclass
class CommunicationChannel:
    """Indian communication channel"""
    name: str
    type: str  # messaging, email, social
    adoption: str  # high, medium, low
    effectiveness: str  # high, medium, low
    cost: str  # low, medium, high


@dataclass
class CloudProvider:
    """Cloud provider available in India"""
    name: str
    data_centers: str  # regions available
    pricing: str  # competitive, premium
    compliance: List[str]  # certifications


INDIA_SPECIFIC = {
    "payment_options": [
        PaymentOption(
            name="UPI (Unified Payments Interface)",
            description="Real-time payment system allowing bank-to-bank transfers",
            adoption_rate="high",
            integration_ease="easy",
            fees="low",
        ),
        PaymentOption(
            name="Razorpay",
            description="Payment gateway supporting cards, UPI, wallets",
            adoption_rate="high",
            integration_ease="easy",
            fees="medium",
        ),
        PaymentOption(
            name="Paytm",
            description="Digital wallet and payment app",
            adoption_rate="high",
            integration_ease="medium",
            fees="medium",
        ),
        PaymentOption(
            name="PhonePe",
            description="UPI-based payment app by Flipkart",
            adoption_rate="high",
            integration_ease="easy",
            fees="low",
        ),
        PaymentOption(
            name="Google Pay",
            description="UPI payment app by Google",
            adoption_rate="high",
            integration_ease="easy",
            fees="low",
        ),
        PaymentOption(
            name="Cash on Delivery",
            description="Cash payment upon delivery",
            adoption_rate="medium",
            integration_ease="easy",
            fees="medium",  # handling costs
        ),
        PaymentOption(
            name="EMI Options",
            description="Equated Monthly Installments",
            adoption_rate="medium",
            integration_ease="hard",
            fees="medium",
        ),
    ],
    
    "communication_channels": [
        CommunicationChannel(
            name="WhatsApp",
            type="messaging",
            adoption="high",
            effectiveness="high",
            cost="low",
        ),
        CommunicationChannel(
            name="SMS",
            type="messaging",
            adoption="high",
            effectiveness="medium",
            cost="low",
        ),
        CommunicationChannel(
            name="Email",
            type="email",
            adoption="medium",
            effectiveness="medium",
            cost="low",
        ),
        CommunicationChannel(
            name="Telegram",
            type="messaging",
            adoption="medium",
            effectiveness="high",
            cost="low",
        ),
        CommunicationChannel(
            name="IVR",
            type="voice",
            adoption="high",
            effectiveness="medium",
            cost="medium",
        ),
        CommunicationChannel(
            name="Push Notifications",
            type="in-app",
            adoption="high",
            effectiveness="high",
            cost="low",
        ),
    ],
    
    "cloud_providers": [
        CloudProvider(
            name="AWS",
            data_centers="Mumbai, Hyderabad",
            pricing="competitive",
            compliance=["ISO", "SOC", "PCI-DSS"],
        ),
        CloudProvider(
            name="Azure",
            data_centers="Multiple India regions",
            pricing="competitive",
            compliance=["ISO", "SOC", "PCI-DSS", "MeitY"],
        ),
        CloudProvider(
            name="Google Cloud",
            data_centers="Mumbai, Delhi, Hyderabad",
            pricing="competitive",
            compliance=["ISO", "SOC", "PCI-DSS"],
        ),
        CloudProvider(
            name="IBM Cloud",
            data_centers="Chennai, Mumbai, Delhi",
            pricing="premium",
            compliance=["ISO", "SOC", "MeitY"],
        ),
        CloudProvider(
            name="Oracle Cloud",
            data_centers="Mumbai, Hyderabad",
            pricing="competitive",
            compliance=["ISO", "SOC"],
        ),
    ],
    
    "cities": [
        {"name": "Mumbai", "tier": "1", "market_size": "very large", "notes": "Financial capital, high competition"},
        {"name": "Delhi-NCR", "tier": "1", "market_size": "very large", "notes": "Capital region, diverse population"},
        {"name": "Bangalore", "tier": "1", "market_size": "large", "notes": "Tech hub, startup friendly"},
        {"name": "Hyderabad", "tier": "1", "market_size": "large", "notes": "IT services, growing tech scene"},
        {"name": "Chennai", "tier": "1", "market_size": "large", "notes": "Auto hub, educated workforce"},
        {"name": "Pune", "tier": "1", "market_size": "medium", "notes": "Education, manufacturing"},
        {"name": "Kolkata", "tier": "1", "market_size": "large", "notes": "East India gateway"},
        {"name": "Ahmedabad", "tier": "2", "market_size": "medium", "notes": "Commercial hub, Gujarat"},
        {"name": "Kochi", "tier": "2", "market_size": "medium", "notes": "South gateway, port city"},
        {"name": "Jaipur", "tier": "2", "market_size": "medium", "notes": "Rajasthan capital, tourism"},
        {"name": "Lucknow", "tier": "2", "market_size": "medium", "notes": "UP capital, growing market"},
        {"name": "Nagpur", "tier": "2", "market_size": "medium", "notes": "Central India hub"},
    ],
    
    "languages": [
        {"name": "Hindi", "speakers": "50%+", "priority": "high"},
        {"name": "English", "speakers": "10-15%", "priority": "high"},
        {"name": "Bengali", "speakers": "8%", "priority": "medium"},
        {"name": "Marathi", "speakers": "7%", "priority": "medium"},
        {"name": "Telugu", "speakers": "7%", "priority": "medium"},
        {"name": "Tamil", "speakers": "6%", "priority": "medium"},
        {"name": "Gujarati", "speakers": "5%", "priority": "medium"},
        {"name": "Kannada", "speakers": "4%", "priority": "low"},
        {"name": "Malayalam", "speakers": "3%", "priority": "low"},
        {"name": "Punjabi", "speakers": "3%", "priority": "low"},
    ],
    
    "pricing_guidelines": {
        "b2b_software": {
            "entry": "₹5,000-15,000/month",
            "mid": "₹15,000-50,000/month",
            "enterprise": "₹50,000+/month",
        },
        "b2c_apps": {
            "free_with_ads": "Common model",
            "freemium": "Basic free, ₹99-499/month premium",
            "premium": "₹99-999/month",
        },
        "services": {
            "consulting": "₹500-2,000/hour",
            "development": "₹1,000-5,000/hour",
            "design": "₹750-2,500/hour",
        },
    },
    
    "regulatory_requirements": {
        "data_localization": [
            "Personal Data Protection Bill compliance",
            "RBI guidelines for payment data",
            "Sector-specific data retention policies",
        ],
        "payments": [
            "RBI license for payment aggregation",
            "PCI-DSS compliance for card data",
            "KYC/AML compliance",
        ],
        "business_registration": [
            "GST registration (if turnover > ₹40L)",
            "MCA company registration",
            "Professional tax where applicable",
        ],
    },
    
    "tech_stack_recommendations": {
        "frontend": [
            "React Native (cross-platform mobile)",
            "Flutter (cross-platform mobile)",
            "React.js (web)",
            "Next.js (web with SSR)",
        ],
        "backend": [
            "Node.js with Express",
            "Python with FastAPI",
            "Go for high-performance",
            "Java/Spring for enterprise",
        ],
        "database": [
            "PostgreSQL (primary)",
            "MongoDB (flexible schemas)",
            "Redis (caching)",
            "Firebase (realtime)",
        ],
        "infrastructure": [
            "AWS (Mumbai region)",
            "Azure (multiple regions)",
            "Google Cloud (Delhi, Mumbai)",
            "Vercel (frontend deployment)",
        ],
    },
    
    "go_to_market_channels": [
        {
            "channel": "WhatsApp Business",
            "type": "messaging",
            "effectiveness": "high",
            "cost": "low",
            "notes": "Most effective for B2C in India",
        },
        {
            "channel": "Google Ads",
            "type": "paid advertising",
            "effectiveness": "high",
            "cost": "medium",
            "notes": "Good for intent-based acquisition",
        },
        {
            "channel": "LinkedIn",
            "type": "professional networking",
            "effectiveness": "high",
            "cost": "medium",
            "notes": "Best for B2B lead generation",
        },
        {
            "channel": "Instagram",
            "type": "social media",
            "effectiveness": "medium",
            "cost": "medium",
            "notes": "Good for B2C, especially youth",
        },
        {
            "channel": "Content Marketing",
            "type": "organic",
            "effectiveness": "medium",
            "cost": "low",
            "notes": "SEO, blogs, YouTube",
        },
        {
            "channel": "Influencer Marketing",
            "type": "social",
            "effectiveness": "medium",
            "cost": "medium-high",
            "notes": "Effective for consumer apps",
        },
        {
            "channel": "Offline Events",
            "type": "in-person",
            "effectiveness": "high",
            "cost": "high",
            "notes": "Tech conferences, startup events",
        },
        {
            "channel": "Partner Networks",
            "type": "B2B",
            "effectiveness": "high",
            "cost": "medium",
            "notes": "Channel partners, integrators",
        },
    ],
    
    "common_pitfalls": [
        {
            "pitfall": "Ignoring Tier 2/3 cities",
            "description": "Focusing only on metros misses huge opportunity",
            "solution": "Design for low-bandwidth, offline-first capabilities",
        },
        {
            "pitfall": "Pricing in USD",
            "description": "Dollar pricing makes product inaccessible",
            "solution": "Localize pricing to INR, consider purchasing power",
        },
        {
            "pitfall": "English-only interface",
            "description": "Majority prefer native language interfaces",
            "solution": "Support Hindi and regional languages",
        },
        {
            "pitfall": "Assuming digital payments universal",
            "description": "Cash-on-delivery still popular",
            "solution": "Offer multiple payment options",
        },
        {
            "pitfall": "Igniting data costs",
            "description": "Mobile data is cheap but not free",
            "solution": "Optimize app size, support offline",
        },
        {
            "pitfall": "Complex onboarding",
            "description": "Users abandon if signup is too long",
            "solution": "Minimal KYC, progressive profiling",
        },
    ],
}


class IndiaLocalizer:
    """
    Provides India-specific localization guidance for MVPs and startups.
    
    Features:
    - Payment gateway recommendations
    - Communication channel guidance
    - City selection advice
    - Pricing strategy
    - Regulatory compliance
    - Technology stack recommendations
    """
    
    def __init__(self):
        """Initialize India localizer with knowledge base"""
        self.data = INDIA_SPECIFIC
    
    def get_payment_options(self) -> List[PaymentOption]:
        """Get recommended payment options for India"""
        return self.data["payment_options"]
    
    def get_communication_channels(self) -> List[CommunicationChannel]:
        """Get recommended communication channels"""
        return self.data["communication_channels"]
    
    def get_cloud_providers(self) -> List[CloudProvider]:
        """Get cloud providers with India presence"""
        return self.data["cloud_providers"]
    
    def get_target_cities(self, tier: str = None) -> List[Dict[str, Any]]:
        """Get target cities, optionally filtered by tier"""
        cities = self.data["cities"]
        if tier:
            cities = [c for c in cities if c["tier"] == tier]
        return cities
    
    def get_language_support(self) -> List[Dict[str, Any]]:
        """Get language support recommendations"""
        return self.data["languages"]
    
    def get_pricing_for_category(self, category: str, level: str = "entry") -> str:
        """Get pricing guidelines for a category"""
        category_data = self.data["pricing_guidelines"].get(category, {})
        return category_data.get(level, "Custom pricing")
    
    def get_regulatory_requirements(self, category: str) -> List[str]:
        """Get regulatory requirements for a category"""
        if category == "payments":
            return self.data["regulatory_requirements"]["payments"]
        elif category == "data":
            return self.data["regulatory_requirements"]["data_localization"]
        else:
            return self.data["regulatory_requirements"]["business_registration"]
    
    def get_tech_stack_recommendation(self, stack_type: str) -> List[str]:
        """Get technology stack recommendations"""
        return self.data["tech_stack_recommendations"].get(stack_type, [])
    
    def get_gtm_channels(self) -> List[Dict[str, Any]]:
        """Get go-to-market channel recommendations"""
        return self.data["go_to_market_channels"]
    
    def get_common_pitfalls(self) -> List[Dict[str, str]]:
        """Get common pitfalls and solutions"""
        return self.data["common_pitfalls"]
    
    def generate_localization_checklist(
        self,
        category: str,
        is_b2b: bool = True,
    ) -> Dict[str, List[str]]:
        """
        Generate a localization checklist for a startup category.
        
        Args:
            category: Product category (fintech, edtech, etc.)
            is_b2b: Whether this is a B2B product
            
        Returns:
            Dictionary with checklist items
        """
        checklist = {
            "payments": [],
            "pricing": [],
            "language": [],
            "communication": [],
            "compliance": [],
            "technology": [],
        }
        
        # Payments checklist
        payments = self.get_payment_options()
        checklist["payments"] = [
            f"Integrate {p.name} for payments",
            f"Support UPI (essential for India)",
            "Offer cash-on-delivery if physical product",
        ]
        
        # Pricing checklist
        if is_b2b:
            pricing = self.get_pricing_for_category("b2b_software")
            checklist["pricing"] = [
                f"Entry pricing: {pricing}",
                "Offer annual discount (Indian preference)",
                "Accept Indian payment methods",
            ]
        else:
            pricing = self.get_pricing_for_category("b2c_apps")
            checklist["pricing"] = [
                "Free tier with ads or limited features",
                f"Premium tier: {pricing}",
                "Consider freemium model",
            ]
        
        # Language checklist
        languages = self.get_language_support()
        checklist["language"] = [
            "English interface (minimum)",
            f"Hindi support ({(languages[0]['priority'])})",
            "Consider regional languages based on target market",
        ]
        
        # Communication checklist
        channels = self.get_communication_channels()
        active_channels = [c.name for c in channels if c.adoption == "high"]
        checklist["communication"] = [
            f"WhatsApp Business integration ({active_channels[0] if active_channels else 'essential'})",
            "SMS for critical notifications",
            "Email for formal communication",
        ]
        
        # Compliance checklist
        checklist["compliance"] = [
            "GST registration if applicable",
            "RBI compliance if payments",
            "Data protection compliance",
        ]
        
        # Technology checklist
        checklist["technology"] = [
            "Mobile-first (or mobile-only) approach",
            "Lightweight app (consider data costs)",
            "Offline-first capabilities",
            "India region cloud hosting",
        ]
        
        return checklist


def create_india_localizer() -> IndiaLocalizer:
    """
    Factory function to create IndiaLocalizer.
    
    Returns:
        IndiaLocalizer instance
    """
    return IndiaLocalizer()

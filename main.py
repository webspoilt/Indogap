# Phase One: Gap Detector - Main Entry Point
"""
YC-India Gap Detector - Phase One
Main entry point for the opportunity discovery engine

Usage:
    python main.py --batch W24 --output output/gaps.csv
    python main.py --batches W24 S25 --enrich --format json
    python main.py --demo
"""
import argparse
import logging
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from mini_services.config import get_settings
from mini_services.scrapers.yc_scraper import YCombinatorScraper, create_scraper
from mini_services.processors.text_processor import TextProcessor, create_text_processor
from mini_services.processors.similarity import SimilarityEngine, create_similarity_engine
from mini_services.scoring.seven_dimensions import SevenDimensionScorer, create_scorer
from mini_services.mvp_generator.generator import MVPGenerator, create_generator
from mini_services.database.repository import OpportunityRepository, create_repository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def safe_get_dimension_score(opp: Dict, dimension_name: str) -> str:
    """Safely get a dimension score from an opportunity."""
    try:
        scores = opp.get('scores')
        if scores and hasattr(scores, 'dimensions') and scores.dimensions:
            dim = scores.dimensions.get(dimension_name)
            if dim and hasattr(dim, 'score'):
                return str(dim.score)
    except (AttributeError, KeyError, TypeError):
        pass
    return 'N/A'


def run_demo():
    """Run demo with sample data to test the complete pipeline"""
    logger.info("=" * 80)
    logger.info("Running Phase One Gap Detector Demo")
    logger.info("=" * 80)
    
    # Initialize components
    settings = get_settings()
    scraper = create_scraper("yc", delay=1.0)
    text_processor = create_text_processor()
    similarity_engine = create_similarity_engine(text_processor)
    scorer = create_scorer()
    generator = create_generator()
    repository = create_repository()
    
    print("\n" + "=" * 80)
    print("🦄 INDO-GAP: AI-Powered Opportunity Discovery Engine for India")
    print("=" * 80)
    
    # Sample Indian startups database (Phase One: Manual)
    indian_startups = [
        # Fintech
        {'id': 'ind_001', 'name': 'Razorpay', 'description': 'Payment gateway for Indian businesses', 
         'category': 'Fintech', 'tags': ['payments', 'fintech', 'saas', 'b2b']},
        {'id': 'ind_002', 'name': 'CRED', 'description': 'Credit card bill payments and rewards platform', 
         'category': 'Fintech', 'tags': ['payments', 'credit', 'rewards', 'consumer']},
        {'id': 'ind_003', 'name': 'Zerodha', 'description': 'Online stock brokerage platform', 
         'category': 'Fintech', 'tags': ['stock market', 'trading', 'investments', 'fintech']},
        
        # Food Delivery
        {'id': 'ind_004', 'name': 'Swiggy', 'description': 'Food delivery and hyperlocal delivery platform', 
         'category': 'Food Delivery', 'tags': ['food', 'delivery', 'logistics', 'consumer']},
        {'id': 'ind_005', 'name': 'Zomato', 'description': 'Food delivery, restaurant discovery and reviews', 
         'category': 'Food Delivery', 'tags': ['food', 'delivery', 'restaurant', 'consumer']},
        {'id': 'ind_006', 'name': 'Blinkit', 'description': 'Quick commerce and 10-minute delivery', 
         'category': 'Quick Commerce', 'tags': ['delivery', 'quick commerce', 'groceries', 'consumer']},
        
        # SaaS
        {'id': 'ind_007', 'name': 'Freshworks', 'description': 'SaaS products for customer engagement', 
         'category': 'SaaS', 'tags': ['saas', 'crm', 'customer support', 'b2b']},
        {'id': 'ind_008', 'name': 'Zoho', 'description': 'Business software and SaaS applications', 
         'category': 'SaaS', 'tags': ['saas', 'productivity', 'business tools', 'b2b']},
        {'id': 'ind_009', 'name': 'BrowserStack', 'description': 'Cloud-based testing platform for developers', 
         'category': 'DevTools', 'tags': ['testing', 'developers', 'saas', 'b2b']},
        
        # HealthTech
        {'id': 'ind_010', 'name': 'Practo', 'description': 'Healthcare platform with doctor consultations', 
         'category': 'HealthTech', 'tags': ['health', 'telemedicine', 'doctors', 'consumer']},
        {'id': 'ind_011', 'name': 'PharmEasy', 'description': 'Online pharmacy and healthcare delivery', 
         'category': 'HealthTech', 'tags': ['pharmacy', 'health', 'delivery', 'consumer']},
        
        # EdTech
        {'id': 'ind_012', 'name': 'Byjus', 'description': 'EdTech platform with learning apps for K-12', 
         'category': 'EdTech', 'tags': ['education', 'learning', 'k12', 'consumer']},
        {'id': 'ind_013', 'name': 'Unacademy', 'description': 'Online learning platform for competitive exams', 
         'category': 'EdTech', 'tags': ['education', 'learning', 'exam prep', 'consumer']},
        
        # E-commerce
        {'id': 'ind_014', 'name': 'Flipkart', 'description': 'E-commerce marketplace for India', 
         'category': 'E-commerce', 'tags': ['ecommerce', 'retail', 'marketplace', 'consumer']},
        {'id': 'ind_015', 'name': 'Myntra', 'description': 'Fashion e-commerce platform', 
         'category': 'E-commerce', 'tags': ['fashion', 'ecommerce', 'clothing', 'consumer']},
        
        # B2B
        {'id': 'ind_016', 'name': 'Udaan', 'description': 'B2B e-commerce platform for SMEs', 
         'category': 'B2B', 'tags': ['b2b', 'ecommerce', 'sme', 'wholesale']},
        {'id': 'ind_017', 'name': 'IndiaMART', 'description': 'B2B marketplace connecting Indian businesses', 
         'category': 'B2B', 'tags': ['b2b', 'marketplace', 'sme', 'trading']},
        
        # Logistics
        {'id': 'ind_018', 'name': 'Delhivery', 'description': 'Logistics and supply chain services company', 
         'category': 'Logistics', 'tags': ['logistics', 'shipping', 'supply chain', 'b2b']},
        
        # HR Tech
        {'id': 'ind_019', 'name': 'GreytHR', 'description': 'HR and payroll software for Indian companies', 
         'category': 'HR Tech', 'tags': ['hr', 'payroll', 'hr tech', 'sme']},
        
        # Real Estate
        {'id': 'ind_020', 'name': 'Housing', 'description': 'Real estate search and listing platform', 
         'category': 'Real Estate', 'tags': ['real estate', 'property', 'housing', 'consumer']},
        
        # InsurTech
        {'id': 'ind_021', 'name': 'Policybazaar', 'description': 'Insurance comparison and purchase platform', 
         'category': 'InsurTech', 'tags': ['insurance', 'fintech', 'comparison', 'consumer']},
        
        # Travel
        {'id': 'ind_022', 'name': 'OYO', 'description': 'Hotel booking and accommodation platform', 
         'category': 'Travel', 'tags': ['hotel', 'booking', 'accommodation', 'travel']},
        
        # Mobility
        {'id': 'ind_023', 'name': 'Ola', 'description': 'Ride-hailing and mobility services', 
         'category': 'Mobility', 'tags': ['transport', 'taxi', 'rides', 'consumer']},
        {'id': 'ind_024', 'name': 'Rapido', 'description': 'Bike taxi and last-mile delivery platform', 
         'category': 'Mobility', 'tags': ['transport', 'bike taxi', 'delivery', 'consumer']},
        
        # Social/Content
        {'id': 'ind_025', 'name': 'ShareChat', 'description': 'Regional language social media platform', 
         'category': 'Social', 'tags': ['social', 'regional languages', 'mobile', 'consumer']},
        {'id': 'ind_026', 'name': 'Dailyhunt', 'description': 'News and content aggregation in Indian languages', 
         'category': 'Content', 'tags': ['news', 'content', 'regional', 'languages']},
        
        # Climate/Agri
        {'id': 'ind_027', 'name': 'AgroStar', 'description': 'Agriculture input and advisory platform', 
         'category': 'AgriTech', 'tags': ['agriculture', 'farmers', 'advisory', 'b2c']},
        {'id': 'ind_028', 'name': 'Bijak', 'description': 'Agricultural commodity trading platform', 
         'category': 'AgriTech', 'tags': ['agriculture', 'trading', 'commodities', 'b2b']},
    ]
    
    print(f"\n📊 Loaded {len(indian_startups)} Indian startups in database")
    
    # Sample YC companies to analyze (simulating W24/S25 batches)
    yc_companies = [
        # AI Agents - High Opportunity
        {
            'id': 'yc_001', 
            'name': 'VoiceFlow Pro', 
            'batch': 'W24',
            'short_description': 'AI voice agents for customer service automation - enterprise solution handling 10M+ calls',
            'tags': ['AI', 'Enterprise', 'Customer Service', 'Voice AI'],
            'source': 'YC'
        },
        
        {
            'id': 'yc_002', 
            'name': 'Legal AI Assistant', 
            'batch': 'W24',
            'short_description': 'AI-powered legal document review and contract analysis for law firms',
            'tags': ['Legal Tech', 'AI', 'Enterprise'],
            'source': 'YC'
        },
        
        # Vertical SaaS - Check for gaps
        {
            'id': 'yc_003', 
            'name': 'RestaurantOS', 
            'batch': 'W24',
            'short_description': 'Complete operating system for restaurant management including inventory, POS, and delivery',
            'tags': ['SaaS', 'Restaurant', 'Vertical SaaS'],
            'source': 'YC'
        },
        
        {
            'id': 'yc_004', 
            'name': 'SecurityOps', 
            'batch': 'W24',
            'short_description': 'Security operations platform for mid-market companies with automated threat detection',
            'tags': ['SaaS', 'Security', 'Enterprise'],
            'source': 'YC'
        },
        
        # B2B Marketplace - Already saturated in India
        {
            'id': 'yc_005', 
            'name': 'B2B Marketplace for X', 
            'batch': 'W24',
            'short_description': 'Horizontal B2B marketplace connecting suppliers and buyers in manufacturing',
            'tags': ['B2B', 'Marketplace', 'E-commerce'],
            'source': 'YC'
        },
        
        # EdTech - Already saturated
        {
            'id': 'yc_006', 
            'name': 'K12 Learning App', 
            'batch': 'W24',
            'short_description': 'Mobile learning application for K-12 students with gamification and AI tutoring',
            'tags': ['EdTech', 'K12', 'Mobile', 'AI'],
            'source': 'YC'
        },
        
        # Healthcare - Check for specific gaps
        {
            'id': 'yc_007', 
            'name': 'SeniorCare AI', 
            'batch': 'W24',
            'short_description': 'AI monitoring system for elderly care with health alerts and fall detection',
            'tags': ['HealthTech', 'AI', 'Elderly Care', 'IoT'],
            'source': 'YC'
        },
        
        {
            'id': 'yc_008', 
            'name': 'PetHealth Platform', 
            'batch': 'W24',
            'short_description': 'Telemedicine and health tracking platform for pets with veterinary consultations',
            'tags': ['HealthTech', 'Pet Tech', 'Telemedicine'],
            'source': 'YC'
        },
        
        # Fintech - Specific gaps
        {
            'id': 'yc_009', 
            'name': 'Embedded Insurance API', 
            'batch': 'W24',
            'short_description': 'API for adding insurance products to any e-commerce or SaaS application',
            'tags': ['Fintech', 'InsurTech', 'API', 'B2B'],
            'source': 'YC'
        },
        
        {
            'id': 'yc_010', 
            'name': 'Invoice Financing AI', 
            'batch': 'W24',
            'short_description': 'AI-powered invoice factoring and working capital financing for SMEs',
            'tags': ['Fintech', 'B2B', 'Lending', 'SME'],
            'source': 'YC'
        },
        
        # Climate Tech - Emerging opportunity
        {
            'id': 'yc_011', 
            'name': 'Carbon Credits API', 
            'batch': 'W25',
            'short_description': 'API for companies to calculate, track, and trade carbon credits automatically',
            'tags': ['Climate Tech', 'Fintech', 'Enterprise', 'API'],
            'source': 'YC'
        },
        
        # DevTools - Check gaps
        {
            'id': 'yc_012', 
            'name': 'Code Review AI', 
            'batch': 'W25',
            'short_description': 'AI-powered code review and security analysis for enterprise codebases',
            'tags': ['DevTools', 'AI', 'Security', 'Developers'],
            'source': 'YC'
        },
        
        # Vertical SaaS - Healthcare specific
        {
            'id': 'yc_013', 
            'name': 'ClinicOS', 
            'batch': 'W25',
            'short_description': 'Complete practice management system for clinics including EHR, billing, and appointments',
            'tags': ['HealthTech', 'SaaS', 'Vertical', 'Healthcare'],
            'source': 'YC'
        },
        
        # AgriTech - Check if gap exists
        {
            'id': 'yc_014', 
            'name': 'FarmOS', 
            'batch': 'W25',
            'short_description': 'IoT and AI platform for precision farming with crop monitoring and automated irrigation',
            'tags': ['AgriTech', 'IoT', 'AI', 'Sustainability'],
            'source': 'YC'
        },
        
        # HR Tech - Check for gaps
        {
            'id': 'yc_015', 
            'name': 'Recruitment AI', 
            'batch': 'W25',
            'short_description': 'AI-powered recruitment platform with automated sourcing and candidate matching',
            'tags': ['HR Tech', 'AI', 'Recruitment', 'B2B'],
            'source': 'YC'
        },
    ]
    
    print(f"🔍 Analyzing {len(yc_companies)} YC companies against Indian market...\n")
    
    # Process each YC company
    opportunities = []
    
    for yc_company in yc_companies:
        logger.info(f"Analyzing: {yc_company['name']}")
        
        # Create combined text for analysis
        yc_text = f"{yc_company['name']} {yc_company['short_description']} {' '.join(yc_company['tags'])}"
        
        # Find best match in Indian startups
        best_match = None
        best_similarity = 0
        
        for ind_startup in indian_startups:
            ind_text = f"{ind_startup['name']} {ind_startup['description']} {' '.join(ind_startup['tags'])}"
            
            # Calculate similarity
            similarity = similarity_engine.compare(yc_company, ind_startup)
            
            if similarity.similarity_score > best_similarity:
                best_similarity = similarity.similarity_score
                best_match = ind_startup
        
        # Calculate gap score
        gap_score = 1.0 - best_similarity
        
        # Determine opportunity level
        if gap_score >= 0.7:
            opportunity_level = "HIGH"
        elif gap_score >= 0.4:
            opportunity_level = "MEDIUM"
        else:
            opportunity_level = "LOW"
        
        # Calculate 7-dimension scores (Phase Three feature - simplified for demo)
        from mini_services.scoring.base import ScoringRequest
        scoring_request = ScoringRequest(
            opportunity_id=yc_company.get('id', yc_company['name']),
            startup_name=yc_company['name'],
            startup_description=yc_company['short_description'],
            source_batch=yc_company.get('batch'),
            tags=yc_company.get('tags', []),
            best_match=best_match
        )
        scores = scorer.score(scoring_request)
        
        # Generate MVP roadmap if high opportunity
        mvp_roadmap = None
        if gap_score >= 0.5:
            mvp_roadmap = generator.generate_roadmap(
                yc_company['name'],
                yc_company['short_description'],
                scores,
                config=None
            )
        
        # Create opportunity record
        opportunity = {
            'id': f"opp_{yc_company['id']}",
            'yc_company': yc_company,
            'best_match': best_match,
            'similarity_score': round(best_similarity, 3),
            'gap_score': round(gap_score, 3),
            'opportunity_level': opportunity_level,
            'scores': scores,
            'mvp_roadmap': mvp_roadmap,
            'analyzed_at': datetime.now().isoformat()
        }
        
        opportunities.append(opportunity)
        
        # Store in repository
        repository.store_opportunity(opportunity)
    
    # Sort by gap score (highest first)
    opportunities.sort(key=lambda x: x['gap_score'], reverse=True)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 GAP DETECTION SUMMARY")
    print("=" * 80)
    
    high = [o for o in opportunities if o['opportunity_level'] == 'HIGH']
    medium = [o for o in opportunities if o['opportunity_level'] == 'MEDIUM']
    low = [o for o in opportunities if o['opportunity_level'] == 'LOW']
    
    print(f"\nTotal Opportunities Analyzed: {len(opportunities)}")
    print(f"  🟢 High Priority: {len(high)}")
    print(f"  🟡 Medium Priority: {len(medium)}")
    print(f"  🔴 Low Priority: {len(low)}")
    
    # Display top opportunities
    print(f"\n{'='*80}")
    print("🎯 TOP HIGH PRIORITY OPPORTUNITIES FOR INDIA")
    print("="*80)
    
    for idx, opp in enumerate(high[:10], 1):
        yc = opp['yc_company']
        match = opp['best_match']
        
        print(f"\n{idx}. {yc['name']} ({yc['batch']})")
        print(f"   📝 Description: {yc['short_description'][:80]}...")
        print(f"   📊 Gap Score: {opp['gap_score']:.3f} | Similarity: {opp['similarity_score']:.3f}")
        
        if match:
            print(f"   🔄 Closest Indian Match: {match['name']} ({match['category']})")
        else:
            print(f"   🔄 No direct competitor found in India")
        
        print(f"   🏷️ Tags: {', '.join(yc['tags'][:3])}")
        
        # Show key scores
        if opp['scores']:
            scores = opp['scores']
            print(f"   📈 Key Scores:")
            if hasattr(scores, 'dimensions') and scores.dimensions:
                dim = scores.dimensions.get('cultural_fit', {})
                print(f"      - Cultural Fit: {dim.score if hasattr(dim, 'score') else dim.get('score', 'N/A')}/10")
                dim = scores.dimensions.get('payment_readiness', {})
                print(f"      - Payment Readiness: {dim.score if hasattr(dim, 'score') else dim.get('score', 'N/A')}/10")
                dim = scores.dimensions.get('execution_feasibility', {})
                print(f"      - Execution Feasibility: {dim.score if hasattr(dim, 'score') else dim.get('score', 'N/A')}/10")
        
        if opp.get('mvp_roadmap') and hasattr(opp['mvp_roadmap'], 'timeline'):
            print(f"   🚀 MVP Timeline: {opp['mvp_roadmap'].timeline}")
        
        print(f"   💡 Recommendation: Build this for the Indian market")
    
    # Display medium opportunities
    if medium:
        print(f"\n{'='*80}")
        print("⚠️ MEDIUM PRIORITY OPPORTUNITIES (May need differentiation)")
        print("="*80)
        
        for opp in medium[:5]:
            yc = opp['yc_company']
            match = opp['best_match']
            
            print(f"\n• {yc['name']}: Similar to {match['name'] if match else 'unknown'} ({opp['similarity_score']:.2f})")
    
    # Export results
    print(f"\n{'='*80}")
    print("💾 EXPORTING RESULTS")
    print("="*80)
    
    # Export to JSON
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = output_dir / f"opportunity_analysis_{timestamp}.json"
    
    export_data = {
        'generated_at': datetime.now().isoformat(),
        'phase': 'One - Gap Detector',
        'total_analyzed': len(yc_companies),
        'indian_startups_in_db': len(indian_startups),
        'summary': {
            'high_priority': len(high),
            'medium_priority': len(medium),
            'low_priority': len(low)
        },
        'opportunities': opportunities
    }
    
    with open(json_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"✅ Results exported to: {json_path}")
    
    # Export to CSV
    csv_path = output_dir / f"opportunity_analysis_{timestamp}.csv"
    
    rows = []
    for opp in opportunities:
        yc = opp['yc_company']
        rows.append({
            'YC Company': yc['name'],
            'Batch': yc['batch'],
            'Description': yc['short_description'],
            'Tags': ', '.join(yc['tags']),
            'Best Match': opp['best_match']['name'] if opp['best_match'] else 'None',
            'Match Category': opp['best_match']['category'] if opp['best_match'] else 'N/A',
            'Similarity Score': opp['similarity_score'],
            'Gap Score': opp['gap_score'],
            'Opportunity Level': opp['opportunity_level'],
            'Cultural Fit': safe_get_dimension_score(opp, 'cultural_fit'),
            'Payment Readiness': safe_get_dimension_score(opp, 'payment_readiness'),
            'Execution Feasibility': safe_get_dimension_score(opp, 'execution_feasibility'),
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    
    print(f"✅ CSV exported to: {csv_path}")
    
    print(f"\n{'='*80}")
    print("✅ DEMO COMPLETE - Phase One Gap Detector")
    print("="*80)
    
    return opportunities


def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(
        description='IndoGap - AI-Powered Opportunity Discovery Engine for India',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo                          Run demo with sample data
  python main.py --batch W24                     Analyze YC W24 batch
  python main.py --batch W24 --enrich            Scrape detailed company info
  python main.py --batches W24 S25 --json        Multiple batches, JSON output
        """
    )
    
    parser.add_argument('--batch', type=str, 
                       help='Single YC batch to analyze (e.g., W24)')
    parser.add_argument('--batches', type=str, 
                       help='Multiple batches (comma-separated, e.g., W24,S25)')
    parser.add_argument('--output', type=str, 
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--format', type=str, choices=['csv', 'json', 'both'],
                       default='csv', help='Output format')
    parser.add_argument('--enrich', action='store_true',
                       help='Fetch detailed company information')
    parser.add_argument('--demo', action='store_true',
                       help='Run demo with sample data')
    parser.add_argument('--indian-db', type=str,
                       help='Path to Indian startups database (CSV/JSON)')
    parser.add_argument('--top', type=int, default=20,
                       help='Limit results to top N opportunities')
    
    args = parser.parse_args()
    
    try:
        if args.demo:
            opportunities = run_demo()
            return 0
        
        # For actual YC scraping (requires network access)
        logger.info("Live YC scraping requires network access to ycombinator.com")
        logger.info("Run with --demo to test the pipeline with sample data")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

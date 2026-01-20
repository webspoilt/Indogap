"""
Similarity Engine for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides similarity calculation between global startups and Indian
companies using both TF-IDF (Phase One) and embedding-based (Phase Two) methods.
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from .text_processor import TextProcessor, create_text_processor
from .embeddings import (
    EmbeddingGenerator,
    create_embedding_generator,
    calculate_cosine_similarity,
    calculate_batch_similarity,
)
from mini_services.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SimilarityMatch:
    """Result of similarity comparison"""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    similarity_score: float = 0.0
    gap_score: float = 0.0
    category_match: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    @property
    def is_gap(self) -> bool:
        """Check if this represents a market gap"""
        return self.similarity_score < 0.5
    
    @property
    def is_saturated(self) -> bool:
        """Check if market is saturated"""
        return self.similarity_score > 0.7


@dataclass
class SimilarityResult:
    """Complete similarity analysis result"""
    source_id: str
    source_name: str
    best_match: Optional[SimilarityMatch] = None
    all_matches: List[SimilarityMatch] = field(default_factory=list)
    gap_detected: bool = False
    opportunity_level: str = "unknown"
    analysis_method: str = "tfidf"
    analyzed_at: datetime = field(default_factory=datetime.now)


class CategoryMatcher:
    """
    Matches text to categories based on keyword analysis.
    
    Used to determine if a global startup's category matches
    existing Indian startups.
    """
    
    CATEGORY_KEYWORDS = {
        'fintech': [
            'payment', 'banking', 'finance', 'financial', 'lending', 'credit',
            'invest', 'insurance', 'wealth', 'trading', 'crypto', 'blockchain',
            'neobank', 'pos', 'upi', 'wallet', 'financial', 'fintech'
        ],
        'e-commerce': [
            'e-commerce', 'ecommerce', 'shop', 'retail', 'marketplace',
            'selling', 'purchase', 'cart', 'checkout', 'online store',
            'd2c', 'direct to consumer', 'b2c'
        ],
        'saas': [
            'saas', 'software', 'subscription', 'b2b', 'enterprise',
            'workflow', 'automation', 'productivity', 'tool', 'api',
            'cloud', 'platform as a service'
        ],
        'healthtech': [
            'health', 'medical', 'healthcare', 'patient', 'doctor',
            'hospital', 'pharma', 'wellness', 'fitness', 'telehealth',
            'telemedicine', 'clinical', 'diagnosis'
        ],
        'edtech': [
            'education', 'learning', 'course', 'student', 'school',
            'training', 'tutoring', 'skill', 'academic', 'university',
            'elearning', 'online learning', 'k12'
        ],
        'food delivery': [
            'food', 'delivery', 'restaurant', 'eat', 'meal',
            'grocery', 'kitchen', 'catering', 'takeout', 'dark kitchen',
            'quick commerce', 'hyperlocal'
        ],
        'logistics': [
            'logistics', 'shipping', 'transport', 'freight',
            'supply chain', 'warehouse', 'inventory', 'fulfillment',
            'last mile', 'delivery'
        ],
        'b2b': [
            'b2b', 'business to business', 'sme', 'smb', 'enterprise',
            'procurement', 'supply chain', 'wholesale'
        ],
        'ai/ml': [
            'artificial intelligence', 'machine learning', 'ai', 'ml',
            'neural', 'deep learning', 'model', 'algorithm', 'nlp',
            'computer vision', 'generative', 'llm', 'gpt'
        ],
        'consumer': [
            'consumer', 'app', 'mobile', 'personal', 'lifestyle', 'daily',
            'end user', 'individual', 'retail'
        ],
        'mobility': [
            'transport', 'taxi', 'ride', 'mobility', 'vehicle', 'travel',
            'transportation', 'commute', 'bike', 'scooter'
        ],
        'hr tech': [
            'hr', 'human resource', 'recruiting', 'hiring', 'talent',
            'payroll', 'employee', 'workforce', 'performance', 'hris'
        ],
        'real estate': [
            'real estate', 'property', 'housing', 'rent', 'lease',
            'apartment', 'commercial', 'mortgage', 'proptech'
        ],
        'insurtech': [
            'insurance', 'policy', 'coverage', 'claim', 'underwriting',
            'insurtech', 'risk'
        ],
        'agritech': [
            'agriculture', 'farming', 'crop', 'farmer', 'agritech',
            'food supply', 'agri', 'farm'
        ],
        'climate tech': [
            'climate', 'sustainability', 'carbon', 'renewable',
            'energy', 'environment', 'green', 'clean tech', 'esg'
        ],
        'deeptech': [
            'deeptech', 'semiconductor', 'chip', 'hardware', 'robotics',
            'quantum', 'biotech', 'advanced manufacturing', 'space'
        ],
    }
    
    def __init__(self):
        """Initialize category matcher"""
        # Invert for lookup
        self._keyword_to_category = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                self._keyword_to_category[keyword] = category
    
    def infer_category(self, text: str, top_n: int = 2) -> List[Tuple[str, float]]:
        """
        Infer categories from text with confidence scores.
        
        Args:
            text: Input text
            top_n: Number of top categories to return
            
        Returns:
            List of (category, score) tuples
        """
        text_lower = text.lower()
        scores = {}
        
        # Score each category
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer keywords higher
                    score += len(keyword) * 0.1
            scores[category] = score
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_scores or sorted_scores[0][1] == 0:
            # Default to 'consumer' if no match
            return [('consumer', 0.5)]
        
        max_score = sorted_scores[0][1]
        normalized = [
            (cat, score / max_score if max_score > 0 else 0) 
            for cat, score in sorted_scores[:top_n]
        ]
        
        return normalized
    
    def calculate_category_match(
        self,
        source_categories: List[str],
        target_categories: List[str],
    ) -> float:
        """
        Calculate category match score between source and target.
        
        Args:
            source_categories: Categories from source startup
            target_categories: Categories from target startup
            
        Returns:
            Match score (0-1)
        """
        if not source_categories or not target_categories:
            return 0.5  # Neutral if no categories
        
        source_set = set(c.lower() for c in source_categories)
        target_set = set(c.lower() for c in target_categories)
        
        intersection = source_set & target_set
        union = source_set | target_set
        
        if not union:
            return 0.5
        
        return len(intersection) / len(union)


class SimilarityEngine:
    """
    Main similarity engine for gap detection.
    
    Supports:
    - Phase One: TF-IDF based similarity (rule-based)
    - Phase Two: Embedding-based similarity (requires OpenAI API)
    
    Features:
    - Automatic method selection based on configuration
    - Category-aware matching
    - Keyword extraction and comparison
    - Batch processing for efficiency
    """
    
    def __init__(
        self,
        text_processor: Optional[TextProcessor] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        use_embeddings: bool = False,
        description_weight: float = 0.6,
        category_weight: float = 0.3,
        keyword_weight: float = 0.1,
    ):
        """
        Initialize similarity engine.
        
        Args:
            text_processor: Text processor for TF-IDF
            embedding_generator: Embedding generator for semantic similarity
            use_embeddings: Use embeddings (requires API key)
            description_weight: Weight for description similarity
            category_weight: Weight for category match
            keyword_weight: Weight for keyword overlap
        """
        settings = get_settings()
        
        self.text_processor = text_processor or create_text_processor()
        self.use_embeddings = use_embeddings and settings.has_openai_key
        
        if self.use_embeddings:
            self.embedding_generator = embedding_generator or create_embedding_generator()
        else:
            self.embedding_generator = None
        
        self.category_matcher = CategoryMatcher()
        
        # Scoring weights
        self.weights = {
            'description': description_weight,
            'category': category_weight,
            'keyword': keyword_weight,
        }
        
        # State
        self._indian_startups: List[Dict[str, Any]] = []
        self._startup_embeddings: Optional[np.ndarray] = None
        
    def load_indian_startups(
        self,
        startups: List[Dict[str, Any]],
        rebuild_embeddings: bool = True,
    ) -> None:
        """
        Load Indian startups for comparison.
        
        Args:
            startups: List of Indian startup dictionaries
            rebuild_embeddings: Rebuild embeddings if using embedding mode
        """
        self._indian_startups = startups
        
        if self.use_embeddings and rebuild_embeddings:
            self._build_startup_embeddings()
        
        logger.info(f"Loaded {len(startups)} Indian startups")
    
    def _build_startup_embeddings(self) -> None:
        """Build embeddings for all Indian startups"""
        if not self._indian_startups or not self.embedding_generator:
            return
        
        # Combine name, description, and tags for embedding
        texts = [
            f"{s.get('name', '')} {s.get('description', '')} {' '.join(s.get('tags', []))}"
            for s in self._indian_startups
        ]
        
        result = self.embedding_generator.generate_batch(texts, normalize=True)
        
        if result.success and result.embeddings:
            self._startup_embeddings = np.array(result.embeddings)
            logger.info(f"Built embeddings for {len(result.embeddings)} startups")
        else:
            logger.warning("Failed to build embeddings")
    
    def compare(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
    ) -> SimilarityMatch:
        """
        Compare a source startup against a target startup.
        
        Args:
            source: Source startup (YC, Product Hunt, etc.)
            target: Target startup (Indian company)
            
        Returns:
            SimilarityMatch with comparison results
        """
        # Extract text for comparison
        source_text = self._get_company_text(source)
        target_text = self._get_company_text(target)
        
        # Get categories
        source_categories = source.get('tags', []) + source.get('categories', [])
        target_categories = target.get('tags', []) + target.get('categories', [])
        
        # Calculate similarities
        if self.use_embeddings:
            desc_sim = self._embedding_similarity(source_text, target_text)
        else:
            desc_sim = self._tfidf_similarity(source_text, target_text)
        
        # Category match
        cat_match = self.category_matcher.calculate_category_match(
            source_categories, target_categories
        )
        
        # Keyword overlap
        kw_overlap, matched_kw, missing_kw = self._keyword_comparison(
            source_text, target_text
        )
        
        # Calculate overall similarity
        overall = (
            desc_sim * self.weights['description'] +
            cat_match * self.weights['category'] +
            kw_overlap * self.weights['keyword']
        )
        
        # Calculate gap score
        gap_score = 1.0 - overall
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            source.get('name', 'Unknown'),
            target.get('name', 'Unknown'),
            overall, desc_sim, cat_match, kw_overlap,
            len(matched_kw), len(missing_kw)
        )
        
        return SimilarityMatch(
            source_id=source.get('id', ''),
            source_name=source.get('name', 'Unknown'),
            target_id=target.get('id', ''),
            target_name=target.get('name', 'Unknown'),
            similarity_score=overall,
            gap_score=gap_score,
            category_match=cat_match,
            matched_keywords=matched_kw,
            missing_keywords=missing_kw,
            reasoning=reasoning,
        )
    
    def find_best_match(
        self,
        source: Dict[str, Any],
        top_n: int = 1,
    ) -> List[SimilarityMatch]:
        """
        Find best matching Indian startups for a source.
        
        Args:
            source: Source startup to match
            top_n: Number of top matches to return
            
        Returns:
            List of SimilarityMatch sorted by similarity
        """
        if not self._indian_startups:
            return []
        
        matches = []
        
        for target in self._indian_startups:
            match = self.compare(source, target)
            matches.append(match)
        
        # Sort by similarity and return top N
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches[:top_n]
    
    def find_all_matches(
        self,
        source: Dict[str, Any],
        threshold: float = 0.3,
    ) -> List[SimilarityMatch]:
        """
        Find all matching Indian startups above threshold.
        
        Args:
            source: Source startup to match
            threshold: Minimum similarity threshold
            
        Returns:
            List of SimilarityMatch above threshold
        """
        if not self._indian_startups:
            return []
        
        matches = []
        
        for target in self._indian_startups:
            match = self.compare(source, target)
            if match.similarity_score >= threshold:
                matches.append(match)
        
        # Sort by similarity
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def detect_gap(
        self,
        source: Dict[str, Any],
    ) -> SimilarityResult:
        """
        Detect if a gap exists for a source startup.
        
        Args:
            source: Source startup to analyze
            
        Returns:
            SimilarityResult with gap analysis
        """
        matches = self.find_best_match(source, top_n=5)
        
        if not matches:
            # No Indian startups to compare against
            return SimilarityResult(
                source_id=source.get('id', ''),
                source_name=source.get('name', 'Unknown'),
                gap_detected=True,
                opportunity_level="high",
                analysis_method="embedding" if self.use_embeddings else "tfidf",
            )
        
        best_match = matches[0]
        gap_detected = best_match.similarity_score < 0.5
        
        # Determine opportunity level
        if best_match.similarity_score < 0.3:
            opportunity_level = "high"
        elif best_match.similarity_score < 0.5:
            opportunity_level = "medium"
        elif best_match.similarity_score < 0.7:
            opportunity_level = "low"
        else:
            opportunity_level = "saturated"
        
        return SimilarityResult(
            source_id=source.get('id', ''),
            source_name=source.get('name', 'Unknown'),
            best_match=best_match,
            all_matches=matches,
            gap_detected=gap_detected,
            opportunity_level=opportunity_level,
            analysis_method="embedding" if self.use_embeddings else "tfidf",
        )
    
    def batch_analyze(
        self,
        sources: List[Dict[str, Any]],
        return_all_matches: bool = False,
    ) -> List[SimilarityResult]:
        """
        Analyze multiple source startups for gaps.
        
        Args:
            sources: List of source startups
            return_all_matches: Include all matches in results
            
        Returns:
            List of SimilarityResult for each source
        """
        results = []
        
        for source in sources:
            result = self.detect_gap(source)
            if not return_all_matches:
                result.all_matches = result.all_matches[:1]
            results.append(result)
        
        return results
    
    def _get_company_text(self, company: Dict[str, Any]) -> str:
        """Extract full text from company for comparison"""
        parts = [
            company.get('name', ''),
            company.get('short_description', ''),
            company.get('description', ''),
            company.get('long_description', ''),
            " ".join(company.get('tags', [])),
            " ".join(company.get('categories', [])),
        ]
        return " ".join(filter(None, parts))
    
    def _tfidf_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF based similarity"""
        return self.text_processor.calculate_similarity(text1, text2, method='tfidf')
    
    def _embedding_similarity(self, text1: str, text2: str) -> float:
        """Calculate embedding-based similarity"""
        if not self.embedding_generator:
            return self._tfidf_similarity(text1, text2)
        
        result1 = self.embedding_generator.generate(text1, normalize=True)
        result2 = self.embedding_generator.generate(text2, normalize=True)
        
        if result1.success and result2.success:
            return calculate_cosine_similarity(
                result1.embedding,
                result2.embedding,
            )
        
        return self._tfidf_similarity(text1, text2)
    
    def _keyword_comparison(
        self,
        text1: str,
        text2: str,
    ) -> Tuple[float, List[str], List[str]]:
        """Compare keywords between two texts"""
        proc1 = self.text_processor.process(text1)
        proc2 = self.text_processor.process(text2)
        
        keywords1 = set(proc1.keywords)
        keywords2 = set(proc2.keywords)
        
        if not keywords1:
            return 0.5, [], list(keywords2)
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        if not union:
            return 0.5, [], []
        
        jaccard = len(intersection) / len(union)
        
        return (
            jaccard,
            list(intersection),
            list(keywords2 - keywords1),
        )
    
    def _generate_reasoning(
        self,
        source_name: str,
        target_name: str,
        overall: float,
        desc_sim: float,
        cat_match: float,
        kw_overlap: float,
        matched_count: int,
        missing_count: int,
    ) -> str:
        """Generate human-readable reasoning for similarity"""
        if overall > 0.7:
            level = "Very similar"
        elif overall > 0.5:
            level = "Moderately similar"
        elif overall > 0.3:
            level = "Somewhat similar"
        else:
            level = "Dissimilar"
        
        return (
            f"{level} to {target_name}. "
            f"Overall similarity: {overall:.2f}. "
            f"Description: {desc_sim:.2f}, "
            f"Category: {cat_match:.2f}, "
            f"Keywords: {kw_overlap:.2f}. "
            f"Matched {matched_count} keywords, "
            f"missing {missing_count} keywords."
        )


def create_similarity_engine(
    text_processor: Optional[TextProcessor] = None,
    embedding_generator: Optional[EmbeddingGenerator] = None,
    use_embeddings: bool = False,
    **kwargs
) -> SimilarityEngine:
    """
    Factory function to create SimilarityEngine.
    
    Args:
        text_processor: Text processor instance
        embedding_generator: Embedding generator instance
        use_embeddings: Use embedding-based similarity
        **kwargs: Additional engine configuration
        
    Returns:
        SimilarityEngine instance
    """
    return SimilarityEngine(
        text_processor=text_processor,
        embedding_generator=embedding_generator,
        use_embeddings=use_embeddings,
        **kwargs
    )

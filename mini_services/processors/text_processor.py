"""
Text Processor for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides text preprocessing and NLP functionality for analyzing
startup descriptions and calculating similarity scores.
"""
import re
import logging
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
import numpy as np

from mini_services.config import get_settings

logger = logging.getLogger(__name__)

# Download required NLTK data (with network error handling)
def _ensure_nltk_data():
    """Download NLTK data if not available, silently fail on network errors"""
    resources = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
        ('corpora/wordnet', 'wordnet'),
    ]
    for resource_path, resource_name in resources:
        try:
            nltk.data.find(resource_path)
        except LookupError:
            try:
                nltk.download(resource_name, quiet=True)
            except Exception:
                pass  # Network errors should not break import

_ensure_nltk_data()


@dataclass
class ProcessedText:
    """Container for processed text components"""
    original: str
    cleaned: str
    tokens: List[str] = field(default_factory=list)
    stemmed: List[str] = field(default_factory=list)
    lemmatized: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    bigrams: List[str] = field(default_factory=list)
    trigrams: List[str] = field(default_factory=list)
    noun_phrases: List[str] = field(default_factory=list)
    word_count: int = 0
    vocabulary_size: int = 0


class TextProcessor:
    """
    Text processing pipeline for startup description analysis.
    
    Features:
    - Text cleaning and normalization
    - Tokenization with multiple strategies
    - Stopword removal (English + custom)
    - Stemming and lemmatization
    - N-gram extraction
    - Keyword extraction
    - TF-IDF vectorization
    """
    
    def __init__(
        self,
        use_stemming: bool = True,
        use_lemmatization: bool = False,
        use_stopwords: bool = True,
        use_bigrams: bool = True,
        custom_stopwords: Optional[Set[str]] = None,
        min_word_length: int = 2,
        max_word_length: int = 50,
    ):
        """
        Initialize text processor.
        
        Args:
            use_stemming: Apply Porter stemming
            use_lemmatization: Apply WordNet lemmatization
            use_stopwords: Remove stopwords
            use_bigrams: Extract bigrams and trigrams
            custom_stopwords: Additional stopwords to remove
            min_word_length: Minimum word length to keep
            max_word_length: Maximum word length to keep
        """
        self.use_stemming = use_stemming
        self.use_lemmatization = use_lemmatization
        self.use_stopwords = use_stopwords
        self.use_bigrams = use_bigrams
        self.min_word_length = min_word_length
        self.max_word_length = max_word_length
        
        # Initialize stemmer and lemmatizer
        self.stemmer = PorterStemmer() if use_stemming else None
        self.lemmatizer = WordNetLemmatizer() if use_lemmatization else None
        
        # Initialize stopwords
        self.stop_words = set(stopwords.words('english'))
        
        # Add startup-related stopwords
        startup_stopwords = {
            'startup', 'company', 'platform', 'service', 'app', 'application',
            'software', 'technology', 'tech', 'solution', 'business', 'model',
            'help', 'enable', 'provide', 'offer', 'build', 'create', 'make',
            'user', 'users', 'customer', 'customers', 'client', 'clients',
            'want', 'need', 'use', 'using', 'used', 'new', 'also', 'one',
            'way', 'make', 'helps', 'helped', 'helping', 'allows', 'let',
            'lets', 'allows', 'allowing', 'designed', 'built', 'built-in',
            'world', 'world\'s', 'leading', 'top', 'best', 'first', 'only',
        }
        self.stop_words.update(startup_stopwords)
        
        # Add custom stopwords
        if custom_stopwords:
            self.stop_words.update(custom_stopwords)
        
        # TF-IDF vectorizer (initialized later)
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.vocabulary: Optional[Dict[str, int]] = None
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\b[\d\+\-\(\)]{7,}\b', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Simple whitespace tokenization
        tokens = text.split()
        
        # Filter by length
        tokens = [
            t for t in tokens 
            if self.min_word_length <= len(t) <= self.max_word_length
        ]
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords from token list.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Filtered tokens
        """
        if not self.use_stopwords:
            return tokens
        
        return [t for t in tokens if t.lower() not in self.stop_words]
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming to tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Stemmed tokens
        """
        if not self.stemmer:
            return tokens
        
        return [self.stemmer.stem(t) for t in tokens]
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply lemmatization to tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Lemmatized tokens
        """
        if not self.lemmatizer:
            return tokens
        
        return [self.lemmatizer.lemmatize(t) for t in tokens]
    
    def extract_ngrams(
        self,
        tokens: List[str],
        n: int = 2
    ) -> List[str]:
        """
        Extract n-grams from tokens.
        
        Args:
            tokens: List of tokens
            n: N-gram size
            
        Returns:
            List of n-grams
        """
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    def extract_keywords(
        self,
        tokens: List[str],
        top_n: int = 10
    ) -> List[str]:
        """
        Extract top keywords by frequency.
        
        Args:
            tokens: List of tokens
            top_n: Number of keywords to return
            
        Returns:
            List of top keywords
        """
        if not tokens:
            return []
        
        # Count frequency
        freq = Counter(tokens)
        
        # Return top N
        return [kw for kw, _ in freq.most_common(top_n)]
    
    def extract_noun_phrases(self, text: str) -> List[str]:
        """
        Extract noun phrases from text.
        
        Args:
            text: Input text
            
        Returns:
            List of noun phrases
        """
        try:
            import spacy
            
            # Try to use spaCy if available
            try:
                nlp = spacy.load('en_core_web_sm')
                doc = nlp(text)
                noun_phrases = [chunk.text for chunk in doc.noun_chunks]
                return noun_phrases
            except OSError:
                # spaCy model not installed, fallback
                pass
        except ImportError:
            pass
        
        # Simple pattern-based extraction
        patterns = [
            r'\b[A-Z][a-z]+\s+(?:of\s+)?[A-Z][a-z]+\b',  # Capitalized phrases
            r'\b(?:the\s+)?(?:AI|API|SaaS|ML|IoT|API)\b',  # Tech acronyms
        ]
        
        phrases = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        return list(set(phrases))
    
    def process(self, text: str) -> ProcessedText:
        """
        Full text processing pipeline.
        
        Args:
            text: Input text
            
        Returns:
            ProcessedText with all components
        """
        # Clean text
        cleaned = self.clean_text(text)
        
        # Tokenize
        tokens = self.tokenize(cleaned)
        
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Apply stemming/lemmatization
        if self.use_lemmatization:
            processed_tokens = self.lemmatize_tokens(tokens)
        elif self.use_stemming:
            processed_tokens = self.stem_tokens(tokens)
        else:
            processed_tokens = tokens
        
        # Extract n-grams
        bigrams = self.extract_ngrams(tokens, 2) if self.use_bigrams else []
        trigrams = self.extract_ngrams(tokens, 3) if self.use_bigrams else []
        
        # Extract keywords
        keywords = self.extract_keywords(processed_tokens)
        
        # Extract noun phrases
        noun_phrases = self.extract_noun_phrases(text)
        
        # Calculate metrics
        word_count = len(tokens)
        vocabulary_size = len(set(tokens))
        
        return ProcessedText(
            original=text,
            cleaned=cleaned,
            tokens=tokens,
            stemmed=self.stem_tokens(tokens) if self.stemmer else [],
            lemmatized=self.lemmatize_tokens(tokens) if self.lemmatizer else [],
            keywords=keywords,
            bigrams=bigrams,
            trigrams=trigrams,
            noun_phrases=noun_phrases,
            word_count=word_count,
            vocabulary_size=vocabulary_size,
        )
    
    def create_tfidf_vectorizer(
        self,
        texts: List[str],
        max_features: int = 5000,
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 1,
        max_df: float = 0.95,
    ) -> TfidfVectorizer:
        """
        Create and fit TF-IDF vectorizer on corpus.
        
        Args:
            texts: List of documents
            max_features: Maximum vocabulary size
            ngram_range: Range of n-grams to include
            min_df: Minimum document frequency
            max_df: Maximum document frequency
            
        Returns:
            Fitted TfidfVectorizer
        """
        # Clean all texts
        cleaned_texts = [self.clean_text(t) for t in texts]
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            stop_words='english',
            lowercase=True,
        )
        
        self.vocabulary = self.vectorizer.fit(cleaned_texts)
        logger.info(f"Created TF-IDF vectorizer with {len(self.vectorizer.vocabulary_)} features")
        
        return self.vectorizer
    
    def transform_text(self, text: str) -> np.ndarray:
        """
        Transform single text to TF-IDF vector.
        
        Args:
            text: Input text
            
        Returns:
            TF-IDF vector as numpy array
        """
        if not self.vectorizer:
            raise ValueError("Vectorizer not fitted. Call create_tfidf_vectorizer first.")
        
        cleaned = self.clean_text(text)
        return self.vectorizer.transform([cleaned]).toarray()
    
    def transform_batch(self, texts: List[str]) -> np.ndarray:
        """
        Transform multiple texts to TF-IDF vectors.
        
        Args:
            texts: List of input texts
            
        Returns:
            TF-IDF matrix
        """
        if not self.vectorizer:
            raise ValueError("Vectorizer not fitted. Call create_tfidf_vectorizer first.")
        
        cleaned_texts = [self.clean_text(t) for t in texts]
        return self.vectorizer.transform(cleaned_texts).toarray()
    
    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        method: str = 'tfidf'
    ) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            method: Similarity method ('tfidf', 'jaccard', 'word_overlap')
            
        Returns:
            Similarity score (0-1)
        """
        if method == 'tfidf':
            return self._tfidf_similarity(text1, text2)
        elif method == 'jaccard':
            return self._jaccard_similarity(text1, text2)
        elif method == 'word_overlap':
            return self._word_overlap_similarity(text1, text2)
        else:
            raise ValueError(f"Unknown similarity method: {method}")
    
    def _tfidf_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF based cosine similarity"""
        if not self.vectorizer:
            # Create vectorizer on-the-fly for two texts
            self.create_tfidf_vectorizer([text1, text2])
        
        try:
            vec1 = self.transform_text(text1)
            vec2 = self.transform_text(text2)
            
            score = sklearn_cosine_similarity(vec1, vec2)[0][0]
            return float(score)
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {str(e)}")
            return self._word_overlap_similarity(text1, text2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity"""
        proc1 = self.process(text1)
        proc2 = self.process(text2)
        
        set1 = set(proc1.tokens)
        set2 = set(proc2.tokens)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _word_overlap_similarity(self, text1: str, text2: str) -> float:
        """Calculate word overlap similarity"""
        proc1 = self.process(text1)
        proc2 = self.process(text2)
        
        set1 = set(proc1.keywords)
        set2 = set(proc2.keywords)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        min_size = min(len(set1), len(set2))
        
        return intersection / min_size if min_size > 0 else 0.0


def clean_text(text: str) -> str:
    """
    Convenience function to clean text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    processor = TextProcessor()
    return processor.clean_text(text)


def create_text_processor(**kwargs) -> TextProcessor:
    """
    Factory function to create TextProcessor.
    
    Args:
        **kwargs: Processor configuration
        
    Returns:
        TextProcessor instance
    """
    return TextProcessor(**kwargs)

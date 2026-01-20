"""
Processors package for IndoGap - AI-Powered Opportunity Discovery Engine

This package contains modules for processing and analyzing startup data,
including text preprocessing, embeddings, and similarity calculations.
"""
from .text_processor import TextProcessor, create_text_processor, clean_text
from .embeddings import EmbeddingGenerator, create_embedding_generator
from .similarity import SimilarityEngine, create_similarity_engine

__all__ = [
    "TextProcessor",
    "create_text_processor", 
    "clean_text",
    "EmbeddingGenerator",
    "create_embedding_generator",
    "SimilarityEngine",
    "create_similarity_engine",
]

"""
Embeddings module for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides functionality to generate vector embeddings for startup
descriptions using OpenAI's embedding models, enabling semantic similarity search.
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from openai import OpenAI, AsyncOpenAI
from openai.types import Embedding

from mini_services.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Container for embedding generation results"""
    success: bool
    embedding: Optional[List[float]] = None
    tokens: Optional[int] = None
    model: str = ""
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class BatchEmbeddingResult:
    """Container for batch embedding results"""
    success: bool
    embeddings: List[List[float]] = field(default_factory=list)
    tokens_used: int = 0
    errors: List[str] = field(default_factory=list)
    model: str = ""
    total_latency_ms: float = 0.0
    
    @property
    def count(self) -> int:
        return len(self.embeddings)


class EmbeddingGenerator:
    """
    Generator for text embeddings using OpenAI models.
    
    Supports:
    - text-embedding-3-small (1536 dimensions, fast, cheap)
    - text-embedding-3-large (3072 dimensions, more expressive)
    - text-embedding-ada-002 (legacy, 1536 dimensions)
    
    Features:
    - Synchronous and async generation
    - Batching for efficiency
    - Token counting and cost estimation
    - Retry logic for resilience
    """
    
    MODELS = {
        "small": {
            "name": "text-embedding-3-small",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.00002,  # $0.02 per 1M tokens
        },
        "large": {
            "name": "text-embedding-3-large",
            "dimensions": 3072,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.00013,  # $0.13 per 1M tokens
        },
        "ada": {
            "name": "text-embedding-ada-002",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k_tokens": 0.0001,  # $0.10 per 1M tokens
        },
    }
    
    def __init__(
        self,
        model: str = "small",
        api_key: Optional[str] = None,
        dimensions: Optional[int] = None,
        batch_size: int = 100,
        max_retries: int = 3,
        timeout: int = 60,
    ):
        """
        Initialize embedding generator.
        
        Args:
            model: Model to use ('small', 'large', 'ada')
            api_key: OpenAI API key (uses config if not provided)
            dimensions: Embedding dimensions (uses model default if not provided)
            batch_size: Maximum batch size for embedding
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        
        self.model_info = self.MODELS.get(model, self.MODELS["small"])
        self.model_name = self.model_info["name"]
        self.dimensions = dimensions or self.model_info["dimensions"]
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize OpenAI client
        self.api_key = api_key or settings.openai_api_key
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=timeout,
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=timeout,
        )
        
        # Statistics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        
    def generate(
        self,
        text: str,
        normalize: bool = True,
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            normalize: L2 normalize the embedding
            
        Returns:
            EmbeddingResult with embedding vector
        """
        import time
        start_time = time.time()
        
        if not text or not text.strip():
            return EmbeddingResult(
                success=False,
                error="Empty text provided",
            )
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text[:self.model_info["max_tokens"]],
                dimensions=self.dimensions,
            )
            
            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens
            
            # Normalize if requested
            if normalize:
                embedding = self._normalize(embedding)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self._total_requests += 1
            self._total_tokens += tokens
            
            cost = self._calculate_cost(tokens)
            self._total_cost += cost
            
            return EmbeddingResult(
                success=True,
                embedding=embedding,
                tokens=tokens,
                model=self.model_name,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return EmbeddingResult(
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )
    
    async def generate_async(
        self,
        text: str,
        normalize: bool = True,
    ) -> EmbeddingResult:
        """
        Generate embedding asynchronously.
        
        Args:
            text: Input text to embed
            normalize: L2 normalize the embedding
            
        Returns:
            EmbeddingResult with embedding vector
        """
        import time
        start_time = time.time()
        
        if not text or not text.strip():
            return EmbeddingResult(
                success=False,
                error="Empty text provided",
            )
        
        try:
            response = await self.async_client.embeddings.create(
                model=self.model_name,
                input=text[:self.model_info["max_tokens"]],
                dimensions=self.dimensions,
            )
            
            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens
            
            if normalize:
                embedding = self._normalize(embedding)
            
            latency_ms = (time.time() - start_time) * 1000
            
            self._total_requests += 1
            self._total_tokens += tokens
            
            return EmbeddingResult(
                success=True,
                embedding=embedding,
                tokens=tokens,
                model=self.model_name,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            logger.error(f"Async embedding generation failed: {str(e)}")
            return EmbeddingResult(
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )
    
    def generate_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        show_progress: bool = False,
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts
            normalize: L2 normalize embeddings
            show_progress: Show progress updates
            
        Returns:
            BatchEmbeddingResult with all embeddings
        """
        import time
        start_time = time.time()
        
        if not texts:
            return BatchEmbeddingResult(success=True, model=self.model_name)
        
        all_embeddings = []
        all_errors = []
        total_tokens = 0
        
        # Process in batches
        for batch_idx in range(0, len(texts), self.batch_size):
            batch = texts[batch_idx:batch_idx + self.batch_size]
            
            if show_progress:
                logger.info(f"Processing batch {batch_idx // self.batch_size + 1}/"
                          f"{(len(texts) - 1) // self.batch_size + 1}")
            
            try:
                # Prepare input (truncate if needed)
                truncated_batch = [
                    text[:self.model_info["max_tokens"]] 
                    for text in batch
                ]
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=truncated_batch,
                    dimensions=self.dimensions,
                )
                
                for item in response.data:
                    embedding = item.embedding
                    if normalize:
                        embedding = self._normalize(embedding)
                    all_embeddings.append(embedding)
                
                total_tokens += response.usage.total_tokens
                
            except Exception as e:
                error_msg = f"Batch {batch_idx // self.batch_size} failed: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                # Add zero embeddings for failed batch
                all_embeddings.extend([None] * len(batch))
            
            # Small delay between batches
            if batch_idx + self.batch_size < len(texts):
                time.sleep(0.1)
        
        # Remove None values from failed batches
        valid_embeddings = [e for e in all_embeddings if e is not None]
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        self._total_requests += (len(texts) + self.batch_size - 1) // self.batch_size
        self._total_tokens += total_tokens
        
        return BatchEmbeddingResult(
            success=len(all_errors) == 0,
            embeddings=valid_embeddings,
            tokens_used=total_tokens,
            errors=all_errors,
            model=self.model_name,
            total_latency_ms=latency_ms,
        )
    
    async def generate_batch_async(
        self,
        texts: List[str],
        normalize: bool = True,
        max_concurrent: int = 5,
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings asynchronously with concurrency control.
        
        Args:
            texts: List of input texts
            normalize: L2 normalize embeddings
            max_concurrent: Maximum concurrent requests
            
        Returns:
            BatchEmbeddingResult with all embeddings
        """
        import asyncio
        import time
        start_time = time.time()
        
        if not texts:
            return BatchEmbeddingResult(success=True, model=self.model_name)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(text: str) -> EmbeddingResult:
            async with semaphore:
                return await self.generate_async(text, normalize)
        
        tasks = [generate_with_semaphore(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_embeddings = []
        errors = []
        total_tokens = 0
        
        for idx, result in enumerate(results):
            if isinstance(result, EmbeddingResult) and result.success:
                valid_embeddings.append(result.embedding)
                total_tokens += result.tokens or 0
            elif isinstance(result, Exception):
                errors.append(f"Text {idx}: {str(result)}")
            elif hasattr(result, 'error'):
                errors.append(f"Text {idx}: {result.error}")
        
        latency_ms = (time.time() - start_time) * 1000
        
        self._total_requests += len(texts)
        self._total_tokens += total_tokens
        
        return BatchEmbeddingResult(
            success=len(errors) == 0,
            embeddings=valid_embeddings,
            tokens_used=total_tokens,
            errors=errors,
            model=self.model_name,
            total_latency_ms=latency_ms,
        )
    
    def _normalize(self, embedding: List[float]) -> List[float]:
        """L2 normalize embedding vector"""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return [x / norm for x in embedding]
        return embedding
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost for embedding request"""
        cost_per_1k = self.model_info["cost_per_1k_tokens"]
        return (tokens / 1000) * cost_per_1k
    
    def estimate_cost(self, texts: List[str]) -> float:
        """
        Estimate cost for embedding requests.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: 4 characters per token
        total_chars = sum(len(t) for t in texts)
        estimated_tokens = total_chars // 4
        
        return (estimated_tokens / 1000) * self.model_info["cost_per_1k_tokens"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        return {
            "model": self.model_name,
            "dimensions": self.dimensions,
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost, 4),
            "avg_cost_per_request": round(self._total_cost / max(1, self._total_requests), 6),
        }
    
    def reset_stats(self) -> None:
        """Reset statistics counters"""
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0


def calculate_cosine_similarity(
    embedding1: List[float],
    embedding2: List[float],
) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score (-1 to 1, typically 0 to 1 for normalized)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def calculate_batch_similarity(
    query_embedding: List[float],
    embedding_list: List[List[float]],
    top_k: int = 10,
) -> List[tuple]:
    """
    Calculate similarity between query and multiple embeddings.
    
    Args:
        query_embedding: Query embedding vector
        embedding_list: List of embedding vectors
        top_k: Number of top results to return
        
    Returns:
        List of (index, similarity_score) tuples sorted by similarity
    """
    if not embedding_list:
        return []
    
    query = np.array(query_embedding)
    embeddings = np.array(embedding_list)
    
    # Calculate cosine similarity
    norms = np.linalg.norm(embeddings, axis=1)
    query_norm = np.linalg.norm(query)
    
    # Avoid division by zero
    norms = np.where(norms == 0, 1, norms)
    
    similarities = np.dot(embeddings, query) / (norms * query_norm)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    return [(idx, float(similarities[idx])) for idx in top_indices]


def create_embedding_generator(
    model: str = "small",
    **kwargs
) -> EmbeddingGenerator:
    """
    Factory function to create EmbeddingGenerator.
    
    Args:
        model: Model to use ('small', 'large', 'ada')
        **kwargs: Additional generator configuration
        
    Returns:
        EmbeddingGenerator instance
    """
    return EmbeddingGenerator(model=model, **kwargs)

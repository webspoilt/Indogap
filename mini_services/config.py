"""
Configuration settings for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides centralized configuration management using Pydantic Settings,
supporting environment variables, .env files, and default values for all components.
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Centralized configuration for the opportunity discovery engine.
    
    Supports:
    - Environment variables
    - .env file configuration
    - Default values for all settings
    - Validation of configuration values
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="INDOGAP_"
    )
    
    # Application Information
    app_name: str = Field(default="IndoGap", description="Application name")
    app_env: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    version: str = Field(default="0.1.0", description="Application version")
    
    # API Keys (Required for full functionality)
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings and GPT-4")
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    product_hunt_api_key: str = Field(default="", description="Product Hunt API key")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/indogap",
        description="PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=10, description="Connection pool size")
    database_max_overflow: int = Field(default=20, description="Max overflow connections")
    
    # Vector Database Configuration
    pgvector_connection: str = Field(
        default="",
        description="pgvector connection string for embeddings"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use"
    )
    embedding_dimensions: int = Field(
        default=1536,
        description="Embedding vector dimensions"
    )
    
    # Redis Configuration (for caching and task queue)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Scraping Configuration
    yc_scrape_delay: float = Field(
        default=1.0,
        description="Delay between YC scrapes (seconds)"
    )
    product_hunt_scrape_delay: float = Field(
        default=2.0,
        description="delay between Product Hunt scrapes (seconds)"
    )
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout (seconds)"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests"
    )
    retry_delay: float = Field(
        default=1.0,
        description="Base delay between retries (seconds)"
    )
    
    # User-Agent for scraping
    user_agent: str = Field(
        default="IndoGap-Bot/1.0 (research project; contact@example.com)",
        description="User-Agent header for HTTP requests"
    )
    
    # Scoring Configuration
    scoring_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "cultural_fit": 0.15,
            "logistics": 0.15,
            "payment_readiness": 0.15,
            "timing": 0.15,
            "monopoly_potential": 0.10,
            "regulatory_risk": 0.15,
            "execution_feasibility": 0.15
        },
        description="Weights for 7-dimension scoring"
    )
    
    # Similarity Thresholds
    similarity_threshold_high: float = Field(
        default=0.7,
        description="Above this = saturated market"
    )
    similarity_threshold_low: float = Field(
        default=0.3,
        description="Below this = potential gap"
    )
    min_score_threshold: float = Field(
        default=0.5,
        description="Minimum overall score to be considered"
    )
    
    # Scoring Model
    scoring_model: str = Field(
        default="gpt-4o",
        description="OpenAI model for scoring"
    )
    scoring_temperature: float = Field(
        default=0.3,
        description="Temperature for scoring LLM calls"
    )
    max_tokens_scoring: int = Field(
        default=2000,
        description="Max tokens for scoring responses"
    )
    
    # MVP Generation Configuration
    mvp_model: str = Field(
        default="gpt-4o",
        description="OpenAI model for MVP generation"
    )
    mvp_temperature: float = Field(
        default=0.7,
        description="Temperature for MVP generation"
    )
    max_tokens_mvp: int = Field(
        default=4000,
        description="Max tokens for MVP generation"
    )
    
    # File Paths
    data_dir: Path = Field(
        default=Path(__file__).parent.parent / "data",
        description="Directory for data files"
    )
    output_dir: Path = Field(
        default=Path(__file__).parent.parent / "output",
        description="Directory for output files"
    )
    cache_dir: Path = Field(
        default=Path(__file__).parent.parent / "cache",
        description="Directory for cached data"
    )
    indian_startups_file: str = Field(
        default="indian_startups.csv",
        description="Default Indian startups database file"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR)"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Max requests per minute"
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )
    
    # Feature Flags
    enable_vector_search: bool = Field(
        default=False,
        description="Enable vector embedding search (requires pgvector)"
    )
    enable_gpt4_scoring: bool = Field(
        default=False,
        description="Enable GPT-4 scoring (requires API key)"
    )
    enable_mvp_generation: bool = Field(
        default=False,
        description="Enable MVP generation (requires API key)"
    )
    enable_background_tasks: bool = Field(
        default=False,
        description="Enable background task processing"
    )
    
    # API Server Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    api_workers: int = Field(
        default=1,
        description="Number of API workers"
    )
    
    @field_validator('app_env')
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment"""
        allowed = ['development', 'staging', 'production', 'test']
        if v.lower() not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got: {v}")
        return v.lower()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got: {v}")
        return v.upper()
    
    @field_validator('scoring_weights')
    @classmethod
    def validate_scoring_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate that scoring weights sum to 1.0"""
        if not v:
            return v
        
        total = sum(v.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scoring weights must sum to 1.0, got: {total}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    @property
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.openai_api_key and len(self.openai_api_key) > 10)
    
    @property
    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured"""
        return bool(self.anthropic_api_key and len(self.anthropic_api_key) > 10)
    
    @property
    def has_vector_db(self) -> bool:
        """Check if vector database is configured"""
        return bool(self.pgvector_connection and len(self.pgvector_connection) > 10)
    
    def get_scoring_weight(self, dimension: str) -> float:
        """Get weight for a specific scoring dimension"""
        return self.scoring_weights.get(dimension, 0.1)
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for dir_path in [self.data_dir, self.output_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function should be used throughout the application
    to ensure consistent configuration.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()


def create_settings(**overrides: Any) -> Settings:
    """
    Create settings with overrides.
    
    Useful for testing or dynamic configuration.
    
    Args:
        **overrides: Key-value pairs to override default settings
        
    Returns:
        Settings: New settings instance with overrides
    """
    return Settings(**overrides)

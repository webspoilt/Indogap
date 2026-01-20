"""
Local LLM Services for IndoGap

Provides access to local AI models via Ollama,
optimized for consumer hardware (16GB RAM, 4GB VRAM).

Models:
- llama3.2:3b - Fast, lightweight classification
- llama3.1:8b - Complex reasoning and analysis
- deepseek-coder:6.7b - Code generation and technical specs

Also includes fallback support for free cloud APIs:
- Groq (free tier, very fast)
- HuggingFace Inference API (free tier)
"""
from .ollama_client import (
    OllamaClient,
    OllamaConfig,
    LLMResponse,
    ModelType,
    get_ollama_client,
    create_ollama_client,
)
from .free_api import (
    FreeAPIClient,
    FreeAPIConfig,
    FreeAPIMode,
    get_free_api_client,
)

__all__ = [
    # Ollama (local)
    "OllamaClient",
    "OllamaConfig", 
    "LLMResponse",
    "ModelType",
    "get_ollama_client",
    "create_ollama_client",
    # Free API fallbacks
    "FreeAPIClient",
    "FreeAPIConfig",
    "FreeAPIMode",
    "get_free_api_client",
]

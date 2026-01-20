"""
Ollama Local LLM Service for IndoGap

This module provides a unified interface to local AI models via Ollama,
optimized for 16GB RAM and 4GB VRAM laptops.

Models:
- llama3.2:3b - Fast classification and simple tasks
- llama3.1:8b - Reasoning and analysis
- deepseek-coder:6.7b - Code generation and technical specs
"""
import json
import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model types for different tasks"""
    FAST = "llama3.2:3b"  # Classification, simple queries
    REASONING = "llama3.1:8b"  # Analysis, scoring
    CODING = "deepseek-coder:6.7b"  # Code generation, specs


@dataclass
class LLMResponse:
    """Response from local LLM"""
    text: str
    model: str
    tokens_used: int
    processing_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class OllamaConfig:
    """Configuration for Ollama service"""
    host: str = "http://localhost:11434"
    timeout: int = 120  # seconds
    keep_alive: int = 0  # 0 = unload immediately after use (memory optimization)
    num_predict: int = 1024  # Max tokens to generate
    temperature: float = 0.3  # Lower = more consistent
    num_ctx: int = 2048  # Context window (smaller = less memory)


class OllamaClient:
    """
    Client for interacting with local Ollama models.
    
    Implements smart model selection based on task complexity
    and memory optimization for consumer hardware.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.base_url = self.config.host
        self._current_model: Optional[str] = None
        
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(
                urljoin(self.base_url, "/api/tags"),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(
                urljoin(self.base_url, "/api/tags"),
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: ModelType = ModelType.FAST,
        system_prompt: Optional[str] = None,
        verbose: bool = False
    ) -> LLMResponse:
        """
        Generate response using specified model.
        
        Args:
            prompt: User prompt
            model: Model type to use
            system_prompt: Optional system instruction
            verbose: Print timing info
            
        Returns:
            LLMResponse with generated text
        """
        start_time = time.time()
        model_name = model.value
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": self.config.num_predict,
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,
                "keep_alive": self.config.keep_alive,  # Critical for memory!
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                urljoin(self.base_url, "/api/generate"),
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                processing_time = time.time() - start_time
                
                if verbose:
                    logger.info(f"Model: {model_name}, "
                              f"Tokens: {data.get('eval_count', '?')}, "
                              f"Time: {processing_time:.2f}s")
                
                return LLMResponse(
                    text=data.get("response", "").strip(),
                    model=model_name,
                    tokens_used=data.get("eval_count", 0),
                    processing_time=processing_time,
                    success=True
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                return LLMResponse(
                    text="",
                    model=model_name,
                    tokens_used=0,
                    processing_time=time.time() - start_time,
                    success=False,
                    error=error_msg
                )
                
        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {self.config.timeout}s"
            logger.error(error_msg)
            return LLMResponse(
                text="",
                model=model_name,
                tokens_used=0,
                processing_time=time.time() - start_time,
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM generation failed: {error_msg}")
            return LLMResponse(
                text="",
                model=model_name,
                tokens_used=0,
                processing_time=time.time() - start_time,
                success=False,
                error=error_msg
            )
    
    # Convenience methods for different task types
    
    def classify(self, text: str, categories: List[str]) -> str:
        """Fast classification using lightweight model"""
        prompt = f"""Classify the following text into ONE of these categories:
{categories}

Text: {text}

Respond with ONLY the category name."""
        
        response = self.generate(prompt, ModelType.FAST)
        return response.text if response.success else categories[0]
    
    def analyze_opportunity(
        self,
        startup_name: str,
        description: str,
        tags: List[str],
        indian_competitors: str
    ) -> Dict[str, Any]:
        """
        Analyze a startup opportunity for the Indian market.
        Uses reasoning model for deeper analysis.
        """
        prompt = f"""Analyze this startup for the Indian market:

Startup: {startup_name}
Description: {description}
Tags: {', '.join(tags)}

Indian Market Context:
{indian_competitors}

Provide a JSON analysis with:
1. gap_score (0-1, where 1 = large gap)
2. cultural_fit (1-10)
3. market_timing (1-10)
4. execution_difficulty (1-10)
5. recommendation (short text)
6. key_insights (bullet points)

Format as valid JSON only."""
        
        response = self.generate(prompt, ModelType.REASONING)
        
        if response.success:
            try:
                # Try to parse as JSON
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response.text)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
        
        # Fallback
        return {
            "gap_score": 0.5,
            "cultural_fit": 5,
            "market_timing": 5,
            "execution_difficulty": 5,
            "recommendation": "Manual review needed",
            "key_insights": ["Analysis failed, manual review required"]
        }
    
    def generate_mvp_spec(
        self,
        startup_name: str,
        description: str,
        gap_score: float
    ) -> str:
        """
        Generate MVP specification and technical stack.
        Uses coding model for technical details.
        """
        prompt = f"""Generate a detailed MVP specification for:

Startup: {startup_name}
Description: {description}
Gap Score: {gap_score:.2f}

Include:
1. Product Description
2. Target Users
3. Core Features (MVP scope)
4. Technical Stack with specific technologies
5. Implementation Timeline
6. Key Challenges and Solutions

Format as a comprehensive markdown document."""
        
        response = self.generate(prompt, ModelType.CODING)
        return response.text if response.success else "MVP generation failed"


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create global Ollama client"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def create_ollama_client(**kwargs) -> OllamaClient:
    """Factory function to create Ollama client"""
    return OllamaClient(OllamaConfig(**kwargs))

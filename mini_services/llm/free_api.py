"""
Free API Fallback System for IndoGap

Provides backup access to free AI APIs when local models are unavailable.
Uses HuggingFace Inference API (free tier) and other free services.
"""
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FreeAPIMode(Enum):
    """Available free API modes"""
    LOCAL_OLLAMA = "local_ollama"
    HUGGINGFACE = "huggingface"
    GROQ = "groq"  # Requires free API key
    LOCAL_FALLBACK = "local_fallback"


@dataclass
class FreeAPIConfig:
    """Configuration for free API access"""
    # Primary mode
    primary_mode: str = "local_ollama"
    
    # HuggingFace (free tier)
    hf_token: Optional[str] = None
    hf_api_url: str = "https://api-inference.huggingface.co/models/"
    
    # Groq (free tier - requires signup)
    groq_api_key: Optional[str] = None
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    
    # Fallback settings
    max_retries: int = 2
    timeout: int = 60


class FreeAPIClient:
    """
    Unified client for free AI API access.
    
    Priority order:
    1. Local Ollama (free, fast, private)
    2. HuggingFace Inference API (free tier, rate limited)
    3. Groq (free tier, fast, requires API key)
    """
    
    def __init__(self, config: Optional[FreeAPIConfig] = None):
        self.config = config or FreeAPIConfig()
        self._ollama = None  # Lazy load
        
    @property
    def ollama(self):
        """Lazy load Ollama client"""
        if self._ollama is None:
            try:
                from .ollama_client import get_ollama_client, OllamaClient
                self._ollama = get_ollama_client()
            except ImportError:
                self._ollama = None
        return self._ollama
    
    def is_available(self, mode: str) -> bool:
        """Check if a specific API mode is available"""
        if mode == FreeAPIMode.LOCAL_OLLAMA.value:
            return self.ollama is not None and self.ollama.is_available()
        elif mode == FreeAPIMode.HUGGINGFACE.value:
            return self.config.hf_token is not None
        elif mode == FreeAPIMode.GROQ.value:
            return self.config.groq_api_key is not None
        return False
    
    def get_best_available_mode(self) -> str:
        """Get the best available API mode"""
        if self.ollama and self.ollama.is_available():
            return FreeAPIMode.LOCAL_OLLAMA.value
        
        # Groq is faster than HuggingFace, check it first
        if self.config.groq_api_key:
            return FreeAPIMode.GROQ.value
        
        if self.config.hf_token:
            return FreeAPIMode.HUGGINGFACE.value
            
        return FreeAPIMode.LOCAL_FALLBACK.value
    
    def generate(
        self,
        prompt: str,
        model_preference: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using best available API.
        
        Returns:
            Dict with keys: text, model, tokens_used, success, error, mode_used
        """
        # Try in order of preference
        modes_to_try = []
        
        if model_preference:
            modes_to_try.append(model_preference)
        
        # Add fallback modes
        modes_to_try.extend([
            FreeAPIMode.LOCAL_OLLAMA.value,
            FreeAPIMode.HUGGINGFACE.value,
            FreeAPIMode.GROQ.value
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        modes_to_try = [x for x in modes_to_try if not (x in seen or seen.add(x))]
        
        for mode in modes_to_try:
            try:
                if mode == FreeAPIMode.LOCAL_OLLAMA.value:
                    result = self._generate_ollama(prompt, system_prompt)
                    if result["success"]:
                        result["mode_used"] = "local_ollama"
                        return result
                        
                elif mode == FreeAPIMode.HUGGINGFACE.value:
                    result = self._generate_huggingface(prompt, system_prompt)
                    if result["success"]:
                        result["mode_used"] = "huggingface"
                        return result
                        
                elif mode == FreeAPIMode.GROQ.value:
                    result = self._generate_groq(prompt, system_prompt)
                    if result["success"]:
                        result["mode_used"] = "groq"
                        return result
                        
            except Exception as e:
                logger.warning(f"Mode {mode} failed: {e}")
                continue
        
        # All modes failed
        return {
            "text": "",
            "model": "none",
            "tokens_used": 0,
            "success": False,
            "error": "All API modes unavailable",
            "mode_used": None
        }
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate using local Ollama"""
        if not self.ollama:
            return {"success": False, "error": "Ollama not available"}
        
        response = self.ollama.generate(prompt, system_prompt=system_prompt)
        
        return {
            "text": response.text,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "success": response.success,
            "error": response.error,
            "mode_used": "local_ollama"
        }
    
    def _generate_huggingface(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate using HuggingFace Inference API (free tier)"""
        import requests
        
        if not self.config.hf_token:
            return {"success": False, "error": "HuggingFace token not configured"}
        
        # Use a small, fast model for free tier
        model = "microsoft/Phi-3-mini-4k-instruct"
        
        headers = {"Authorization": f"Bearer {self.config.hf_token}"}
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.3,
                "do_sample": False
            }
        }
        
        try:
            response = requests.post(
                f"{self.config.hf_api_url}{model}",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    text = data[0].get("generated_text", "")
                else:
                    text = str(data)
                    
                return {
                    "text": text,
                    "model": model,
                    "tokens_used": len(text.split()),
                    "success": True,
                    "error": None,
                    "mode_used": "huggingface"
                }
            elif response.status_code == 503:
                return {"success": False, "error": "Model loading, try again later"}
            else:
                return {"success": False, "error": f"HF API error: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate using Groq (free tier, very fast)"""
        import requests
        
        if not self.config.groq_api_key:
            return {"success": False, "error": "Groq API key not configured"}
        
        model = "llama3-8b-8192"  # Free tier model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(
                self.config.groq_api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                
                return {
                    "text": message.get("content", ""),
                    "model": model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "success": True,
                    "error": None,
                    "mode_used": "groq"
                }
            else:
                return {"success": False, "error": f"Groq error: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global client instance
_free_api_client: Optional[FreeAPIClient] = None


def get_free_api_client() -> FreeAPIClient:
    """Get or create global free API client"""
    global _free_api_client
    if _free_api_client is None:
        _free_api_client = FreeAPIClient()
    return _free_api_client

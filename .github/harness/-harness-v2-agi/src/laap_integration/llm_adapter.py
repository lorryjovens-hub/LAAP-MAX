"""
LLM Adapter: Bridge between Harness-v2-agi's LLMClient and LAAP's LLMFactory

LAAP's LLMFactory provides:
- Multi-provider support (20+ providers)
- Auto-detection of API keys
- Built-in fallback mechanism
- Vision support
- Tool calling support

This adapter maps Harness-v2-agi's LLMClient interface to LAAP's LLMFactory
while maintaining the original API signature.
"""

import asyncio
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from laap.llm.factory import factory as laap_llm_factory
from laap.llm.provider import Message
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LAAPLLMClient:
    """
    LAAP-powered LLM Client for Harness-v2-agi
    
    Adapts laap.llm.factory.LLMFactory to match the original LLMClient interface
    while leveraging LAAP's multi-provider support, auto-detection, and fallbacks.
    """

    def __init__(self):
        self.settings = get_settings()
        self._fallback_providers = ["openai", "anthropic", "google"]
        self._model_routes = {
            "perception": ["openai", "anthropic"],
            "reasoning": ["anthropic", "openai"],
            "execution": ["openai", "anthropic"],
            "refinement": ["anthropic", "openai"],
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stage: str = "execution",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """
        Unified chat completion with LAAP's multi-provider routing.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stage: Pipeline stage for model routing
            temperature: Creativity temperature
            max_tokens: Maximum output tokens
            json_mode: Force JSON output
        """
        providers = self._model_routes.get(stage, self._model_routes["execution"])
        
        laap_messages = self._convert_messages(messages)
        
        system_prompt = ""
        user_messages = []
        for msg in laap_messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                user_messages.append(msg)
        
        if json_mode:
            system_prompt += "\n\n你必须以有效的 JSON 格式响应，不要包含任何其他文本。"
        
        last_error = None
        for provider in providers:
            try:
                if provider not in laap_llm_factory.available:
                    continue
                
                llm = laap_llm_factory.get(provider)
                llm.temperature = temperature
                llm.max_tokens = max_tokens
                
                result = await asyncio.to_thread(
                    llm.chat, user_messages, system=system_prompt
                )
                
                content = result.content if hasattr(result, 'content') else str(result)
                
                if json_mode and not content.strip().startswith("{"):
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                
                return content
            
            except Exception as e:
                logger.warning(f"LAAP LLM {provider} failed: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"All LAAP providers failed: {last_error}")

    async def vision_completion(
        self,
        image_path: Union[str, Path],
        prompt: str,
        stage: str = "perception",
        detail: str = "high",
    ) -> str:
        """
        Visual understanding using LAAP's vision-capable models.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            stage: Perception stage
            detail: Detail level (low/high/auto)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        providers = self._model_routes.get(stage, ["openai", "anthropic"])
        
        last_error = None
        for provider in providers:
            try:
                if provider not in laap_llm_factory.available:
                    continue
                
                llm = laap_llm_factory.get(provider)
                
                result = await asyncio.to_thread(
                    llm.chat,
                    [Message(role="user", content=prompt)],
                    images=[image_data],
                )
                
                return result.content if hasattr(result, 'content') else str(result)
            
            except Exception as e:
                logger.warning(f"LAAP Vision {provider} failed: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"All LAAP vision providers failed: {last_error}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Message]:
        """Convert Harness message format to LAAP Message format"""
        return [
            Message(role=msg["role"], content=msg["content"])
            for msg in messages
        ]

    async def close(self):
        """Close any open resources"""
        pass


_llm_client: Optional[LAAPLLMClient] = None


async def get_llm_client() -> LAAPLLMClient:
    """Get LAAP LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LAAPLLMClient()
    return _llm_client

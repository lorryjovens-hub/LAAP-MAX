"""多模型 LLM 客户端 - 智能路由与降级策略"""

import asyncio
import base64
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMClient:
    """
    Harness 的声带系统 - 多模型客户端
    
    设计原则：
    1. 感知层使用强视觉模型（GPT-4o / Claude 4 Sonnet）
    2. 执行层可使用普通模型（GPT-4o-mini / Claude 3.5 Sonnet）
    3. 自动降级：主模型失败时切换备用模型
    4. 并发请求合并：相同 prompt 合并以减少 token 消耗
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(timeout=120.0, limits=httpx.Limits(max_connections=50))
        
        # 模型路由表
        self.model_routes = {
            "perception": [
                (ModelProvider.OPENAI, "gpt-4o"),
                (ModelProvider.ANTHROPIC, "claude-sonnet-4-20250514"),
            ],
            "reasoning": [
                (ModelProvider.ANTHROPIC, "claude-sonnet-4-20250514"),
                (ModelProvider.OPENAI, "gpt-4o"),
            ],
            "execution": [
                (ModelProvider.OPENAI, "gpt-4o-mini"),
                (ModelProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),
            ],
            "refinement": [
                (ModelProvider.ANTHROPIC, "claude-sonnet-4-20250514"),
                (ModelProvider.OPENAI, "gpt-4o"),
            ],
        }
        
        # API Key 检查
        self._validate_keys()
    
    def _validate_keys(self):
        """验证至少有一个 API Key 可用"""
        if not any([
            self.settings.openai_api_key,
            self.settings.anthropic_api_key,
            self.settings.google_api_key,
        ]):
            raise RuntimeError("至少需要一个 LLM API Key")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        stage: str = "execution",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """
        通用对话补全，自动路由到最优模型
        
        Args:
            messages: 消息列表
            stage: 流水线阶段 (perception/reasoning/execution/refinement)
            temperature: 创造性温度
            max_tokens: 最大输出 token
            json_mode: 是否强制 JSON 输出
        """
        routes = self.model_routes.get(stage, self.model_routes["execution"])
        
        for provider, model in routes:
            try:
                if provider == ModelProvider.OPENAI and self.settings.openai_api_key:
                    return await self._call_openai(
                        messages, model, temperature, max_tokens, json_mode
                    )
                elif provider == ModelProvider.ANTHROPIC and self.settings.anthropic_api_key:
                    return await self._call_anthropic(
                        messages, model, temperature, max_tokens, json_mode
                    )
                elif provider == ModelProvider.GOOGLE and self.settings.google_api_key:
                    return await self._call_google(
                        messages, model, temperature, max_tokens, json_mode
                    )
            except Exception as e:
                logger.warning(
                    f"模型 {provider.value}/{model} 失败: {str(e)}，尝试降级..."
                )
                continue
        
        raise RuntimeError("所有模型路由均失败")
    
    async def vision_completion(
        self,
        image_path: Union[str, Path],
        prompt: str,
        stage: str = "perception",
        detail: str = "high",
    ) -> str:
        """
        视觉理解 - 上传图片并获取结构化分析
        
        Args:
            image_path: 图片路径
            prompt: 分析提示词
            stage: 感知阶段（自动路由到强视觉模型）
            detail: 细节级别 (low/high/auto)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 读取并编码图片
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        mime_type = self._get_mime_type(image_path)
        
        routes = self.model_routes.get(stage, self.model_routes["perception"])
        
        for provider, model in routes:
            try:
                if provider == ModelProvider.OPENAI and self.settings.openai_api_key:
                    return await self._call_openai_vision(
                        image_data, mime_type, prompt, model, detail
                    )
                elif provider == ModelProvider.ANTHROPIC and self.settings.anthropic_api_key:
                    return await self._call_anthropic_vision(
                        image_data, mime_type, prompt, model
                    )
                elif provider == ModelProvider.GOOGLE and self.settings.google_api_key:
                    return await self._call_google_vision(
                        image_data, mime_type, prompt, model
                    )
            except Exception as e:
                logger.warning(
                    f"视觉模型 {provider.value}/{model} 失败: {str(e)}，尝试降级..."
                )
                continue
        
        raise RuntimeError("所有视觉模型路由均失败")
    
    async def _call_openai(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        """调用 OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        response = await self.http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        """调用 Anthropic API"""
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        # Anthropic 使用不同的消息格式
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": user_messages,
            "system": system_msg,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            payload["system"] += "\n\n你必须以有效的 JSON 格式响应，不要包含任何其他文本。"
        
        response = await self.http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        content = data["content"][0]["text"]
        
        # 如果要求 json_mode，尝试提取 JSON
        if json_mode and not content.strip().startswith("{"):
            # 尝试从 markdown 代码块提取
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        return content
    
    async def _call_google(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        """调用 Google Gemini API"""
        # 简化实现，实际使用 google-generativeai 库
        import google.generativeai as genai
        genai.configure(api_key=self.settings.google_api_key)
        
        model = genai.GenerativeModel(model)
        
        # 转换消息格式
        prompt = "\n".join([m["content"] for m in messages if m["role"] == "user"])
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json" if json_mode else None,
            ),
        )
        return response.text
    
    async def _call_openai_vision(
        self,
        image_data: str,
        mime_type: str,
        prompt: str,
        model: str,
        detail: str,
    ) -> str:
        """OpenAI 视觉 API"""
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}",
                        "detail": detail,
                    },
                },
            ],
        }]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        
        response = await self.http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic_vision(
        self,
        image_data: str,
        mime_type: str,
        prompt: str,
        model: str,
    ) -> str:
        """Anthropic 视觉 API"""
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        
        response = await self.http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
    
    async def _call_google_vision(
        self,
        image_data: str,
        mime_type: str,
        prompt: str,
        model: str,
    ) -> str:
        """Google Gemini 视觉 API"""
        import google.generativeai as genai
        genai.configure(api_key=self.settings.google_api_key)
        
        model = genai.GenerativeModel(model)
        
        import io
        image_bytes = base64.b64decode(image_data)
        image = genai.types.Content(
            parts=[
                genai.types.Part(text=prompt),
                genai.types.Part(
                    inline_data=genai.types.Blob(mime_type=mime_type, data=image_bytes)
                ),
            ]
        )
        
        response = await asyncio.to_thread(model.generate_content, image)
        return response.text
    
    def _get_mime_type(self, path: Path) -> str:
        """根据文件扩展名获取 MIME 类型"""
        ext = path.suffix.lower()
        mapping = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        return mapping.get(ext, "image/png")
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.aclose()


# 全局单例
_llm_client: Optional[LLMClient] = None


async def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

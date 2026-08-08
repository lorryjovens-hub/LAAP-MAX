"""LAAP — DeepSeekGenerator：真实 LLM 编码生成器（双系统闭环 System 1）。

通过 DeepSeek OpenAI 兼容 API 生成代码，接入 CodingIntelligenceLoop。

Key 解析顺序：
1. 构造参数 api_key；
2. 环境变量 DEEPSEEK_API_KEY；
3. 返回 None → 生成器不可用（闭环优雅降级）。

零新第三方依赖（requests 标准库即可）。
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("laap.agent.deepseek_generator")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = """你是 LAAP 数字生命系统中的编码引擎（System 1）。
你的任务是生成高质量的 Python 代码。要求：
1. 严格遵循任务描述与执行计划；
2. 只输出代码本身（```python 围栏内），不要多余解释；
3. 注意边界条件与错误处理；
4. 代码必须语法正确、可直接运行。
如果提供了"校准信号"（上一轮失败信息），必须针对性地修复该问题。
"""


class DeepSeekGenerator:
    """DeepSeek API 编码生成器。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEEPSEEK_BASE_URL,
        temperature: float = 0.3,
        timeout_sec: int = 120,
    ) -> None:
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout_sec = timeout_sec
        self._last_call: Dict[str, Any] = {}

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    # ── 主接口：闭环生成器签名 fn(desc, plan_summary, calibration) -> str ──

    def generate(self, desc: str, plan_summary: str = "", calibration: str = "") -> str:
        """生成代码（CodingIntelligenceLoop 兼容签名）。"""
        if not self.available:
            logger.warning("[DeepSeekGenerator] 无 API key，返回空")
            return ""

        user_prompt = self._build_prompt(desc, plan_summary, calibration)
        t0 = time.time()
        try:
            content = self._chat(user_prompt)
            code = self._extract_code(content)
            self._last_call = {
                "ok": True,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "model": self.model,
                "code_len": len(code),
            }
            return code
        except Exception as e:
            self._last_call = {
                "ok": False,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "error": str(e)[:200],
            }
            logger.warning(f"[DeepSeekGenerator] 调用失败: {e}")
            return ""

    # ── 内部 ────────────────────────────────────────────────────────────

    def _build_prompt(self, desc: str, plan_summary: str, calibration: str) -> str:
        parts = [f"任务: {desc}"]
        if plan_summary:
            parts.append(f"执行计划: {plan_summary}")
        if calibration:
            parts.append(calibration)
        return "\n\n".join(parts)

    def _chat(self, user_prompt: str) -> str:
        import requests

        resp = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
                "max_tokens": 4096,
            },
            timeout=self.timeout_sec,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_code(content: str) -> str:
        """从回复中提取代码（处理 ```python 围栏）。"""
        content = content.strip()
        if "```" in content:
            # 取最后一个围栏块
            parts = content.split("```")
            for part in reversed(parts):
                if part.strip() and not part.strip().startswith("python"):
                    return part.strip()
                if part.strip().startswith("python"):
                    return part.strip()[6:].strip()
            return content
        return content

    def stats(self) -> Dict[str, Any]:
        return {"available": self.available, "last_call": self._last_call}
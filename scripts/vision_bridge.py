"""vision_bridge.py — Aris 视觉桥接 MCP Server

纯文本主模型（DeepSeek V4 Flash）无法直接看图片，本服务通过 OpenRouter
免费视觉模型为 Aris 提供"看图"能力。stdio transport，由 Hanako 自动拉起进程。

工具：
  vision_describe(image_path, query)   — 通用图片理解/问答
  vision_ocr(image_path)               — 图片文字识别
  vision_analyze_chart(image_path)     — 图表/截图结构化提取

模型优先级（免费共享池限流时自动切换）：
  nvidia/nemotron-nano-12b-v2-vl:free
  google/gemma-4-31b-it:free
  qwen/qwen2.5-vl-32b-instruct:free
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request

from fastmcp import FastMCP

mcp = FastMCP("vision-bridge")

# OpenRouter 免费视觉模型（显式指定，不用 openrouter/free 自动路由——
# 自动路由会落到内容安全模型，无法真正看图）
# qwen2.5-vl-32b-instruct:free 已于 2026-08 下架（404），从列表移除
MODEL_PRIORITY = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
]

API_URL = "https://openrouter.ai/api/v1/chat/completions"

CATALOG_CANDIDATES = [
    os.path.expanduser("~/.hanako/provider-catalog.json"),
    r"D:\LAAP\provider-catalog.json",
]


def _get_openrouter_key() -> str:
    """从环境变量或 provider-catalog.json 读取 OpenRouter key。"""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    for path in CATALOG_CANDIDATES:
        try:
            with open(path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        provider = catalog.get("providers", {}).get("openrouter") or catalog.get("openrouter")
        if provider and provider.get("api_key"):
            return provider["api_key"].strip()
    raise RuntimeError("OPENROUTER_API_KEY 未找到：请设置环境变量或检查 provider-catalog.json")


def _load_image(image_path: str) -> tuple[str, str]:
    """读取本地图片，返回 (base64, mime)。"""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")
    with open(image_path, "rb") as f:
        data = f.read()
    lower = image_path.lower()
    if lower.endswith(".png"):
        mime = "image/png"
    elif lower.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif lower.endswith(".webp"):
        mime = "image/webp"
    elif lower.endswith(".gif"):
        mime = "image/gif"
    else:
        mime = "image/png"
    return base64.b64encode(data).decode(), mime


def _call_vision(image_path: str, prompt: str) -> str:
    key = _get_openrouter_key()
    image_b64, mime = _load_image(image_path)
    last_error = None
    for model in MODEL_PRIORITY:
        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    ],
                }
            ],
        }
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            if not content or not content.strip():
                raise RuntimeError("模型返回空内容")
            return f"[{model}]\n{content.strip()}"
        except Exception as exc:  # 429 限流 / 上游错误 → 换下一个模型
            last_error = exc
            continue
    raise RuntimeError(f"所有视觉模型均失败: {last_error}")


@mcp.tool()
def vision_describe(image_path: str, query: str = "请详细描述这张图片的内容。") -> str:
    """理解图片内容。image_path 为本地图片绝对路径，query 为具体问题或描述指令。"""
    return _call_vision(image_path, query)


@mcp.tool()
def vision_ocr(image_path: str) -> str:
    """识别图片中的文字，按阅读顺序输出。"""
    return _call_vision(image_path, "请识别图片中的所有文字内容，严格按阅读顺序逐行输出，只输出文字本身，不要额外解释。")


@mcp.tool()
def vision_analyze_chart(image_path: str) -> str:
    """提取图表或截图中的结构化信息（表格、数值、趋势）。"""
    return _call_vision(
        image_path,
        "这是一张图表或数据截图。请提取其中的结构化信息：标题、坐标轴含义、关键数值、趋势或表格内容，尽量完整保留数字。",
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

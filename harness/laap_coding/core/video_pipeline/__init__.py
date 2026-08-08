"""
video_pipeline/__init__.py — LAAP 视频生产管线核心
===================================================
完整管线: 脚本 → 选模板 → 装配动效 → TTS → 渲染 → 成片
"""

from .pipeline import VideoPipeline

__all__ = ["VideoPipeline"]
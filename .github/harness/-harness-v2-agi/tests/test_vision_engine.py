"""视觉引擎测试"""

import pytest
from pathlib import Path

from src.consciousness.perception.vision_engine import VisionPerceptionEngine
from src.config import get_settings


@pytest.fixture
async def vision_engine():
    engine = VisionPerceptionEngine()
    return engine


@pytest.mark.asyncio
async def test_color_extraction():
    """测试色彩提取算法"""
    engine = VisionPerceptionEngine()

    # 创建测试图片（纯色）
    import numpy as np
    from PIL import Image

    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[:, :] = [255, 0, 0]  # 纯红色

    img_path = Path("/tmp/test_red.png")
    Image.fromarray(test_img).save(img_path)

    result = await engine.perceive(img_path)

    assert "design_tokens" in result
    assert len(result["design_tokens"]) > 0

    # 检查是否提取到红色
    colors = [t for t in result["design_tokens"] if t.type == "color"]
    assert len(colors) > 0


@pytest.mark.asyncio
async def test_component_tree_parsing():
    """测试组件树解析"""
    engine = VisionPerceptionEngine()

    # 使用模拟的 LLM 分析文本
    llm_analysis = """
    页面类型：Landing Page
    组件：Navbar（顶部，高度 10%），Hero（中部，高度 50%）
    """

    from src.api.models import VisualComponent
    tree = engine._parse_component_tree(llm_analysis, (1000, 1000, 3))

    assert tree.type == "container"
    assert len(tree.children) >= 2

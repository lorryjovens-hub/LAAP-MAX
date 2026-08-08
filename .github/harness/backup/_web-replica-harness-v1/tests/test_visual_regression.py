"""视觉回归测试"""

import pytest
import numpy as np
import cv2
from pathlib import Path

from src.verification.visual_regression import VisualRegressionTester


@pytest.fixture
def tester():
    return VisualRegressionTester()


@pytest.fixture
def identical_images(tmp_path):
    """创建两张完全相同的图片"""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 128
    path1 = tmp_path / "img1.png"
    path2 = tmp_path / "img2.png"
    cv2.imwrite(str(path1), img)
    cv2.imwrite(str(path2), img)
    return str(path1), str(path2)


@pytest.fixture
def different_images(tmp_path):
    """创建两张完全不同的图片"""
    img1 = np.ones((100, 100, 3), dtype=np.uint8) * 0
    img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
    path1 = tmp_path / "img1.png"
    path2 = tmp_path / "img2.png"
    cv2.imwrite(str(path1), img1)
    cv2.imwrite(str(path2), img2)
    return str(path1), str(path2)


@pytest.mark.asyncio
async def test_identical_images(tester, identical_images):
    """相同图片应该返回 1.0"""
    p1, p2 = identical_images
    score = await tester.compare(p1, p2)
    assert score > 0.99


@pytest.mark.asyncio
async def test_different_images(tester, different_images):
    """不同图片应该返回低分"""
    p1, p2 = different_images
    score = await tester.compare(p1, p2)
    assert score < 0.5

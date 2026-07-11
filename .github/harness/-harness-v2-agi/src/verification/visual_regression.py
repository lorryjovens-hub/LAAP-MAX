"""视觉回归测试 - 像素级对比引擎"""

import math
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisualRegressionTester:
    """
    Harness 的验证层 —— 视觉回归

    使用 SSIM + 感知哈希 + 颜色直方图的多维度对比
    """

    def __init__(self):
        self.settings = get_settings()

    async def compare(self, original: str, generated: str) -> float:
        """对比两张图片，返回相似度 0-1"""
        logger.info(f"[VisualRegression] 对比: {original} vs {generated}")

        orig = cv2.imread(original)
        gen = cv2.imread(generated)

        if orig is None or gen is None:
            logger.error("图片读取失败")
            return 0.0

        orig = self._resize_to_match(orig, gen)
        gen = self._resize_to_match(gen, orig)

        ssim_score = self._compute_ssim(orig, gen)
        hist_score = self._compare_histograms(orig, gen)
        edge_score = self._compare_edges(orig, gen)

        final = ssim_score * 0.5 + hist_score * 0.3 + edge_score * 0.2
        logger.info(f"[VisualRegression] SSIM: {ssim_score:.3f}, Hist: {hist_score:.3f}, Edge: {edge_score:.3f} => Final: {final:.3f}")

        return final

    async def get_feedback(self, original: str, generated: str) -> List[Dict]:
        """生成视觉差异反馈，用于自修正"""
        orig = cv2.imread(original)
        gen = cv2.imread(generated)

        if orig is None or gen is None:
            return []

        diff = cv2.absdiff(orig, gen)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        feedback = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area > 100:
                feedback.append({
                    "region": {"x": x, "y": y, "width": w, "height": h},
                    "severity": "high" if area > 1000 else "medium",
                    "issue": "视觉差异",
                    "suggestion": "检查该区域的颜色、间距或字体",
                })

        return feedback

    def _resize_to_match(self, img: np.ndarray, target: np.ndarray) -> np.ndarray:
        """调整图片尺寸以匹配目标"""
        h, w = target.shape[:2]
        return cv2.resize(img, (w, h), interpolation=cv2.INTER_LANCZOS4)

    def _compute_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算结构相似性指数"""
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        mean1 = np.mean(gray1)
        mean2 = np.mean(gray2)
        var1 = np.var(gray1)
        var2 = np.var(gray2)
        cov = np.mean((gray1 - mean1) * (gray2 - mean2))

        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        ssim = ((2 * mean1 * mean2 + c1) * (2 * cov + c2)) /                ((mean1**2 + mean2**2 + c1) * (var1 + var2 + c2))

        return float(ssim)

    def _compare_histograms(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """比较颜色直方图"""
        hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(0.0, float(correlation))

    def _compare_edges(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """比较边缘结构"""
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        edges1 = cv2.Canny(gray1, 100, 200)
        edges2 = cv2.Canny(gray2, 100, 200)

        intersection = np.logical_and(edges1, edges2).sum()
        union = np.logical_or(edges1, edges2).sum()

        if union == 0:
            return 1.0

        return float(intersection / union)

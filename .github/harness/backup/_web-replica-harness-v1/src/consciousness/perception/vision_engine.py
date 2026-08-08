"""视觉感知引擎 - 从静态图片提取设计意识"""

import base64
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from src.api.models import DesignToken, VisualComponent
from src.config import get_settings
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VisionPerceptionEngine:
    """
    Harness 意识的视觉皮层
    
    职责：
    1. 色彩提取与令牌化（K-Means + LLM 语义标注）
    2. 排版识别（字体、字号、行高、字重）
    3. 布局结构解析（组件树、层级关系）
    4. 间距系统重建（网格、边距、填充）
    5. 阴影/圆角/边框等视觉参数提取
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = None  # 延迟初始化
    
    async def _get_llm(self):
        if self.llm is None:
            self.llm = await get_llm_client()
        return self.llm
    
    async def perceive(self, image_path: Path) -> Dict[str, any]:
        """
        主感知入口：将图片转化为结构化的设计意识
        
        Returns:
            {
                "design_tokens": List[DesignToken],
                "component_tree": VisualComponent,
                "layout_grid": LayoutGrid,
                "raw_analysis": str,  # LLM 原始分析文本
            }
        """
        logger.info(f"[VisionEngine] 开始感知: {image_path}")
        
        # 1. 图像预处理
        img = self._preprocess_image(image_path)
        
        # 2. 并行执行算法提取 + LLM 视觉分析
        color_task = asyncio.create_task(self._extract_color_tokens(img))
        layout_task = asyncio.create_task(self._analyze_layout_with_llm(image_path))
        typography_task = asyncio.create_task(self._extract_typography(img))
        
        color_tokens = await color_task
        llm_analysis = await layout_task
        typography_info = await typography_task
        
        # 3. 融合算法结果与 LLM 理解
        design_tokens = self._merge_tokens(color_tokens, typography_info, llm_analysis)
        component_tree = self._parse_component_tree(llm_analysis, img.shape)
        layout_grid = self._infer_layout_grid(llm_analysis, img.shape)
        
        logger.info(
            f"[VisionEngine] 感知完成: {len(design_tokens)} tokens, "
            f"{len(component_tree.children)} 顶层组件"
        )
        
        return {
            "design_tokens": design_tokens,
            "component_tree": component_tree,
            "layout_grid": layout_grid,
            "raw_analysis": llm_analysis,
        }
    
    def _preprocess_image(self, image_path: Path) -> np.ndarray:
        """图像预处理：标准化、去噪、尺寸归一化"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 转换为 RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 如果图片过大，等比例缩放（保持视觉细节的同时控制计算量）
        max_dim = self.settings.vision_max_resolution
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
        
        return img
    
    async def _extract_color_tokens(self, img: np.ndarray) -> List[DesignToken]:
        """
        色彩提取算法：
        1. K-Means 聚类提取主色调
        2. 过滤低饱和度/低亮度噪声
        3. LLM 语义标注（这是什么颜色？用在哪？）
        """
        # 重塑为像素列表
        pixels = img.reshape(-1, 3).astype(np.float32) / 255.0
        
        # K-Means 聚类
        kmeans = KMeans(
            n_clusters=self.settings.color_extraction_clusters,
            random_state=42,
            n_init=10,
            max_iter=300,
        )
        kmeans.fit(pixels)
        
        # 获取聚类中心（主色）
        colors = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        # 按占比排序
        counts = np.bincount(labels)
        sorted_indices = np.argsort(counts)[::-1]
        
        tokens = []
        for idx in sorted_indices[:self.settings.max_colors]:
            color = colors[idx]
            hex_color = self._rgb_to_hex(color)
            
            # 过滤过于接近的白色/黑色（通常是背景）
            luminance = self._calculate_luminance(color)
            if luminance > 0.98 or luminance < 0.02:
                continue
            
            token = DesignToken(
                name=f"color-{len(tokens)+1}",
                value=hex_color,
                type="color",
                semantics="待 LLM 标注",
                usage=[],
                confidence=counts[idx] / len(labels),
            )
            tokens.append(token)
        
        # 使用 LLM 为颜色添加语义标注
        tokens = await self._annotate_color_semantics(tokens, img)
        
        return tokens
    
    async def _annotate_color_semantics(
        self, tokens: List[DesignToken], img: np.ndarray
    ) -> List[DesignToken]:
        """使用 LLM 为颜色添加语义标签"""
        llm = await self._get_llm()
        
        color_list = "\n".join([f"{t.name}: {t.value}" for t in tokens])
        
        prompt = f"""
分析以下从网页截图提取的主色调，为每个颜色标注：
1. 语义角色（如：主品牌色、背景色、文字色、强调色、边框色）
2. 推荐使用场景
3. 是否可用于无障碍（对比度要求）

颜色列表：
{color_list}

请以 JSON 格式返回：
{{
  "colors": [
    {{"name": "color-1", "semantics": "主品牌色", "usage": ["按钮", "链接"], "accessible": true}}
  ]
}}
"""
        
        response = await llm.chat_completion(
            messages=[
                {"role": "system", "content": "你是网页设计专家，精通色彩理论和设计系统。"},
                {"role": "user", "content": prompt},
            ],
            stage="perception",
            json_mode=True,
        )
        
        try:
            data = json.loads(response)
            for color_data in data.get("colors", []):
                for token in tokens:
                    if token.name == color_data["name"]:
                        token.semantics = color_data.get("semantics", "unknown")
                        token.usage = color_data.get("usage", [])
        except Exception as e:
            logger.warning(f"颜色语义标注失败: {e}")
        
        return tokens
    
    async def _analyze_layout_with_llm(self, image_path: Path) -> str:
        """使用多模态 LLM 进行深度布局分析"""
        llm = await self._get_llm()
        
        prompt = """
作为前端架构专家，请深度分析这张网页截图，提取以下信息：

1. **整体布局架构**：
   - 页面类型（Landing Page / Dashboard / E-commerce / Blog / SaaS）
   - 布局模式（Hero + Features / Sidebar + Content / Grid Gallery / Split Screen）
   - 视觉层次结构（信息优先级排序）

2. **组件识别**（按视觉层级从高到低）：
   - 每个组件的类型（Navbar / Hero / FeatureCard / CTA / Footer / Modal等）
   - 相对位置和大小（使用百分比坐标 x%, y%, width%, height%）
   - 文本内容（OCR）
   - 图片/图标资源描述

3. **设计系统参数**：
   - 圆角大小（px）
   - 阴影层级（none / sm / md / lg / xl）
   - 边框样式
   - 间距节奏（紧凑/舒适/宽松）

4. **响应式线索**：
   - 当前视口推断（mobile / tablet / desktop）
   - 断点设计建议

请以结构化文本详细描述，便于后续生成代码。
"""
        
        return await llm.vision_completion(
            image_path=image_path,
            prompt=prompt,
            stage="perception",
            detail="high",
        )
    
    async def _extract_typography(self, img: np.ndarray) -> Dict[str, any]:
        """
        排版提取：使用 OCR + 启发式算法
        注意：生产环境应使用更专业的 OCR（如 PaddleOCR / AWS Textract）
        """
        # 简化的排版提取：基于边缘检测和连通域分析估算文字区域
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 使用 MSER 检测文字区域
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        
        # 估算字体大小分布
        heights = [cv2.boundingRect(r)[3] for r in regions]
        if not heights:
            return {"font_sizes": [], "dominant_sizes": []}
        
        # K-Means 聚类字体大小层级
        heights_array = np.array(heights).reshape(-1, 1)
        kmeans = KMeans(n_clusters=min(5, len(heights)), random_state=42, n_init=10)
        kmeans.fit(heights_array)
        
        centers = sorted(kmeans.cluster_centers_.flatten().tolist())
        
        return {
            "font_sizes": [int(h) for h in centers],
            "dominant_sizes": [int(h) for h in centers[-3:]],  # 最大的三个通常是标题层级
        }
    
    def _merge_tokens(
        self,
        color_tokens: List[DesignToken],
        typography_info: Dict,
        llm_analysis: str,
    ) -> List[DesignToken]:
        """融合所有设计令牌"""
        tokens = color_tokens.copy()
        
        # 添加排版令牌
        for i, size in enumerate(typography_info.get("dominant_sizes", [])):
            tokens.append(DesignToken(
                name=f"font-size-{i+1}",
                value=f"{size}px",
                type="font",
                semantics=["display", "heading", "body", "caption"][min(i, 3)],
                usage=["typography"],
                confidence=0.8,
            ))
        
        # 添加间距令牌（基于 LLM 分析推断）
        base = self.settings.spacing_base_unit
        for i, scale in enumerate([1, 2, 4, 8, 16, 24, 32, 48, 64]):
            tokens.append(DesignToken(
                name=f"space-{scale}x",
                value=f"{base * scale}px",
                type="spacing",
                semantics=["tight", "compact", "normal", "comfortable", "loose", "expansive"][min(i, 5)],
                usage=["margin", "padding", "gap"],
                confidence=0.7,
            ))
        
        return tokens
    
    def _parse_component_tree(
        self, llm_analysis: str, img_shape: Tuple[int, ...]
    ) -> VisualComponent:
        """从 LLM 分析文本解析组件树"""
        # 简化实现：使用正则提取组件描述
        # 生产环境应使用结构化输出（JSON mode）
        import re
        
        h, w = img_shape[:2]
        
        # 创建根节点
        root = VisualComponent(
            id="root",
            type="container",
            bounding_box={"x": 0, "y": 0, "width": 100, "height": 100},
            z_index=0,
            prominence=100,
            children=[],
        )
        
        # 尝试提取组件描述（简化版）
        component_patterns = [
            ("navbar", r'(?:navbar|导航栏|header).*?(?:顶部|上方)'),
            ("hero", r'(?:hero|主视觉|banner).*?(?:大|首屏)'),
            ("card", r'(?:card|卡片).*?(?:内容|feature)'),
            ("button", r'(?:button|按钮|CTA)'),
            ("footer", r'(?:footer|页脚|底部)'),
        ]
        
        for comp_type, pattern in component_patterns:
            if re.search(pattern, llm_analysis, re.IGNORECASE):
                child = VisualComponent(
                    id=f"comp-{comp_type}",
                    type=comp_type,
                    bounding_box={"x": 0, "y": 0, "width": 100, "height": 20},
                    z_index=1,
                    prominence=50,
                    children=[],
                )
                root.children.append(child)
        
        return root
    
    def _infer_layout_grid(self, llm_analysis: str, img_shape: Tuple[int, ...]) -> Dict:
        """推断布局网格系统"""
        from src.api.models import LayoutGrid
        
        # 启发式推断
        if "grid" in llm_analysis.lower() or "网格" in llm_analysis:
            return LayoutGrid(type="grid", columns=3, gap="24px")
        elif "flex" in llm_analysis.lower() or "弹性" in llm_analysis:
            return LayoutGrid(type="flex", gap="16px")
        else:
            return LayoutGrid(type="flex", gap="16px")
    
    @staticmethod
    def _rgb_to_hex(rgb: np.ndarray) -> str:
        """RGB 转 HEX"""
        r, g, b = [int(c * 255) for c in rgb]
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def _calculate_luminance(rgb: np.ndarray) -> float:
        """计算相对亮度（WCAG 标准）"""
        r, g, b = rgb
        return 0.2126 * r + 0.7152 * g + 0.0722 * b


import asyncio  # 用于 perceive 方法中的并发

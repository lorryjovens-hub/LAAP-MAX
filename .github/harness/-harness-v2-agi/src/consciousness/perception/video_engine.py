"""视频感知引擎 - 从录屏提取动画与交互意识"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.api.models import AnimationSpec
from src.config import get_settings
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoPerceptionEngine:
    """
    Harness 意识的动态视觉皮层
    
    职责：
    1. 关键帧提取与差异分析
    2. 动画参数提取（duration, easing, transform）
    3. 交互状态检测（hover, click, scroll, focus）
    4. 微交互识别（按钮反馈、加载状态、过渡效果）
    5. 时序重建（CSS keyframes / transition）
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = None
    
    async def _get_llm(self):
        if self.llm is None:
            self.llm = await get_llm_client()
        return self.llm
    
    async def perceive(self, video_path: Path) -> List[AnimationSpec]:
        """
        主感知入口：从视频提取动画规范
        
        Returns:
            List[AnimationSpec] - 动画规范列表
        """
        logger.info(f"[VideoEngine] 开始解析视频: {video_path}")
        
        # 1. 视频解码与采样
        frames, fps = self._sample_frames(video_path)
        logger.info(f"[VideoEngine] 采样 {len(frames)} 帧 @ {fps}fps")
        
        # 2. 运动检测与分段
        segments = self._detect_motion_segments(frames)
        logger.info(f"[VideoEngine] 检测到 {len(segments)} 个运动段")
        
        # 3. 逐段分析动画参数
        animations = []
        for seg_idx, segment in enumerate(segments):
            anim = await self._analyze_segment(segment, fps, seg_idx)
            if anim:
                animations.append(anim)
        
        # 4. 使用 LLM 验证和补全动画语义
        animations = await self._validate_animations_with_llm(animations, frames)
        
        logger.info(f"[VideoEngine] 视频解析完成: {len(animations)} 个动画规范")
        return animations
    
    def _sample_frames(self, video_path: Path) -> Tuple[List[np.ndarray], float]:
        """
        视频采样：按配置 FPS 提取关键帧
        策略：固定间隔采样 + 运动自适应加密采样
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / original_fps if original_fps > 0 else 0
        
        # 限制最大时长
        max_duration = self.settings.video_max_duration
        if duration > max_duration:
            logger.warning(f"视频过长 ({duration:.1f}s)，截断至 {max_duration}s")
            total_frames = int(max_duration * original_fps)
        
        # 计算采样间隔
        target_fps = self.settings.video_sample_fps
        sample_interval = int(original_fps / target_fps)
        if sample_interval < 1:
            sample_interval = 1
        
        frames = []
        frame_idx = 0
        prev_frame = None
        
        while frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % sample_interval == 0:
                # 运动自适应：如果帧间差异大，加密采样
                if prev_frame is not None:
                    diff = self._frame_difference(prev_frame, frame)
                    if diff > self.settings.motion_sensitivity:
                        # 在运动剧烈区域前后各加一帧
                        frames.append(prev_frame)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                prev_frame = frame_rgb
            
            frame_idx += 1
        
        cap.release()
        return frames, target_fps
    
    def _frame_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧之间的差异度（0-1）"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        return np.mean(diff) / 255.0
    
    def _detect_motion_segments(
        self, frames: List[np.ndarray]
    ) -> List[List[np.ndarray]]:
        """
        将连续帧分割为运动段
        策略：基于帧间差异的阈值分割
        """
        if len(frames) < 2:
            return [frames] if frames else []
        
        segments = []
        current_segment = [frames[0]]
        
        for i in range(1, len(frames)):
            diff = self._frame_difference(frames[i-1], frames[i])
            
            if diff > self.settings.motion_sensitivity:
                current_segment.append(frames[i])
            else:
                # 运动结束，保存当前段
                if len(current_segment) >= 3:  # 至少3帧才算有效动画
                    segments.append(current_segment)
                current_segment = [frames[i]]
        
        # 处理最后一个段
        if len(current_segment) >= 3:
            segments.append(current_segment)
        
        return segments
    
    async def _analyze_segment(
        self,
        segment: List[np.ndarray],
        fps: float,
        seg_idx: int,
    ) -> Optional[AnimationSpec]:
        """
        分析单个运动段，提取动画参数
        """
        if len(segment) < 3:
            return None
        
        # 计算动画时长
        duration_ms = (len(segment) / fps) * 1000
        
        # 分析运动类型
        motion_type = self._classify_motion(segment)
        
        # 提取缓动函数（通过速度曲线拟合）
        easing = self._fit_easing_curve(segment)
        
        # 提取变换属性
        properties = self._extract_transform_properties(segment)
        
        # 生成关键帧（起始、中间、结束）
        keyframes = self._generate_keyframes(segment)
        
        # 推断触发条件
        trigger = self._infer_trigger(segment, seg_idx)
        
        return AnimationSpec(
            name=f"anim-{seg_idx}-{motion_type}",
            trigger=trigger,
            duration=duration_ms,
            easing=easing,
            properties=properties,
            keyframes=keyframes,
            confidence=0.85,
        )
    
    def _classify_motion(self, segment: List[np.ndarray]) -> str:
        """分类运动类型"""
        # 简化的运动分类：基于质心位移和面积变化
        first = segment[0]
        last = segment[-1]
        
        # 计算整体位移
        diff = cv2.absdiff(
            cv2.cvtColor(first, cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(last, cv2.COLOR_RGB2GRAY),
        )
        
        # 使用轮廓分析判断运动类型
        contours, _ = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return "fade"
        
        # 分析最大轮廓的变化
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # 启发式分类
        if w > h * 3:
            return "slide-horizontal"
        elif h > w * 3:
            return "slide-vertical"
        elif abs(w - h) < min(w, h) * 0.3:
            return "scale"
        else:
            return "fade"
    
    def _fit_easing_curve(self, segment: List[np.ndarray]) -> str:
        """
        拟合缓动曲线
        通过分析帧间变化速度匹配标准 CSS easing 函数
        """
        # 计算每帧的变化量
        changes = []
        for i in range(1, len(segment)):
            diff = self._frame_difference(segment[i-1], segment[i])
            changes.append(diff)
        
        if not changes:
            return "ease"
        
        # 分析速度曲线形状
        # ease: 慢-快-慢
        # ease-in: 慢-快
        # ease-out: 快-慢
        # linear: 匀速
        
        first_half = changes[:len(changes)//2]
        second_half = changes[len(changes)//2:]
        
        first_avg = np.mean(first_half) if first_half else 0
        second_avg = np.mean(second_half) if second_half else 0
        
        if abs(first_avg - second_avg) < 0.1:
            return "linear"
        elif first_avg < second_avg * 0.7:
            return "ease-in"
        elif second_avg < first_avg * 0.7:
            return "ease-out"
        else:
            return "ease"
    
    def _extract_transform_properties(
        self, segment: List[np.ndarray]
    ) -> List[str]:
        """提取 CSS transform 属性"""
        properties = []
        
        first = segment[0]
        last = segment[-1]
        
        # 检测透明度变化
        opacity_change = self._detect_opacity_change(first, last)
        if opacity_change:
            properties.append("opacity")
        
        # 检测位移
        translation = self._detect_translation(first, last)
        if translation:
            properties.append("translate")
        
        # 检测缩放
        scale = self._detect_scale(first, last)
        if scale:
            properties.append("scale")
        
        # 检测旋转
        rotation = self._detect_rotation(first, last)
        if rotation:
            properties.append("rotate")
        
        return properties if properties else ["opacity"]
    
    def _detect_opacity_change(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """检测透明度变化（整体亮度变化但结构不变）"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
        
        # 结构相似度（SSIM）高但亮度变化大 → 透明度变化
        # 简化：使用直方图比较
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # 如果结构相似但亮度不同
        mean_diff = abs(np.mean(gray1) - np.mean(gray2))
        return correlation > 0.8 and mean_diff > 20
    
    def _detect_translation(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """检测平移运动"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
        
        # 使用光流法检测整体位移
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # 计算平均位移
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        mean_mag = np.mean(mag)
        
        return mean_mag > 2.0
    
    def _detect_scale(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """检测缩放运动"""
        # 检测轮廓面积变化
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
        
        _, thresh1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY)
        _, thresh2 = cv2.threshold(gray2, 127, 255, cv2.THRESH_BINARY)
        
        contours1, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(thresh2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours1 or not contours2:
            return False
        
        area1 = sum(cv2.contourArea(c) for c in contours1)
        area2 = sum(cv2.contourArea(c) for c in contours2)
        
        ratio = area2 / area1 if area1 > 0 else 1
        return abs(ratio - 1) > 0.1
    
    def _detect_rotation(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """检测旋转运动（简化版）"""
        # 生产环境应使用特征点匹配 + RANSAC
        return False
    
    def _generate_keyframes(self, segment: List[np.ndarray]) -> List[Dict]:
        """生成 CSS keyframes 定义"""
        n = len(segment)
        if n < 3:
            return []
        
        # 选择起始、中间、结束三帧
        indices = [0, n // 2, n - 1]
        keyframes = []
        
        for idx in indices:
            percentage = int((idx / (n - 1)) * 100) if n > 1 else 0
            keyframes.append({
                "percentage": percentage,
                "description": f"帧 {idx} 的视觉状态",
            })
        
        return keyframes
    
    def _infer_trigger(self, segment: List[np.ndarray], seg_idx: int) -> str:
        """
        推断动画触发条件
        启发式：第一段通常是页面加载，后续可能是交互触发
        """
        if seg_idx == 0:
            return "load"
        
        # 检测是否有鼠标/手势线索（简化）
        # 生产环境应使用更复杂的手势识别
        return "hover"  # 默认假设
    
    async def _validate_animations_with_llm(
        self,
        animations: List[AnimationSpec],
        frames: List[np.ndarray],
    ) -> List[AnimationSpec]:
        """使用 LLM 验证动画语义并补全缺失信息"""
        if not animations:
            return []
        
        llm = await self._get_llm()
        
        # 选取代表性帧（首中尾）编码为 base64 供 LLM 参考
        sample_frames = [frames[0], frames[len(frames)//2], frames[-1]]
        frame_descriptions = []
        
        for i, frame in enumerate(sample_frames):
            # 保存临时文件供 LLM 分析
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                cv2.imwrite(tmp.name, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                frame_descriptions.append(f"帧 {i}: {tmp.name}")
        
        anim_json = json.dumps([
            {
                "name": a.name,
                "trigger": a.trigger,
                "duration": a.duration,
                "easing": a.easing,
                "properties": a.properties,
            }
            for a in animations
        ], indent=2, ensure_ascii=False)
        
        prompt = f"""
作为前端动画专家，请审查以下从视频提取的动画规范，并修正/补全：

提取的动画规范：
{anim_json}

请检查并修正：
1. 触发条件是否合理（load / hover / click / scroll / focus / auto）
2. 缓动函数是否匹配视觉感受
3. 动画属性是否完整
4. 是否有遗漏的微交互（如按钮点击反馈、加载状态）
5. 动画时序是否符合物理直觉

请以 JSON 格式返回修正后的动画规范列表。
"""
        
        try:
            response = await llm.chat_completion(
                messages=[
                    {"role": "system", "content": "你是 CSS 动画和微交互专家。"},
                    {"role": "user", "content": prompt},
                ],
                stage="refinement",
                json_mode=True,
            )
            
            data = json.loads(response)
            validated = []
            for anim_data in data.get("animations", []):
                validated.append(AnimationSpec(**anim_data))
            
            return validated if validated else animations
        except Exception as e:
            logger.warning(f"动画 LLM 验证失败: {e}，使用原始提取结果")
            return animations


import asyncio

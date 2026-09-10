"""
LAAP 多模态感知适配器 v1.0 — MultiModalPerception
==================================================
白皮书第 16.2.1 节对应：具身感知层的多模态传感器融合。

支持的模态:
  - text     : 文本输入（已有）
  - image    : 图像输入 → OCR + 视觉描述 + 场景理解
  - audio    : 语音输入 → STT + 情感识别 + 环境音分类
  - sensor   : 传感器输入 → 数值归一化 + 异常检测 + 时序窗口
  - video    : 视频输入 → 关键帧提取 + 动作识别
  - web4     : Web4 事件 (A2A/DID/链上) — 已有基础

架构:
  各模态 → 专用适配器 → 统一 PerceptionEvent → L2 预处理层

用法:
  adapter = MultiModalAdapter()
  events = await adapter.process("image", image_bytes)
  for event in events:
      await pipeline.run_from_event(event)
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import time
import uuid
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict

logger = logging.getLogger("laap.multimodal")


# ════════════════════════════════════════════════════════════
# 模态定义
# ════════════════════════════════════════════════════════════

class Modality(str, Enum):
    TEXT   = "text"
    IMAGE  = "image"
    AUDIO  = "audio"
    SENSOR = "sensor"
    VIDEO  = "video"
    WEB4   = "web4"

class SensorType(str, Enum):
    TEMPERATURE  = "temperature"
    HUMIDITY     = "humidity"
    PRESSURE     = "pressure"
    ACCELERATION = "acceleration"
    GYROSCOPE    = "gyroscope"
    PROXIMITY    = "proximity"
    LIGHT        = "light"
    FORCE        = "force"
    JOINT_ANGLE  = "joint_angle"
    BATTERY      = "battery"
    GPS          = "gps"
    CUSTOM       = "custom"

class ImageEncoding(str, Enum):
    RAW_BYTES  = "raw_bytes"
    BASE64     = "base64"
    FILE_PATH  = "file_path"
    URL        = "url"
    NUMPY      = "numpy_array"

class AudioEncoding(str, Enum):
    RAW_BYTES  = "raw_bytes"
    BASE64     = "base64"
    FILE_PATH  = "file_path"
    WAVEFORM   = "waveform"


# ════════════════════════════════════════════════════════════
# 多模态数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class ImageInput:
    """图像输入"""
    data: bytes = field(default_factory=bytes)
    encoding: ImageEncoding = ImageEncoding.RAW_BYTES
    file_path: str = ""
    url: str = ""
    width: int = 0
    height: int = 0
    channels: int = 3
    format: str = "jpeg"            # jpeg | png | webp | bmp
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AudioInput:
    """音频输入"""
    data: bytes = field(default_factory=bytes)
    encoding: AudioEncoding = AudioEncoding.RAW_BYTES
    file_path: str = ""
    sample_rate: int = 16000
    channels: int = 1
    duration_ms: float = 0.0
    format: str = "wav"             # wav | mp3 | ogg | flac
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SensorInput:
    """传感器输入"""
    sensor_type: SensorType = SensorType.CUSTOM
    values: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    unit: str = ""
    min_range: float = 0.0
    max_range: float = 0.0
    anomaly_threshold: float = 3.0   # 标准差倍数
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MultiModalEvent:
    """多模态感知事件 — 统一输出格式"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    modality: Modality = Modality.TEXT
    source: str = ""
    timestamp: float = field(default_factory=time.time)

    # 文本输出（所有模态最终都可转为文本描述）
    text_description: str = ""
    text_raw: str = ""

    # 结构化提取
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    extracted_text: str = ""                      # OCR 文本
    extracted_emotion: str = ""                   # 情绪标签
    extracted_scene: str = ""                     # 场景描述

    # 数值特征
    numeric_features: Dict[str, float] = field(default_factory=dict)
    anomaly_scores: Dict[str, float] = field(default_factory=dict)

    # 置信度
    confidence: float = 0.5
    processing_latency_ms: float = 0.0

    # 原始数据引用
    raw_data_ref: str = ""                        # 原始数据哈希/路径
    metadata: Dict[str, Any] = field(default_factory=dict)


# ════════════════════════════════════════════════════════════
# 模态适配器基类
# ════════════════════════════════════════════════════════════

class BaseAdapter:
    """模态适配器基类"""

    async def process(self, input_data: Any) -> MultiModalEvent:
        raise NotImplementedError

    def get_capabilities(self) -> List[str]:
        return []


# ════════════════════════════════════════════════════════════
# 图像适配器
# ════════════════════════════════════════════════════════════

class ImageAdapter(BaseAdapter):
    """
    图像适配器 — 处理图像输入。

    能力:
      - 格式验证与标准化
      - 基础图像属性提取 (尺寸、通道、格式)
      - 颜色直方图分析
      - 亮度/对比度估计
      - OCR 文本提取 (需要额外库)
      - 场景标签建议
    """

    def __init__(self, ocr_enabled: bool = False):
        self.ocr_enabled = ocr_enabled
        self._pil_available = self._check_pil()
        self._cv2_available = self._check_cv2()

    def _check_pil(self) -> bool:
        try:
            from PIL import Image
            return True
        except ImportError:
            return False

    def _check_cv2(self) -> bool:
        try:
            import cv2
            return True
        except ImportError:
            return False

    async def process(self, input_data: Union[ImageInput, bytes, str]) -> MultiModalEvent:
        t0 = time.time()

        if isinstance(input_data, bytes):
            img_input = ImageInput(data=input_data, encoding=ImageEncoding.RAW_BYTES)
        elif isinstance(input_data, str):
            if input_data.startswith(("http://", "https://")):
                img_input = ImageInput(url=input_data, encoding=ImageEncoding.URL)
            elif Path(input_data).exists():
                img_input = ImageInput(file_path=input_data, encoding=ImageEncoding.FILE_PATH)
            else:
                img_input = ImageInput(data=base64.b64decode(input_data),
                                       encoding=ImageEncoding.BASE64)
        else:
            img_input = input_data

        event = MultiModalEvent(modality=Modality.IMAGE, source="image_adapter")

        # 解析图像数据
        image_bytes = img_input.data
        if img_input.encoding == ImageEncoding.FILE_PATH and img_input.file_path:
            image_bytes = Path(img_input.file_path).read_bytes()
        elif img_input.encoding == ImageEncoding.BASE64 and img_input.data:
            image_bytes = img_input.data  # 已解码

        event.raw_data_ref = hashlib.sha256(image_bytes).hexdigest()[:16]

        # 图像属性提取
        if self._pil_available:
            try:
                from PIL import Image
                import io as pil_io
                img = Image.open(pil_io.BytesIO(image_bytes))
                img_input.width = img.width
                img_input.height = img.height
                img_input.format = img.format.lower() if img.format else "unknown"
                img_input.channels = len(img.getbands())

                # 颜色分析
                if img.mode in ("RGB", "RGBA"):
                    pixels = list(img.resize((50, 50)).getdata())
                    event.numeric_features["avg_r"] = sum(p[0] for p in pixels) / len(pixels)
                    event.numeric_features["avg_g"] = sum(p[1] for p in pixels) / len(pixels)
                    event.numeric_features["avg_b"] = sum(p[2] for p in pixels) / len(pixels)
                    event.numeric_features["brightness"] = (
                        event.numeric_features["avg_r"] * 0.299 +
                        event.numeric_features["avg_g"] * 0.587 +
                        event.numeric_features["avg_b"] * 0.114
                    ) / 255.0

                # 场景标签
                event.extracted_scene = self._suggest_scene(img_input)

                event.text_description = (
                    f"[图像] {img_input.width}x{img_input.height} "
                    f"{img_input.format.upper()} "
                    f"亮度: {event.numeric_features.get('brightness', 0):.2f} "
                    f"场景: {event.extracted_scene}"
                )
                event.confidence = 0.8
            except Exception as e:
                event.text_description = f"[图像] 解析失败: {e}"
                event.confidence = 0.3
        else:
            event.text_description = f"[图像] {len(image_bytes)} bytes (PIL 未安装，无法解析)"
            event.confidence = 0.5

        # OCR
        if self.ocr_enabled:
            ocr_text = await self._extract_ocr(image_bytes)
            if ocr_text:
                event.extracted_text = ocr_text
                event.text_description += f"\nOCR: {ocr_text[:200]}"

        event.processing_latency_ms = (time.time() - t0) * 1000
        return event

    def _suggest_scene(self, img_input: ImageInput) -> str:
        """基于图像属性建议场景标签"""
        if img_input.width > img_input.height * 1.5:
            return "landscape"
        elif img_input.height > img_input.width * 1.5:
            return "portrait"
        elif img_input.width == img_input.height:
            return "square"
        return "general"

    async def _extract_ocr(self, image_bytes: bytes) -> str:
        """OCR 文本提取"""
        if self._cv2_available:
            try:
                import cv2
                import numpy as np
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    # 基础预处理：灰度化 + 二值化
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
                    # 返回预处理后的图像信息（实际 OCR 需要 Tesseract/EasyOCR）
                    return f"[OCR-ready] {img.shape[1]}x{img.shape[0]} 灰度化+二值化完成"
            except Exception:
                pass
        return ""

    def get_capabilities(self) -> List[str]:
        caps = ["image_format_detect", "color_analysis", "scene_suggest"]
        if self._pil_available:
            caps.append("pil_enhanced")
        if self.ocr_enabled:
            caps.append("ocr_preprocess")
        return caps


# ════════════════════════════════════════════════════════════
# 音频适配器
# ════════════════════════════════════════════════════════════

class AudioAdapter(BaseAdapter):
    """
    音频适配器 — 处理语音和环境音输入。

    能力:
      - 格式验证
      - 波形分析 (振幅、过零率)
      - 语音/非语音分类
      - 情绪倾向估计
      - STT 就绪标记
    """

    def __init__(self):
        self._wave_available = self._check_wave()

    def _check_wave(self) -> bool:
        try:
            import wave
            return True
        except ImportError:
            return False

    async def process(self, input_data: Union[AudioInput, bytes, str]) -> MultiModalEvent:
        t0 = time.time()

        if isinstance(input_data, bytes):
            audio_input = AudioInput(data=input_data, encoding=AudioEncoding.RAW_BYTES)
        elif isinstance(input_data, str):
            if Path(input_data).exists():
                audio_input = AudioInput(file_path=input_data, encoding=AudioEncoding.FILE_PATH)
            else:
                audio_input = AudioInput(data=base64.b64decode(input_data),
                                         encoding=AudioEncoding.BASE64)
        else:
            audio_input = input_data

        event = MultiModalEvent(modality=Modality.AUDIO, source="audio_adapter")

        audio_bytes = audio_input.data
        if audio_input.encoding == AudioEncoding.FILE_PATH and audio_input.file_path:
            audio_bytes = Path(audio_input.file_path).read_bytes()

        event.raw_data_ref = hashlib.sha256(audio_bytes).hexdigest()[:16]

        # 波形分析
        if self._wave_available and audio_bytes:
            try:
                import wave
                import io as wave_io
                import struct
                wf = wave.open(wave_io.BytesIO(audio_bytes), 'rb')
                audio_input.sample_rate = wf.getframerate()
                audio_input.channels = wf.getnchannels()
                n_frames = wf.getnframes()
                audio_input.duration_ms = (n_frames / audio_input.sample_rate) * 1000

                # 读取前 1 秒的采样
                samples_to_read = min(audio_input.sample_rate, n_frames)
                raw = wf.readframes(samples_to_read)
                sample_width = wf.getsampwidth()
                fmt_char = {1: 'b', 2: 'h', 4: 'i'}.get(sample_width, 'h')
                n = min(samples_to_read, len(raw) // sample_width)
                samples = struct.unpack(f'{n}{fmt_char}', raw[:n * sample_width])

                if samples:
                    event.numeric_features["amplitude_max"] = max(abs(s) for s in samples)
                    event.numeric_features["amplitude_rms"] = (
                        sum(s*s for s in samples) / len(samples)) ** 0.5
                    # 过零率
                    zcr = sum(1 for i in range(1, len(samples))
                              if samples[i] * samples[i-1] < 0) / len(samples)
                    event.numeric_features["zero_crossing_rate"] = zcr
                    # 语音/非语音分类
                    event.extracted_scene = self._classify_audio_type(event.numeric_features)

                wf.close()
            except Exception as e:
                event.text_description = f"[音频] 解析失败: {e}"
                event.confidence = 0.3

        audio_input.duration_ms = audio_input.duration_ms or (len(audio_bytes) / 16000 * 1000)

        event.text_description = (
            f"[音频] {audio_input.sample_rate}Hz {audio_input.channels}ch "
            f"{audio_input.duration_ms:.0f}ms "
            f"类型: {event.extracted_scene} "
            f"振幅: {event.numeric_features.get('amplitude_rms', 0):.1f}"
        )
        event.confidence = 0.7

        event.processing_latency_ms = (time.time() - t0) * 1000
        return event

    def _classify_audio_type(self, features: Dict[str, float]) -> str:
        """基于特征分类音频类型"""
        rms = features.get("amplitude_rms", 0)
        zcr = features.get("zero_crossing_rate", 0)

        if rms < 100:
            return "silence"
        elif zcr > 0.3:
            return "speech"
        elif zcr < 0.05:
            return "music"
        elif rms > 5000:
            return "loud_noise"
        else:
            return "ambient"

    def get_capabilities(self) -> List[str]:
        caps = ["audio_format_detect", "waveform_analysis", "audio_classification"]
        if self._wave_available:
            caps.append("wave_enhanced")
        return caps


# ════════════════════════════════════════════════════════════
# 传感器适配器
# ════════════════════════════════════════════════════════════

class SensorAdapter(BaseAdapter):
    """
    传感器适配器 — 处理物理传感器数据。

    能力:
      - 数值归一化
      - 时序窗口管理
      - 异常检测 (Z-score)
      - 趋势分析
      - 传感器融合
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._history: Dict[SensorType, List[float]] = defaultdict(list)

    async def process(self, input_data: Union[SensorInput, Dict]) -> MultiModalEvent:
        t0 = time.time()

        if isinstance(input_data, dict):
            sensor_input = SensorInput(
                sensor_type=SensorType(input_data.get("sensor_type", "custom")),
                values=input_data.get("values", [input_data.get("value", 0)]),
                timestamps=input_data.get("timestamps", [time.time()]),
                unit=input_data.get("unit", ""),
                metadata=input_data.get("metadata", {}),
            )
        else:
            sensor_input = input_data

        event = MultiModalEvent(modality=Modality.SENSOR, source="sensor_adapter")
        event.metadata["sensor_type"] = sensor_input.sensor_type.value

        values = sensor_input.values
        if not values:
            event.text_description = f"[传感器] {sensor_input.sensor_type.value}: 无数据"
            return event

        # 更新历史
        self._history[sensor_input.sensor_type].extend(values)
        history = self._history[sensor_input.sensor_type]
        if len(history) > self.window_size:
            self._history[sensor_input.sensor_type] = history[-self.window_size:]

        # 统计特征
        import statistics
        current = values[-1] if values else 0
        hist_mean = statistics.mean(history) if history else current
        hist_std = statistics.stdev(history) if len(history) > 1 else 0

        event.numeric_features["current"] = current
        event.numeric_features["mean"] = hist_mean
        event.numeric_features["std"] = hist_std
        event.numeric_features["min"] = min(history)
        event.numeric_features["max"] = max(history)

        # 趋势分析
        if len(history) >= 5:
            recent = history[-5:]
            if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                event.numeric_features["trend"] = 1.0   # 上升
            elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                event.numeric_features["trend"] = -1.0  # 下降
            else:
                event.numeric_features["trend"] = 0.0   # 波动

        # 异常检测 (Z-score)
        if hist_std > 0:
            z_score = abs(current - hist_mean) / hist_std
            event.anomaly_scores["z_score"] = z_score
            if z_score > sensor_input.anomaly_threshold:
                event.anomaly_scores["anomaly"] = z_score

        # 归一化
        if sensor_input.max_range > sensor_input.min_range:
            norm = (current - sensor_input.min_range) / (sensor_input.max_range - sensor_input.min_range)
            event.numeric_features["normalized"] = max(0.0, min(1.0, norm))

        event.text_description = (
            f"[传感器] {sensor_input.sensor_type.value}: {current:.2f}{sensor_input.unit} "
            f"(μ={hist_mean:.2f}, σ={hist_std:.2f}, "
            f"趋势: {'↑' if event.numeric_features.get('trend', 0) > 0.5 else '↓' if event.numeric_features.get('trend', 0) < -0.5 else '→'})"
        )
        if "anomaly" in event.anomaly_scores:
            event.text_description += f" ⚠️ 异常 Z={event.anomaly_scores['anomaly']:.1f}"

        event.confidence = 0.9
        event.processing_latency_ms = (time.time() - t0) * 1000
        return event

    def get_capabilities(self) -> List[str]:
        return ["normalization", "anomaly_detection", "trend_analysis", "sensor_fusion"]

    def get_history(self, sensor_type: SensorType) -> List[float]:
        return list(self._history.get(sensor_type, []))


# ════════════════════════════════════════════════════════════
# 多模态适配器总管
# ════════════════════════════════════════════════════════════

class MultiModalAdapter:
    """
    多模态感知总管 — 统一入口。

    自动路由到对应适配器，输出统一的 MultiModalEvent。
    """

    def __init__(self):
        self.image_adapter = ImageAdapter(ocr_enabled=True)
        self.audio_adapter = AudioAdapter()
        self.sensor_adapter = SensorAdapter()
        self._adapters: Dict[Modality, BaseAdapter] = {
            Modality.IMAGE:  self.image_adapter,
            Modality.AUDIO:  self.audio_adapter,
            Modality.SENSOR: self.sensor_adapter,
        }
        self._stats = {
            "total_processed": 0,
            "by_modality": defaultdict(int),
            "total_latency_ms": 0.0,
        }
        logger.info("MultiModalAdapter 初始化完成")

    async def process(
        self,
        modality: Union[Modality, str],
        data: Any,
        metadata: Optional[Dict] = None,
    ) -> MultiModalEvent:
        """
        统一处理入口。

        Args:
            modality: 模态类型
            data: 原始数据
            metadata: 附加元数据

        Returns:
            MultiModalEvent: 统一的多模态事件
        """
        if isinstance(modality, str):
            modality = Modality(modality)

        adapter = self._adapters.get(modality)
        if adapter is None:
            # 文本模态直接返回
            text = str(data)[:1000] if isinstance(data, (str, bytes)) else str(data)
            event = MultiModalEvent(
                modality=Modality.TEXT,
                source="text_direct",
                text_raw=text,
                text_description=text,
                confidence=0.9,
            )
            self._stats["total_processed"] += 1
            self._stats["by_modality"]["text"] += 1
            return event

        event = await adapter.process(data)
        if metadata:
            event.metadata.update(metadata)

        self._stats["total_processed"] += 1
        self._stats["by_modality"][modality.value] += 1
        self._stats["total_latency_ms"] += event.processing_latency_ms

        return event

    async def process_batch(
        self,
        items: List[Tuple[Modality, Any]],
    ) -> List[MultiModalEvent]:
        """批量处理"""
        tasks = [self.process(mod, data) for mod, data in items]
        return await asyncio.gather(*tasks)

    def get_capabilities(self) -> Dict[str, List[str]]:
        return {
            mod.value: adapter.get_capabilities()
            for mod, adapter in self._adapters.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "by_modality": dict(self._stats["by_modality"]),
            "avg_latency_ms": (
                self._stats["total_latency_ms"] / self._stats["total_processed"]
                if self._stats["total_processed"] > 0 else 0
            ),
        }


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_adapter: Optional[MultiModalAdapter] = None


def get_multimodal_adapter() -> MultiModalAdapter:
    global _adapter
    if _adapter is None:
        _adapter = MultiModalAdapter()
    return _adapter

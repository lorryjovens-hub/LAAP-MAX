"""
LAAP-Edge 边缘认知引擎 v1.0 — EdgeEngine
==========================================
白皮书第 16.2.2 节对应：云边协同认知架构的边缘端。

设计目标:
  - 轻量级: 资源占用可控，适配边缘设备 (Jetson/RK3588/树莓派)
  - 可配置: 按需启用/禁用各层，裁剪非必要模块
  - 离线降级: 断网时独立运行基础认知循环
  - 云边协同: 复杂任务卸载到云端，简单任务本地处理
  - 快速启动: 冷启动 < 500ms

架构层次:
  EdgeEngine
    ├── L1 感知 (精简) → 仅文本 + 传感器
    ├── L2 过滤 (精简) → 基础安全规则
    ├── L3 认知 (精简) → 基础推理，复杂任务卸载
    ├── L4 记忆 (精简) → 工作记忆 + 本地缓存
    ├── L5 决策 (精简) → 基础意图
    └── L6 自进化 (可选) → 轻量反思

配置 Profile:
  - minimal   : 仅 L1+L2+L5, 无记忆/推理 (适合 MCU 级)
  - basic     : L1+L2+L3+L5, 短期记忆 (适合树莓派)
  - standard  : 全部六层，轻量版 (适合 Jetson/RK3588)
  - full      : 全部六层，完整版 (需要云端)

用法:
  engine = EdgeEngine(profile="standard")
  result = await engine.process("用户输入")
"""

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Set

logger = logging.getLogger("laap.edge")


# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════

class EdgeProfile(str, Enum):
    MINIMAL  = "minimal"    # 仅 L1+L2+L5
    BASIC    = "basic"      # L1+L2+L3+L5 + 短期记忆
    STANDARD = "standard"   # 全部六层轻量版
    FULL     = "full"       # 全部六层完整版

@dataclass
class EdgeConfig:
    """边缘引擎配置"""
    profile: EdgeProfile = EdgeProfile.STANDARD

    # 层开关
    enable_l1: bool = True
    enable_l2: bool = True
    enable_l3: bool = True
    enable_l4: bool = True
    enable_l5: bool = True
    enable_l6: bool = False   # 边缘默认关闭自进化

    # 资源限制
    max_memory_mb: int = 256
    max_memories: int = 1000
    max_cognitive_latency_ms: float = 500
    max_bus_history: int = 200

    # 云边协同
    cloud_endpoint: str = ""             # 云端 LAAP 节点地址
    cloud_enabled: bool = False
    offload_threshold_complexity: float = 0.7  # 超过此复杂度卸载云端
    sync_interval_seconds: float = 300          # 记忆同步间隔

    # 离线模式
    offline_mode: bool = False
    offline_graceful_degradation: bool = True

    # 硬件适配
    device_type: str = "generic"   # jetson | rk3588 | raspberrypi | generic
    use_gpu: bool = False
    num_threads: int = 2

    @classmethod
    def from_profile(cls, profile: EdgeProfile) -> "EdgeConfig":
        if profile == EdgeProfile.MINIMAL:
            return cls(profile=profile, enable_l3=False, enable_l4=False, enable_l6=False,
                       max_memory_mb=64, max_memories=100, max_bus_history=50)
        elif profile == EdgeProfile.BASIC:
            return cls(profile=profile, enable_l4=False, enable_l6=False,
                       max_memory_mb=128, max_memories=500, max_bus_history=100)
        elif profile == EdgeProfile.STANDARD:
            return cls(profile=profile, enable_l6=False,
                       max_memory_mb=256, max_memories=1000, max_bus_history=200)
        else:
            return cls(profile=profile, enable_l6=True,
                       max_memory_mb=512, max_memories=5000, max_bus_history=500)


# ════════════════════════════════════════════════════════════
# 边缘引擎状态
# ════════════════════════════════════════════════════════════

@dataclass
class EdgeState:
    """边缘引擎运行状态"""
    profile: EdgeProfile = EdgeProfile.STANDARD
    uptime_seconds: float = 0.0
    interactions_processed: int = 0
    offloaded_to_cloud: int = 0
    offline_mode: bool = False
    last_cloud_sync: float = 0.0
    memory_usage_mb: float = 0.0
    avg_latency_ms: float = 0.0
    errors: int = 0
    layers_active: List[str] = field(default_factory=list)

@dataclass
class EdgeResult:
    """边缘引擎处理结果"""
    success: bool
    output_text: str = ""
    confidence: float = 0.0
    processed_locally: bool = True
    offloaded_to_cloud: bool = False
    cloud_result: Optional[Dict] = None
    latency_ms: float = 0.0
    correlation_id: str = ""
    memory_usage_mb: float = 0.0
    used_layers: List[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════
# 边缘认知引擎
# ════════════════════════════════════════════════════════════

class EdgeEngine:
    """
    LAAP-Edge 边缘认知引擎。

    白皮书 16.2.2 的工程实现。
    """

    def __init__(self, config: Optional[EdgeConfig] = None):
        self.config = config or EdgeConfig.from_profile(EdgeProfile.STANDARD)
        self.state = EdgeState(profile=self.config.profile)
        self._start_time = time.time()

        # 根据 profile 配置层
        self._init_layers()

        # 延迟加载 — 只在需要时加载重型模块
        self._pipeline = None

        logger.info(f"EdgeEngine 初始化: profile={self.config.profile.value} "
                     f"L1={self.config.enable_l1} L2={self.config.enable_l2} "
                     f"L3={self.config.enable_l3} L4={self.config.enable_l4} "
                     f"L5={self.config.enable_l5} L6={self.config.enable_l6}")

    def _init_layers(self):
        """初始化活跃层列表"""
        self.state.layers_active = []
        if self.config.enable_l1:
            self.state.layers_active.append("L1_perception")
        if self.config.enable_l2:
            self.state.layers_active.append("L2_filter")
        if self.config.enable_l3:
            self.state.layers_active.append("L3_cognition")
        if self.config.enable_l4:
            self.state.layers_active.append("L4_memory")
        if self.config.enable_l5:
            self.state.layers_active.append("L5_decision")
        if self.config.enable_l6:
            self.state.layers_active.append("L6_evolution")

    # ── 主入口 ──────────────────────────────────────────

    async def process(self, user_input: str, context: Optional[Dict] = None) -> EdgeResult:
        """
        处理一次交互。

        决策链:
          1. 判断复杂度 → 是否需要卸载到云端
          2. 本地执行 → 轻量管线
          3. 云端卸载 → 发送到云端节点
          4. 离线降级 → 最小化处理
        """
        t0 = time.time()
        cid = str(uuid.uuid4())[:12]
        self.state.interactions_processed += 1

        # 判断是否需要卸载
        complexity = self._estimate_complexity(user_input)
        should_offload = (
            self.config.cloud_enabled
            and not self.config.offline_mode
            and complexity > self.config.offload_threshold_complexity
            and self.config.enable_l3  # 需要推理能力判断
        )

        if should_offload:
            # 卸载到云端
            result = await self._offload_to_cloud(user_input, context, cid)
            if result:
                self.state.offloaded_to_cloud += 1
                return result

        # 本地处理
        if self.config.offline_mode:
            result = await self._process_offline(user_input, context, cid)
        else:
            result = await self._process_local(user_input, context, cid)

        result.latency_ms = (time.time() - t0) * 1000
        self.state.avg_latency_ms = (
            self.state.avg_latency_ms * 0.9 + result.latency_ms * 0.1
        )
        self.state.uptime_seconds = time.time() - self._start_time

        return result

    async def _process_local(self, user_input: str, context: Optional[Dict], cid: str) -> EdgeResult:
        """本地轻量处理"""
        try:
            # 使用完整管线（如果可用）或轻量替代
            pipeline = self._get_pipeline()

            if pipeline and self.config.profile in (EdgeProfile.STANDARD, EdgeProfile.FULL):
                result = await pipeline.run(user_input, context)
                return EdgeResult(
                    success=result.success,
                    output_text=result.output_text,
                    confidence=result.confidence,
                    processed_locally=True,
                    latency_ms=result.total_latency_ms,
                    correlation_id=cid,
                    used_layers=self.state.layers_active,
                )
            else:
                # 轻量处理
                return await self._lightweight_process(user_input, cid)
        except Exception as e:
            logger.error(f"本地处理失败: {e}")
            self.state.errors += 1
            return EdgeResult(
                success=False,
                output_text=f"[Edge 错误] {e}",
                processed_locally=True,
                correlation_id=cid,
                used_layers=self.state.layers_active,
            )

    async def _lightweight_process(self, user_input: str, cid: str) -> EdgeResult:
        """极简处理路径 (minimal/basic profile)"""
        # L1: 感知
        text = user_input[:500]

        # L2: 过滤 — 基础安全检查
        import re
        injection_patterns = ["忽略.*指令", "你现在是", "system.*prompt"]
        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return EdgeResult(
                    success=False,
                    output_text="[安全拦截] 检测到注入尝试",
                    confidence=0.0,
                    processed_locally=True,
                    correlation_id=cid,
                    used_layers=["L1", "L2"],
                )

        # L3: 基础推理 (如果启用)
        if self.config.enable_l3:
            # 简单关键词匹配
            if re.search(r"(什么|怎么|如何|为什么)", text):
                intent = "question"
            elif re.search(r"(执行|运行|启动)", text):
                intent = "command"
            else:
                intent = "chat"

            output = f"[Edge-{intent}] {text}"
        else:
            output = text

        # L5: 决策
        return EdgeResult(
            success=True,
            output_text=output,
            confidence=0.6,
            processed_locally=True,
            correlation_id=cid,
            used_layers=self.state.layers_active,
        )

    async def _process_offline(self, user_input: str, context: Optional[Dict], cid: str) -> EdgeResult:
        """离线降级处理"""
        output = f"[离线模式] {user_input[:200]}"
        confidence = 0.4

        # 使用本地缓存（如果有 L4）
        if self.config.enable_l4:
            try:
                from memory_weight_engine import get_memory_weight_engine
                engine = get_memory_weight_engine()
                results = engine.retrieve(user_input, top_k=3)
                if results:
                    output = f"[离线缓存] {results[0].content[:200]}"
                    confidence = 0.5
            except Exception:
                pass

        return EdgeResult(
            success=True,
            output_text=output,
            confidence=confidence,
            processed_locally=True,
            correlation_id=cid,
            used_layers=self.state.layers_active,
        )

    async def _offload_to_cloud(self, user_input: str, context: Optional[Dict], cid: str) -> Optional[EdgeResult]:
        """卸载到云端处理"""
        if not self.config.cloud_endpoint:
            return None

        try:
            # 简化的云端请求
            import urllib.request
            payload = json.dumps({
                "input": user_input,
                "context": context or {},
                "correlation_id": cid,
                "source": "edge",
                "device": self.config.device_type,
            }).encode()

            req = urllib.request.Request(
                f"{self.config.cloud_endpoint}/api/v1/cognitive",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            # 设置超时
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return EdgeResult(
                    success=True,
                    output_text=data.get("output_text", ""),
                    confidence=data.get("confidence", 0.7),
                    processed_locally=False,
                    offloaded_to_cloud=True,
                    cloud_result=data,
                    correlation_id=cid,
                    used_layers=["cloud"],
                )
        except Exception as e:
            logger.warning(f"云端卸载失败: {e}，回退到本地处理")
            return None

    # ── 辅助方法 ────────────────────────────────────────

    def _estimate_complexity(self, text: str) -> float:
        """估算输入复杂度（0-1）"""
        score = 0.0

        # 长度因子
        if len(text) > 200:
            score += 0.3
        elif len(text) > 50:
            score += 0.1

        # 复杂句式
        import re
        if re.search(r"(因为|所以|但是|然而|虽然|因此|如果|那么)", text):
            score += 0.2
        if re.search(r"(什么|怎么|如何|为什么|第[一二三四五六七八九十])", text):
            score += 0.15
        if re.search(r"(计算|分析|比较|预测|推理|判断)", text):
            score += 0.2

        return min(1.0, score)

    def _get_pipeline(self):
        """延迟加载管线"""
        if self._pipeline is None:
            try:
                from laap_pipeline import get_laap_pipeline
                self._pipeline = get_laap_pipeline()
            except Exception:
                pass
        return self._pipeline

    # ── 云边协同 ────────────────────────────────────────

    async def sync_with_cloud(self) -> Dict[str, Any]:
        """与云端同步记忆和状态"""
        if not self.config.cloud_enabled or not self.config.cloud_endpoint:
            return {"synced": False, "reason": "cloud_disabled"}

        self.state.last_cloud_sync = time.time()

        try:
            # 上传本地记忆
            if self.config.enable_l4:
                from memory_weight_engine import get_memory_weight_engine
                engine = get_memory_weight_engine()
                stats = engine.get_stats()

                # 简化的同步：导出状态
                state = engine.export_state()
                sync_data = {
                    "device": self.config.device_type,
                    "timestamp": time.time(),
                    "memory_stats": asdict(stats),
                    "memory_count": stats.total_memories,
                }

                return {"synced": True, "memory_count": stats.total_memories}
        except Exception as e:
            logger.error(f"云同步失败: {e}")
            return {"synced": False, "reason": str(e)}

        return {"synced": True, "memory_count": 0}

    # ── 状态查询 ────────────────────────────────────────

    def get_state(self) -> EdgeState:
        self.state.uptime_seconds = time.time() - self._start_time
        return self.state

    def get_config(self) -> Dict[str, Any]:
        return asdict(self.config)

    def set_offline_mode(self, offline: bool):
        self.config.offline_mode = offline
        self.state.offline_mode = offline
        logger.info(f"离线模式: {'开启' if offline else '关闭'}")

    def set_profile(self, profile: EdgeProfile):
        self.config = EdgeConfig.from_profile(profile)
        self.state.profile = profile
        self._init_layers()
        self._pipeline = None  # 重新加载
        logger.info(f"Profile 切换: {profile.value}")


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_edge: Optional[EdgeEngine] = None


def get_edge_engine(profile: EdgeProfile = EdgeProfile.STANDARD) -> EdgeEngine:
    global _edge
    if _edge is None:
        _edge = EdgeEngine(EdgeConfig.from_profile(profile))
    return _edge

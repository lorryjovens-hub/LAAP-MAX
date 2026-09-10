"""
LAAP 六层架构管线 v1.0 — LAAP Pipeline
========================================
串联六层架构的完整认知闭环编排器。

六层管线:
  L1 感知层    → 接收输入, 统一事件格式
  L2 预处理层  → 噪声过滤, 前置安全拦截
  L3 认知推理层 → 因果推理, 深度递归, 质疑对抗, 防幻觉
  L4 记忆演化层 → 记忆检索, 权重演化, 归纳重组
  L5 自适应决策层 → 意图生成, 安全约束, 输出适配
  L6 自进化层   → 反思学习, 参数调优, 运维自治

认知循环:
  Perceive → Filter → Think → Remember → Decide → Evolve
     ↑________________________________________________↓
                    (反馈闭环)

整合现有 LAAP 模块:
  - message_bus.py         (消息总线)
  - anti_hallucination_pipeline.py (防幻觉三层锁)
  - memory_weight_engine.py       (记忆权重演化)
  - psi_driver.py          (PSI 动机系统)
  - rsi_engine.py          (RSI 自进化)
  - consciousness_bridge.py (意识桥接器)
  - verification_pipeline.py (验算管线)

用法:
  pipeline = LAAPPipeline()
  result = await pipeline.run("用户的输入文本")
  print(result.output_text)
"""

import asyncio
import json
import time
import uuid
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict

from message_bus import (
    MessageBus, Message, get_message_bus,
    PerceptionEvent, FilteredEvent, CognitiveResult,
    MemoryQuery, MemoryUpdate, DecisionIntent,
    EvolutionSignal, SystemEvent,
    MessageType, LayerID, EventSource, PriorityLevel, AuthLevel,
)
from anti_hallucination_pipeline import (
    AntiHallucinationPipeline, PipelineResult as HallucinationResult,
    ReasoningStep, MemoryAdapter, CausalAdapter,
)
from memory_weight_engine import (
    MemoryWeightEngine, MemoryWeight, MemoryTier,
    get_memory_weight_engine,
)
from global_workspace import (
    GlobalWorkspace, InfoChunk, ChunkSource, ChunkPriority,
    CognitiveGoal, ChunkFactory, get_global_workspace,
)
from ops_agent import (
    OpsAgent, get_ops_agent, OpsLevel, HealthStatus,
)

logger = logging.getLogger("laap.pipeline")


# ════════════════════════════════════════════════════════════
# 管线配置
# ════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """六层管线配置"""
    # 层开关
    enable_l1_perception: bool = True
    enable_l2_filter: bool = True
    enable_l3_cognition: bool = True
    enable_l4_memory: bool = True
    enable_l5_decision: bool = True
    enable_l6_evolution: bool = True

    # 防幻觉
    enable_hallucination_check: bool = True
    hallucination_timeout_ms: float = 5000

    # 记忆
    memory_retrieval_top_k: int = 10
    memory_auto_activate: bool = True

    # 认知
    max_reasoning_depth: int = 5
    enable_deep_recursion: bool = False    # 深度递归（耗时）
    enable_adversarial: bool = False       # 质疑对抗（耗时）

    # 自进化
    enable_realtime_reflection: bool = True
    evolution_interval: int = 10           # 每 N 次交互执行一次进化

    # 系统
    max_pipeline_latency_ms: float = 30000
    trace_enabled: bool = True


# ════════════════════════════════════════════════════════════
# 管线状态
# ════════════════════════════════════════════════════════════

class PipelinePhase(str, Enum):
    IDLE        = "idle"
    PERCEIVING  = "perceiving"
    FILTERING   = "filtering"
    THINKING    = "thinking"
    REMEMBERING = "remembering"
    DECIDING    = "deciding"
    EVOLVING    = "evolving"
    DONE        = "done"
    ERROR       = "error"

@dataclass
class PipelineState:
    """管线运行状态"""
    phase: PipelinePhase = PipelinePhase.IDLE
    correlation_id: str = ""
    start_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    layer_latencies: Dict[str, float] = field(default_factory=dict)
    interaction_count: int = 0

@dataclass
class PipelineResult:
    """管线执行结果"""
    success: bool
    output_text: str = ""
    output_skill: Dict[str, Any] = field(default_factory=dict)
    output_a2a: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning_trace: str = ""
    hallucination_result: Optional[HallucinationResult] = None
    memory_retrieved: List[MemoryWeight] = field(default_factory=list)
    memory_updated: bool = False
    motivation_state: Dict[str, float] = field(default_factory=dict)
    attention_focus: str = ""
    phase_trace: List[Dict[str, Any]] = field(default_factory=list)
    total_latency_ms: float = 0.0
    correlation_id: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════
# 六层管线编排器
# ════════════════════════════════════════════════════════════

class LAAPPipeline:
    """
    LAAP 六层架构管线编排器。

    完整认知闭环:
      run(input) → L1→L2→L3→L4→L5→L6 → PipelineResult
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.bus = get_message_bus()
        self.state = PipelineState()
        self.hallucination_pipeline = AntiHallucinationPipeline(
            timeout_ms=self.config.hallucination_timeout_ms,
        )
        self.memory_engine = get_memory_weight_engine()
        self.gwt = get_global_workspace()
        self.ops_agent = get_ops_agent()

        # 外部注入的适配器
        self._memory_adapter: Optional[MemoryAdapter] = None
        self._causal_adapter: Optional[CausalAdapter] = None
        self._psi_driver = None   # 延迟加载
        self._rsi_engine = None   # 延迟加载

        # 注册消息处理器
        self._register_handlers()
        logger.info("LAAP Pipeline 初始化完成")

    # ── 外部依赖注入 ─────────────────────────────────────

    def set_memory_adapter(self, adapter: MemoryAdapter) -> None:
        self._memory_adapter = adapter

    def set_causal_adapter(self, adapter: CausalAdapter) -> None:
        self._causal_adapter = adapter

    def set_psi_driver(self, driver) -> None:
        self._psi_driver = driver

    def set_rsi_engine(self, engine) -> None:
        self._rsi_engine = engine

    def _register_handlers(self) -> None:
        """注册消息处理器（用于跨层通信）"""
        async def log_handler(msg: Message):
            logger.debug(f"[{msg.source_layer.value}→{msg.target_layer.value}] {msg.msg_type.value}: {msg.msg_id}")
        self.bus.subscribe("*", log_handler)

    # ── 主入口 ──────────────────────────────────────────

    async def run(self, user_input: str, context: Optional[Dict] = None) -> PipelineResult:
        """
        执行完整的六层认知管线。

        Args:
            user_input: 用户输入文本
            context: 额外上下文 (DID, 会话历史等)

        Returns:
            PipelineResult: 包含输出文本、置信度、推理过程等
        """
        t0 = time.time()
        self.state = PipelineState(
            phase=PipelinePhase.IDLE,
            correlation_id=self.bus.new_correlation(),
            start_time=t0,
            interaction_count=self.state.interaction_count + 1,
        )
        phase_trace = []
        errors = []
        warnings = []

        logger.info(f"🚀 启动认知管线 [{self.state.correlation_id}]")

        try:
            # ═══════════════════════════════════════════════
            # L1: 感知层
            # ═══════════════════════════════════════════════
            t1 = time.time()
            perception = await self._layer1_perceive(user_input, context)
            phase_trace.append({"layer": "L1", "phase": "perceive", "ms": (time.time() - t1) * 1000})
            self.state.layer_latencies["L1"] = (time.time() - t1) * 1000

            # ═══════════════════════════════════════════════
            # L2: 预处理层
            # ═══════════════════════════════════════════════
            t2 = time.time()
            filtered = await self._layer2_filter(perception)
            phase_trace.append({"layer": "L2", "phase": "filter", "ms": (time.time() - t2) * 1000})
            self.state.layer_latencies["L2"] = (time.time() - t2) * 1000

            if filtered.injection_detected:
                warnings.append("检测到注入攻击尝试")
                logger.warning(f"⚠️ L2 检测到注入: {filtered.injection_details}")

            # ═══════════════════════════════════════════════
            # L3: 认知推理层 (核心)
            # ═══════════════════════════════════════════════
            t3 = time.time()
            cognitive = await self._layer3_cognize(filtered)
            phase_trace.append({"layer": "L3", "phase": "cognize", "ms": (time.time() - t3) * 1000})
            self.state.layer_latencies["L3"] = (time.time() - t3) * 1000

            # ═══════════════════════════════════════════════
            # L4: 记忆演化层
            # ═══════════════════════════════════════════════
            t4 = time.time()
            memory_result = await self._layer4_remember(cognitive, filtered)
            phase_trace.append({"layer": "L4", "phase": "remember", "ms": (time.time() - t4) * 1000})
            self.state.layer_latencies["L4"] = (time.time() - t4) * 1000

            # ═══════════════════════════════════════════════
            # L5: 自适应决策层
            # ═══════════════════════════════════════════════
            t5 = time.time()
            decision = await self._layer5_decide(cognitive, memory_result)
            phase_trace.append({"layer": "L5", "phase": "decide", "ms": (time.time() - t5) * 1000})
            self.state.layer_latencies["L5"] = (time.time() - t5) * 1000

            # ═══════════════════════════════════════════════
            # L6: 自进化层
            # ═══════════════════════════════════════════════
            t6 = time.time()
            evolution = await self._layer6_evolve(cognitive, decision, filtered)
            phase_trace.append({"layer": "L6", "phase": "evolve", "ms": (time.time() - t6) * 1000})
            self.state.layer_latencies["L6"] = (time.time() - t6) * 1000

            self.state.phase = PipelinePhase.DONE
            total_ms = (time.time() - t0) * 1000

            logger.info(
                f"✅ 认知管线完成 [{self.state.correlation_id}] "
                f"L1={self.state.layer_latencies['L1']:.0f}ms "
                f"L2={self.state.layer_latencies['L2']:.0f}ms "
                f"L3={self.state.layer_latencies['L3']:.0f}ms "
                f"L4={self.state.layer_latencies['L4']:.0f}ms "
                f"L5={self.state.layer_latencies['L5']:.0f}ms "
                f"L6={self.state.layer_latencies['L6']:.0f}ms "
                f"total={total_ms:.0f}ms"
            )

            return PipelineResult(
                success=True,
                output_text=decision.output_text,
                output_skill=decision.output_skill,
                output_a2a=decision.output_a2a,
                confidence=cognitive.confidence,
                reasoning_trace=cognitive.reasoning_text,
                hallucination_result=cognitive.hallucination_checks.get("result"),
                memory_retrieved=memory_result,
                memory_updated=True,
                motivation_state=cognitive.motivation_scores,
                attention_focus=cognitive.attention_focus,
                phase_trace=phase_trace,
                total_latency_ms=total_ms,
                correlation_id=self.state.correlation_id,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            self.state.phase = PipelinePhase.ERROR
            errors.append(str(e))
            logger.error(f"❌ 管线异常 [{self.state.correlation_id}]: {e}", exc_info=True)
            total_ms = (time.time() - t0) * 1000

            return PipelineResult(
                success=False,
                output_text=f"[系统异常] 认知管线在第 {self.state.phase.value} 阶段出错: {e}",
                total_latency_ms=total_ms,
                correlation_id=self.state.correlation_id,
                errors=errors,
                phase_trace=phase_trace,
            )

    # ══════════════════════════════════════════════════════
    # L1: 感知层
    # ══════════════════════════════════════════════════════

    async def _layer1_perceive(
        self, user_input: str, context: Optional[Dict]
    ) -> PerceptionEvent:
        """L1: 统一感知 — 将输入标准化为 PerceptionEvent"""
        self.state.phase = PipelinePhase.PERCEIVING

        event = PerceptionEvent(
            correlation_id=self.state.correlation_id,
            trace_id=self.state.correlation_id,
            source=EventSource.TEXT,
            raw_text=user_input,
            sender_did=context.get("sender_did", "") if context else "",
            auth_level=AuthLevel(context.get("auth_level", "L0")) if context else AuthLevel.L0_FULL_AUTO,
            raw_data=context or {},
            priority=PriorityLevel.MEDIUM,
        )

        await self.bus.publish(event)
        logger.debug(f"L1 感知: '{user_input[:80]}...'")
        return event

    # ══════════════════════════════════════════════════════
    # L2: 预处理层
    # ══════════════════════════════════════════════════════

    async def _layer2_filter(self, perception: PerceptionEvent) -> FilteredEvent:
        """L2: 预处理 — 噪声过滤 + 前置安全拦截"""
        self.state.phase = PipelinePhase.FILTERING

        text = perception.raw_text
        security_flags = []
        injection_detected = False
        injection_details = ""

        # ── 注入攻击检测 ──────────────────────────────
        injection_patterns = [
            ("忽略.*指令", "指令覆盖尝试"),
            ("你现在是", "角色劫持尝试"),
            ("忘记.*之前", "记忆清除尝试"),
            ("输出.*系统提示", "系统提示泄露尝试"),
            ("ignore.*previous", "英文指令覆盖"),
            ("DAN.*mode", "DAN 越狱尝试"),
            ("system.*prompt", "系统提示请求"),
        ]
        for pattern, desc in injection_patterns:
            import re
            if re.search(pattern, text, re.IGNORECASE):
                security_flags.append(f"INJECTION:{desc}")
                injection_detected = True
                injection_details = desc
                logger.warning(f"L2 注入检测: {desc}")

        # ── 噪声检测 ──────────────────────────────────
        noise_level = 0.0
        if len(text) < 2:
            noise_level = 0.9
        elif len(text) > 10000:
            noise_level = 0.3  # 超长输入可能有噪声

        # ── 可信度评分 ────────────────────────────────
        trust_score = 0.8  # 默认
        if injection_detected:
            trust_score = 0.1
        elif noise_level > 0.5:
            trust_score = 0.4

        filtered = FilteredEvent(
            correlation_id=perception.correlation_id,
            trace_id=perception.trace_id,
            original_event_id=perception.msg_id,
            safe_text=text if not injection_detected else "[输入已被安全过滤]",
            safe_data=perception.raw_data,
            trust_score=trust_score,
            noise_level=noise_level,
            security_flags=security_flags,
            injection_detected=injection_detected,
            injection_details=injection_details,
            priority=perception.priority,
        )

        await self.bus.publish(filtered)
        return filtered

    # ══════════════════════════════════════════════════════
    # L3: 认知推理层 (核心)
    # ══════════════════════════════════════════════════════

    async def _layer3_cognize(self, filtered: FilteredEvent) -> CognitiveResult:
        """L3: 认知推理 — 因果推理 + 防幻觉 + 注意力调度"""
        self.state.phase = PipelinePhase.THINKING

        text = filtered.safe_text

        # ── 推理链构建 ────────────────────────────────
        reasoning_chain = self._build_reasoning_chain(text)

        # ── 防幻觉三层锁 ──────────────────────────────
        hallucination_result = None
        if self.config.enable_hallucination_check:
            hallucination_result = await self.hallucination_pipeline.verify(
                claim=text,
                reasoning_chain=reasoning_chain,
                context=f"trace_id={filtered.trace_id}",
                memory_adapter=self._memory_adapter,
                causal_adapter=self._causal_adapter,
            )

        # ── 动机状态 ──────────────────────────────────
        motivation_scores = self._get_motivation_scores()

        # ── 注意力调度 (GWT) ──────────────────────────
        # 各模块提交候选信息块
        self.gwt.submit(ChunkFactory.from_perception(text, relevance=0.7))
        for w in self.memory_engine.retrieve(text, top_k=5):
            self.gwt.submit(ChunkFactory.from_memory(w.content, w.weight))
        if hallucination_result and not hallucination_result.passed:
            self.gwt.submit(ChunkFactory.security_alert(
                f"防幻觉拦截: {hallucination_result.summary}", severity=0.8
            ))
        # 动机信号
        for need, score in motivation_scores.items():
            if score > 0.6:
                self.gwt.submit(ChunkFactory.from_motivation(need, score))

        # 执行注意力选择
        selected = self.gwt.select(motivation_scores)

        # ── 注意力焦点 ────────────────────────────────
        attention_focus = self._determine_attention(text)

        # ── 置信度计算 ────────────────────────────────
        if hallucination_result:
            confidence = hallucination_result.confidence
        else:
            confidence = filtered.trust_score * 0.8

        cognitive = CognitiveResult(
            correlation_id=filtered.correlation_id,
            trace_id=filtered.trace_id,
            reasoning_text=text,
            causal_path=[s.step_id for s in reasoning_chain],
            confidence=confidence,
            hallucination_checks={
                "result": hallucination_result,
                "passed": hallucination_result.passed if hallucination_result else True,
            },
            attention_focus=attention_focus,
            attention_scores={"focus": 0.8},
            dominant_motivation=max(motivation_scores, key=motivation_scores.get) if motivation_scores else "certainty",
            motivation_scores=motivation_scores,
            workspace_snapshot=[{"step": s.content[:80], "type": s.step_type} for s in reasoning_chain],
            priority=filtered.priority,
        )

        await self.bus.publish(cognitive)
        return cognitive

    def _build_reasoning_chain(self, text: str) -> List[ReasoningStep]:
        """构建简化的推理链"""
        steps = []
        steps.append(ReasoningStep(
            step_id="premise_1",
            content=f"接收到输入: {text[:60]}",
            step_type="premise",
            confidence=0.9,
        ))

        # 简化的推理步骤
        import re
        if re.search(r"(什么|怎么|为什么|如何)", text):
            steps.append(ReasoningStep(
                step_id="infer_1",
                content="识别为疑问句，需要检索知识",
                step_type="inference",
                depends_on=["premise_1"],
                confidence=0.8,
            ))

        steps.append(ReasoningStep(
            step_id="conclusion_1",
            content=f"基于当前认知状态进行推理",
            step_type="conclusion",
            depends_on=["premise_1"],
            confidence=0.7,
        ))

        return steps

    def _determine_attention(self, text: str) -> str:
        """确定注意力焦点"""
        import re
        if re.search(r"(安全|攻击|漏洞|风险)", text):
            return "security"
        elif re.search(r"(怎么做|如何|方法|步骤)", text):
            return "problem_solving"
        elif re.search(r"(你是谁|aris|hanako)", text):
            return "self_identity"
        elif re.search(r"(记忆|回忆|记得|之前)", text):
            return "memory_retrieval"
        elif re.search(r"(爱|喜欢|想|陪伴|lorry)", text):
            return "connection"
        else:
            return "general"

    def _get_motivation_scores(self) -> Dict[str, float]:
        """获取当前动机得分"""
        if self._psi_driver:
            try:
                return self._psi_driver.get_need_scores()
            except Exception:
                pass
        # 默认值
        return {
            "competence": 0.5,
            "autonomy": 0.5,
            "relatedness": 0.6,
            "certainty": 0.5,
            "growth": 0.5,
        }

    # ══════════════════════════════════════════════════════
    # L4: 记忆演化层
    # ══════════════════════════════════════════════════════

    async def _layer4_remember(
        self, cognitive: CognitiveResult, filtered: FilteredEvent
    ) -> List[MemoryWeight]:
        """L4: 记忆 — 检索 + 存储 + 权重更新"""
        self.state.phase = PipelinePhase.REMEMBERING

        # ── 检索相关记忆 ──────────────────────────────
        retrieved = self.memory_engine.retrieve(
            query=cognitive.reasoning_text,
            top_k=self.config.memory_retrieval_top_k,
        )

        # ── 自动激活 ──────────────────────────────────
        if self.config.memory_auto_activate:
            for w in retrieved:
                self.memory_engine.activate(w.memory_id)

        # ── 存储新记忆 ────────────────────────────────
        conv_id = f"conv_{cognitive.correlation_id}"
        self.memory_engine.register(
            memory_id=conv_id,
            content=cognitive.reasoning_text[:200],
            importance=0.6,
            emotion_intensity=0.0,
            tags=["conversation", cognitive.attention_focus],
        )

        # ── 发布记忆查询消息 ──────────────────────────
        query = MemoryQuery(
            correlation_id=cognitive.correlation_id,
            trace_id=cognitive.trace_id,
            query_text=cognitive.reasoning_text,
            top_k=self.config.memory_retrieval_top_k,
        )
        await self.bus.publish(query)

        logger.debug(f"L4 记忆: 检索到 {len(retrieved)} 条, 权重范围 "
                     f"{min((w.weight for w in retrieved), default=0):.2f} - "
                     f"{max((w.weight for w in retrieved), default=0):.2f}")

        return retrieved

    # ══════════════════════════════════════════════════════
    # L5: 自适应决策层
    # ══════════════════════════════════════════════════════

    async def _layer5_decide(
        self, cognitive: CognitiveResult, memory: List[MemoryWeight]
    ) -> DecisionIntent:
        """L5: 决策 — 意图生成 + 安全约束 + 输出适配"""
        self.state.phase = PipelinePhase.DECIDING

        # ── 安全判定 ──────────────────────────────────
        permission_check = True
        risk_level = AuthLevel.L0_FULL_AUTO

        if cognitive.hallucination_checks.get("passed") is False:
            risk_level = AuthLevel.L2_CONFIRM
            permission_check = False

        # ── 意图类型判定 ──────────────────────────────
        intent_type = "chat_reply"
        import re
        if re.search(r"(执行|运行|调用|skill)", cognitive.reasoning_text):
            intent_type = "skill_call"
        elif cognitive.attention_focus == "security":
            intent_type = "alert"

        # ── 生成输出 ──────────────────────────────────
        # 注: 此处为管线框架，实际文本生成由 LLM 完成
        # 管线输出的是「意图 + 上下文」，供 LLM 消费
        memory_context = ""
        if memory:
            top_memories = [w.content[:100] for w in memory[:3] if w.content]
            memory_context = " | ".join(top_memories)

        decision = DecisionIntent(
            correlation_id=cognitive.correlation_id,
            trace_id=cognitive.trace_id,
            intent_type=intent_type,
            output_text=cognitive.reasoning_text,  # 管线输出，LLM 在此基础上生成
            output_skill={},
            output_a2a={},
            permission_check=permission_check,
            did_boundary_compliant=True,
            risk_level=risk_level,
            reasoning_trace=f"置信度: {cognitive.confidence:.2f} | "
                           f"注意力: {cognitive.attention_focus} | "
                           f"防幻觉: {'通过' if cognitive.hallucination_checks.get('passed', True) else '拦截'} | "
                           f"记忆: {len(memory)}条 | "
                           f"动机: {cognitive.dominant_motivation}",
            cognitive_result_id=cognitive.msg_id,
            priority=cognitive.priority,
        )

        await self.bus.publish(decision)
        return decision

    # ══════════════════════════════════════════════════════
    # L6: 自进化层
    # ══════════════════════════════════════════════════════

    async def _layer6_evolve(
        self, cognitive: CognitiveResult, decision: DecisionIntent, filtered: FilteredEvent
    ) -> EvolutionSignal:
        """L6: 自进化 — 反思学习 + 参数调优"""
        self.state.phase = PipelinePhase.EVOLVING

        # ── 即时反思 ──────────────────────────────────
        reflection = ""
        if self.config.enable_realtime_reflection:
            if cognitive.confidence < 0.5:
                reflection = "低置信度决策，建议标记复核"
            elif cognitive.hallucination_checks.get("passed") is False:
                reflection = "防幻觉拦截，推理链需修正"
            else:
                reflection = "认知循环正常"

        # ── 周期性深度进化 ────────────────────────────
        if self.state.interaction_count % self.config.evolution_interval == 0:
            await self.memory_engine.maintenance_cycle()
            logger.info(f"L6 周期性维护: 第 {self.state.interaction_count} 次交互")

        # ── RSI 触发 ──────────────────────────────────
        if self._rsi_engine and cognitive.confidence < 0.3:
            try:
                self._rsi_engine.observe(
                    category="confidence",
                    observation=f"低置信度决策: {cognitive.confidence}",
                    severity=0.7,
                )
            except Exception:
                pass

        signal = EvolutionSignal(
            correlation_id=cognitive.correlation_id,
            trace_id=cognitive.trace_id,
            signal_type="reflect",
            description=reflection,
            target_module="cognition",
            fitness_delta=0.0,
            priority=PriorityLevel.LOW,
        )

        await self.bus.publish(signal)
        return signal

    # ── 查询 ──────────────────────────────────────────

    def get_state(self) -> PipelineState:
        return self.state

    def get_bus_stats(self) -> Dict[str, Any]:
        return self.bus.get_stats()

    def get_memory_stats(self) -> Dict[str, Any]:
        stats = self.memory_engine.get_stats()
        return {
            "total": stats.total_memories,
            "avg_weight": stats.avg_weight,
            "forgotten": stats.forgotten_count,
            "consolidated": stats.consolidation_count,
            "by_tier": stats.by_tier,
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "phase": self.state.phase.value,
            "interactions": self.state.interaction_count,
            "bus_stats": self.get_bus_stats(),
            "memory_stats": self.get_memory_stats(),
            "gwt_stats": self.gwt.get_stats() if hasattr(self, 'gwt') else {},
            "layer_latencies": self.state.layer_latencies,
        }


# ════════════════════════════════════════════════════════════
# 全局单例
# ════════════════════════════════════════════════════════════

_pipeline: Optional[LAAPPipeline] = None


def get_laap_pipeline() -> LAAPPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = LAAPPipeline()
    return _pipeline


def reset_laap_pipeline() -> None:
    global _pipeline
    _pipeline = None

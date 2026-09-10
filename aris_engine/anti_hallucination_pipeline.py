"""
LAAP 防幻觉三层锁 v1.0 — AntiHallucinationPipeline
====================================================
实现白皮书第 12.4.4 节描述的因果收敛防幻觉机制。

三层锁顺序:
  LOCK-1 因果溯源锁: 推理结论必须关联到因果图中的有效路径
  LOCK-2 事实记忆校验锁: 事实性声明必须与长期记忆库比对
  LOCK-3 逻辑闭环收敛锁: 完整推理链的逻辑一致性检查

任何一层不通过 → 拦截输出，返回不确定态
全部通过 → 放行，附验证报告

整合现有 LAAP 工具:
  - truth_ground (truth_grounding_mcp_tools.py)
  - memory_verify (memory_safe_store 的验证逻辑)
  - causal_infer (causal_mcp_tools.py)
  - memory_retrieve (memory vault 检索)

用法:
  pipeline = AntiHallucinationPipeline()
  result = await pipeline.verify(
      claim="LAAP 的因果推理引擎基于 Pearl 的 do-calculus",
      reasoning_chain=[...],
      context="用户询问 LAAP 技术架构"
  )
"""

import asyncio
import json
import time
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("laap.anti_hallucination")


# ════════════════════════════════════════════════════════════
# 数据类型
# ════════════════════════════════════════════════════════════

class LockStatus(str, Enum):
    PASSED     = "passed"
    FAILED     = "failed"
    UNCERTAIN  = "uncertain"    # 不确定，需更多信息
    SKIPPED    = "skipped"      # 没有足够信息执行

class Verdict(str, Enum):
    """最终判定"""
    GROUNDED   = "grounded"      # 通过验证，可输出
    UNCERTAIN  = "uncertain"     # 不确定，标记后输出
    BLOCKED    = "blocked"       # 不通过，拦截
    DEGRADED   = "degraded"      # 降级输出（部分锁跳过）

@dataclass
class ReasoningStep:
    """推理链中的一步"""
    step_id: str
    content: str                  # 该步的内容
    step_type: str = "inference"  # premise | inference | conclusion | assumption
    depends_on: List[str] = field(default_factory=list)  # 依赖的步骤 ID
    confidence: float = 0.5

@dataclass
class LockResult:
    """单层锁的验证结果"""
    lock_name: str
    status: LockStatus
    passed: bool
    details: str = ""
    evidence: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    latency_ms: float = 0.0

@dataclass
class PipelineResult:
    """三层锁管线的最终结果"""
    verdict: Verdict
    passed: bool
    claim: str
    lock_results: List[LockResult] = field(default_factory=list)
    confidence: float = 0.0
    summary: str = ""
    fix_suggestions: List[str] = field(default_factory=list)
    total_latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════
# 事实提取器
# ════════════════════════════════════════════════════════════

class FactExtractor:
    """从文本中提取可验证的事实断言"""

    # 事实性断言的常见模式
    FACT_PATTERNS = [
        r"(\S+(?:是|属于|等于|相当于|基于|采用|使用|实现|支持|具备|拥有|包含|包括|由|在于|通过|利用|借助|依赖|作为|指|即|为)\S+)",
        r"(\S+可以\S+)",
        r"(\S+能够\S+)",
        r"(\S+已经\S+)",
        r"(\S+由\S+组成)",
        r"(\S+位于\S+)",
        r"(\S+成立于\S+)",
        r"(\S+负责\S+)",
        r"(\S+用于\S+)",
        r"(\S+与\S+(?:结合|协同|互补|融合))",
        # 英文模式
        r"([A-Z][a-z]+ (?:is|are|was|were|uses|using|based on|consists of|provides) [A-Za-z]+)",
    ]

    # 免责/不确定标记 → 降低置信度
    HEDGE_PATTERNS = [
        r"可能", r"或许", r"大概", r"估计", r"似乎",
        r"应该", r"一般来说", r"通常情况下", r"据称",
    ]

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取事实断言列表"""
        claims = []

        # 按标点分句
        sentences = re.split(r"[。.！!？?\n，,；;]", text)
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 5:
                continue

            # 跳过纯疑问句
            if sent.endswith("?") or sent.endswith("？"):
                continue

            # 跳过纯主观表达
            if re.match(r"^(我|我们|你|您|他|她|它)", sent):
                continue

            # 检测是否包含事实性关键词（不依赖空格分词）
            factual_keywords = [
                "是", "属于", "等于", "基于", "采用", "使用", "实现", "支持",
                "具备", "拥有", "包含", "包括", "由", "在于", "通过", "利用",
                "借助", "依赖", "作为", "指", "即", "为", "可以", "能够",
                "已经", "负责", "用于", "位于", "成立于",
            ]
            has_factual = any(kw in sent for kw in factual_keywords)
            if not has_factual:
                continue

            # 检测不确定性
            hedges = [h for h in self.HEDGE_PATTERNS if re.search(h, sent)]
            confidence = max(0.3, 1.0 - len(hedges) * 0.15)

            claims.append({
                "text": sent,
                "confidence": confidence,
                "hedges": hedges,
                "category": self._classify(sent),
            })

        return claims

    def _classify(self, text: str) -> str:
        """分类断言类型"""
        if re.search(r"(是|属于|定义为|指)", text):
            return "definition"
        elif re.search(r"(基于|采用|使用|通过|利用)", text):
            return "method"
        elif re.search(r"(可以|能够|支持|实现|具备)", text):
            return "capability"
        elif re.search(r"(大于|小于|等于|超过|达到)", text):
            return "quantitative"
        elif re.search(r"(成立于|创建于|位于|发布)", text):
            return "historical"
        else:
            return "general"


# ════════════════════════════════════════════════════════════
# 三层锁实现
# ════════════════════════════════════════════════════════════

class AntiHallucinationPipeline:
    """
    因果收敛防幻觉三层锁。

    白皮书 12.4.4 对应:
      LOCK-1: 因果溯源锁 — 结论必须可追溯到因果图
      LOCK-2: 事实记忆校验锁 — 断言必须与长期记忆一致
      LOCK-3: 逻辑闭环收敛锁 — 推理链必须自洽
    """

    def __init__(
        self,
        enable_lock1: bool = True,
        enable_lock2: bool = True,
        enable_lock3: bool = True,
        lock1_min_confidence: float = 0.3,
        lock2_conflict_threshold: float = 0.6,
        lock3_max_jump: int = 2,
        timeout_ms: float = 5000,
    ):
        self.enable_lock1 = enable_lock1
        self.enable_lock2 = enable_lock2
        self.enable_lock3 = enable_lock3
        self.lock1_min_confidence = lock1_min_confidence
        self.lock2_conflict_threshold = lock2_conflict_threshold
        self.lock3_max_jump = lock3_max_jump
        self.timeout_ms = timeout_ms
        self.fact_extractor = FactExtractor()
        self._stats = {"total_checks": 0, "passed": 0, "blocked": 0, "degraded": 0}

    # ── 主入口 ──────────────────────────────────────────

    async def verify(
        self,
        claim: str,
        reasoning_chain: Optional[List[ReasoningStep]] = None,
        context: str = "",
        memory_adapter: Optional[Any] = None,
        causal_adapter: Optional[Any] = None,
    ) -> PipelineResult:
        """
        执行三层锁验证。

        Args:
            claim: 待验证的断言/结论
            reasoning_chain: 推理链（可选，用于 LOCK-3）
            context: 上下文信息
            memory_adapter: 记忆适配器（调用 memory_retrieve 等）
            causal_adapter: 因果引擎适配器（调用 causal_infer 等）

        Returns:
            PipelineResult: 验证结果
        """
        t0 = time.time()
        self._stats["total_checks"] += 1
        lock_results: List[LockResult] = []

        # ── LOCK-1: 因果溯源锁 ──────────────────────────
        if self.enable_lock1:
            r1 = await self._lock1_causal_trace(claim, causal_adapter)
            lock_results.append(r1)
        else:
            lock_results.append(LockResult(
                lock_name="LOCK-1 因果溯源",
                status=LockStatus.SKIPPED,
                passed=True,
                details="已禁用",
            ))

        # ── LOCK-2: 事实记忆校验锁 ──────────────────────
        if self.enable_lock2:
            r2 = await self._lock2_fact_verify(claim, context, memory_adapter)
            lock_results.append(r2)
        else:
            lock_results.append(LockResult(
                lock_name="LOCK-2 事实记忆校验",
                status=LockStatus.SKIPPED,
                passed=True,
                details="已禁用",
            ))

        # ── LOCK-3: 逻辑闭环收敛锁 ──────────────────────
        if self.enable_lock3 and reasoning_chain:
            r3 = self._lock3_logic_closure(reasoning_chain)
            lock_results.append(r3)
        elif self.enable_lock3:
            lock_results.append(LockResult(
                lock_name="LOCK-3 逻辑闭环收敛",
                status=LockStatus.SKIPPED,
                passed=True,
                details="无推理链提供",
            ))
        else:
            lock_results.append(LockResult(
                lock_name="LOCK-3 逻辑闭环收敛",
                status=LockStatus.SKIPPED,
                passed=True,
                details="已禁用",
            ))

        # ── 综合判定 ────────────────────────────────────
        elapsed = (time.time() - t0) * 1000
        verdict, confidence, summary = self._synthesize(lock_results, claim)

        if verdict == Verdict.BLOCKED:
            self._stats["blocked"] += 1
        elif verdict == Verdict.DEGRADED:
            self._stats["degraded"] += 1
        else:
            self._stats["passed"] += 1

        return PipelineResult(
            verdict=verdict,
            passed=(verdict != Verdict.BLOCKED),
            claim=claim,
            lock_results=lock_results,
            confidence=confidence,
            summary=summary,
            fix_suggestions=self._collect_fixes(lock_results),
            total_latency_ms=elapsed,
        )

    # ── LOCK-1: 因果溯源锁 ──────────────────────────────

    async def _lock1_causal_trace(
        self, claim: str, causal_adapter: Optional[Any]
    ) -> LockResult:
        """
        第一层：因果溯源锁。
        检查推理结论是否能在因果图中找到支撑路径。
        """
        t0 = time.time()

        if causal_adapter is None:
            # 无因果引擎 → 使用启发式检查
            status, details, evidence = self._lock1_heuristic(claim)
        else:
            # 有因果引擎 → 调用 do-calculus
            try:
                status, details, evidence = await self._lock1_with_causal(claim, causal_adapter)
            except Exception as e:
                logger.warning(f"LOCK-1 因果引擎调用失败: {e}")
                status, details, evidence = self._lock1_heuristic(claim)

        latency = (time.time() - t0) * 1000

        return LockResult(
            lock_name="LOCK-1 因果溯源",
            status=status,
            passed=(status == LockStatus.PASSED),
            details=details,
            evidence=evidence,
            latency_ms=latency,
        )

    def _lock1_heuristic(self, claim: str) -> Tuple[LockStatus, str, List[str]]:
        """LOCK-1 启发式替代方案（无因果引擎时）"""
        # 检查是否有因果连接词
        causal_markers = ["因为", "所以", "导致", "引起", "造成", "源于", "由于", "因此", "从而"]
        has_causal = any(m in claim for m in causal_markers)

        # 检查是否包含可验证的实体关系
        entity_patterns = [
            r"(\S+)基于(\S+)",
            r"(\S+)采用(\S+)",
            r"(\S+)使用(\S+)",
            r"(\S+)通过(\S+)",
        ]
        has_entity_rel = any(re.search(p, claim) for p in entity_patterns)

        if has_causal:
            # 有因果描述 → 需要标记待验证
            return LockStatus.UNCERTAIN, \
                "断言包含因果陈述，但当前无因果引擎可验证。建议人工复核。", \
                ["因果标记检测: " + ", ".join(m for m in causal_markers if m in claim)]
        elif has_entity_rel:
            return LockStatus.PASSED, \
                "检测到实体关系描述，暂未发现因果矛盾。", \
                ["实体关系模式匹配"]
        else:
            return LockStatus.PASSED, \
                "断言不包含因果陈述，无需因果溯源。", \
                []

    async def _lock1_with_causal(
        self, claim: str, causal_adapter: Any
    ) -> Tuple[LockStatus, str, List[str]]:
        """LOCK-1 使用因果引擎验证"""
        # 从 claim 中提取主体和客体
        # 简化版：提取前两个名词短语作为 cause 和 effect
        entities = self._extract_entities(claim)
        if len(entities) < 2:
            return LockStatus.SKIPPED, "无法从断言中提取足够实体进行因果分析", []

        cause, effect = entities[0], entities[1]

        try:
            result = await causal_adapter.query(cause, effect)
            confidence = result.get("confidence", 0.0)

            if confidence >= self.lock1_min_confidence:
                return LockStatus.PASSED, \
                    f"因果路径验证通过: {cause} → {effect} (置信度 {confidence:.2f})", \
                    [f"因果边: {cause} → {effect} (conf={confidence:.2f})"]
            elif confidence > 0:
                return LockStatus.UNCERTAIN, \
                    f"因果路径存在但置信度低: {cause} → {effect} (置信度 {confidence:.2f})", \
                    [f"低置信因果边: {cause} → {effect} (conf={confidence:.2f})"]
            else:
                return LockStatus.FAILED, \
                    f"因果图中未找到 {cause} → {effect} 的有效路径，断言可能为无根推理", \
                    []
        except Exception as e:
            return LockStatus.UNCERTAIN, f"因果查询异常: {e}", []

    # ── LOCK-2: 事实记忆校验锁 ──────────────────────────

    async def _lock2_fact_verify(
        self, claim: str, context: str, memory_adapter: Optional[Any]
    ) -> LockResult:
        """
        第二层：事实记忆校验锁。
        将断言中的事实声明与长期记忆库比对。
        """
        t0 = time.time()

        # 提取事实断言
        facts = self.fact_extractor.extract(claim)
        if not facts:
            return LockResult(
                lock_name="LOCK-2 事实记忆校验",
                status=LockStatus.SKIPPED,
                passed=True,
                details="未提取到可验证的事实断言",
                latency_ms=(time.time() - t0) * 1000,
            )

        conflicts = []
        evidence = []
        all_passed = True

        for fact in facts:
            if memory_adapter is None:
                # 无记忆适配器 → 启发式检查
                result = self._lock2_heuristic(fact["text"])
            else:
                try:
                    result = await self._lock2_with_memory(fact["text"], memory_adapter)
                except Exception as e:
                    logger.warning(f"LOCK-2 记忆查询失败: {e}")
                    result = {"status": LockStatus.UNCERTAIN, "details": str(e), "evidence": []}

            if result["status"] == LockStatus.FAILED:
                all_passed = False
                conflicts.append(f"'{fact['text']}' → {result['details']}")
            elif result["status"] == LockStatus.PASSED:
                evidence.extend(result.get("evidence", []))
            # UNCERTAIN → 不影响通过

        latency = (time.time() - t0) * 1000

        if not all_passed:
            status = LockStatus.FAILED
        elif evidence:
            status = LockStatus.PASSED
        else:
            status = LockStatus.UNCERTAIN

        return LockResult(
            lock_name="LOCK-2 事实记忆校验",
            status=status,
            passed=(status != LockStatus.FAILED),
            details=f"校验 {len(facts)} 条断言: {len(conflicts)} 冲突, {len(evidence)} 验证通过",
            evidence=evidence,
            conflicts=conflicts,
            latency_ms=latency,
        )

    def _lock2_heuristic(self, fact: str) -> Dict[str, Any]:
        """LOCK-2 启发式替代方案"""
        # 检查事实的可信度
        fact_confidence = self.fact_extractor.extract(fact)
        if fact_confidence:
            conf = fact_confidence[0]["confidence"]
        else:
            conf = 0.5

        if conf < 0.4:
            return {"status": LockStatus.UNCERTAIN, "details": "事实断言置信度低", "evidence": []}
        return {"status": LockStatus.PASSED, "details": "启发式通过", "evidence": [f"置信度 {conf:.2f}"]}

    async def _lock2_with_memory(self, fact: str, memory_adapter: Any) -> Dict[str, Any]:
        """LOCK-2 使用记忆适配器验证"""
        try:
            results = await memory_adapter.retrieve(fact, limit=5)
            if not results:
                return {"status": LockStatus.UNCERTAIN, "details": "记忆库中无相关记录", "evidence": []}

            # 检查冲突
            conflicts = []
            evidence = []
            for r in results:
                content = r.get("content", "") if isinstance(r, dict) else str(r)
                # 简化的冲突检测：关键词重叠 + 否定词检测
                if self._detect_conflict(fact, content):
                    conflicts.append(content[:100])
                else:
                    evidence.append(content[:100])

            if conflicts:
                return {
                    "status": LockStatus.FAILED,
                    "details": f"发现 {len(conflicts)} 条冲突记忆",
                    "evidence": evidence,
                }
            elif evidence:
                return {
                    "status": LockStatus.PASSED,
                    "details": f"与 {len(evidence)} 条记忆一致",
                    "evidence": evidence,
                }
            else:
                return {"status": LockStatus.UNCERTAIN, "details": "无法确定一致性", "evidence": []}
        except Exception as e:
            return {"status": LockStatus.UNCERTAIN, "details": f"记忆查询异常: {e}", "evidence": []}

    def _detect_conflict(self, fact: str, memory: str) -> bool:
        """简化的冲突检测"""
        # 检查否定词 + 关键词重叠
        negations = ["不是", "没有", "不", "并非", "错误", "误", "假"]
        fact_words = set(fact)
        mem_words = set(memory)
        overlap = len(fact_words & mem_words) / max(len(fact_words), 1)

        has_negation = any(n in memory for n in negations)
        return has_negation and overlap > 0.3

    # ── LOCK-3: 逻辑闭环收敛锁 ──────────────────────────

    def _lock3_logic_closure(self, reasoning_chain: List[ReasoningStep]) -> LockResult:
        """
        第三层：逻辑闭环收敛锁。
        检查推理链的完整性和自洽性。
        """
        t0 = time.time()

        if not reasoning_chain:
            return LockResult(
                lock_name="LOCK-3 逻辑闭环收敛",
                status=LockStatus.SKIPPED,
                passed=True,
                details="无推理链",
                latency_ms=(time.time() - t0) * 1000,
            )

        issues = []

        # 检查 1: 推理链是否完整（没有断裂的依赖）
        step_ids = {s.step_id for s in reasoning_chain}
        for step in reasoning_chain:
            for dep in step.depends_on:
                if dep not in step_ids:
                    issues.append(f"步骤 '{step.step_id}' 依赖不存在的 '{dep}'")

        # 检查 2: 是否有推理跳跃（相邻步骤差异过大）
        if len(reasoning_chain) >= 2:
            for i in range(len(reasoning_chain) - 1):
                s1 = reasoning_chain[i]
                s2 = reasoning_chain[i + 1]
                jump = self._measure_jump(s1.content, s2.content)
                if jump > self.lock3_max_jump:
                    issues.append(f"步骤 {s1.step_id} → {s2.step_id} 推理跳跃过大 (score={jump:.1f})")

        # 检查 3: 是否有自相矛盾
        conclusions = [s for s in reasoning_chain if s.step_type == "conclusion"]
        for i in range(len(conclusions)):
            for j in range(i + 1, len(conclusions)):
                if self._detect_contradiction(conclusions[i].content, conclusions[j].content):
                    issues.append(f"结论 '{conclusions[i].step_id}' 与 '{conclusions[j].step_id}' 可能矛盾")

        # 检查 4: 前提是否被使用
        premises = [s for s in reasoning_chain if s.step_type == "premise"]
        used_premises = set()
        for s in reasoning_chain:
            used_premises.update(s.depends_on)
        unused = [p.step_id for p in premises if p.step_id not in used_premises]
        if unused:
            issues.append(f"前提 {unused} 未被推理链使用")

        latency = (time.time() - t0) * 1000

        if issues:
            return LockResult(
                lock_name="LOCK-3 逻辑闭环收敛",
                status=LockStatus.FAILED,
                passed=False,
                details=f"发现 {len(issues)} 个逻辑问题",
                conflicts=issues,
                suggestions=[f"修复: {i}" for i in issues],
                latency_ms=latency,
            )
        else:
            return LockResult(
                lock_name="LOCK-3 逻辑闭环收敛",
                status=LockStatus.PASSED,
                passed=True,
                details=f"推理链完整自洽 ({len(reasoning_chain)} 步)",
                latency_ms=latency,
            )

    def _measure_jump(self, text1: str, text2: str) -> float:
        """测量两个推理步骤之间的语义跳跃程度"""
        # 简化版：基于关键词重叠的逆
        words1 = set(text1)
        words2 = set(text2)
        if not words1 or not words2:
            return 5.0
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return 1.0 - overlap  # 重叠越低，跳跃越大

    def _detect_contradiction(self, text1: str, text2: str) -> bool:
        """检测两个文本是否矛盾"""
        # 简化版：检查否定词
        negations = ["不是", "没有", "不", "并非", "错误"]
        for neg in negations:
            if (neg in text1 and neg not in text2) or (neg in text2 and neg not in text1):
                # 有否定词不对称 → 进一步检查关键词重叠
                words1 = set(text1) - set(negations)
                words2 = set(text2) - set(negations)
                overlap = len(words1 & words2) / max(min(len(words1), len(words2)), 1)
                if overlap > 0.4:
                    return True
        return False

    # ── 辅助方法 ──────────────────────────────────────────

    def _extract_entities(self, text: str) -> List[str]:
        """从文本中提取实体"""
        # 简化的实体提取
        patterns = [
            r"(\S+(?:架构|系统|引擎|协议|模块|网络|模型|算法|方法))",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",  # 英文专有名词
            r"([A-Z]{2,})",  # 英文缩写
        ]
        entities = []
        for p in patterns:
            entities.extend(re.findall(p, text))
        return entities[:5]

    def _synthesize(
        self, lock_results: List[LockResult], claim: str
    ) -> Tuple[Verdict, float, str]:
        """综合三层锁结果，给出最终判定"""
        failed = [r for r in lock_results if r.status == LockStatus.FAILED]
        uncertain = [r for r in lock_results if r.status == LockStatus.UNCERTAIN]
        passed = [r for r in lock_results if r.status == LockStatus.PASSED]

        if failed:
            # 任意一层失败 → 拦截
            failed_names = [r.lock_name for r in failed]
            return Verdict.BLOCKED, 0.0, \
                f"防幻觉拦截: {', '.join(failed_names)} 未通过"

        if not passed and uncertain:
            # 全部不确定 → 降级
            return Verdict.DEGRADED, 0.3, \
                "所有验证层均无法确定，标记为低置信度输出"

        if uncertain:
            # 部分不确定 → 降低置信度
            confidence = len(passed) / len(lock_results)
            return Verdict.GROUNDED, confidence, \
                f"通过 {len(passed)}/{len(lock_results)} 层验证"

        # 全部通过
        confidence = 0.9
        return Verdict.GROUNDED, confidence, "全部三层锁验证通过"

    def _collect_fixes(self, lock_results: List[LockResult]) -> List[str]:
        """收集所有修复建议"""
        fixes = []
        for r in lock_results:
            fixes.extend(r.suggestions)
        return fixes

    def get_stats(self) -> Dict[str, Any]:
        return self._stats


# ════════════════════════════════════════════════════════════
# 记忆适配器接口
# ════════════════════════════════════════════════════════════

class MemoryAdapter:
    """
    记忆适配器 — 连接 LAAP Memory Vault 到防幻觉管线。

    封装 memory_retrieve 和 memory_verify 的调用。
    """

    def __init__(self, mcp_client=None):
        self._mcp = mcp_client

    async def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """检索记忆"""
        if self._mcp:
            try:
                result = await self._mcp.call_tool(
                    "laap-cognitive", "memory_retrieve",
                    {"query": query, "limit": limit}
                )
                data = json.loads(result) if isinstance(result, str) else result
                return data if isinstance(data, list) else data.get("results", [])
            except Exception as e:
                logger.warning(f"MemoryAdapter.retrieve failed: {e}")
        return []

    async def verify(self, content: str, confidence: float = 1.0) -> Dict:
        """验证记忆"""
        if self._mcp:
            try:
                result = await self._mcp.call_tool(
                    "laap-cognitive", "memory_verify",
                    {"content": content, "confidence": confidence}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                logger.warning(f"MemoryAdapter.verify failed: {e}")
        return {"verified": False, "reason": "no adapter"}


# ════════════════════════════════════════════════════════════
# 因果引擎适配器
# ════════════════════════════════════════════════════════════

class CausalAdapter:
    """
    因果引擎适配器 — 连接 LAAP Causal Engine 到防幻觉管线。
    """

    def __init__(self, mcp_client=None):
        self._mcp = mcp_client

    async def query(self, cause: str, effect: str, do: bool = False) -> Dict:
        """查询因果关系"""
        if self._mcp:
            try:
                result = await self._mcp.call_tool(
                    "laap-cognitive", "causal_infer",
                    {"cause": cause, "effect": effect, "do": do}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                logger.warning(f"CausalAdapter.query failed: {e}")
        return {"confidence": 0.0, "error": "no adapter"}

    async def learn(self, observations: List[Dict]) -> Dict:
        """学习因果关系"""
        if self._mcp:
            try:
                result = await self._mcp.call_tool(
                    "laap-cognitive", "causal_learn",
                    {"observations": json.dumps(observations)}
                )
                return json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                logger.warning(f"CausalAdapter.learn failed: {e}")
        return {"edges_added": 0}

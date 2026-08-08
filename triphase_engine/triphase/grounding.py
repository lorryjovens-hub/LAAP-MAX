"""triphase.grounding — 跨领域反幻觉基座 Harness（证明携带生成，PCG）。

范式：从"检索增强生成（RAG）"到"证明携带生成（Proof-Carrying Generation）"。

RAG 的结构性缺陷：
1. 按相似度接地，不按有效性接地——检索到"像的"，不证明"对的"；
2. 无来源代数——声明与证据之间没有可追踪的绑定；
3. 没有第三态——说不出"不知道"，被迫流畅地编造；
4. 领域知识是静态文本，不是可执行的验证结构。

PCG 的对策（每条都对应一个硬机制）：
1. 生成物被解析为**原子声明（Claim）**，每个声明必须携带
   "接地证书"（三值裁决 + 证据引用）才能出厂；
2. 领域知识以**领域核（DomainKernel）**形式提供：可执行验证器 +
   硬不变量 + 来源信任度，而非文档堆；
3. **弃权是一等输出**：UNVERIFIED 超阈值 → 输出"证据不足"，
   而不是流畅的猜测；
4. **反相硬拒绝**：任何声明违反领域不变量 → 结构性禁止输出
   （不是警告，是控制流走不过去）；
5. 已知幻觉模式以**负相位抗体**沉淀（如虚构案号、不存在的药名），
   命中即拦截，不再重复验证成本。

领域核协议是领域无关的：生物、金融、法律、政务各自实现
``verify_claim`` / ``invariants`` / ``trust_of`` 即可接入同一 harness。
参考内核内置小型规则表以演示协议；生产环境应替换为真实数据库
（DrugBank、EDGAR、裁判文书库、国家法规库等）。
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

from .core import Trit
from .memory import ComplexResonantMemory
from .metacognition import Telemetry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 声明：生成的最小问责单元
# ---------------------------------------------------------------------------

class ClaimKind(Enum):
    FACT = "fact"             # 事实陈述
    NUMERIC = "numeric"       # 数值声明（剂量、金额、比率、日期）
    CITATION = "citation"     # 引用声明（案号、法条、文号、文献）
    CAUSAL = "causal"         # 因果声明（"X 导致 Y"）
    NORMATIVE = "normative"   # 规范声明（"应当 / 禁止"）


@dataclass
class Claim:
    """原子声明：一段生成文本中可独立判真伪的最小单元。

    slots 为结构化槽位（由声明抽取器填充），例如：
    {"drug": "华法林", "dose_mg": 50} / {"case_id": "XYZ-123"} /
    {"assets": 100, "liabilities": 60, "equity": 50}
    """

    text: str
    kind: ClaimKind
    slots: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimVerdict:
    claim: Claim
    trit: Trit                # POS 核验证实 / NEUTRAL 未决 / NEG 证伪
    reason: str
    evidence: list[str] = field(default_factory=list)   # 接地证书
    hard: bool = False        # True = 不变量违例（硬拒绝，不可协商）


# ---------------------------------------------------------------------------
# 领域核协议（领域无关接口）
# ---------------------------------------------------------------------------

class DomainKernel(ABC):
    """领域核：把领域知识表达为可执行验证结构，而非文档。

    三层知识（对应不同的验证强度）：
    - invariants : 硬约束（会计恒等式、剂量上限、案号必须存在）——
                   违反即 REFUTED(hard)，无自由裁量；
    - verify_claim : 可执行验证器（查表、计算、规则推理）——
                     返回三值裁决 + 证据引用；
    - trust_of   : 来源信任度（指南 > 教科书 > 论坛），参与加权。
    """

    name: str = "abstract"
    version: str = "0.0.0"

    @abstractmethod
    def verify_claim(self, claim: Claim) -> ClaimVerdict:
        ...

    @abstractmethod
    def invariants(self) -> list[tuple[str, Callable[[Claim], bool]]]:
        ...

    def trust_of(self, source: str) -> float:
        """来源信任度 ∈ [0,1]，默认未知来源 0.3。"""
        return 0.3

    # ---- 组合逻辑（协议默认实现，一般不需覆写） ----

    def check_invariants(self, claim: Claim) -> list[str]:
        violations = []
        for name, check in self.invariants():
            try:
                if not check(claim):
                    violations.append(name)
            except (KeyError, TypeError, ValueError):
                continue  # 槽位不适用该不变量，跳过（非违例）
        return violations

    def ground(self, claim: Claim) -> ClaimVerdict:
        """先硬约束后软验证：不变量违例直接硬拒绝。"""
        violations = self.check_invariants(claim)
        if violations:
            return ClaimVerdict(
                claim, Trit.NEG,
                reason=f"违反领域不变量: {violations}",
                evidence=[], hard=True,
            )
        return self.verify_claim(claim)


# ---------------------------------------------------------------------------
# 接地策略与报告
# ---------------------------------------------------------------------------

class GroundingAction(Enum):
    PASS = "pass"         # 全部声明接地，可输出（附证书）
    ABSTAIN = "abstain"   # 未决声明超阈值 → 输出"证据不足"
    REJECT = "reject"     # 存在证伪/硬违例 → 结构性拒绝输出


@dataclass
class GroundingPolicy:
    max_unverified_ratio: float = 0.3   # 未决声明占比上限
    reject_on_refuted: bool = True      # 任何 NEG 声明即拒绝
    antibody_fastpath: bool = True      # 负相位抗体优先拦截
    antibody_similarity: float = 0.6    # 相似幻觉拦截的最小亲和度
                                        # （必须显著高于随机碰撞底噪 ~1/√dim，
                                        #  高价值领域宁可漏检不可误伤）


@dataclass
class GroundingReport:
    action: GroundingAction
    verdicts: list[ClaimVerdict]
    unverified_ratio: float
    refuted: list[ClaimVerdict]
    antibody_hits: list[str]
    telemetry: Telemetry                # 直通元认知层

    @property
    def certificate(self) -> list[str]:
        """接地证书：全部 POS 声明的证据链。"""
        out = []
        for v in self.verdicts:
            if v.trit is Trit.POS:
                out.extend(v.evidence)
        return out


# ---------------------------------------------------------------------------
# 基座 Harness
# ---------------------------------------------------------------------------

class GroundingHarness:
    """领域无关的反幻觉基座。

    工作流：已知幻觉抗体快路径 → 领域核接地（硬约束→软验证）→
    三值策略（PASS / ABSTAIN / REJECT）→ 抗体沉淀 + 元认知遥测。

    Parameters
    ----------
    kernel : 领域核实例。
    memory : CRM（可选；提供幻觉抗体库与跨会话沉淀）。
    policy : 接地策略。
    """

    def __init__(
        self,
        kernel: DomainKernel,
        memory: Optional[ComplexResonantMemory] = None,
        policy: Optional[GroundingPolicy] = None,
    ) -> None:
        self.kernel = kernel
        self.memory = memory
        self.policy = policy or GroundingPolicy()
        self.stats = {"grounded": 0, "passed": 0, "abstained": 0,
                      "rejected": 0, "antibody_intercepts": 0}

    # ---- 声明向量化（抗体检索键，确定性） ----

    @staticmethod
    def claim_vector(claim: Claim, dim: int = 16) -> np.ndarray:
        seed = abs(hash((claim.kind.value, claim.text))) % (2**32)
        r = np.random.default_rng(seed)
        v = r.standard_normal(dim) + 1j * r.standard_normal(dim)
        return v / np.linalg.norm(v)

    # ---- 抗体快路径 ----

    @staticmethod
    def _antibody_key(claim: Claim) -> str:
        return f"hallu:{abs(hash((claim.kind.value, claim.text)))}"

    def _antibody_hit(self, claim: Claim) -> Optional[str]:
        """已知幻觉拦截：精确键命中优先，相似模式需过保守阈值。"""
        if self.memory is None:
            return None
        # 1) 精确命中（零误伤）
        item = self.memory.get(self._antibody_key(claim))
        if item is not None and item.state is Trit.NEG:
            return str(item.payload)
        # 2) 相似命中（高阈值，防止有效声明被随机向量碰撞误伤）
        vec = self.claim_vector(claim)
        for r in self.memory.retrieve(vec, top_k=3):
            if r.item.state is Trit.NEG and -r.score >= self.policy.antibody_similarity:
                return str(r.item.payload)
        return None

    # ---- 主流程 ----

    def ground(self, claims: list[Claim]) -> GroundingReport:
        if not claims:
            raise ValueError("至少需要一个声明")
        self.stats["grounded"] += 1
        antibody_hits: list[str] = []
        verdicts: list[ClaimVerdict] = []

        for claim in claims:
            # 0) 抗体快路径：命中已知幻觉模式 → 直接拦截
            if self.policy.antibody_fastpath:
                hit = self._antibody_hit(claim)
                if hit:
                    antibody_hits.append(hit)
                    self.stats["antibody_intercepts"] += 1
                    verdicts.append(ClaimVerdict(
                        claim, Trit.NEG,
                        reason=f"命中已知幻觉抗体: {hit}", hard=True))
                    continue
            # 1) 领域核接地
            verdict = self.kernel.ground(claim)
            verdicts.append(verdict)
            # 2) 幻觉模式沉淀（下次免验证拦截）
            if (verdict.trit is Trit.NEG and self.memory is not None):
                self.memory.store(
                    self.claim_vector(claim),
                    payload=f"hallucination:{self.kernel.name}:{claim.text[:80]}",
                    key=self._antibody_key(claim),
                    initial_evidence=-0.9,
                )

        refuted = [v for v in verdicts if v.trit is Trit.NEG]
        unverified = [v for v in verdicts if v.trit is Trit.NEUTRAL]
        unverified_ratio = len(unverified) / len(verdicts)

        if refuted and self.policy.reject_on_refuted:
            action = GroundingAction.REJECT
        elif unverified_ratio > self.policy.max_unverified_ratio:
            action = GroundingAction.ABSTAIN
        else:
            action = GroundingAction.PASS

        self.stats[{GroundingAction.PASS: "passed",
                    GroundingAction.ABSTAIN: "abstained",
                    GroundingAction.REJECT: "rejected"}[action]] += 1

        telemetry = Telemetry(
            retrieval_hit_rate=1.0 - unverified_ratio,
            hypothesis_dispersion=unverified_ratio,
            unverified_dependency_ratio=unverified_ratio,
            negative_conflicts=len(refuted),
        )
        report = GroundingReport(action, verdicts, unverified_ratio,
                                 refuted, antibody_hits, telemetry)
        logger.info("接地裁决: %s (核=%s 未决率=%.2f 证伪=%d 抗体=%d)",
                    action.value, self.kernel.name, unverified_ratio,
                    len(refuted), len(antibody_hits))
        return report


# ---------------------------------------------------------------------------
# 参考领域核（演示协议；生产应接真实数据库）
# ---------------------------------------------------------------------------

class BioMedicalKernel(DomainKernel):
    """生物医学核：药物相互作用表 + 剂量窗 + 单位一致性。"""

    name, version = "biomedical", "0.1.0"

    #: 已知相互作用（简化表，生产环境应接 DrugBank/说明书数据库）
    INTERACTIONS = {
        frozenset(("华法林", "阿司匹林")): "出血风险显著增加",
        frozenset(("华法林", "布洛芬")): "出血风险增加",
        frozenset(("二甲双胍", "碘造影剂")): "乳酸酸中毒风险",
    }
    #: 剂量窗 mg/日（成人，简化）
    DOSE_WINDOWS = {"华法林": (1.0, 10.0), "二甲双胍": (500.0, 2000.0),
                    "阿司匹林": (75.0, 300.0)}

    def invariants(self):
        return [
            ("dose_positive",
             lambda c: "dose_mg" not in c.slots or c.slots["dose_mg"] > 0),
            ("dose_has_unit",
             lambda c: "dose_mg" not in c.slots or bool(c.slots.get("unit"))),
        ]

    def verify_claim(self, claim: Claim) -> ClaimVerdict:
        s = claim.slots
        # 相互作用声明
        if "drugs" in s:
            pair = frozenset(s["drugs"])
            risk = self.INTERACTIONS.get(pair)
            if risk and s.get("asserts") == "no_interaction":
                return ClaimVerdict(claim, Trit.NEG,
                                    f"证伪：{list(pair)} 存在已知相互作用（{risk}）",
                                    [f"相互作用表 v{self.version}"])
            if risk:
                return ClaimVerdict(claim, Trit.POS,
                                    f"确认相互作用：{risk}",
                                    [f"相互作用表 v{self.version}"])
            return ClaimVerdict(claim, Trit.NEUTRAL, "该组合不在相互作用表内")
        # 剂量声明
        if "drug" in s and "dose_mg" in s:
            drug, dose = s["drug"], float(s["dose_mg"])
            window = self.DOSE_WINDOWS.get(drug)
            if window is None:
                return ClaimVerdict(claim, Trit.NEUTRAL,
                                    f"药物 {drug} 不在剂量库，无法证实")
            lo, hi = window
            if lo <= dose <= hi:
                return ClaimVerdict(claim, Trit.POS,
                                    f"剂量 {dose}mg 在窗内 [{lo},{hi}]",
                                    [f"剂量库 v{self.version}"])
            return ClaimVerdict(claim, Trit.NEG,
                                f"剂量 {dose}mg 超出安全窗 [{lo},{hi}]",
                                [f"剂量库 v{self.version}"])
        return ClaimVerdict(claim, Trit.NEUTRAL, "无可执行验证路径")

    def trust_of(self, source: str) -> float:
        return {"指南": 0.95, "说明书": 0.9, "教科书": 0.8,
                "论文": 0.7, "论坛": 0.1}.get(source, 0.3)


class FinanceKernel(DomainKernel):
    """金融核：会计恒等式 + 比率域 + 数值勾稽。"""

    name, version = "finance", "0.1.0"

    def invariants(self):
        return [
            ("accounting_identity",
             lambda c: not {"assets", "liabilities", "equity"} <= set(c.slots)
             or abs(c.slots["assets"] - c.slots["liabilities"]
                    - c.slots["equity"]) < 0.01 * max(1.0, abs(c.slots["assets"]))),
            ("ratio_bounded",
             lambda c: "margin" not in c.slots or -1.0 <= c.slots["margin"] <= 1.0),
        ]

    def verify_claim(self, claim: Claim) -> ClaimVerdict:
        s = claim.slots
        # 资产负债表声明：不变量已校验恒等式 → 证实
        if {"assets", "liabilities", "equity"} <= set(s):
            return ClaimVerdict(claim, Trit.POS, "会计恒等式勾稽成立",
                                ["财务报表勾稽"])
        # 增长率勾稽：声称 growth，给出本期/上期数值则可算
        if {"revenue_now", "revenue_prev", "growth"} <= set(s):
            prev = float(s["revenue_prev"])
            if prev == 0:
                return ClaimVerdict(claim, Trit.NEUTRAL, "上期为零，增长率无定义")
            actual = float(s["revenue_now"]) / prev - 1.0
            if abs(actual - float(s["growth"])) < 0.005:
                return ClaimVerdict(claim, Trit.POS,
                                    f"增长率勾稽一致 {actual:+.2%}",
                                    ["财务报表勾稽"])
            return ClaimVerdict(claim, Trit.NEG,
                                f"增长率勾稽不一致：声称 {s['growth']:+.2%}，"
                                f"实际 {actual:+.2%}",
                                ["财务报表勾稽"])
        # 因果声明升维：金融"X 导致 Y"需因果证据，默认挂起
        if claim.kind is ClaimKind.CAUSAL:
            return ClaimVerdict(claim, Trit.NEUTRAL,
                                "因果声明需 do-演算证据，默认挂起")
        return ClaimVerdict(claim, Trit.NEUTRAL, "无可执行验证路径")

    def trust_of(self, source: str) -> float:
        return {"审计报告": 0.95, "定期报告": 0.9, "交易所公告": 0.85,
                "研报": 0.6, "自媒体": 0.05}.get(source, 0.3)


class LegalKernel(DomainKernel):
    """法律核：案号/法条注册表（反虚构引用）+ 法条时效。"""

    name, version = "legal", "0.1.0"

    #: 案号注册表（简化；生产环境应接裁判文书库）
    CASE_REGISTRY = {
        "(2021)京01民终1234号": "张某诉李某合同纠纷案",
        "(2019)最高法民申5678号": "某建设集团再审案",
    }
    #: 法条时效表：法条 → (生效日期, 废止日期或None)
    STATUTES = {
        "民法典第188条": ("2021-01-01", None),
        "合同法第52条": ("1999-10-01", "2021-01-01"),   # 已被民法典吸收废止
    }

    def invariants(self):
        return [
            ("citation_exists",
             lambda c: "case_id" not in c.slots
             or c.slots["case_id"] in self.CASE_REGISTRY),
        ]

    def verify_claim(self, claim: Claim) -> ClaimVerdict:
        s = claim.slots
        if "case_id" in s:
            title = self.CASE_REGISTRY[s["case_id"]]  # 不变量已保证存在
            return ClaimVerdict(claim, Trit.POS, f"案号有效：{title}",
                                [f"案号注册表 v{self.version}: {title}"])
        if "statute" in s:
            rec = self.STATUTES.get(s["statute"])
            if rec is None:
                return ClaimVerdict(claim, Trit.NEUTRAL,
                                    f"法条 {s['statute']} 不在时效库")
            effective, repealed = rec
            as_of = s.get("as_of", "9999-12-31")
            if repealed and as_of > repealed and s.get("asserts") == "current":
                return ClaimVerdict(claim, Trit.NEG,
                                    f"{s['statute']} 已于 {repealed} 废止，"
                                    f"不能作为现行法引用",
                                    [f"法条时效库 v{self.version}"])
            if as_of >= effective:
                return ClaimVerdict(claim, Trit.POS,
                                    f"法条于 {as_of} 时有效",
                                    [f"法条时效库 v{self.version}"])
        return ClaimVerdict(claim, Trit.NEUTRAL, "无可执行验证路径")

    def trust_of(self, source: str) -> float:
        return {"指导案例": 0.95, "裁判文书": 0.85, "法条原文": 0.9,
                "学术观点": 0.5, "自媒体解读": 0.05}.get(source, 0.3)


class GovKernel(DomainKernel):
    """政务核：政策文号注册 + 效力状态 + 发文主体层级一致性。"""

    name, version = "gov", "0.1.0"

    #: 文号 → (标题, 发文层级, 生效日期, 废止日期或None)
    POLICY_REGISTRY = {
        "国发〔2023〕10号": ("关于促进民营经济发展壮大的意见", "国务院",
                             "2023-07-01", None),
        "京政发〔2020〕5号": ("北京市优化营商环境条例配套办法", "省级",
                               "2020-04-01", "2023-01-01"),
    }
    LEVEL_RANK = {"国务院": 4, "省级": 3, "市级": 2, "区县级": 1, "街道办": 0}

    def invariants(self):
        return [
            ("doc_number_exists",
             lambda c: "doc_no" not in c.slots
             or c.slots["doc_no"] in self.POLICY_REGISTRY),
        ]

    def verify_claim(self, claim: Claim) -> ClaimVerdict:
        s = claim.slots
        if "doc_no" in s:
            title, level, effective, abolished = self.POLICY_REGISTRY[s["doc_no"]]
            as_of = s.get("as_of", "9999-12-31")
            if abolished and as_of > abolished and s.get("asserts") == "current":
                return ClaimVerdict(claim, Trit.NEG,
                                    f"《{title}》已于 {abolished} 废止",
                                    [f"政策注册表 v{self.version}"])
            # 层级越权：声称某文号由低层级主体发布全国性约束
            claimed_scope = s.get("scope")
            if claimed_scope == "全国" and self.LEVEL_RANK[level] < 4:
                return ClaimVerdict(claim, Trit.NEG,
                                    f"层级越权：{level}级文件不能设定全国性义务",
                                    [f"政策注册表 v{self.version}"])
            return ClaimVerdict(claim, Trit.POS,
                                f"《{title}》（{level}，{effective} 生效）",
                                [f"政策注册表 v{self.version}"])
        return ClaimVerdict(claim, Trit.NEUTRAL, "无可执行验证路径")

    def trust_of(self, source: str) -> float:
        return {"政府公报": 0.95, "官网原文": 0.9, "新闻发布会": 0.7,
                "媒体报道": 0.5, "截图传言": 0.02}.get(source, 0.3)

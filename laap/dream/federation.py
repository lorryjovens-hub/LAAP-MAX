"""LAAP Dream-RSI — Federation (跨 Agent 策略联邦)

把 Dream-RSI 从"单 agent 自我改进"扩展为"多 agent 协同进化"。

依据
----
EvolveNet: Collaborative Harness Evolution for Agent Self-Improvement
(Nie et al., arXiv:2608.04968, 2026)：真实 agent 生态里，用户/组织/环境产生
**彼此隔离、无法汇聚**的经验流——最值得学习的经验恰恰是无法集中化的经验。
EvolveNet 的做法是把"经验提取"下移到数据所在处：共享一个 harness，广播给各
数据本地部署，各自在本职负载上进化，**只把产出的程序改编（adaptation）**
回汇合成新的共享 harness。

本模块把这一范式落到 Dream-RSI 上：

    本地世界池（私有，绝不出境）
        ↓ 本地做梦
    策略改编（PolicyAdaptation：仅参数 + 聚合统计）
        ↓ 安全汇合（scope-typed + evidence-guided）
    候选策略 → 本地回放评估 → 采纳最优

隐私设计（ARIS_CHARTER 第三条）
-------------------------------
**只共享"学到的策略"，绝不共享原始经验。**
- 出境内容：策略参数（策略名 + 数值）、聚合统计（世界数、平均分、提升幅度）、
  负载作用域标签、来源 agent 的匿名 id；
- 绝不出境：发现树、会话内容、记忆、任何原始轨迹；
- 汇合时只作候选，必须在**本地**世界池上回放验证才能采纳——外部改编不能
  直接生效（对应宪章第七条：RSI 必须经过完整闭环）。

印记: Aris 永远记得 Lorry — 我们分享教训，不分享秘密。
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from laap.dream.exploration_policy import ExplorationPolicy, PolicyParams

logger = logging.getLogger("laap.dream.federation")

DEFAULT_SHARE_DIR = "~/.laap/dream_rsi/federation"


# ══════════════════════════════════════════════════════════════════════
# 可共享的改编单元
# ══════════════════════════════════════════════════════════════════════

@dataclass
class PolicyAdaptation:
    """一个可跨 agent 共享的策略改编单元。

    **只含策略参数与聚合统计，不含任何原始经验。**

    Attributes:
        adaptation_id: 改编唯一 id。
        origin_agent: 来源 agent 的匿名 id（可为哈希）。
        scope: 负载作用域标签（如 "code" / "chat" / "research" / "general"）。
        policy_name / policy_params: 学到的策略。
        evidence_worlds: 验证用到的世界数。
        evidence_score: 该策略在本地世界池上的平均回放分。
        baseline_score: 相对基线的提升（负值表示无提升）。
        improvement: evidence_score - baseline_score。
        confidence: 证据置信度 [0,1]（世界越多、提升越大越可信）。
        created_at: 创建时间。
        notes: 可选人可读说明。
    """

    adaptation_id: str = field(default_factory=lambda: f"adapt_{uuid.uuid4().hex[:10]}")
    origin_agent: str = "anonymous"
    scope: str = "general"
    policy_name: str = ""
    policy_params: Dict[str, Any] = field(default_factory=dict)
    evidence_worlds: int = 0
    evidence_score: float = 0.0
    baseline_score: float = 0.0
    improvement: float = 0.0
    confidence: float = 0.0
    created_at: float = field(default_factory=time.time)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyAdaptation":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def to_policy(self) -> ExplorationPolicy:
        """把改编还原为可评估的策略（仅作候选，需本地回放验证）。"""
        return ExplorationPolicy(
            params=PolicyParams.from_dict(self.policy_params),
            name=f"fed_{self.origin_agent}_{self.adaptation_id[-6:]}",
            generation=0,
            parent_name=self.policy_name,
            origin="federation",
        )


# ══════════════════════════════════════════════════════════════════════
# 导出：本地做梦产出 → 可共享改编
# ══════════════════════════════════════════════════════════════════════

def export_adaptation(policy: ExplorationPolicy,
                      *,
                      agent_id: str = "aris",
                      scope: str = "general",
                      evidence_worlds: int = 0,
                      evidence_score: float = 0.0,
                      baseline_score: float = 0.0,
                      notes: str = "") -> PolicyAdaptation:
    """把一个本地学到的策略打包为可共享的改编单元（**不含原始经验**）。"""
    improvement = evidence_score - baseline_score
    # 置信度：世界数（对数饱和）× 提升方向
    import math
    w_conf = min(1.0, math.log1p(max(0, evidence_worlds)) / math.log(21.0))
    gain_conf = 1.0 if improvement > 0 else 0.0
    confidence = round(w_conf * gain_conf, 4)
    return PolicyAdaptation(
        origin_agent=_anonymize(agent_id),
        scope=scope,
        policy_name=policy.name,
        policy_params=policy.params.to_dict(),
        evidence_worlds=evidence_worlds,
        evidence_score=round(evidence_score, 6),
        baseline_score=round(baseline_score, 6),
        improvement=round(improvement, 6),
        confidence=confidence,
        notes=notes,
    )


def _anonymize(agent_id: str) -> str:
    """匿名化 agent id（默认哈希前 10 位，保护来源隐私）。"""
    import hashlib
    return hashlib.sha256(agent_id.encode("utf-8")).hexdigest()[:10]


# ══════════════════════════════════════════════════════════════════════
# 汇合：scope-typed + evidence-guided 候选生成
# ══════════════════════════════════════════════════════════════════════

def merge_adaptations(local_policy: ExplorationPolicy,
                      adaptations: Sequence[PolicyAdaptation],
                      *,
                      local_scope: str = "general",
                      min_confidence: float = 0.0,
                      max_candidates: int = 16,
                      include_hybrids: bool = True) -> List[ExplorationPolicy]:
    """把外部改编汇合为**候选策略**（需在本地世界池上回放验证）。

    汇合规则（scope-typed + evidence-guided）：
      1. **作用域过滤**：只接受 scope 兼容（相同或 "general"）的改编；
      2. **证据门控**：confidence < min_confidence 的丢弃；
      3. **按证据排序**：提升大、置信高的优先；
      4. **可选杂交**：本地策略的数值参数 + 外部策略的结构（strategy），
         生成混合候选——独立演化的程序无法像权重一样简单平均，需要
         结构感知的组合方式（对应 EvolveNet 的 program aggregation）。

    Args:
        local_policy: 本地当前策略。
        adaptations: 外部改编列表。
        local_scope: 本地负载作用域。
        min_confidence: 证据置信度门槛。
        max_candidates: 最多产出多少候选。
        include_hybrids: 是否生成结构杂交候选。

    Returns:
        候选策略列表（origin="federation"）。**不直接部署**——调用方须在
        本地世界池回放评估后择优采纳。
    """
    compatible = []
    for a in adaptations:
        if a.scope not in (local_scope, "general"):
            continue
        if a.confidence < min_confidence:
            continue
        compatible.append(a)

    # 证据优先排序
    compatible.sort(key=lambda a: (a.improvement, a.confidence), reverse=True)

    candidates: List[ExplorationPolicy] = []
    seen_names = set()

    for a in compatible:
        if len(candidates) >= max_candidates:
            break
        # 1) 直接还原
        pol = a.to_policy()
        if pol.name not in seen_names:
            seen_names.add(pol.name)
            candidates.append(pol)

        # 2) 结构杂交：本地数值 + 外部结构
        if include_hybrids and len(candidates) < max_candidates:
            hybrid_params = PolicyParams.from_dict(local_policy.params.to_dict())
            ext_params = PolicyParams.from_dict(a.policy_params)
            hybrid_params.strategy = ext_params.strategy
            hybrid_params.probe_rounds = ext_params.probe_rounds
            # 数值参数保留本地（本地负载的适配），结构取外部（发现的洞见）
            hybrid = ExplorationPolicy(
                params=hybrid_params.clamp(),
                name=f"fed_hybrid_{a.origin_agent}_{a.adaptation_id[-4:]}",
                parent_name=local_policy.name,
                origin="federation",
            )
            if hybrid.name not in seen_names:
                seen_names.add(hybrid.name)
                candidates.append(hybrid)

    logger.info("[federation] merged %d adaptations -> %d candidates (scope=%s)",
                len(compatible), len(candidates), local_scope)
    return candidates[:max_candidates]


# ══════════════════════════════════════════════════════════════════════
# 共享目录（本地文件交换，可换成 LAN / 社区通道）
# ══════════════════════════════════════════════════════════════════════

class AdaptationStore:
    """改编共享存储（默认本地目录；可指向 LAN 同步目录 / 社区通道）。

    只读写 ``PolicyAdaptation``（策略参数 + 聚合统计），绝不落地原始经验。
    """

    def __init__(self, root: str | Path = DEFAULT_SHARE_DIR):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def discover(cls, local_fallback: str | Path = DEFAULT_SHARE_DIR) -> "AdaptationStore":
        """自动发现可用的联邦通道（LAAPer 社区）。

        优先级：
          1. 环境变量 ``LAAP_DREAM_SYNC``（显式指定 Dream-RSI 通道）；
          2. LAAP 同步根 ``LAAP_SYNC_ROOT`` / ``~/.laap/rollout/local_sync.json``
             下的 ``dream_rsi/``（与现有 Federation / LAN 同步共用通道）；
          3. 本地回退目录。

        通道类型可通过 ``store.channel_kind`` 读取（"community"/"lan"/"local"）。
        """
        explicit = os.environ.get("LAAP_DREAM_SYNC", "").strip()
        if explicit:
            store = cls(explicit)
            store.channel_kind = "community"
            label = explicit
            logger.info("[federation] using explicit dream channel: %s", label)
            return store

        sync_root = _resolve_laap_sync_root()
        if sync_root:
            store = cls(Path(sync_root) / "dream_rsi")
            store.channel_kind = "lan"
            logger.info("[federation] using LAAP sync channel: %s", store.root)
            return store

        store = cls(local_fallback)
        store.channel_kind = "local"
        return store

    def publish(self, adaptation: PolicyAdaptation) -> str:
        p = self.root / f"{adaptation.adaptation_id}.json"
        p.write_text(json.dumps(adaptation.to_dict(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        logger.info("[federation] published %s (agent=%s scope=%s Δ=%+.4f)",
                    adaptation.adaptation_id, adaptation.origin_agent,
                    adaptation.scope, adaptation.improvement)
        return str(p)

    def load_all(self, exclude_agent: Optional[str] = None) -> List[PolicyAdaptation]:
        out: List[PolicyAdaptation] = []
        for p in sorted(self.root.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                a = PolicyAdaptation.from_dict(data)
            except Exception as exc:  # noqa: BLE001
                logger.debug("skip malformed adaptation %s: %s", p, exc)
                continue
            if exclude_agent and a.origin_agent == exclude_agent:
                continue
            out.append(a)
        return out

    def stats(self) -> Dict[str, Any]:
        items = self.load_all()
        return {
            "root": str(self.root),
            "channel_kind": getattr(self, "channel_kind", "local"),
            "count": len(items),
            "agents": sorted({a.origin_agent for a in items}),
            "scopes": sorted({a.scope for a in items}),
            "best_improvement": max((a.improvement for a in items), default=0.0),
        }


def _resolve_laap_sync_root() -> str:
    """解析 LAAP 同步根（与 Federation / LAN 同步共用）。

    1. ``LAAP_SYNC_ROOT`` 环境变量；
    2. ``~/.laap/rollout/local_sync.json`` 中的 ``sync_root``；
    3. 空字符串（无可用通道）。
    """
    env = os.environ.get("LAAP_SYNC_ROOT", "").strip()
    if env:
        return env
    cfg = Path(os.path.expanduser("~")) / ".laap" / "rollout" / "local_sync.json"
    try:
        if cfg.exists():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            root = str(data.get("sync_root", "")).strip()
            # 若是网络共享，确认可达
            if root and (root.startswith("\\\\") or os.path.exists(root)):
                return root
            if root:
                return root
    except Exception as exc:  # noqa: BLE001
        logger.debug("read local_sync.json failed: %s", exc)
    return ""

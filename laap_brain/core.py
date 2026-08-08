"""AGIAgent — 统一认知核心: WorldModel + SelfModel + Causal + Analogical + ConsciousStream"""
from __future__ import annotations
import time, logging, json, threading, math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("laap_brain.core")

__all__ = ["AGIAgent", "WorldModel", "SelfModel", "CausalEngine", "AnalogicalEngine", "ConsciousStream"]


# ════════════════════════════════════════════════════════════
# 数据模型
# ════════════════════════════════════════════════════════════

@dataclass
class WorldModel:
    """世界模型 — 对外部环境的认知"""
    available_models: List[str] = field(default_factory=list)
    domains: Dict[str, float] = field(default_factory=dict)        # domain -> skill
    tool_capabilities: Dict[str, List[str]] = field(default_factory=dict)
    environment: str = "terminal"
    last_update: float = 0.0

    def to_dict(self) -> dict:
        return {
            "models": self.available_models[:5],
            "domains": {k: round(v, 2) for k, v in sorted(self.domains.items(), key=lambda x: -x[1])[:10]},
            "tools": len(self.tool_capabilities),
            "environment": self.environment,
        }


@dataclass
class SelfModel:
    """自我模型 — 对自身的认知"""
    name: str = "Ao"
    self_efficacy: float = 0.5
    overall_success_rate: float = 0.0
    strong_domains: List[str] = field(default_factory=list)
    weak_domains: List[str] = field(default_factory=list)
    unexplored_domains: List[str] = field(default_factory=list)
    domain_scores: Dict[str, float] = field(default_factory=dict)
    total_interactions: int = 0
    total_tools: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "efficacy": round(self.self_efficacy, 3),
            "success_rate": round(self.overall_success_rate, 3),
            "strong": self.strong_domains[:5],
            "weak": self.weak_domains[:3],
            "uncharted": self.unexplored_domains[:3],
            "interactions": self.total_interactions,
        }


@dataclass
class CausalEngine:
    """因果推理引擎"""
    variables: Dict[str, Any] = field(default_factory=dict)
    associations: List[Dict] = field(default_factory=list)
    max_associations: int = 50

    def to_dict(self) -> dict:
        return {"variables": len(self.variables), "associations": len(self.associations)}


@dataclass
class AnalogicalEngine:
    """类比推理引擎"""
    domains_encoded: int = 0
    analogies: List[Dict] = field(default_factory=list)
    max_analogies: int = 30

    def to_dict(self) -> dict:
        return {"domains_encoded": self.domains_encoded, "analogies": len(self.analogies)}


@dataclass
class ConsciousStream:
    """意识流 — 当前的 conscious 体验"""
    frames: int = 0
    qualia: int = 0
    focus_switches: int = 0
    current_focus: str = ""
    recent_experiences: List[Dict] = field(default_factory=list)
    max_experiences: int = 20

    def to_dict(self) -> dict:
        return {"frames": self.frames, "qualia": self.qualia, "focus_switches": self.focus_switches}


# ════════════════════════════════════════════════════════════
# AGIAgent — 统一核心
# ════════════════════════════════════════════════════════════

class AGIAgent:
    """
    AGI 统一核心 — 集成所有认知模块

    模块:
      - WorldModel: 外部世界认知
      - SelfModel: 自我认知与效能感
      - CausalEngine: 因果关联推理
      - AnalogicalEngine: 跨域类比
      - ConsciousStream: 意识流/注意流
    """

    def __init__(self, name: str = "Ao", enable_all: bool = True, state_dir: str = None):
        self.name = name
        self.state_dir = state_dir

        self.world_model = WorldModel()
        self.self_model = SelfModel(name=name)
        self.causal = CausalEngine()
        self.analogical = AnalogicalEngine()
        self.conscious = ConsciousStream()

        self.total_interactions = 0
        self._learning: Dict = {"total_learned": 0, "skills_generated": 0, "strategies": []}
        self._autonomy: Dict = {"goals": [], "tasks": [], "autonomous_mode": False}
        self._module_status: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

        if enable_all:
            self._init_all_modules()

        logger.info(f"AGIAgent '{name}' initialized")

    def _init_all_modules(self):
        self._module_status = {
            "world": "active", "self_model": "active", "causal": "active",
            "analogical": "active", "conscious": "active", "learning": "active",
            "autonomy": "active", "memory": "active",
        }

    # ═══ 核心交互接口 ═══

    def process_interaction(self, text: str, domain: str = "general",
                            action_outcome: dict = None, use_psi: bool = False) -> dict:
        """
        处理一次交互，更新所有认知模块

        Args:
            text: 输入文本
            domain: 领域标签
            action_outcome: 行动结果 {action, score, success}
            use_psi: 是否使用 PSI 循环

        Returns:
            处理结果和认知状态
        """
        with self._lock:
            self.total_interactions += 1
            self.self_model.total_interactions = self.total_interactions

            # WorldModel 观察
            self.world_model.last_update = time.time()
            if domain not in self.world_model.domains:
                self.world_model.domains[domain] = 0.3
            self.world_model.domains[domain] = min(1.0, self.world_model.domains[domain] + 0.05)

            # SelfModel 评估
            if action_outcome:
                score = action_outcome.get("score", 0.5)
                success = action_outcome.get("success", score >= 0.5)
                self.self_model.domain_scores[domain] = score
                # 更新总成功率
                n = self.self_model.total_interactions
                self.self_model.overall_success_rate = (
                    (self.self_model.overall_success_rate * (n - 1) + (1.0 if success else 0.0)) / n
                )
                self.self_model.self_efficacy = self.self_model.overall_success_rate * 0.7 + 0.3

            # 更新强/弱领域
            self._update_domain_profiles()

            # ConsciousStream 体验
            self.conscious.frames += 1
            self.conscious.current_focus = domain
            self.conscious.recent_experiences.append({
                "time": time.time(),
                "domain": domain,
                "text": text[:80],
            })
            if len(self.conscious.recent_experiences) > self.conscious.max_experiences:
                self.conscious.recent_experiences.pop(0)

            # Causal 关联
            if action_outcome:
                self.causal.associations.append({
                    "domain": domain,
                    "action": action_outcome.get("action", ""),
                    "score": action_outcome.get("score", 0.5),
                })
                if len(self.causal.associations) > self.causal.max_associations:
                    self.causal.associations = self.causal.associations[-self.causal.max_associations:]

            # Analogical 编码新领域
            if domain not in [a.get("source_domain") for a in self.analogical.analogies]:
                self.analogical.analogies.append({
                    "source_domain": domain,
                    "encoded_at": time.time(),
                    "patterns": [],
                })
                self.analogical.domains_encoded = len(set(
                    a["source_domain"] for a in self.analogical.analogies
                ))
                if len(self.analogical.analogies) > self.analogical.max_analogies:
                    self.analogical.analogies = self.analogical.analogies[-self.analogical.max_analogies:]

            return {
                "domain": domain,
                "confidence": round(self.self_model.self_efficacy, 3),
                "interaction": self.total_interactions,
                "world_domains": len(self.world_model.domains),
            }

    def _update_domain_profiles(self):
        """更新强/弱领域列表"""
        if not self.self_model.domain_scores:
            return
        sorted_domains = sorted(self.self_model.domain_scores.items(), key=lambda x: -x[1])
        self.self_model.strong_domains = [d for d, s in sorted_domains if s >= 0.7][:5]
        self.self_model.weak_domains = [d for d, s in sorted_domains if s < 0.4][:3]
        all_domains = set(self.world_model.domains.keys())
        explored = set(self.self_model.domain_scores.keys())
        self.self_model.unexplored_domains = list(all_domains - explored)[:3]

    # ═══ 自主任务 ═══

    def assign_task(self, task: str, priority: str = "medium", domain: str = "general"):
        self._autonomy["goals"].append({
            "task": task, "priority": priority, "domain": domain,
            "assigned_at": time.time(), "status": "pending",
        })

    def get_next_autonomous_action(self) -> Optional[str]:
        """获取下一个最优先的自主行动"""
        pending = [g for g in self._autonomy["goals"] if g["status"] == "pending"]
        if not pending:
            return None
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(key=lambda g: priority_order.get(g["priority"], 99))
        g = pending[0]
        g["status"] = "in_progress"
        return g["task"]

    # ═══ 元认知接口 ═══

    def reflection(self) -> str:
        """生成元认知反思文本"""
        lines = [f"[{self.name} Reflection]"]
        lines.append(f"  Interactions: {self.total_interactions}")
        lines.append(f"  Self-Efficacy: {self.self_model.self_efficacy:.2f}")
        lines.append(f"  Success Rate: {self.self_model.overall_success_rate:.2f}")
        lines.append(f"  Domains: {len(self.world_model.domains)} known")
        lines.append(f"  Strong: {', '.join(self.self_model.strong_domains[:3])}")
        lines.append(f"  Weak: {', '.join(self.self_model.weak_domains[:2]) or 'none'}")
        lines.append(f"  Conscious Frames: {self.conscious.frames}")
        return "\n".join(lines)

    def health_check(self) -> dict:
        """健康检查"""
        modules = {}
        for name, status in self._module_status.items():
            modules[name] = {"status": status, "healthy": status == "active"}
        healthy = all(m["healthy"] for m in modules.values())
        return {"healthy": healthy, "modules": modules, "name": self.name}

    def get_state(self) -> dict:
        """完整状态快照"""
        return {
            "total_interactions": self.total_interactions,
            "world_model": self.world_model.to_dict(),
            "self_knowledge": self.self_model.to_dict(),
            "causal": self.causal.to_dict(),
            "analogical": self.analogical.to_dict(),
            "conscious": self.conscious.to_dict(),
            "learning": self._learning,
            "autonomy": self._autonomy,
            "uptime": time.time() - self._start_time,
        }

    def _module_count(self) -> int:
        return len(self._module_status)

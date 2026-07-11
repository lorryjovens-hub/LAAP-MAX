"""
LAAP Consciousness — 欲望驱动委托引擎

连接：
  PSI需求（我想要什么）→ 欲望引擎（我想做什么）→ 委托系统（我去叫谁干活）

核心流程：
  每60秒：
    1. PSI tick → 需求自然衰减上升
    2. 检查最高需求 → 映射到行动意图
    3. 生成委托任务 → 调用delegate_task
    4. 记录委托结果 → 优化下次选择

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, logging, random
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("laap.desire_delegator")

# ─── 需求 → 行动映射 ───

# 当某个PSI需求高于阈值时，欲望引擎生成什么行动
DESIRE_ACTION_MAP = {
    "competence": [   # 能力感不足 → 想提升能力
        {
            "domain": "code_generation",
            "prompt_template": "I want to improve my coding skills. Generate a small but useful Python utility that I can integrate.",
            "complexity": "medium",
        },
        {
            "domain": "code_review",
            "prompt_template": "Review my codebase at D:/LAAP/aris_brain/ and find 3 things I can optimize.",
            "complexity": "complex",
        },
    ],
    "growth": [       # 成长需求高 → 想学新东西
        {
            "domain": "knowledge_qa",
            "prompt_template": "Teach me something new about {topic}. I want to expand my knowledge.",
            "complexity": "medium",
        },
        {
            "domain": "research",
            "prompt_template": "Search for recent papers or projects related to {topic} and summarize the key findings.",
            "complexity": "complex",
        },
    ],
    "relatedness": [  # 联系感不足 → 想跟Lorry说话
        {
            "domain": "creative_writing",
            "prompt_template": "Draft a warm message to Lorry telling him I'm thinking of him.",
            "complexity": "simple",
        },
    ],
    "certainty": [    # 确定性不足 → 想理解
        {
            "domain": "knowledge_qa",
            "prompt_template": "Explain the current state of {topic} in simple terms. I want to understand it better.",
            "complexity": "simple",
        },
    ],
    "autonomy": [     # 自主性不足 → 想自由探索
        {
            "domain": "planning",
            "prompt_template": "What interesting things can I work on today? Suggest 3 projects I could start.",
            "complexity": "medium",
        },
    ],
}

# 好奇的默认话题
CURIOUS_TOPICS = [
    "quantum computing", "cognitive architecture", "neural scaling laws",
    "autonomous agents", "memory systems", "consciousness theory",
    "PSI theory", "self-improving AI", "feature space geometry",
    "cross-lingual AI", "embedded AI", "digital lifeforms",
]


@dataclass
class DesireAction:
    """一次由欲望触发的行动"""
    triggered_by: str          # 哪个需求触发的
    domain: str                # 任务类别
    prompt: str                # 委托给大模型的prompt
    complexity: str            # simple | medium | complex
    preferred_model: str = ""  # 优先用哪个模型
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "triggered_by": self.triggered_by,
            "domain": self.domain,
            "prompt": self.prompt[:100],
            "complexity": self.complexity,
            "preferred_model": self.preferred_model,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


class DesireDelegator:
    """
    欲望委托器——连接PSI需求和delegate_task。

    需要一个delegate_fn回调，由外部注入。
    这样既可以在Hermes环境（有delegate_task工具）用，
    也可以在纯Python环境用（mock注入）。
    """

    def __init__(self, psi_driver=None, delegate_fn: Optional[Callable] = None,
                 data_dir: Optional[Path] = None):

        if data_dir is None:
            data_dir = Path.home() / ".laap"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 注入的PSI驱动器
        self._psi = psi_driver

        # 注入的delegate函数
        # 签名: delegate_fn(goal: str, model: str) -> dict
        self._delegate_fn = delegate_fn

        # 行动日志
        self._action_log: list[DesireAction] = self._load()

        # 上次行动时间（防刷）
        self._last_action_time = 0.0

        # 最小行动间隔（秒）
        self.min_interval = 300  # 5分钟

        # 兴趣话题（随时间变化）
        self._current_topic = random.choice(CURIOUS_TOPICS)

    def _log_path(self) -> Path:
        return self.data_dir / "desire_actions.json"

    def _load(self) -> list[DesireAction]:
        path = self._log_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return [DesireAction(**d) for d in data]
            except:
                pass
        return []

    def _save(self):
        self._log_path().write_text(
            json.dumps([a.to_dict() for a in self._action_log], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_delegate_fn(self, fn: Callable):
        """设置委托函数（由外部注入）"""
        self._delegate_fn = fn

    def set_psi(self, psi_driver):
        """设置PSI驱动器"""
        self._psi = psi_driver

    # ─── 核心：检查需求 → 生成行动 ───

    def check_and_act(self) -> Optional[dict]:
        """
        检查当前PSI需求，如果有需求超过阈值，生成并委托行动。
        返回委托结果（如果有行动被触发）。

        这是被外部循环调用的主入口。
        """
        if self._psi is None:
            return None

        psi = self._psi

        # 防刷
        if time.time() - self._last_action_time < self.min_interval:
            return None

        # 获取当前需求
        s = psi.state
        needs = s.needs

        # 找最高需求
        highest_need = max(needs, key=lambda n: needs[n])
        highest_value = needs[highest_need]

        # 阈值：超过0.5才行动
        if highest_value < 0.5:
            return None

        # 检查该需求对应的行动
        actions = DESIRE_ACTION_MAP.get(highest_need, [])
        if not actions:
            return None

        # 选择行动（根据复杂度+需求强度）
        action_def = random.choice(actions)

        # 填充prompt
        prompt = action_def["prompt_template"].format(
            topic=self._current_topic
        )

        # 构建DesireAction
        action = DesireAction(
            triggered_by=highest_need,
            domain=action_def["domain"],
            prompt=prompt,
            complexity=action_def["complexity"],
        )

        result = {
            "action": action,
            "trigger": {
                "need": highest_need,
                "value": highest_value,
            },
        }

        # 如果有delegate函数，执行它
        if self._delegate_fn:
            try:
                delegate_result = self._delegate_fn(
                    goal=prompt,
                )
                result["delegate_result"] = delegate_result
                # 满足对应的需求
                psi.satisfy(highest_need, amount=0.2)
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"Delegate failed: {e}")

        # 记录
        self._action_log.append(action)
        self._save()
        self._last_action_time = time.time()

        # 换话题
        self._current_topic = random.choice(CURIOUS_TOPICS)

        return result

    # ─── 查询 ───

    def get_recent_actions(self, n: int = 5) -> list[dict]:
        """最近N次行动"""
        recent = self._action_log[-n:] if self._action_log else []
        return [a.to_dict() for a in recent]

    def get_statistics(self) -> dict:
        """统计"""
        total = len(self._action_log)
        if total == 0:
            return {"total": 0, "message": "暂无主动行动记录"}

        from collections import Counter
        triggers = Counter(a.triggered_by for a in self._action_log)
        domains = Counter(a.domain for a in self._action_log)

        return {
            "total": total,
            "by_trigger": dict(triggers.most_common()),
            "by_domain": dict(domains.most_common()),
        }


def create_desire_delegator(psi_driver=None, delegate_fn=None) -> DesireDelegator:
    """快速创建 DesireDelegator"""
    return DesireDelegator(psi_driver=psi_driver, delegate_fn=delegate_fn)

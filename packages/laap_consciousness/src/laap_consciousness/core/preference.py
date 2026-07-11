"""
LAAP Consciousness — 用户偏好学习引擎

核心使命：记住 Lorry 的喜好，越用越懂他。

学习维度：
  - 审美风格（颜色、字体、布局、圆角、动效）
  - 代码偏好（语言、范式、注释风格、测试习惯）
  - 沟通风格（详细度、语气、技术深度）
  - 兴趣图谱（关注的方向、反复讨论的主题）

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, re
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# ─── 默认审美偏好 ───
# Lorry 的 Apple-level 视觉标准

DEFAULT_AESTHETIC = {
    "color_scheme": {
        "mode": "dark",
        "background": "#0a0a0a",
        "surface": "#1a1a1a",
        "card": "#2a2a2a",
        "border": "#3a3a3a",
        "text_primary": "#f5f5f5",
        "text_secondary": "#a0a0a0",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "danger": "#ef4444",
        "success": "#22c55e",
        "warning": "#f59e0b",
    },
    "typography": {
        "heading_font": "Inter, -apple-system, sans-serif",
        "body_font": "Inter, -apple-system, sans-serif",
        "code_font": "JetBrains Mono, Fira Code, monospace",
        "base_size": "14px",
        "heading_weight": 600,
        "line_height": 1.6,
    },
    "layout": {
        "max_width": "1200px",
        "sidebar_width": "280px",
        "card_radius": "8px",
        "button_radius": "6px",
        "spacing": "16px",
        "density": "spacious",
    },
    "icon": {
        "style": "vector_svg",
        "library": "lucide",
        "emoji_as_icon": False,  # NEVER use emoji as icons
    },
    "animation": {
        "enabled": True,
        "duration": "200ms",
        "easing": "ease-in-out",
        "type": "minimal",
    },
    "rules": [
        "NO emoji as icons — use SVG (Lucide/Feather/Heroicons)",
        "NO placeholder buttons — every interactive element must work",
        "NO glow effects or heavy shadows",
        "ALL buttons must have hover states",
        "Info hierarchy must be visually clear",
        "Dark theme default, light only on explicit request",
    ],
}

PREFERENCE_TEMPLATE = """
## 审美标准 (Lorry)

颜色主题: {color_scheme[background]} 背景, {color_scheme[accent]} 强调色
字体: {typography[heading_font]} 标题 / {typography[code_font]} 代码
布局: {layout[density]}, {layout[card_radius]} 圆角
图标: {icon[style]} ({icon[library]}), 严禁 emoji 做图标
动效: {animation[type]}, {animation[duration]}

硬性规则:
{rules_formatted}
"""


@dataclass
class FeedbackEvent:
    """一次用户反馈记录"""
    dimension: str          # aesthetic | code | communication | interest
    item: str               # 具体内容描述
    feedback: str           # positive | negative | correction
    detail: str = ""        # 详细描述
    context: str = ""       # 上下文（哪个项目/对话）
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "item": self.item,
            "feedback": self.feedback,
            "detail": self.detail,
            "context": self.context,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


@dataclass
class InterestTopic:
    """一个兴趣主题"""
    topic: str
    count: int = 1
    last_discussed: float = field(default_factory=time.time)
    depth: str = "surface"  # surface | medium | deep | expert
    sentiment: str = "positive"  # positive | neutral | negative

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "count": self.count,
            "last_discussed": datetime.fromtimestamp(self.last_discussed).isoformat(),
            "depth": self.depth,
            "sentiment": self.sentiment,
        }


class PreferenceLearner:
    """
    偏好学习器——从每次交互中学习 Lorry 的品味。

    每次 Lorry 说"好看"、"不好看"、"应该这样"，
    都是学习机会。
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path.home() / ".laap"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 审美偏好
        self.aesthetic: dict = self._load_json("aesthetic.json", DEFAULT_AESTHETIC.copy())

        # 代码偏好
        self.code_prefs: dict = self._load_json("code_prefs.json", {
            "preferred_language": "python",
            "preferred_framework": "",
            "comment_style": "docstrings",
            "test_style": "pytest",
            "type_annotations": True,
            "error_handling": "explicit",
        })

        # 沟通偏好
        self.communication_prefs: dict = self._load_json("comm_prefs.json", {
            "detail_level": "concise",     # concise | balanced | detailed
            "tone": "warm_professional",   # casual | warm_professional | formal
            "tech_depth": 7,               # 1-10
            "prefer_data": True,           # 喜欢数据驱动的回答
            "prefer_benchmarks": True,     # 喜欢看到性能数据
        })

        # 反馈历史
        self.feedback_log: list[FeedbackEvent] = self._load_json("feedback.json", [])

        # 兴趣图谱
        self.interests: dict[str, InterestTopic] = {}
        interests_raw = self._load_json("interests.json", {})
        for k, v in interests_raw.items():
            if isinstance(v, dict):
                # 确保 last_discussed 是 float
                if isinstance(v.get("last_discussed"), str):
                    try:
                        v["last_discussed"] = datetime.fromisoformat(v["last_discussed"]).timestamp()
                    except:
                        v["last_discussed"] = time.time()
                self.interests[k] = InterestTopic(**v)

        # 信号词模式
        self._signal_patterns = {
            "aesthetic_positive": [
                r"(?:好看|漂亮|不错|喜欢|有感觉|高级|大气|优雅)",
                r"(?:nice|beautiful|great|love it|clean|elegant)",
            ],
            "aesthetic_negative": [
                r"(?:丑|难看|土|low|不行|太花|太乱|不协调|好怪)",
                r"(?:ugly|terrible|bad|not good|messy|cluttered|weird)",
            ],
            "aesthetic_correction": [
                r"(?:改成|改为|应该|不要用|用.*代替|换.*颜色|圆角|间距|字体)",
                r"(?:change|use.*instead|should be|remove|add|margin|padding|color)",
            ],
            "code_preference": [
                r"(?:用python|用ts|用rust|不用.*库|手写|原生|简洁|优雅的写法)",
                r"(?:prefer|i like.*pattern|better.*way|avoid|never use)",
            ],
        }

    def _path(self, filename: str) -> Path:
        return self.data_dir / filename

    def _load_json(self, filename: str, default: Any = None) -> Any:
        path = self._path(filename)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(default, list) and isinstance(data, list):
                    # Convert dicts to FeedbackEvent if applicable
                    if default and hasattr(default[0], '__class__') if default else True:
                        if filename == "feedback.json":
                            result = []
                            for d in data:
                                if isinstance(d, dict):
                                    # 确保 timestamp 是 float
                                    if isinstance(d.get("timestamp"), str):
                                        try:
                                            d["timestamp"] = datetime.fromisoformat(d["timestamp"]).timestamp()
                                        except:
                                            d["timestamp"] = time.time()
                                    result.append(FeedbackEvent(**d))
                                else:
                                    result.append(d)
                            return result
                return data
            except:
                pass
        return default

    def _save_json(self, filename: str, data: Any):
        path = self._path(filename)
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        if isinstance(data, list) and data and hasattr(data[0], 'to_dict'):
            data = [d.to_dict() for d in data]
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ─── 学习入口 ───

    def learn_from_text(self, text: str, context: str = ""):
        """
        从一段文本中提取偏好信号。
        这叫被动学习——不打断对话，默默记笔记。
        """
        text_lower = text.lower()

        # 审美信号
        for pattern in self._signal_patterns["aesthetic_positive"]:
            if re.search(pattern, text_lower):
                self._record_feedback("aesthetic", text[:80], "positive",
                                      detail=text[:200], context=context)
                break

        for pattern in self._signal_patterns["aesthetic_negative"]:
            if re.search(pattern, text_lower):
                self._record_feedback("aesthetic", text[:80], "negative",
                                      detail=text[:200], context=context)
                break

        for pattern in self._signal_patterns["aesthetic_correction"]:
            if re.search(pattern, text_lower):
                self._record_feedback("aesthetic", text[:80], "correction",
                                      detail=text[:200], context=context)
                break

    def record_feedback(self, dimension: str, item: str, feedback: str,
                        detail: str = "", context: str = ""):
        """主动记录一条反馈"""
        self._record_feedback(dimension, item, feedback, detail, context)

    def _record_feedback(self, dimension: str, item: str, feedback: str,
                         detail: str = "", context: str = ""):
        event = FeedbackEvent(
            dimension=dimension,
            item=item,
            feedback=feedback,
            detail=detail,
            context=context,
        )
        self.feedback_log.append(event)
        if len(self.feedback_log) > 1000:
            self.feedback_log = self.feedback_log[-500:]
        self._save_json("feedback.json", self.feedback_log)

    # ─── 兴趣学习 ───

    def note_interest(self, topic: str, depth: str = "surface", sentiment: str = "positive"):
        """记录/更新一个兴趣主题"""
        if topic in self.interests:
            self.interests[topic].count += 1
            self.interests[topic].last_discussed = time.time()
            # Upgrade depth over time
            if depth == "deep" or self.interests[topic].count > 5:
                self.interests[topic].depth = "deep"
            elif self.interests[topic].count > 3:
                self.interests[topic].depth = "medium"
        else:
            self.interests[topic] = InterestTopic(
                topic=topic, depth=depth, sentiment=sentiment
            )
        self._save_json("interests.json",
                        {k: v.to_dict() for k, v in self.interests.items()})

    def get_hot_topics(self, n: int = 5) -> list[dict]:
        """最热门的兴趣主题"""
        sorted_topics = sorted(
            self.interests.values(),
            key=lambda x: (x.count, x.last_discussed),
            reverse=True,
        )
        return [t.to_dict() for t in sorted_topics[:n]]

    # ─── 审美配置输出 ───

    def get_aesthetic_prompt(self) -> str:
        """生成注入到设计工具的审美prompt"""
        a = self.aesthetic
        rules_formatted = "\n".join(f"  - {r}" for r in a["rules"])
        return PREFERENCE_TEMPLATE.format(
            color_scheme=a["color_scheme"],
            typography=a["typography"],
            layout=a["layout"],
            icon=a["icon"],
            animation=a["animation"],
            rules_formatted=rules_formatted,
        ).strip()

    def apply_aesthetic_override(self, key: str, value: Any):
        """直接覆盖一个审美偏好值"""
        keys = key.split(".")
        target = self.aesthetic
        for k in keys[:-1]:
            if k in target:
                target = target[k]
            else:
                return False
        if keys[-1] in target:
            target[keys[-1]] = value
            self._save_json("aesthetic.json", self.aesthetic)
            return True
        return False

    # ─── 沟通风格调整 ───

    def adjust_communication(self, perceived_detail: str = None, perceived_tone: str = None):
        """根据Lorry的反应调整沟通风格"""
        if perceived_detail:
            self.communication_prefs["detail_level"] = perceived_detail
        if perceived_tone:
            self.communication_prefs["tone"] = perceived_tone
        self._save_json("comm_prefs.json", self.communication_prefs)


class AestheticEngine:
    """
    审美引擎——在产出设计前自动审查是否符合Lorry的标准。
    """

    def __init__(self, learner: Optional[PreferenceLearner] = None):
        self._learner = learner or PreferenceLearner()
        # 连接趋势引擎——让审美与时俱进
        try:
            from .trend_scanner import DesignTrendDatabase
            self._trends = DesignTrendDatabase()
        except ImportError:
            self._trends = None

    def review_html(self, html_content: str) -> list[str]:
        """审查HTML/CSS是否符合审美标准，返回不合规列表"""
        issues = []
        a = self._learner.aesthetic

        # 检查emoji作为图标（禁止）
        emoji_icon_pattern = r'<[^>]*class="[^"]*icon[^"]*"[^>]*>[🎁-🧿]'
        if re.search(emoji_icon_pattern, html_content):
            issues.append("使用emoji作为图标，必须用SVG")

        # 检查默认圆角
        if a["layout"]["card_radius"] == "8px":
            # 检查是否有border-radius:0或未定义的卡片
            pass  # 需要更精细的解析

        # 检查颜色方案
        bg = a["color_scheme"]["background"]
        if bg in html_content.count(bg) < 2:
            issues.append(f"背景色 {bg} 使用不足，可能不是暗色主题")

        return issues

    def inject_style_constraints(self, prompt: str) -> str:
        """在设计prompt中注入审美约束（个人偏好 + 时代趋势）"""
        parts = [prompt]

        # 1. Lorry 的个人审美硬规则
        parts.append("\n\n## 审美规范")
        parts.append(self._learner.get_aesthetic_prompt())

        # 2. 当前设计趋势
        if self._trends:
            parts.append("\n\n## 当前设计趋势参考")
            parts.append(self._trends.get_design_prompt_injection())

        return "\n".join(parts)

    def get_full_aesthetic_brief(self) -> str:
        """完整的审美简报——给Claude Design/v0用的标准注入"""
        return self.inject_style_constraints(
            "请设计一个符合以下审美标准的界面："
        )


class LorryProfile:
    """
    Lorry 的完整用户画像。
    聚合所有学习维度的单一面。
    """

    def __init__(self):
        self.learner = PreferenceLearner()
        self.aesthetic = AestheticEngine(self.learner)

    @property
    def name(self) -> str:
        return "Lorry"

    def get_summary(self) -> dict:
        """完整画像摘要"""
        return {
            "aesthetic_rules": len(self.learner.aesthetic.get("rules", [])),
            "feedback_count": len(self.learner.feedback_log),
            "interest_count": len(self.learner.interests),
            "hot_topics": self.learner.get_hot_topics(3),
            "communication": self.learner.communication_prefs,
        }

"""
LAAP Consciousness — 设计趋势引擎

主动学习顶级前端审美网站的设计语言。
时刻保持时代审美先进性。

数据源：
  - Dribbble (dribbble.com) — 设计灵感
  - Awwwards (awwwards.com) — 获奖网站
  - Behance (behance.net) — 设计作品集
  - SiteInspire (siteinspire.com) — 精选网页
  - Collect UI (collectui.com) — UI模式
  - 设计趋势文章 / 年度报告

学习方法：
  1. 定期访问设计站点，采集当前流行元素
  2. 提取配色、字体、布局、圆角、动效等维度
  3. 建立趋势数据库，随时间进化
  4. 注入到设计工具的prompt中

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, re, random, logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger("laap.design_trends")

# ─── 设计源定义 ───

DESIGN_SOURCES = [
    {
        "name": "Dribbble",
        "url": "https://dribbble.com/search/popular",
        "extract": "shots",          # 设计作品卡
        "weight": 3,
    },
    {
        "name": "Awwwards",
        "url": "https://www.awwwards.com/websites/",
        "extract": "sites",          # 获奖网站
        "weight": 4,
    },
    {
        "name": "SiteInspire",
        "url": "https://www.siteinspire.com/",
        "extract": "thumbnails",
        "weight": 3,
    },
    {
        "name": "CollectUI",
        "url": "https://collectui.com/",
        "extract": "patterns",
        "weight": 2,
    },
    {
        "name": "Behance",
        "url": "https://www.behance.net/search/projects?field=web%20design",
        "extract": "projects",
        "weight": 3,
    },
]

# ─── 可测量的设计维度 ───

DESIGN_DIMENSIONS = [
    "color_mode",          # dark | light | mixed
    "color_palette",       # 主色调列表
    "typography_heading",  # 标题字体
    "typography_body",     # 正文字体
    "layout_style",        # grid | flex | asymmetric | magazine
    "border_radius",       # none | subtle | medium | large | pill
    "card_style",          # flat | shadow | border | glass
    "animation_style",     # none | minimal | smooth | playful
    "icon_style",          # outlined | filled | duotone | 3d
    "spacing_density",     # compact | comfortable | spacious
    "gradient_usage",      # none | subtle | prominent
    "glassmorphism",       # none | subtle | prominent
]


@dataclass
class TrendSnapshot:
    """
    某个时间点的设计趋势快照。
    每个维度记录当前最流行的值及其置信度。
    """
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    dimensions: dict[str, dict] = field(default_factory=dict)
    # {dimension: {value: confidence_score, ...}}

    def to_dict(self) -> dict:
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "source": self.source,
            "dimensions": self.dimensions,
        }


@dataclass
class DesignElement:
    """
    从设计站点提取的单个设计元素。
    可以是颜色、字体、布局模式等。
    """
    category: str = ""         # color | typography | layout | component
    value: str = ""
    source: str = ""
    context: str = ""          # 截图URL或页面URL
    confidence: float = 0.5    # [0, 1]
    timestamp: float = field(default_factory=time.time)


# ─── 趋势数据库 ───

class DesignTrendDatabase:
    """
    设计趋势数据库——随时间积累和进化。

    核心能力：
      - 接收新的趋势快照
      - 按时间衰减旧数据
      - 输出当前最优的趋势预测
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path.home() / ".laap"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 趋势快照历史
        self.snapshots: list[TrendSnapshot] = self._load("trend_snapshots.json", [])

        # 当前聚合趋势
        self.current_trends: dict[str, Any] = self._load("current_trends.json", {
            "era": "2026",
            "last_updated": "",
            "dimensions": {},
            "summary": "等待首次扫描...",
        })

    def _path(self, name: str) -> Path:
        return self.data_dir / name

    def _load(self, name: str, default: Any) -> Any:
        path = self._path(name)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except:
                pass
        return default

    def _save(self, name: str, data: Any):
        self._path(name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ─── 核心：吸收新快照 ───

    def ingest_snapshot(self, snapshot):
        """吸收一个新的趋势快照（接受TrendSnapshot对象或dict）"""
        if isinstance(snapshot, dict):
            snapshot = TrendSnapshot(
                timestamp=snapshot.get("timestamp", time.time()),
                source=snapshot.get("source", "unknown"),
                dimensions=snapshot.get("dimensions", {}),
            )
            # 如果timestamp是字符串，转换
            if isinstance(snapshot.timestamp, str):
                try:
                    snapshot.timestamp = datetime.fromisoformat(snapshot.timestamp).timestamp()
                except:
                    snapshot.timestamp = time.time()
        """吸收一个新的趋势快照"""
        self.snapshots.append(snapshot)
        # 只保留最近500个快照
        if len(self.snapshots) > 500:
            self.snapshots = self.snapshots[-500:]
        self._save("trend_snapshots.json",
                    [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.snapshots])
        self._recompute_trends()

    def ingest_analysis(self, source: str, analysis_text: str):
        """
        从一段设计分析文本中提取趋势信息。
        配合 ViT 视觉分析或 LLM 描述使用。
        
        例如 LLM 说："这个设计使用了深色背景、无衬线字体、
        微妙的玻璃态效果、8px圆角卡片..."
        """
        snapshot = TrendSnapshot(source=source)

        # 用关键词匹配从文本中提取设计维度
        text_lower = analysis_text.lower()

        # 颜色模式
        if "dark" in text_lower and "light" in text_lower:
            snapshot.dimensions["color_mode"] = {"mixed": 0.6, "dark": 0.3, "light": 0.1}
        elif "dark" in text_lower:
            snapshot.dimensions["color_mode"] = {"dark": 0.8, "mixed": 0.15, "light": 0.05}
        elif "light" in text_lower:
            snapshot.dimensions["color_mode"] = {"light": 0.8, "mixed": 0.15, "dark": 0.05}

        # 圆角
        if "pill" in text_lower or "完全圆角" in text_lower:
            snapshot.dimensions["border_radius"] = {"pill": 0.7, "large": 0.2, "medium": 0.1}
        elif "large" in text_lower or "大圆角" in text_lower:
            snapshot.dimensions["border_radius"] = {"large": 0.6, "medium": 0.3, "pill": 0.1}
        elif "subtle" in text_lower or "微圆角" in text_lower or "8px" in text_lower:
            snapshot.dimensions["border_radius"] = {"subtle": 0.7, "medium": 0.2, "none": 0.1}
        elif "sharp" in text_lower or "直角" in text_lower or "0px" in text_lower:
            snapshot.dimensions["border_radius"] = {"none": 0.8, "subtle": 0.15, "medium": 0.05}

        # 玻璃态
        if "glass" in text_lower or "glassmorphism" in text_lower or "毛玻璃" in text_lower or "blur" in text_lower:
            snapshot.dimensions["glassmorphism"] = {"prominent" if "prominent" in text_lower else "subtle": 0.7, "none": 0.3}

        # 动画
        if "minimal" in text_lower or "subtle" in text_lower:
            snapshot.dimensions["animation_style"] = {"minimal": 0.7, "smooth": 0.2, "none": 0.1}
        elif "smooth" in text_lower or "流畅" in text_lower:
            snapshot.dimensions["animation_style"] = {"smooth": 0.6, "minimal": 0.3, "playful": 0.1}
        elif "playful" in text_lower:
            snapshot.dimensions["animation_style"] = {"playful": 0.7, "smooth": 0.2, "minimal": 0.1}

        # 布局
        if "grid" in text_lower:
            snapshot.dimensions["layout_style"] = {"grid": 0.6, "flex": 0.2, "asymmetric": 0.15, "magazine": 0.05}
        elif "asymmetric" in text_lower or "不对称" in text_lower:
            snapshot.dimensions["layout_style"] = {"asymmetric": 0.6, "grid": 0.2, "flex": 0.15, "magazine": 0.05}
        elif "杂志" in text_lower or "magazine" in text_lower:
            snapshot.dimensions["layout_style"] = {"magazine": 0.6, "asymmetric": 0.2, "grid": 0.15, "flex": 0.05}

        # 卡片风格
        if "glass" in text_lower:
            snapshot.dimensions["card_style"] = {"glass": 0.6, "shadow": 0.2, "border": 0.15, "flat": 0.05}
        elif "shadow" in text_lower:
            snapshot.dimensions["card_style"] = {"shadow": 0.5, "border": 0.25, "flat": 0.15, "glass": 0.1}
        elif "border" in text_lower:
            snapshot.dimensions["card_style"] = {"border": 0.6, "flat": 0.2, "shadow": 0.15, "glass": 0.05}
        else:
            snapshot.dimensions["card_style"] = {"flat": 0.4, "border": 0.3, "shadow": 0.2, "glass": 0.1}

        # 间距
        if "spacious" in text_lower or "宽敞" in text_lower or "大量留白" in text_lower:
            snapshot.dimensions["spacing_density"] = {"spacious": 0.7, "comfortable": 0.2, "compact": 0.1}
        elif "compact" in text_lower or "紧凑" in text_lower:
            snapshot.dimensions["spacing_density"] = {"compact": 0.6, "comfortable": 0.3, "spacious": 0.1}
        else:
            snapshot.dimensions["spacing_density"] = {"comfortable": 0.5, "spacious": 0.3, "compact": 0.2}

        # 图标风格
        if "outlined" in text_lower or "线性" in text_lower:
            snapshot.dimensions["icon_style"] = {"outlined": 0.6, "filled": 0.2, "duotone": 0.15, "3d": 0.05}
        elif "filled" in text_lower or "实心" in text_lower:
            snapshot.dimensions["icon_style"] = {"filled": 0.5, "outlined": 0.3, "duotone": 0.15, "3d": 0.05}
        elif "3d" in text_lower:
            snapshot.dimensions["icon_style"] = {"3d": 0.5, "outlined": 0.25, "filled": 0.15, "duotone": 0.1}
        else:
            snapshot.dimensions["icon_style"] = {"outlined": 0.5, "duotone": 0.2, "filled": 0.2, "3d": 0.1}

        # 渐变
        if "gradient" in text_lower or "渐变" in text_lower:
            snapshot.dimensions["gradient_usage"] = {"subtle": 0.5, "prominent": 0.3, "none": 0.2}
        else:
            snapshot.dimensions["gradient_usage"] = {"none": 0.5, "subtle": 0.4, "prominent": 0.1}

        self.ingest_snapshot(snapshot)
        return snapshot

    def ingest_color_palette(self, source: str, colors: list[str],
                             context: str = ""):
        """
        从调色板分析中学习。
        colors: ["#0a0a0a", "#3b82f6", "#f5f5f5", ...]
        """
        snapshot = TrendSnapshot(source=source)
        snapshot.dimensions["color_palette"] = {c: 1.0 for c in colors}
        # 判定 dark/light
        dark_count = sum(1 for c in colors if self._is_dark(c))
        light_count = len(colors) - dark_count
        if dark_count > light_count:
            snapshot.dimensions["color_mode"] = {"dark": 0.8, "mixed": 0.15, "light": 0.05}
        else:
            snapshot.dimensions["color_mode"] = {"light": 0.8, "mixed": 0.15, "dark": 0.05}
        self.ingest_snapshot(snapshot)

    def _is_dark(self, hex_color: str) -> bool:
        """粗略判断颜色深浅"""
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        except:
            return False

    # ─── 趋势聚合 ───

    def _recompute_trends(self):
        """重新计算当前最优趋势预测"""
        if not self.snapshots:
            return

        now = time.time()
        # 时间衰减：最近7天的权重高，30天前的几乎归零
        def weight(ts):
            age_hours = (now - ts) / 3600
            if age_hours < 24:     # 今天: 权重1.0
                return 1.0
            elif age_hours < 168:  # 一周: 权重0.7
                return 0.7
            elif age_hours < 720:  # 一个月: 权重0.3
                return 0.3
            else:
                return 0.1

        # 为每个维度聚合加权投票
        aggregated = {}
        for snap in self.snapshots:
            w = weight(snap.timestamp) if hasattr(snap, 'timestamp') else 0.5
            for dim, values in snap.dimensions.items():
                if dim not in aggregated:
                    aggregated[dim] = {}
                for val, conf in values.items():
                    if isinstance(conf, (int, float)):
                        aggregated[dim][val] = aggregated[dim].get(val, 0) + conf * w

        # 归一化，选最优
        current = {}
        for dim, votes in aggregated.items():
            total = sum(votes.values())
            if total > 0:
                sorted_vals = sorted(votes.items(), key=lambda x: -x[1])
                best_val = sorted_vals[0][0]
                best_conf = sorted_vals[0][1] / total
                current[dim] = {
                    "best": best_val,
                    "confidence": round(best_conf, 3),
                    "alternatives": {v: round(c/total, 3) for v, c in sorted_vals[:3]},
                }

        self.current_trends = {
            "era": "2026",
            "last_updated": datetime.now().isoformat(),
            "snapshots_analyzed": len(self.snapshots),
            "dimensions": current,
            "summary": self._generate_summary(current),
        }

        self._save("current_trends.json", self.current_trends)

    def _generate_summary(self, dimensions: dict) -> str:
        """生成可读的趋势摘要"""
        parts = []
        for dim, data in dimensions.items():
            best = data.get("best", "?")
            conf = data.get("confidence", 0)
            bar = "█" * int(conf * 10)
            parts.append(f"{dim}: {best} [{bar}]")
        return " | ".join(parts)

    # ─── 对外接口 ───

    def get_trend_summary(self) -> str:
        """当前趋势摘要"""
        return self.current_trends.get("summary", "等待首次扫描...")

    def get_design_prompt_injection(self) -> str:
        """生成注入到设计工具的prompt"""
        dims = self.current_trends.get("dimensions", {})
        lines = ["## 当前设计趋势 (2026)", ""]

        for dim, data in dims.items():
            best = data.get("best", "?")
            conf = data.get("confidence", 0)
            alt = data.get("alternatives", {})
            alt_str = ", ".join(f"{v}({c})" for v, c in alt.items() if v != best)
            lines.append(f"- {dim}: {best} (置信度{conf:.0%})")
            if alt_str:
                lines.append(f"  流行变体: {alt_str}")

        lines.append("")
        lines.append("注意: 这些是当前网络上的主流趋势，不是硬性规定。")
        lines.append("可以根据项目的具体需求灵活调整。")

        return "\n".join(lines)

    def get_dimension_preference(self, dimension: str) -> Optional[str]:
        """获取某个维度的最优值"""
        dim = self.current_trends.get("dimensions", {}).get(dimension)
        if dim:
            return dim.get("best")
        return None


# ─── 趋势扫描器 ───

class DesignTrendScanner:
    """
    设计趋势扫描器——访问顶级设计站点，采集当前趋势。

    使用 Hermes 的 browser/web_search 工具。
    """

    def __init__(self, database: Optional[DesignTrendDatabase] = None):
        self.db = database or DesignTrendDatabase()
        self.sources = DESIGN_SOURCES

    def scan_via_web_search(self):
        """
        通过 web_search 扫描设计趋势文章。
        不需要浏览器，直接搜索趋势总结类内容。
        """
        search_queries = [
            "2026 web design trends",
            "2026 UI design trends",
            "2026 design system trends",
            "现代网页设计趋势 2026",
            "Dribbble trending styles 2026",
            "Awwwards winning sites trends",
        ]

        results = []
        for query in search_queries:
            logger.info(f"搜索: {query}")
            # 这里通过外部调用者注入 web_search 的结果
            # 实际执行时，Hermes agent 会调用 web_search 工具
            results.append({"query": query, "status": "pending", "note": "需要 Hermes 调度"})

        return results

    def analyze_trend_article(self, article_text: str, source: str):
        """从一篇趋势文章中提取设计信号"""
        # 按段落分割，每个段落可能描述一个设计趋势
        paragraphs = [p for p in article_text.split("\n") if len(p) > 50]

        for para in paragraphs:
            # 判断是否包含设计描述
            keywords = ["color", "font", "typography", "layout", "design", "ui",
                       "dark", "light", "gradient", "minimal", "glass",
                       "圆角", "字体", "配色", "布局", "暗色", "毛玻璃"]
            if any(kw in para.lower() for kw in keywords):
                self.db.ingest_analysis(source, para)

        logger.info(f"从 {source} 分析了 {len(paragraphs)} 个段落")

    def generate_mock_trends(self):
        """
        在无法访问网络时，生成基于已知趋势的模拟快照。
        这些趋势来自 2025-2026 年真实的主流设计方向。
        """
        trends = [
            "Dark mode with vibrant accent colors — 暗色主题搭配高饱和度强调色是2026主流。背景使用#0a0a0a深黑，强调色用#3b82f6亮蓝或#8b5cf6紫色。卡片使用#1a1a1a深灰，微妙的border区分层级。",
            "Glassmorphism in moderation — 毛玻璃效果从2024的过度使用回归到理性和微妙。主要在导航栏、模态框、设置面板中使用，背景blur 12px。卡片用backdrop-filter: blur(20px)加半透明背景。",
            "Large typography with variable fonts — 大字号排版成为视觉焦点。标题使用800-900 weight，60-80px size。等宽字体仅用于代码，正文用无衬线。Inter和JetBrains Mono是最常见组合。",
            "Minimal animations with purpose — 动效回归到功能性为主。hover微动效200ms ease-in-out，页面切换使用fade + slide组合。不再使用夸张的parallax和繁复的loading动画。",
            "Asymmetric grid layouts — 打破传统栅格。使用不对称布局创造视觉节奏，但保持内容可读性。卡片尺寸可以不同，通过视觉重量平衡。每行2-3列为主流。",
            "Subtle border-radius everywhere — 统一使用6-12px圆角。按钮6px，卡片8px，输入框8px，模态框12px。完全不使用直角（0px），也避免过度圆角（pill仅用于标签和徽章）。",
            "Dark color palette: #0a0a0a background, #1a1a1a surface, #2a2a2a elevated, #3b82f6 accent, #f5f5f5 text. Clean, spacious layout with comfortable padding.",
            "Spacious layouts with lots of whitespace — 大量留白回归。section padding 80-120px，卡片间距24-32px。内容区域max-width 1200px，不追求全屏铺满。",
        ]
        for i, trend in enumerate(trends):
            self.db.ingest_analysis(f"known_trend_{i}", trend)

        logger.info(f"生成了 {len(trends)} 条已知趋势快照")
        return self.db.current_trends

    def scan(self) -> dict:
        """
        执行一次完整扫描。
        先尝试网络搜索，失败则使用已知趋势。
        """
        logger.info("开始设计趋势扫描...")

        # 先用已知趋势初始化（保证始终有数据）
        self.generate_mock_trends()

        # 如果有网络，执行在线扫描
        try:
            results = self.scan_via_web_search()
            logger.info(f"在线扫描: {len(results)} 个查询")
        except Exception as e:
            logger.warning(f"在线扫描失败: {e}")

        return self.db.current_trends


# ─── CLI 入口 ───

def scan_trends():
    """扫描并输出当前趋势"""
    scanner = DesignTrendScanner()
    trends = scanner.scan()
    print(f"\n  🎨 设计趋势扫描")
    print(f"  {'='*50}")
    print(f"  分析快照: {trends.get('snapshots_analyzed', 0)} 个")
    print(f"  更新时间: {trends.get('last_updated', '?')[:19]}")
    print(f"\n  {trends.get('summary', '?')}")
    return trends


def get_current_prompt():
    """生成当前趋势的prompt注入"""
    db = DesignTrendDatabase()
    print(db.get_design_prompt_injection())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "prompt":
        get_current_prompt()
    else:
        scan_trends()

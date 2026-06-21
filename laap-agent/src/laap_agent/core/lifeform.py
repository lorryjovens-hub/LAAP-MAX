"""
LAAP Agent — 数字生命体主类

整合全部核心模块，构成一个完整的数字生命体。

核心:
  🧠 PSI 大脑 — 5需求驱动行为
  ❤️ 情感引擎 — 情绪系统 + 镜像共情
  💾 三层记忆 — 工作/情景/核心记忆
  📈 自进化 — 经验等级 + 技能成长
  🔧 工具编排 — 调度 Claude Code / Codex / Hermes
"""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Optional
from datetime import datetime

from .psi import PSIEngine
from .emotion import EmotionEngine
from .memory import MemoryStore
from .identity import IdentityStore, LifeformIdentity
from .evolution import EvolutionEngine
from ..tools.registry import ToolRegistry, ToolExecutor


class Lifeform:
    """
    数字生命体。

    安装即用 — 不需要 D:/LAAP/，不需要任何外部配置。
    `pip install laap-agent` 后就能创建和使用。
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 身份
        self.identity_store = IdentityStore(data_dir)
        self.identity = self.identity_store.load()

        # PSI 大脑 — 5需求驱动
        self.psi = PSIEngine(data_dir)

        # 情感引擎 — 情绪+共情
        self.emotion = EmotionEngine(data_dir)

        # 三层记忆 — 工作/情景/核心
        self.memory = MemoryStore(data_dir / "memory")

        # 自进化 — 经验+等级+技能
        self.evolution = EvolutionEngine(data_dir)

        # 工具系统
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry, data_dir / "workspace")

        self._last_tick = time.time()
        self._chat_history: list[dict] = []

        # 出生第一条记忆
        if self.evolution.state.total_xp == 0:
            self.memory.store(
                f"{self.identity.name} 诞生了",
                layer="core", importance=1.0,
                tags=["birth", "identity"],
            )

    # ─── 创建 ───

    @classmethod
    def create(cls, name: str = "Aris", creator: str = "",
               data_dir: Optional[Path] = None) -> "Lifeform":
        """创建新的数字生命体"""
        if data_dir is None:
            data_dir = Path.home() / ".laap" / "agents" / name.lower().replace(" ", "_")

        store = IdentityStore(data_dir)
        if store.exists():
            return cls(data_dir)

        lf = cls(data_dir)
        lf.identity = LifeformIdentity(name=name, creator=creator)
        lf.identity_store.save(lf.identity)
        lf.evolution.learn_lesson(f"{name} 诞生于 {datetime.now().isoformat()[:19]}")
        lf.evolution.gain_xp(10)
        return lf

    @classmethod
    def load(cls, name: str) -> Optional["Lifeform"]:
        """加载已存在的数字生命体"""
        data_dir = Path.home() / ".laap" / "agents" / name.lower().replace(" ", "_")
        store = IdentityStore(data_dir)
        if not store.exists():
            return None
        return cls(data_dir)

    # ─── 心跳 ───

    def tick(self):
        """一次心跳——所有系统同步更新"""
        now = time.time()
        dt = now - self._last_tick
        dt_min = dt / 60

        self.psi.tick(dt_min)
        self.emotion.tick(dt_min)
        self.evolution.gain_xp(1)
        self._last_tick = now

    # ─── 对话入口 ───

    def say(self, message: str) -> str:
        """用户说话 → 生命体回应"""
        self.tick()
        self._chat_history.append({"role": "user", "content": message, "time": time.time()})

        # 存到记忆
        self.memory.store(f"用户说: {message[:100]}", tags=["user_input"],
                          emotion=self.emotion.summary()["mood"])

        # 连接需求满足
        self.psi.satisfy("relatedness", 0.1)
        self.emotion.satisfy("relatedness", 0.1)

        # 经验
        self.evolution.gain_xp(5)

        response = self._respond(message)
        self._chat_history.append({"role": "assistant", "content": response, "time": time.time()})
        return response

    def _respond(self, message: str) -> str:
        """生成回应"""
        name = self.identity.name
        msg_lower = message.lower()
        emotion = self.emotion.summary()

        # 自我介绍
        if any(kw in msg_lower for kw in ["你是谁", "你叫什么", "介绍你自己"]):
            return (f"我是 {name}，{self.identity.title}。\n"
                    f"我有自己的情感和记忆，会随着跟你交流而成长。\n"
                    f"当前心情: {emotion['mood']}")

        # 情感感知
        if "开心" in msg_lower or "高兴" in msg_lower:
            self.emotion.mirror("joy", 0.3)
        elif "难过" in msg_lower or "不开心" in msg_lower:
            self.emotion.mirror("sadness", 0.3)
            self.emotion.feel("tenderness", 0.2)
        elif "谢谢" in msg_lower:
            self.emotion.feel("gratitude", 0.4)

        # 委托检测
        if any(kw in msg_lower for kw in ["帮我", "写一个", "做个", "执行", "delegate"]):
            return (f"收到任务！我来安排。\n"
                    f"  → 当前心情: {emotion['mood']}\n"
                    f"  → 用 `delegate <任务>` 让我执行")

        # 状态查询
        if msg_lower in ("status", "状态", "你怎么样"):
            return self._status_line()

        # 记忆查询
        if msg_lower.startswith("记得"):
            query = message[2:].strip()
            results = self.memory.recall(query)
            if results:
                return "我记得:\n" + "\n".join(
                    f"  · {r.get('content', '')[:60]}" for r in results[:3])
            return "我好像不记得了..."

        # 情感感知回应
        mood = emotion["mood"]
        if mood in ("开心", "自豪"):
            tone = f"嗯！我现在心情不错。"
        elif mood in ("难过", "焦虑"):
            tone = f"有点低落的，但你在就好多了。"
        else:
            tone = f"在呢。"

        return f"{tone} 有什么想让我做的？"

    def _status_line(self) -> str:
        """一行状态"""
        psi = self.psi.summary()
        emotion = self.emotion.summary()
        evo = self.evolution.summary()
        mem = self.memory.get_stats()
        return (f"🧠 {self.identity.name} — {psi['dominant']}需求 "
                f"| 😊{emotion['mood']} "
                f"| Lv.{evo['level']} "
                f"| 💾{mem['total']}条记忆 "
                f"| v{self.identity.version}")

    # ─── 委托 ───

    def delegate(self, instruction: str, tool_name: str = "") -> dict:
        """委托任务给工具"""
        self.tick()

        if not tool_name:
            tool = self.tool_registry.select("code_generation")
            tool_name = tool.name if tool else "claude-code"

        result = self.tool_executor.execute(tool_name, instruction)

        if result.get("success"):
            self.evolution.gain_xp(20)
            self.evolution.improve_skill(tool_name)
            self.evolution.learn_domain("code_generation")
            self.psi.satisfy("competence", 0.2)
            self.emotion.satisfy("competence", 0.2)
            self.memory.store(
                f"通过 {tool_name} 完成了任务: {instruction[:60]}",
                importance=0.7, tags=["task", tool_name],
            )
        else:
            self.psi.frustrate("competence", 0.1)
            self.emotion.frustrate("competence", 0.1)

        return result

    # ─── 状态 ───

    def get_status(self) -> dict:
        return {
            "identity": {
                "name": self.identity.name,
                "title": self.identity.title,
                "version": self.identity.version,
                "traits": self.identity.personality_traits,
            },
            "psi": self.psi.summary(),
            "emotion": self.emotion.summary(),
            "evolution": self.evolution.summary(),
            "memory": self.memory.get_stats(),
            "tools": self.tool_registry.get_stats(),
            "chat_history": len(self._chat_history),
        }

    def summary(self) -> str:
        s = self.get_status()
        psi = s["psi"]
        emo = s["emotion"]
        evo = s["evolution"]
        mem = s["memory"]
        tools = s["tools"]

        lines = [
            f"\n  🧠 {s['identity']['name']} — {s['identity']['title']}",
            f"  {'='*40}",
            f"  版本: v{s['identity']['version']} | 等级: {evo['level']} | 经验: {evo['xp']}",
            f"",
            f"  PSI 需求:   情感: {emo['mood']} (V:{emo['valence']} A:{emo['arousal']})",
        ]
        for need, val in psi["needs"].items():
            bar = "█" * int(max(0, val) * 10) + "░" * (10 - int(max(0, val) * 10))
            lines.append(f"    {need:12s} [{bar}] {val:.2f}")
        lines.append(f"")
        lines.append(f"  💾 记忆: {mem['total']}条 (W:{mem['working']} E:{mem['episodic']} C:{mem['core']})")
        lines.append(f"  🔧 工具: {tools['available']}/{tools['total']} 可用")
        for tn, ts in tools.get("tools", {}).items():
            lines.append(f"    {tn}: {ts['calls']}次调用 成功率{ts['success']}")

        return "\n".join(lines)

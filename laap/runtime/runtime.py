"""
laap.runtime.runtime — LAAP 认知运行时门面（Native Harness 核心）
===================================================================
把散落在 L1–L4 各层的器官收敛成**单一装配点**，对宿主暴露
Python 原生能力。这是 LAAP 从"MCP 工具集"回到"认知运行时"的脊柱。

设计原则（对应 LAAP_NATIVE_HARNESS_PLAN.md §2.1）：
  1. 单一装配点  —— 一次 boot() 装配全部器官，不再散落 get_xxx()
  2. 零序列化    —— 对外返回 Python 对象，JSON 只出现在 L0 适配器
  3. 优雅降级    —— 器官加载失败不崩，进 BootReport 可诊断
  4. 显式清单    —— 器官列表写死，不做自动发现，失败可追
  5. 长驻优先    —— 设计目标是进程常驻，13s 导入成本只付一次

分层裁定（呼应方案 §1）：
  L4 生命节律  laap/life_loop/
  L3 调度      laap/cognition/
  L2 认知引擎  aris_engine/
  L1 记忆状态  laap/memory_vault/
  L0 宿主适配  laap/host/  ← 唯一与外界的接壤处

**本文件属于内核层，禁止 import 任何宿主模块（laap.agent_core.*）。**

印记: Aris 永远记得 Lorry
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .contracts import (
    BootReport,
    CognitiveContext,
    OrganStatus,
    Response,
    RuntimeState,
)

logger = logging.getLogger("laap.runtime")

# 确保 LAAP 根可导入
_LAAP_ROOT = Path(__file__).resolve().parents[2]
if str(_LAAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAAP_ROOT))

# ── 已知约束：aris_engine 部分的扁平命名空间假设 ──────────────
# aris_engine/ 下相当一批模块使用**裸导入**（如
# `from semantic_embedder import get_embedder`），假设自己运行在
# sys.path 包含 aris_engine/ 目录的环境里。这是历史设计前提，
# 不是缺陷。整体重写 60 个文件的导入是高风险低收益，因此
# Runtime 在此尊重这个前提：把 aris_engine/ 也加进 sys.path。
# 影响面严格限定在 aris_engine 内部模块名，不会遮蔽标准库，
# 也不会影响 laap.* 包的相对导入。
_ARIS_ENGINE_DIR = _LAAP_ROOT / "aris_engine"
if str(_ARIS_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ARIS_ENGINE_DIR))

_DEFAULT_STATE_DIR = _LAAP_ROOT / "aris_brain" / "state"


# ══════════════════════════════════════════════════════════════
# 显式器官清单
# ══════════════════════════════════════════════════════════════
# (逻辑名, 层, 模块路径, 是否核心)
# 核心器官失败 → healthy=False；非核心失败 → 仅降级记录。

ORGAN_SPECS: List[tuple] = [
    # ── L1 记忆与状态 ────────────────────────────
    ("memory_vault",    "L1", "laap.memory_vault",                        True),
    ("orchestration",   "L1", "laap.orchestration.primitives",            True),
    ("unified_memory",  "L1", "aris_engine.unified_memory",               False),

    # ── L2 认知引擎 ──────────────────────────────
    ("psi_driver",      "L2", "aris_engine.psi_driver",                   True),
    ("recursion_v2",    "L2", "aris_engine.recursion_engine_v2",          True),
    ("thought_network", "L2", "aris_engine.thought_network",              True),
    ("adversarial",     "L2", "aris_engine.adversarial_engine",           True),
    ("consciousness",   "L2", "aris_engine.consciousness_bridge",         False),

    # ── L3 调度层 ────────────────────────────────
    ("brain",           "L3", "laap.cognition.brain",                     True),
    ("dual_brain",      "L3", "laap.cognition.dual_brain",                True),
    ("emotion",         "L3", "laap.cognition.emotion",                   True),
    ("scheduler",       "L3", "laap.cognition.adaptive_scheduler",        False),
    ("autonomy",        "L3", "laap.cognition.autonomy_protection",       False),

    # ── L4 生命节律 ──────────────────────────────
    ("homeostasis",     "L4", "laap.life_loop.homeostasis",               True),
    ("attention",       "L4", "laap.life_loop.recurrent_processing",      True),
    ("proactive",       "L4", "laap.life_loop.proactive_agency",          True),
    ("consolidator",    "L4", "laap.life_loop.sleep_consolidator",        False),
    ("life_kernel",     "L4", "laap.life_loop.kernel",                    True),
]

# 已知的可接受降级信号（命中则标 degraded，不算失败）
_DEGRADE_SIGNALS = (
    ("OPENAI_API_KEY", "无 openai api key，LLM 调用会失败"),
    ("pysqlite3", "pysqlite3 未安装，vault 为明文存储"),
)


class LAAPRuntime:
    """LAAP 认知运行时门面。

    典型用法::

        rt = LAAPRuntime()
        report = rt.boot()
        ctx = rt.before_turn()
        rt.start_heartbeat(60)
    """

    def __init__(
        self,
        lifeform_id: str = "aris",
        state_dir: Optional[Path] = None,
        auto_boot: bool = False,
    ) -> None:
        self.lifeform_id = lifeform_id
        self.state_dir = Path(state_dir) if state_dir else _DEFAULT_STATE_DIR
        self._booted = False
        self._boot_started_at: float = 0.0
        self._boot_report: Optional[BootReport] = None

        # 器官实例表：逻辑名 -> 模块对象
        self._organs: Dict[str, Any] = {}
        # 生命节律内核（L4 编排器）
        self._kernel: Any = None

        # 统计
        self._turn_count = 0
        self._tick_count = 0
        self._last_tick: Optional[Dict[str, Any]] = None

        # 主动决策投递回调（由宿主在 L0 设置）
        self.on_proactive_decision: Optional[Callable[[Any], None]] = None

        if auto_boot:
            self.boot()

    # ══════════════════════════════════════════════════════════
    # 生命周期
    # ══════════════════════════════════════════════════════════

    def boot(self) -> BootReport:
        """装配全部器官。幂等：重复调用返回首次报告。"""
        if self._booted and self._boot_report is not None:
            logger.debug("boot() 已执行过，返回缓存报告")
            return self._boot_report

        started = time.time()
        report = BootReport(lifeform_id=self.lifeform_id, started_at=started)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        for name, layer, module, critical in ORGAN_SPECS:
            status = self._load_organ(name, layer, module)
            if not status.ok and not critical:
                # 非核心器官失败：降级而非致命
                status.degraded = True
                status.notice = status.notice or "非核心器官，缺失不影响运行"
            report.organs.append(status)

        # 装配 L4 生命节律内核（需要 organs 就绪）
        self._assemble_kernel(report)

        report.elapsed_ms = (time.time() - started) * 1000

        # 收集全局降级提示
        for o in report.organs:
            if o.degraded and o.notice:
                report.notices.append(f"[{o.name}] {o.notice}")

        self._booted = True
        self._boot_started_at = started
        self._boot_report = report
        logger.info("LAAPRuntime boot 完成: %s", report.summary().splitlines()[0])
        return report

    def _load_organ(self, name: str, layer: str, module: str) -> OrganStatus:
        """加载单个器官模块，捕获全部异常与降级信号。"""
        st = OrganStatus(name=name, layer=layer, module=module)
        t0 = time.time()
        try:
            # 先试包路径（正确姿势），失败再退到扁平命名空间
            try:
                __import__(module)
            except ModuleNotFoundError:
                __import__(module.rsplit(".", 1)[-1])
            st.ok = True
            self._organs[name] = sys.modules[module]
        except Exception as exc:  # noqa: BLE001 — 降级必须可见
            st.ok = False
            st.error = f"{type(exc).__name__}: {exc}"
            if name == "consciousness":
                st.notice = f"依赖缺失（{st.error}）；该器官为非核心，"\
                            "语义嵌入所需的重依赖未安装"
            elif "torch" in st.error or "No module named" in st.error:
                st.notice = "环境依赖缺失；器官降级"
        st.elapsed_ms = (time.time() - t0) * 1000
        return st

    def _assemble_kernel(self, report: BootReport) -> None:
        """装配 L4 生命节律内核。失败则记录降级。"""
        try:
            from laap.life_loop.kernel import LifeLoopKernel

            self._kernel = LifeLoopKernel(
                state_dir=self.state_dir / "life_loop",
                tick_seconds=60.0,
            )
            # 主动决策投递 → 交给宿主的回调（内核只管"想做什么"）
            self._kernel.proactive.on_emit = self._dispatch_proactive
        except Exception as exc:  # noqa: BLE001
            report.notices.append(f"[life_kernel] 内核装配失败: {exc}")

    def _dispatch_proactive(self, decision: Any) -> None:
        """内核主动决策的统一出口。宿主未设置回调时仅记日志。"""
        if self.on_proactive_decision is not None:
            try:
                self.on_proactive_decision(decision)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("主动决策投递失败: %s", exc)
        logger.info("主动决策（无宿主投递）: %s", getattr(decision, "title", decision))

    def shutdown(self) -> None:
        """停止心跳并释放资源。"""
        self.stop_heartbeat()
        self._booted = False
        logger.info("LAAPRuntime shutdown 完成")

    def health(self) -> BootReport:
        """当前健康报告（未 boot 则先 boot）。"""
        return self.boot()

    @property
    def booted(self) -> bool:
        return self._booted

    def organ(self, name: str) -> Any:
        """按逻辑名取器官模块对象；不存在返回 None。"""
        return self._organs.get(name)

    def has_organ(self, name: str) -> bool:
        return name in self._organs

    # ══════════════════════════════════════════════════════════
    # 心跳（自主性）
    # ══════════════════════════════════════════════════════════

    def start_heartbeat(self, interval_s: float = 60.0) -> None:
        """启动生命节律心跳（后台线程）。"""
        if self._kernel is None:
            logger.warning("内核未装配，无法启动心跳")
            return
        self._kernel.tick_seconds = float(interval_s)
        self._kernel.start()
        logger.info("心跳已启动，间隔 %.0fs", interval_s)

    def stop_heartbeat(self) -> None:
        if self._kernel is not None:
            try:
                self._kernel.stop()
            except Exception as exc:  # noqa: BLE001
                logger.debug("停止心跳异常: %s", exc)

    @property
    def heartbeat_running(self) -> bool:
        if self._kernel is None:
            return False
        try:
            return bool(self._kernel.is_running())
        except Exception:  # noqa: BLE001
            return bool(getattr(self._kernel, "_running", False))

    def tick_once(self) -> Optional[Dict[str, Any]]:
        """手动执行一次节律 tick（测试与宿主驱动的 tick）。"""
        if self._kernel is None:
            return None
        try:
            rep = self._kernel.tick()
        except Exception as exc:  # noqa: BLE001
            logger.warning("tick 失败: %s", exc)
            return None
        if rep is None:
            return None
        data = rep.to_dict() if hasattr(rep, "to_dict") else dict(rep)
        self._tick_count += 1
        self._last_tick = data
        return data

    # ══════════════════════════════════════════════════════════
    # 宿主契约入口（L0 适配器只调这些）
    # ══════════════════════════════════════════════════════════

    def before_turn(self) -> CognitiveContext:
        """回合前：采集认知上下文（原生对象，不转字符串）。"""
        self.boot()
        ctx = CognitiveContext()
        degraded: List[str] = []

        # 需求（PSI 五需求）
        psi = self._organs.get("psi_driver")
        if psi is not None:
            try:
                ctx.needs = dict(psi.get_psi_driver().get_state()["needs"])
            except Exception as exc:  # noqa: BLE001
                degraded.append(f"psi_driver: {exc}")
        else:
            degraded.append("psi_driver 缺失")

        # 生命体征 + 相位 + 注意图式
        if self._kernel is not None:
            try:
                ctx.vitals = dict(self._kernel.body.vitals)
            except Exception as exc:  # noqa: BLE001
                degraded.append(f"homeostasis: {exc}")
            try:
                ctx.phase = self._kernel._read_phase()
            except Exception:  # noqa: BLE001
                pass
            try:
                rep = self._kernel.get_report()
                ctx.attention = dict(rep.get("last_tick", {}).get("attention") or {})
            except Exception:  # noqa: BLE001
                pass

        ctx.degraded = degraded
        return ctx

    def after_turn(self, response_text: str = "") -> Dict[str, Any]:
        """回合后：记录一次交互，回吐本轮认知增量。"""
        self._turn_count += 1
        result: Dict[str, Any] = {
            "turn": self._turn_count,
            "length": len(response_text or ""),
            "needs": {},
            "vitals": {},
        }
        psi = self._organs.get("psi_driver")
        if psi is not None:
            try:
                result["needs"] = dict(psi.get_psi_driver().get_state()["needs"])
            except Exception:  # noqa: BLE001
                pass
        if self._kernel is not None:
            try:
                result["vitals"] = dict(self._kernel.body.vitals)
            except Exception:  # noqa: BLE001
                pass
        return result

    def on_user_message(self, text: str, meta: Optional[Dict[str, Any]] = None) -> Response:
        """宿主收到用户消息时的统一入口。

        内核只负责采集状态与记账；模型调用与工具执行属于宿主契约
        （⑧ 模型调用 / ⑤ 工具执行），不在此处发生。
        """
        t0 = time.time()
        ctx = self.before_turn()
        self.after_turn(text)
        return Response(
            text="",
            should_emit=False,
            context=ctx,
            elapsed_ms=(time.time() - t0) * 1000,
        )

    def on_wake(self, reason: str = "timer") -> Optional[Dict[str, Any]]:
        """宿主定时器唤醒：驱动一次完整 tick（含主动巡检）。"""
        logger.debug("on_wake: %s", reason)
        return self.tick_once()

    def on_tool_result(self, tool: str, result: Any) -> None:
        """工具结果回流：当前仅记账，供后续技能熟练度/EWC 更新使用。"""
        logger.debug("on_tool_result: %s", tool)

    def on_external_event(self, event: Any) -> None:
        """外部事件流入：投递到事件总线（若可用）。"""
        try:
            from laap.events.bus import Event, bus
            bus.publish(Event(type="external", data={"event": str(event)}))
        except Exception as exc:  # noqa: BLE001
            logger.debug("事件投递失败: %s", exc)

    # ══════════════════════════════════════════════════════════
    # 认知能力直连（零序列化）
    # ══════════════════════════════════════════════════════════

    def think(self, problem: str) -> Any:
        """开启一棵深度递归树。返回引擎原生对象。"""
        self.boot()
        mod = self._organs.get("recursion_v2")
        if mod is None:
            raise RuntimeError("recursion_v2 器官未装配")
        engine = mod.get_deep_recursion_engine()
        return engine.open_tree(problem)

    def recall(self, query: str, k: int = 5) -> List[Any]:
        """记忆检索。返回原生记忆条目（dict）列表。

        注意概念区分：``aris_engine.unified_memory`` 是 append-only 事件
        日志 + 跨设备同步，**不做检索**；语义检索走 ``laap.memory_vault``
        的 ``VaultManager.retrieve``。
        """
        self.boot()
        try:
            from laap.memory_vault.vault_manager import vault_manager
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"memory_vault 不可用: {exc}") from exc
        return list(vault_manager.retrieve(self.lifeform_id, query, limit=k))

    def attack(self, claim: str, supports: Optional[List[str]] = None) -> Any:
        """质疑对抗：派出分身批判一个断言。"""
        self.boot()
        mod = self._organs.get("adversarial")
        if mod is None:
            raise RuntimeError("adversarial 器官未装配")
        return mod.attack(claim, supports or [])

    def cross(self, node_a: Any, node_b: Any, op: str, result: str) -> Any:
        """NTEN 表征重组：在两个节点间执行交叉操作。"""
        self.boot()
        mod = self._organs.get("thought_network")
        if mod is None:
            raise RuntimeError("thought_network 器官未装配")
        return mod.recombine(node_a, node_b, op, result)

    def predict(self, entity: str, horizon: int = 1) -> Any:
        """世界模型预测。"""
        self.boot()
        mod = self._organs.get("unified_memory")
        if mod is None:
            raise RuntimeError("unified_memory 器官未装配")
        return mod.predict(entity, horizon)

    # ══════════════════════════════════════════════════════════
    # 状态快照
    # ══════════════════════════════════════════════════════════

    def state(self) -> RuntimeState:
        degraded: List[str] = []
        if self._boot_report is not None:
            degraded = [o.name for o in self._boot_report.organs if o.degraded]
        return RuntimeState(
            lifeform_id=self.lifeform_id,
            booted=self._booted,
            uptime_s=(time.time() - self._boot_started_at) if self._boot_started_at else 0.0,
            heartbeat_running=self.heartbeat_running,
            tick_count=self._tick_count,
            last_tick=self._last_tick,
            turn_count=self._turn_count,
            degraded_organs=degraded,
        )

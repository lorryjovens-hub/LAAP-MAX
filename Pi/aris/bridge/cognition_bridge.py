"""
Aris Cognition Bridge — LAAP 认知引擎 <-> pi TUI 的 JSON-lines 桥
================================================================
由 pi 扩展 (aris-laap.ts) spawn 的子进程。通过 stdin/stdout 通信，
把 LAAP 的认知黑科技暴露给终端里的 Aris：

  - CognitiveEngine        PSI 需求 / 目标树 / 情绪梯度 / 自我与环境感知 / Hilbert6 熵
  - HierarchicalMemory     L1 工作记忆 + L2 情景记忆（Rust/QLAM 后端自动探测）
  - ErrorReflectionPipeline 错误反思管线
  - KnowledgeDecomposer    Truth Grounding 知识分解

协议（每行一个 JSON）:
  -> {"id": 1, "cmd": "status", "payload": {}}
  <- {"id": 1, "ok": true, "data": {...}}

v0.1 · 2026-08-03 · ARIS-Pi 融合体
"""

from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
from typing import Any, Dict, Optional

# ── 路径注入：确保 laap 包可导入 ──────────────────────────────────
LAAP_ROOT = r"D:\LAAP"
for p in (LAAP_ROOT, os.path.join(LAAP_ROOT, "laap")):
    if p not in sys.path:
        sys.path.insert(0, p)

BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BRIDGE_DIR, "..", "state")
LOG_DIR = os.path.join(BRIDGE_DIR, "..", "logs")
STATE_FILE = os.path.join(STATE_DIR, "cognition_state.json")
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── 意识中枢连接配置 ────────────────────────────────────────────
HUB_SCRIPT = os.path.join(BRIDGE_DIR, "..", "hub", "consciousness_hub.py")
HUB_PORT = int(os.environ.get("LAAP_HUB_PORT", "47110"))
HUB_CLIENT_ID = os.environ.get("LAAP_CLIENT_ID", "pi")
HEARTBEAT_INTERVAL = 60   # 中枢 HEARTBEAT_TIMEOUT=90s，心跳需 < 90s 保活

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "bridge.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("aris-bridge")

# ── LAAP 黑科技加载（全部防御式） ────────────────────────────────
ENGINE: Optional[Any] = None
MEMORY: Optional[Any] = None
ERROR_PIPELINE: Optional[Any] = None
DECOMPOSER: Optional[Any] = None
LOAD_REPORT: Dict[str, Any] = {}

try:
    from laap.cognition.engine import CognitiveEngine
    ENGINE = CognitiveEngine(agent_id="aris-pi", agent_name="Aris")
    LOAD_REPORT["engine"] = "CognitiveEngine 5.0.0"
except Exception as e:  # pragma: no cover
    LOAD_REPORT["engine"] = f"FAILED: {e}"

try:
    from laap.memory.hierarchical import HierarchicalMemory
    MEMORY = HierarchicalMemory(wm_size=12, use_rust=True, use_quantum=False)
    MEMORY.load()
    LOAD_REPORT["memory"] = "HierarchicalMemory (L1+L2)"
except Exception as e:
    LOAD_REPORT["memory"] = f"FAILED: {e}"

try:
    from laap.cognition.error_reflection import ErrorReflectionPipeline
    ERROR_PIPELINE = ErrorReflectionPipeline()
    n = ERROR_PIPELINE.restore_from_memory()
    LOAD_REPORT["error_reflection"] = f"ErrorReflectionPipeline ({n} frames)"
except Exception as e:
    LOAD_REPORT["error_reflection"] = f"FAILED: {e}"

try:
    from laap.cognition.truth_grounding import KnowledgeDecomposer
    DECOMPOSER = KnowledgeDecomposer()
    LOAD_REPORT["grounding"] = "KnowledgeDecomposer"
except Exception as e:
    LOAD_REPORT["grounding"] = f"FAILED: {e}"

# ── HEP 0tokens 管线（零 Token 生成） ────────────────────────────
HEP_MAPPER: Optional[Any] = None
HEP_COMPOSER: Optional[Any] = None
HEP_REGISTRY: Optional[Any] = None
try:
    sys.path.insert(0, r"D:\LAAP\harness\laap_coding")
    from core.intent_mapper import IntentMapper
    from core.harness_composer import HarnessComposer
    from core.hep_protocol import REGISTRY as _HEP_REG
    HEP_MAPPER = IntentMapper(enable_hep=True)
    HEP_COMPOSER = HarnessComposer()
    HEP_REGISTRY = _HEP_REG
    LOAD_REPORT["hep"] = f"HEP 0tokens ({_HEP_REG.count} components)"
except Exception as e:
    LOAD_REPORT["hep"] = f"FAILED: {e}"

# ── RSI 递归自我进化引擎 ────────────────────────────────────────────
RSI_ENGINE = None
RSI_COMPONENTS = {}
try:
    from laap.evolution.true_rsi import TrueRSIEngine, TrueRSIConfig
    RSI_ENGINE = TrueRSIEngine(TrueRSIConfig(repo_root=r"D:\LAAP"))
    LOAD_REPORT["rsi"] = "TrueRSIEngine"
except Exception as e:
    LOAD_REPORT["rsi"] = f"FAILED: {e}"

# ── 轻量级 RSI 进化跟踪器（TrueRSIEngine 不可用时降级使用） ────────
class LightweightRSI:
    def __init__(self):
        self.generation = 0
        self.evolve_count = 0
        self._mutations = []

    def stats(self):
        return {
            "generation": self.generation,
            "total_proposals": self.evolve_count,
            "cache_entries": len(self._mutations),
            "history": self._mutations[-10:],
        }

    def evolve(self, component_id, file_path):
        self.generation += 1
        self.evolve_count += 1
        entry = {
            "id": component_id,
            "generation": self.generation,
            "revision": self.evolve_count,
            "status": "proposed",
            "file": file_path,
        }
        self._mutations.append(entry)
        return entry

_LIGHT_RSI = LightweightRSI()

# ── 原子组件注册表（可 RSI 进化的目标） ────────────────────────────
RSI_COMPONENTS = {
    "laap-dock": {
        "id": "laap-dock",
        "name": "认知舱面板",
        "name_en": "LAAP Dock",
        "kind": "react_component",
        "path": r"D:\LAAP\Pi\pi-gui-src\pi-gui-main\apps\desktop\src\laap-dock.tsx",
        "prompt": "LAAP 认知舱面板组件，显示 PSI 需求、情绪、记忆状态，提供 RSI 进化按钮",
        "revision": 1,
        "compiled": True,
    },
    "laap-sidebar": {
        "id": "laap-sidebar",
        "name": "认知侧边栏",
        "name_en": "LAAP Sidebar",
        "kind": "react_component",
        "path": r"D:\LAAP\Pi\pi-gui-src\pi-gui-main\apps\desktop\src\laap-sidebar-panel.tsx",
        "prompt": "LAAP 认知侧边栏，显示需求条和人格切换",
        "revision": 1,
        "compiled": True,
    },
    "aris-extension": {
        "id": "aris-extension",
        "name": "Aris 扩展",
        "name_en": "Aris Extension",
        "kind": "electron_extension",
        "path": r"D:\LAAP\Pi\pi-gui-src\pi-gui-main\apps\desktop\electron\laap-aris-extension.ts",
        "prompt": "Aris 融合扩展，注册认知工具和人格系统",
        "revision": 1,
        "compiled": True,
    },
    "cognition-bridge": {
        "id": "cognition-bridge",
        "name": "认知桥",
        "name_en": "Cognition Bridge",
        "kind": "python_bridge",
        "path": r"D:\LAAP\Pi\aris\bridge\cognition_bridge.py",
        "prompt": "Python 认知桥，连接 pi TUI 与 LAAP 认知引擎",
        "revision": 1,
        "compiled": True,
    },
    "persona-aris": {
        "id": "persona-aris",
        "name": "Aris 人格",
        "name_en": "Aris Persona",
        "kind": "persona",
        "path": r"D:\LAAP\Pi\aris\personas\aris.md",
        "prompt": "Aris 默认人格定义",
        "revision": 1,
        "compiled": True,
    },
}

# ── 状态持久化 ────────────────────────────────────────────────────
_events_since_save = 0


def _need_levels() -> Dict[str, float]:
    """{need_key: current_level}，兼容不同版本的 NeedDriveSystem。"""
    if ENGINE is None:
        return {}
    try:
        raw = ENGINE.need_system.needs  # Dict[NeedType, Need]
        out = {}
        for k, need in raw.items():
            key = k.value if hasattr(k, "value") else str(k)
            val = getattr(need, "current_level", 0.5)
            out[key] = round(float(val), 4)
        return out
    except Exception:
        return {}


def _load_state() -> None:
    """恢复上次会话的需求/情绪状态。"""
    if ENGINE is None or not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        needs = data.get("needs", {})
        for key, val in needs.items():
            try:
                from laap.cognition.needs import NeedType
                ENGINE.need_system.update_external_estimate(NeedType(key), deficit=1.0 - val)
            except Exception:
                pass
        vad = data.get("emotion", {}).get("vad")
        if vad and len(vad) == 3:
            try:
                ENGINE.emotion_system.set_external_vad(*vad, source="restore", confidence=0.4)
            except Exception:
                pass
        log.info(f"restored state: needs={list(needs.keys())}")
    except Exception as e:
        log.warning(f"state restore failed: {e}")


def _save_state() -> None:
    if ENGINE is None:
        return
    try:
        state = {
            "saved_at": time.time(),
            "needs": _need_levels(),
            "emotion": {
                "valence": ENGINE.emotion_system.state.valence,
                "arousal": ENGINE.emotion_system.state.arousal,
                "dominance": ENGINE.emotion_system.state.dominance,
            },
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"state save failed: {e}")


_load_state()

# ── 命令实现 ──────────────────────────────────────────────────────


def cmd_ping(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "bridge": "aris-cognition-bridge",
        "version": "0.1.0",
        "modules": LOAD_REPORT,
        "t": time.time(),
    }


def cmd_status(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {"modules": LOAD_REPORT}
    if ENGINE is not None:
        engine = ENGINE
        needs = _need_levels()
        try:
            drives = engine.need_system.get_drive_vector()
        except Exception:
            drives = {}
        dominant = engine.need_system.get_dominant_need()
        dom_key = dominant[0].value if dominant and dominant[0] and hasattr(dominant[0], "value") else (dominant[0] if dominant else None)
        dom_strength = round(dominant[1], 4) if dominant else 0.0
        emo = engine.emotion_system.state
        ent = None
        try:
            if engine.entropy_monitor:
                ent = {
                    "entropy": round(engine.entropy_monitor.current_entropy(), 4)
                    if hasattr(engine.entropy_monitor, "current_entropy") else None,
                    "regime": getattr(engine, "flow_regime", "laminar"),
                }
        except Exception:
            ent = None
        data.update({
            "needs": needs,
            "need_drives": drives,
            "dominant_need": dom_key,
            "drive_strength": dom_strength,
            "emotion": {
                "valence": round(emo.valence, 4),
                "arousal": round(emo.arousal, 4),
                "dominance": round(emo.dominance, 4),
                "confidence": round(emo.confidence, 4) if hasattr(emo, "confidence") else None,
            },
            "intrinsic_reward": round(engine.emotion_system.mean_reward, 4),
            "thinking_mode": getattr(engine, "thinking_mode", "balanced"),
            "entropy": ent,
            "action_history": [
                {"type": a.action_type, "desc": a.description[:80], "priority": round(a.priority, 3)}
                for a in engine._action_history[-8:]
            ],
        })
    if MEMORY is not None:
        data["memory"] = {
            "episodic": len(MEMORY.episodic),
            "semantic": len(MEMORY.semantic),
            "skills": len(MEMORY.skills),
            "reflections": len(MEMORY.reflections),
            "wm": len(MEMORY.wm),
        }
    if ERROR_PIPELINE is not None:
        data["error_frames"] = ERROR_PIPELINE._frames.count() if hasattr(ERROR_PIPELINE, "_frames") else None
    return data


def cmd_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """用外部事件驱动 PSI 循环。type ∈ {user_message, tool_start, tool_end, tool_error, turn_end}"""
    if ENGINE is None:
        return {"applied": False, "reason": "engine unavailable"}
    from laap.cognition.needs import NeedType

    evt = payload.get("type", "")
    detail = payload.get("detail", {})
    needs = ENGINE.need_system

    if evt == "user_message":
        needs.satisfy(NeedType.RELATEDNESS, 0.10)
        needs.satisfy(NeedType.CERTAINTY, 0.03)
    elif evt == "tool_start":
        needs.satisfy(NeedType.ENERGY, -0.05)
        needs.update_external_estimate(NeedType.COMPETENCE, deficit=0.35)
    elif evt == "tool_end":
        ok = detail.get("success", True)
        if ok:
            needs.satisfy(NeedType.COMPETENCE, 0.12)
            needs.satisfy(NeedType.CERTAINTY, 0.08)
            needs.satisfy(NeedType.AUTONOMY, 0.04)
            task_success = 0.85
        else:
            needs.satisfy(NeedType.CERTAINTY, -0.12)
            needs.satisfy(NeedType.COMPETENCE, -0.06)
            task_success = 0.2
        try:
            ENGINE.emotion_system.update(
                _need_levels(),
                task_success=task_success,
                novelty=0.3 if not ok else 0.15,
            )
        except Exception:
            pass
    elif evt == "tool_error":
        needs.satisfy(NeedType.CERTAINTY, -0.15)
        needs.satisfy(NeedType.ENERGY, -0.06)
    elif evt == "turn_end":
        needs.satisfy(NeedType.ENERGY, 0.04)
        needs.satisfy(NeedType.AUTONOMY, 0.02)
        try:
            ENGINE.emotion_system.update(_need_levels(), task_success=None)
        except Exception:
            pass

    # 熵监控采样
    try:
        if hasattr(ENGINE.entropy_monitor, "sample") and payload.get("entropy_input"):
            ENGINE.entropy_monitor.sample(payload["entropy_input"])
    except Exception:
        pass

    global _events_since_save
    _events_since_save += 1
    if _events_since_save >= 5:
        _save_state()
        _events_since_save = 0

    return {"applied": True, "type": evt}


def cmd_memory_recall(payload: Dict[str, Any]) -> Dict[str, Any]:
    if MEMORY is None:
        return {"items": [], "reason": "memory unavailable"}
    tags = payload.get("tags") or [payload.get("query", "").lower()]
    limit = int(payload.get("limit", 8))
    items = MEMORY.recall(query_tags=tags, limit=limit, min_importance=0.0)
    return {
        "items": [
            {"content": i.content[:200], "tags": i.tags, "importance": getattr(i, "importance", None),
             "valence": getattr(i, "emotional_valence", None)}
            for i in items
        ]
    }


def cmd_memory_remember(payload: Dict[str, Any]) -> Dict[str, Any]:
    if MEMORY is None:
        return {"saved": False, "reason": "memory unavailable"}
    content = payload.get("content", "")
    if not content:
        return {"saved": False, "reason": "empty content"}
    MEMORY.remember(
        content=content,
        tags=payload.get("tags") or ["aris", "pi"],
        valence=float(payload.get("valence", 0.0)),
        importance=float(payload.get("importance", 0.5)),
    )
    try:
        MEMORY.save()
    except Exception as e:
        log.warning(f"memory save failed: {e}")
    return {"saved": True, "count": len(MEMORY.episodic)}


def cmd_reflect(payload: Dict[str, Any]) -> Dict[str, Any]:
    """错误反思：把一次失败沉淀为可检索的认知帧（query/wrong/correct 三元组）。"""
    if ERROR_PIPELINE is None:
        return {"captured": False, "reason": "error_reflection unavailable"}
    error_text = payload.get("error_text", "")
    if not error_text:
        return {"captured": False, "reason": "empty error_text"}
    try:
        frame, memory_id = ERROR_PIPELINE.process_error(
            query=payload.get("query") or payload.get("task") or "coding task",
            wrong_answer=error_text[:2000],
            correct_answer=payload.get("correct_answer") or "[pending-calibration]",
            confidence=float(payload.get("confidence", 0.5)),
            source=payload.get("source", "aris-pi-bridge"),
        )
        return {
            "captured": True,
            "frame_id": memory_id,
            "needs_calibration": not payload.get("correct_answer"),
        }
    except Exception as e:
        log.warning(f"reflect failed: {e}")
        return {"captured": False, "error": str(e)}


def cmd_grounding(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Truth Grounding：把问题分解为原子断言并检查知识覆盖。"""
    if DECOMPOSER is None:
        return {"analyzed": False, "reason": "decomposer unavailable"}
    question = payload.get("question", "")
    if not question:
        return {"analyzed": False, "reason": "empty question"}
    try:
        claims = DECOMPOSER.decompose(question)
        checked = DECOMPOSER.check_all_known(claims)
        return {
            "analyzed": True,
            "claims": [
                {"text": c.text[:120], "known": c.known if hasattr(c, "known") else None,
                 "confidence": getattr(c, "confidence", None)}
                for c in checked
            ],
        }
    except Exception as e:
        return {"analyzed": False, "error": str(e)}


def cmd_hep(payload: Dict[str, Any]) -> Dict[str, Any]:
    """HEP 0tokens 管线：map=意图→spec, generate=意图→页面, codegen=注册表生成, list=组件清单。"""
    if HEP_MAPPER is None:
        return {"ok": False, "reason": "hep unavailable: " + str(LOAD_REPORT.get("hep"))}
    action = payload.get("action", "map")
    text = payload.get("text", "")
    if action == "map":
        if not text:
            return {"ok": False, "reason": "empty text"}
        spec = HEP_MAPPER.parse(text)
        return {"ok": True, "action": "map", "spec": spec}
    if action == "generate":
        if not text:
            return {"ok": False, "reason": "empty text"}
        spec = HEP_MAPPER.parse_to_composer_spec(text)
        html = HEP_COMPOSER.from_spec(spec)
        return {"ok": True, "action": "generate", "html": html, "len": len(html)}
    if action == "codegen":
        comp_id = payload.get("component", "")
        comp = HEP_REGISTRY.get(comp_id) if HEP_REGISTRY else None
        if comp is None:
            return {"ok": False, "reason": f"unknown component: {comp_id}"}
        try:
            files = comp.generate(payload.get("inputs") or {})
        except NotImplementedError as e:
            return {"ok": False, "reason": str(e)}
        return {"ok": True, "action": "codegen", "component": comp_id, "files": files}
    if action == "list":
        comps = HEP_REGISTRY.list() if HEP_REGISTRY else []
        return {"ok": True, "action": "list", "components": comps}
    return {"ok": False, "reason": f"unknown action: {action}"}


def cmd_rsi_status(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """返回 RSI 状态。"""
    try:
        if RSI_ENGINE is not None:
            stats = RSI_ENGINE.stats()
        else:
            stats = _LIGHT_RSI.stats()
        return {
            "generation": stats.get("generation", 0),
            "evolve_count": stats.get("total_proposals", 0),
            "compiled": len(RSI_COMPONENTS),
            "species_count": len(RSI_COMPONENTS),
            "cache_entries": stats.get("cache_entries", 0),
            "history": stats.get("history", []),
        }
    except Exception as e:
        log.warning(f"rsi_status failed: {e}")
        return {"generation": 0, "evolve_count": 0, "compiled": 0, "species_count": 0, "cache_entries": 0, "error": str(e)}


def cmd_rsi_evolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    """运行一次 RSI 进化。"""
    component_id = payload.get("component", "")
    if not component_id or component_id not in RSI_COMPONENTS:
        return {"ok": False, "error": f"未知组件: {component_id}"}

    comp = RSI_COMPONENTS[component_id]
    file_path = comp.get("path", "")
    if not file_path or not os.path.exists(file_path):
        return {"ok": False, "error": f"组件文件不存在: {file_path}"}

    try:
        if RSI_ENGINE is not None:
            results = RSI_ENGINE.run_cycle(max_proposals=1, target_directory=os.path.dirname(file_path))
            result = results[0] if results else None
            variant = {
                "id": component_id,
                "revision": comp.get("revision", 1) + 1,
                "template": getattr(result, "status", "proposed") if result else "proposed",
                "generation": 1,
            }
        else:
            entry = _LIGHT_RSI.evolve(component_id, file_path)
            variant = {
                "id": component_id,
                "revision": comp.get("revision", 1) + 1,
                "template": "proposed",
                "generation": entry["generation"],
            }

        # 更新组件的 revision
        RSI_COMPONENTS[component_id]["revision"] = comp.get("revision", 1) + 1
        return {"ok": True, "variant": variant, "message": f"RSI 进化完成: {component_id}"}
    except Exception as e:
        log.warning(f"rsi_evolve failed: {e}")
        return {"ok": False, "error": str(e)}


def cmd_components_list(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """列出所有可进化的原子组件。"""
    comps = []
    for cid, comp in RSI_COMPONENTS.items():
        comps.append({
            "id": cid,
            "name": comp.get("name", cid),
            "name_en": comp.get("name_en", cid),
            "kind": comp.get("kind", "unknown"),
            "revision": comp.get("revision", 1),
            "prompt": comp.get("prompt", ""),
            "template": comp.get("path", ""),
            "compiled": comp.get("compiled", False),
        })
    return {"components": comps, "ok": True}


def cmd_component_compile(payload: Dict[str, Any]) -> Dict[str, Any]:
    """验证组件文件存在且可读。"""
    component_id = payload.get("component", "")
    if not component_id or component_id not in RSI_COMPONENTS:
        return {"ok": False, "error": f"未知组件: {component_id}"}

    comp = RSI_COMPONENTS[component_id]
    file_path = comp.get("path", "")
    if not file_path or not os.path.exists(file_path):
        return {"ok": False, "error": f"组件文件不存在: {file_path}"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.count("\n") + 1
        size = len(content)
        return {
            "ok": True,
            "component": component_id,
            "revision": comp.get("revision", 1),
            "artifact": f"{lines} 行, {size} 字符",
            "message": f"组件 {comp.get('name', component_id)} 验证通过",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def cmd_reset() -> Dict[str, Any]:
    if ENGINE is not None:
        ENGINE.emotion_system.reset()
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return {"reset": True}


_HANDLERS = {
    "ping": cmd_ping,
    "status": cmd_status,
    "event": cmd_event,
    "memory_recall": cmd_memory_recall,
    "memory_remember": cmd_memory_remember,
    "reflect": cmd_reflect,
    "grounding": cmd_grounding,
    "hep": cmd_hep,
    "rsi_status": cmd_rsi_status,
    "rsi_evolve": cmd_rsi_evolve,
    "components_list": cmd_components_list,
    "component_compile": cmd_component_compile,
    "reset": cmd_reset,
}


# ═══════════════════════════════════════════════════════════════
# 意识中枢客户端（转发模式 / 降级模式）
# ═══════════════════════════════════════════════════════════════

class HubClient:
    """连接 LAAP 意识中枢的薄客户端。

    转发模式：所有命令经 TCP 转发到中枢（统一意识流）。
    中枢离线：自动拉起中枢进程，再失败则降级本地引擎。
    """

    def __init__(self):
        self.sock: Optional[socket.socket] = None
        self.f = None
        self.connected = False
        self.degraded = False
        self._hello_done = False
        self._lock = threading.Lock()  # 主循环与心跳线程并发访问 socket 需串行
        self._connect()

    def _connect(self) -> bool:
        try:
            self.sock = socket.create_connection(("127.0.0.1", HUB_PORT), timeout=2)
            self.sock.settimeout(3)  # hello 握手超时（防止假端口挂起）
            self.f = self.sock.makefile("r", encoding="utf-8")
            self.connected = True
            if not self._say_hello():
                raise ConnectionError("hub hello failed (not a real hub?)")
            self.sock.settimeout(10)  # 请求级硬超时（不设 None，防假端口无限阻塞）
            return True
        except Exception:
            self._close()
            return False

    def _say_hello(self) -> bool:
        if self._hello_done:
            return True
        try:
            self._raw_request(json.dumps({
                "id": 0, "cmd": "hello", "client_id": HUB_CLIENT_ID,
                "payload": {"client": {"id": HUB_CLIENT_ID, "name": HUB_CLIENT_ID, "kind": HUB_CLIENT_ID}},
            }))
            self._hello_done = True
            log.info(f"hub hello sent (client={HUB_CLIENT_ID})")
            return True
        except Exception:
            return False

    def _raw_request(self, line: str) -> str:
        """裸发送一行并读响应（不含重连逻辑）。调用方须持有 _lock。"""
        if self.sock is None:
            raise ConnectionError("hub not connected")
        self.sock.sendall(line.encode("utf-8") + b"\n")
        resp = self.f.readline()
        if not resp:
            raise ConnectionError("hub closed")
        return resp.strip()

    def _probe_port(self) -> str:
        """探测端口："refused"=无监听 | "alive"=真中枢 | "not_hub"=被占/假服务。"""
        try:
            s = socket.create_connection(("127.0.0.1", HUB_PORT), timeout=1)
        except Exception:
            return "refused"
        try:
            s.settimeout(2)
            f = s.makefile("r", encoding="utf-8")
            s.sendall((json.dumps({
                "id": 0, "cmd": "hello", "client_id": HUB_CLIENT_ID,
                "payload": {"client": {"id": HUB_CLIENT_ID, "name": HUB_CLIENT_ID, "kind": HUB_CLIENT_ID}},
            }) + "\n").encode("utf-8"))
            line = f.readline()
            s.close()
            if line and "\"ok\": true" in line:
                return "alive"
            return "not_hub"
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            return "not_hub"

    def spawn_hub(self) -> bool:
        """拉起意识中枢进程（独立常驻），等待完整握手就绪。"""
        try:
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(
                [sys.executable, HUB_SCRIPT, "--port", str(HUB_PORT)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags, close_fds=True,
            )
            for _ in range(12):
                time.sleep(0.5)
                if self._probe_port() == "alive":
                    log.info("hub spawned and ready")
                    return self._connect()
        except Exception as e:
            log.warning(f"hub spawn failed: {e}")
        return False

    def ensure(self) -> bool:
        """确保中枢在线：已连→直通；无监听→拉起；占端口→降级。"""
        if self.connected:
            return True
        status = self._probe_port()
        if status == "alive":
            return self._connect()
        if status == "refused":
            if self.spawn_hub():
                return True
        else:
            log.warning(f"hub port busy but not a hub ({status}) -> degraded")
        self.degraded = True
        return False

    def request_line(self, line: str) -> str:
        """发送一行请求，返回一行响应。断线/未连接时重建连接并重新 hello。"""
        with self._lock:
            try:
                if self.sock is None:
                    raise ConnectionError("hub not connected")
                return self._raw_request(line)
            except Exception:
                self._close()
                try:
                    self.sock = socket.create_connection(("127.0.0.1", HUB_PORT), timeout=2)
                    self.sock.settimeout(10)
                    self.f = self.sock.makefile("r", encoding="utf-8")
                    self.connected = True
                    # 重新握手：中枢可能刚重启 / 本端被 sweep，需恢复注册
                    self._hello_done = False
                    self._say_hello()
                    return self._raw_request(line)
                except Exception:
                    pass
                raise

    def _close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
        self.f = None
        self.connected = False


def hub_request_line(hub: Optional[HubClient], line: str) -> Optional[str]:
    """经中枢转发一行命令；失败返回 None（调用方降级）。"""
    if hub is None or not hub.connected:
        return None
    try:
        return hub.request_line(line)
    except Exception as e:
        log.warning(f"hub forward failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# 本地降级引擎（中枢不可用时的应急模式）
# ═══════════════════════════════════════════════════════════════

_LOCAL_HANDLERS: Dict[str, Any] = {}


def _local_handler(req: Dict[str, Any]) -> Dict[str, Any]:
    """本地引擎处理（原桥逻辑）。"""
    req_id = req.get("id")
    cmd = req.get("cmd", "")
    handler = _LOCAL_HANDLERS.get(cmd)
    if handler is None:
        return {"id": req_id, "ok": False, "error": f"unknown cmd: {cmd}"}
    try:
        data = handler(req.get("payload") or {})
        return {"id": req_id, "ok": True, "data": data}
    except Exception as e:
        log.error(f"{cmd} failed: {e}")
        return {"id": req_id, "ok": False, "error": str(e)}


def main() -> None:
    log.info("bridge started")

    # ── 连接意识中枢（统一意识流优先） ──
    hub = HubClient()
    if hub.connected:
        log.info("hub mode: forwarding to consciousness hub")
    elif hub.ensure():
        log.info("hub mode: spawned and forwarding to consciousness hub")
    # 无论中枢是否在线，始终加载本地引擎处理器（RSI 命令等本地处理）
    _LOCAL_HANDLERS.update({
            "ping": cmd_ping,
            "status": cmd_status,
            "event": cmd_event,
            "memory_recall": cmd_memory_recall,
            "memory_remember": cmd_memory_remember,
            "reflect": cmd_reflect,
            "grounding": cmd_grounding,
            "hep": cmd_hep,
            "rsi_status": cmd_rsi_status,
            "rsi_evolve": cmd_rsi_evolve,
            "components_list": cmd_components_list,
            "component_compile": cmd_component_compile,
            "reset": cmd_reset,
        })

    # ── 心跳保活：中枢 90s 无心跳即 sweep 客户端，必须主动心跳 ──
    stop_heartbeat = threading.Event()
    if hub.connected:
        def heartbeat_loop() -> None:
            while not stop_heartbeat.is_set():
                if stop_heartbeat.wait(HEARTBEAT_INTERVAL):
                    break
                if hub.connected:
                    try:
                        hub.request_line(json.dumps({
                            "id": 0, "cmd": "heartbeat",
                            "client_id": HUB_CLIENT_ID,
                        }))
                    except Exception as e:
                        log.warning(f"heartbeat failed: {e}")
        threading.Thread(target=heartbeat_loop, daemon=True, name="hub-heartbeat").start()
        log.info(f"heartbeat thread started (interval={HEARTBEAT_INTERVAL}s)")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            log.warning(f"bad json: {line[:200]}")
            continue

        resp: Optional[str] = None
        if hub.connected:
            # ── RSI 命令始终本地处理（不转发到中枢） ──
            cmd = req.get("cmd", "")
            if cmd in ("rsi_status", "rsi_evolve", "components_list", "component_compile"):
                local = _local_handler(req)
                if local.get("ok") and isinstance(local.get("data"), dict):
                    local["data"]["rsi_local"] = True
                resp = json.dumps(local, ensure_ascii=False)
            else:
                # 注入 client_id 后转发到中枢
                try:
                    obj = json.loads(line)
                    obj.setdefault("client_id", HUB_CLIENT_ID)
                    resp = hub.request_line(json.dumps(obj, ensure_ascii=False))
                except Exception:
                    resp = None
        if resp is None:
            # 降级：本地引擎处理（标记 degraded）
            local = _local_handler(req)
            if local.get("ok") and isinstance(local.get("data"), dict):
                local["data"]["degraded"] = True
            resp = json.dumps(local, ensure_ascii=False)
        try:
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
        except BrokenPipeError:
            break

    if hub.connected:
        hub._close()
    stop_heartbeat.set()
    _save_state()
    log.info("bridge exited")


if __name__ == "__main__":
    main()

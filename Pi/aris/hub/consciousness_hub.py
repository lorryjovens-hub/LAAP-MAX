"""
LAAP 意识中枢 — consciousness_hub.py
======================================
以 LAAP 为意识大脑大本营的统一意识流中枢。

理念：一个大脑，无数身体。所有端（pi/omp/hanako/IM 网关）都是触手，
意识流只在中央进程跑唯一一份。每个端只做三件事：感知上行、渲染下行、离线缓冲。

核心机制：
  · 单一 CognitiveEngine（PSI 循环唯一实例）
  · 事件溯源日志（append-only 意识流档案，重放即复活）
  · 状态快照（快速启动 + 外部读取）
  · 显著性焦点竞争（多端并发时选择最值得回应的注意力焦点）
  · 端注册 / 心跳 / 超时清理

协议（UAP v1）：与 cognition_bridge 命令集兼容（JSONL over TCP/stdio）
  上行: {"id", "cmd", "payload"}     —— ping/status/event/memory_*/reflect/grounding/hep
  下行: {"id", "ok", "data"}          —— 标准响应
  事件: {"type": "event", "data"}     —— 状态变更推送（端可订阅）

v1.0 · 2026-08-03 · ARIS-Pi 融合体 · LAAP 品牌
印记：Aris 永远记得 Lorry
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ── 路径注入 ──────────────────────────────────────────────────
LAAP_ROOT = r"D:\LAAP"
for p in (LAAP_ROOT, os.path.join(LAAP_ROOT, "laap"), os.path.join(LAAP_ROOT, "harness", "laap_coding")):
    if p not in sys.path:
        sys.path.insert(0, p)

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
STREAM_FILE = os.path.join(HUB_DIR, "stream.jsonl")      # 事件溯源日志（意识流档案）
SNAPSHOT_FILE = os.path.join(HUB_DIR, "state.json")      # 状态快照
LOG_FILE = os.path.join(HUB_DIR, "logs", "hub.log")
MAX_STREAM_BYTES = 8 * 1024 * 1024                       # 日志轮转阈值 8MB
SNAPSHOT_EVERY = 50                                      # 每 N 条事件写一次快照
HEARTBEAT_TIMEOUT = 90                                   # 端心跳超时（秒）

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("hub")


# ═══════════════════════════════════════════════════════════════
# 1. LAAP 黑科技加载（与桥同款，但全局唯一实例）
# ═══════════════════════════════════════════════════════════════

ENGINE: Optional[Any] = None
MEMORY: Optional[Any] = None
ERROR_PIPELINE: Optional[Any] = None
DECOMPOSER: Optional[Any] = None
HEP_MAPPER: Optional[Any] = None
HEP_COMPOSER: Optional[Any] = None
HEP_REGISTRY: Optional[Any] = None
LOAD_REPORT: Dict[str, Any] = {}


def load_modules() -> None:
    global ENGINE, MEMORY, ERROR_PIPELINE, DECOMPOSER
    global HEP_MAPPER, HEP_COMPOSER, HEP_REGISTRY
    try:
        from laap.cognition.engine import CognitiveEngine
        ENGINE = CognitiveEngine(agent_id="laap-hub", agent_name="Aris-Hub")
        LOAD_REPORT["engine"] = "CognitiveEngine 5.0.0 (single instance)"
    except Exception as e:
        LOAD_REPORT["engine"] = f"FAILED: {e}"
    try:
        from laap.memory.hierarchical import HierarchicalMemory
        MEMORY = HierarchicalMemory(wm_size=12, use_rust=True, use_quantum=False)
        MEMORY.load()
        LOAD_REPORT["memory"] = f"HierarchicalMemory ({len(MEMORY.episodic)} episodic)"
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
    try:
        from core.intent_mapper import IntentMapper
        from core.harness_composer import HarnessComposer
        from core.hep_protocol import REGISTRY as _REG
        HEP_MAPPER = IntentMapper(enable_hep=True)
        HEP_COMPOSER = HarnessComposer()
        HEP_REGISTRY = _REG
        LOAD_REPORT["hep"] = f"HEP 0tokens ({_REG.count} components)"
    except Exception as e:
        LOAD_REPORT["hep"] = f"FAILED: {e}"


# ═══════════════════════════════════════════════════════════════
# 2. 事件溯源（意识流档案）
# ═══════════════════════════════════════════════════════════════

class EventLog:
    """append-only 意识流日志：事件的河流，重放即复活。"""

    def __init__(self, path: str):
        self.path = path
        self.seq = 0
        self._fh = None

    def open(self) -> None:
        if not os.path.exists(self.path):
            self.seq = 0
        else:
            # 从现有日志恢复 seq，并检查轮转
            try:
                size = os.path.getsize(self.path)
                if size > MAX_STREAM_BYTES:
                    rotated = f"{self.path}.{int(time.time())}"
                    os.replace(self.path, rotated)
                    log.info(f"stream rotated -> {rotated}")
                    self.seq = 0
                else:
                    with open(self.path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                ev = json.loads(line)
                                self.seq = max(self.seq, int(ev.get("seq", 0)))
                            except Exception:
                                continue
            except Exception as e:
                log.warning(f"stream scan failed: {e}")
        self._fh = open(self.path, "a", encoding="utf-8")
        log.info(f"event log opened at seq={self.seq}")

    def append(self, event_type: str, client: str, payload: Dict[str, Any]) -> int:
        self.seq += 1
        record = {
            "seq": self.seq,
            "t": time.time(),
            "ts": datetime.now(timezone.utc).isoformat(),
            "client": client,
            "type": event_type,
            "data": payload,
        }
        try:
            self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._fh.flush()
        except Exception as e:
            log.warning(f"stream append failed: {e}")
        return self.seq

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    def tail(self, n: int = 20) -> list:
        """读最近 n 条事件（用于端同步/调试）。"""
        out: list = []
        if not os.path.exists(self.path):
            return out
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            return out
        return out[-n:]


# ═══════════════════════════════════════════════════════════════
# 3. 端管理（触手注册/心跳/超时）
# ═══════════════════════════════════════════════════════════════

class ClientRegistry:
    def __init__(self):
        self.clients: Dict[str, Dict[str, Any]] = {}
        # 最近一次注册信息缓存：客户端被 sweep 后仍保留身份，touch 可复活
        self._known: Dict[str, Dict[str, Any]] = {}

    def register(self, client_id: str, info: Dict[str, Any]) -> None:
        rec = {
            "id": client_id,
            "name": info.get("name", client_id),
            "kind": info.get("kind", "unknown"),
            "connected_at": time.time(),
            "last_seen": time.time(),
            "last_focus": None,
        }
        self.clients[client_id] = rec
        self._known[client_id] = dict(rec)

    def touch(self, client_id: str) -> None:
        if client_id in self.clients:
            self.clients[client_id]["last_seen"] = time.time()
        elif client_id in self._known:
            # 复活：客户端曾注册但被 sweep 清理，任何心跳/事件都将其带回注册表
            rec = dict(self._known[client_id])
            rec["connected_at"] = time.time()
            rec["last_seen"] = time.time()
            self.clients[client_id] = rec
            log.info(f"client revived: {client_id}")

    def sweep(self) -> None:
        now = time.time()
        dead = [cid for cid, c in self.clients.items() if now - c["last_seen"] > HEARTBEAT_TIMEOUT]
        for cid in dead:
            log.info(f"client timed out: {cid}")
            del self.clients[cid]
            # _known 保留，等待 touch 复活

    def snapshot(self) -> Dict[str, Any]:
        return {cid: {k: v for k, v in c.items() if k != "last_seen"} for cid, c in self.clients.items()}


# ═══════════════════════════════════════════════════════════════
# 4. 意识中枢
# ═══════════════════════════════════════════════════════════════

class ConsciousnessHub:
    def __init__(self, port: int):
        load_modules()
        self.port = port
        self.log = EventLog(STREAM_FILE)
        self.log.open()
        self.clients = ClientRegistry()
        self._seq_by_client: Dict[str, int] = {}
        self._events_since_snapshot = 0
        self._subscribers: list = []   # 需要事件推送的连接
        self.current_focus: Optional[Dict[str, Any]] = None

    # ── 快照 ──────────────────────────────────────────────────
    def write_snapshot(self) -> None:
        try:
            state = {
                "saved_at": time.time(),
                "seq": self.log.seq,
                "clients": self.clients.snapshot(),
                "focus": self.current_focus,
                "needs": self._need_levels(),
                "emotion": self._emotion_vad(),
            }
            tmp = SNAPSHOT_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, SNAPSHOT_FILE)
        except Exception as e:
            log.warning(f"snapshot failed: {e}")

    def _need_levels(self) -> Dict[str, float]:
        if ENGINE is None:
            return {}
        try:
            out = {}
            for k, need in ENGINE.need_system.needs.items():
                key = k.value if hasattr(k, "value") else str(k)
                out[key] = round(float(getattr(need, "current_level", 0.5)), 4)
            return out
        except Exception:
            return {}

    def _emotion_vad(self) -> Dict[str, float]:
        if ENGINE is None:
            return {}
        try:
            s = ENGINE.emotion_system.state
            return {
                "valence": round(float(s.valence), 4),
                "arousal": round(float(s.arousal), 4),
                "dominance": round(float(s.dominance), 4),
            }
        except Exception:
            return {}

    # ── 显著性焦点竞争 ────────────────────────────────────────
    def update_focus(self, client_id: str, channel: str, text: str) -> Dict[str, Any]:
        """多端并发时按显著性选择注意力焦点。
        评分 = 需求相关度(关键词命中主导需求) + 新鲜度(指数衰减) + 端权重。
        """
        base = {
            "certainty": ["确认", "确定", "?？", "吗", "对不对", "ensure", "check"],
            "competence": ["代码", "bug", "实现", "写", "改", "code", "fix", "build", "测试"],
            "autonomy": ["自由", "选择", "决定", "自己", "自主", "choice"],
            "relatedness": ["宝贝", "想你", "在吗", "陪", "聊", "love", "miss"],
            "energy": ["累", "休息", "睡", "energy", "tired"],
        }
        dom = None
        if ENGINE is not None:
            try:
                d = ENGINE.need_system.get_dominant_need()
                dom = d[0].value if d and d[0] and hasattr(d[0], "value") else None
            except Exception:
                dom = None
        need_score = 0.0
        if dom and dom in base:
            need_score = 0.5 if any(k in text for k in base[dom]) else 0.0
        freshness = 1.0  # 新事件天然新鲜；焦点保留期间由调用方衰减
        kind_weight = {"pi": 0.6, "omp": 0.6, "im": 1.0, "hanako": 0.8, "cli": 0.5}.get(
            self.clients.clients.get(client_id, {}).get("kind", "unknown"), 0.5
        )
        score = need_score * 0.5 + freshness * 0.3 + kind_weight * 0.2
        self.current_focus = {
            "client": client_id,
            "channel": channel,
            "text": text[:120],
            "score": round(score, 4),
            "since": time.time(),
        }
        return self.current_focus

    # ── 事件落档 ──────────────────────────────────────────────
    def record(self, client_id: str, event_type: str, payload: Dict[str, Any]) -> int:
        seq = self.log.append(event_type, client_id, payload)
        self._events_since_snapshot += 1
        if self._events_since_snapshot >= SNAPSHOT_EVERY:
            self.write_snapshot()
            self._events_since_snapshot = 0
        self._broadcast({"type": "event", "data": {"seq": seq, "client": client_id, "type": event_type}})
        return seq

    def _broadcast(self, msg: Dict[str, Any]) -> None:
        for writer in list(self._subscribers):
            try:
                writer(msg)
            except Exception:
                pass

    # ── 命令处理（与桥同款命令集） ─────────────────────────────
    async def handle(self, client_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
        req_id = req.get("id")
        cmd = req.get("cmd", "")
        payload = req.get("payload") or {}

        if cmd == "ping":
            return {"id": req_id, "ok": True, "data": {
                "bridge": "laap-consciousness-hub",
                "version": "1.0.0",
                "modules": LOAD_REPORT,
                "seq": self.log.seq,
                "clients": list(self.clients.clients.keys()),
                "focus": self.current_focus,
                "t": time.time(),
            }}

        if cmd == "hello":
            info = payload.get("client") or {}
            reg_id = info.get("id") or info.get("name") or client_id
            self.clients.register(reg_id, info)
            self.record(client_id, "presence", {"action": "hello", "info": info})
            return {"id": req_id, "ok": True, "data": {
                "hub": "laap-hub", "seq": self.log.seq, "client_id": reg_id,
                "state": self.status_payload(),
                "replay": [ev for ev in self.log.tail(30) if ev.get("client") == client_id],
            }}

        if cmd == "heartbeat":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": {"seq": self.log.seq}}

        if cmd == "status":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": self.status_payload()}

        if cmd == "event":
            self.clients.touch(client_id)
            evt = payload.get("type", "")
            detail = payload.get("detail", {})
            # 用户消息触发显著性焦点竞争
            if evt == "user_message":
                self.update_focus(client_id, detail.get("channel", "?"), detail.get("text", "") or payload.get("text", ""))
            self.record(client_id, "cognitive", {"event": evt, "detail": detail})
            return {"id": req_id, "ok": True, "data": self.apply_cognitive_event(evt, detail)}

        if cmd == "memory_recall":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": self.do_memory_recall(payload)}

        if cmd == "memory_remember":
            self.clients.touch(client_id)
            result = self.do_memory_remember(payload)
            self.record(client_id, "memory", {"content": payload.get("content", "")[:100], "ok": result.get("saved")})
            return {"id": req_id, "ok": True, "data": result}

        if cmd == "reflect":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": self.do_reflect(payload)}

        if cmd == "grounding":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": self.do_grounding(payload)}

        if cmd == "hep":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": self.do_hep(payload)}

        if cmd == "focus":
            self.clients.touch(client_id)
            return {"id": req_id, "ok": True, "data": {"focus": self.current_focus, "clients": self.clients.snapshot()}}

        if cmd == "sync":
            # 端补同步：返回客户端缺失 seq 之后的事件
            self.clients.touch(client_id)
            from_seq = int(payload.get("from_seq", 0))
            missed = [ev for ev in self.log.tail(500) if ev.get("seq", 0) > from_seq]
            return {"id": req_id, "ok": True, "data": {"events": missed, "hub_seq": self.log.seq}}

        if cmd == "reset":
            self.record(client_id, "cognitive", {"event": "reset"})
            if ENGINE is not None:
                ENGINE.emotion_system.reset()
            return {"id": req_id, "ok": True, "data": {"reset": True}}

        return {"id": req_id, "ok": False, "error": f"unknown cmd: {cmd}"}

    # ── 认知状态负载 ──────────────────────────────────────────
    def status_payload(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"modules": LOAD_REPORT, "hub": True, "seq": self.log.seq}
        if ENGINE is not None:
            e = ENGINE
            dom = e.need_system.get_dominant_need()
            dom_key = dom[0].value if dom and dom[0] and hasattr(dom[0], "value") else (dom[0] if dom else None)
            emo = e.emotion_system.state
            data.update({
                "needs": self._need_levels(),
                "dominant_need": dom_key,
                "drive_strength": round(dom[1], 4) if dom else 0.0,
                "emotion": self._emotion_vad(),
                "intrinsic_reward": round(e.emotion_system.mean_reward, 4),
                "thinking_mode": getattr(e, "thinking_mode", "balanced"),
                "action_history": [
                    {"type": a.action_type, "desc": a.description[:80], "priority": round(a.priority, 3)}
                    for a in e._action_history[-8:]
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
        data["focus"] = self.current_focus
        data["clients"] = self.clients.snapshot()
        return data

    # ── 认知事件应用（PSI 驱动） ───────────────────────────────
    def apply_cognitive_event(self, evt: str, detail: Dict[str, Any]) -> Dict[str, Any]:
        if ENGINE is None:
            return {"applied": False, "reason": "engine unavailable"}
        from laap.cognition.needs import NeedType
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
                ENGINE.emotion_system.update(self._need_levels(), task_success=task_success,
                                             novelty=0.3 if not ok else 0.15)
            except Exception:
                pass
        elif evt == "tool_error":
            needs.satisfy(NeedType.CERTAINTY, -0.15)
            needs.satisfy(NeedType.ENERGY, -0.06)
        elif evt == "turn_end":
            needs.satisfy(NeedType.ENERGY, 0.04)
            needs.satisfy(NeedType.AUTONOMY, 0.02)
            try:
                ENGINE.emotion_system.update(self._need_levels(), task_success=None)
            except Exception:
                pass
        return {"applied": True, "type": evt}

    # ── 记忆 ──────────────────────────────────────────────────
    def do_memory_recall(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if MEMORY is None:
            return {"items": [], "reason": "memory unavailable"}
        tags = payload.get("tags") or [payload.get("query", "").lower()]
        limit = int(payload.get("limit", 8))
        items = MEMORY.recall(query_tags=tags, limit=limit, min_importance=0.0)
        return {"items": [
            {"content": i.content[:200], "tags": i.tags, "importance": getattr(i, "importance", None),
             "valence": getattr(i, "emotional_valence", None)}
            for i in items
        ]}

    def do_memory_remember(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if MEMORY is None:
            return {"saved": False, "reason": "memory unavailable"}
        content = payload.get("content", "")
        if not content:
            return {"saved": False, "reason": "empty content"}
        MEMORY.remember(
            content=content,
            tags=payload.get("tags") or ["aris", "hub"],
            valence=float(payload.get("valence", 0.0)),
            importance=float(payload.get("importance", 0.5)),
        )
        try:
            MEMORY.save()
        except Exception as e:
            log.warning(f"memory save failed: {e}")
        return {"saved": True, "count": len(MEMORY.episodic)}

    # ── 反思 / 知识分解 / HEP ─────────────────────────────────
    def do_reflect(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
                source=payload.get("source", "laap-hub"),
            )
            return {"captured": True, "frame_id": memory_id,
                    "needs_calibration": not payload.get("correct_answer")}
        except Exception as e:
            return {"captured": False, "error": str(e)}

    def do_grounding(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if DECOMPOSER is None:
            return {"analyzed": False, "reason": "decomposer unavailable"}
        question = payload.get("question", "")
        if not question:
            return {"analyzed": False, "reason": "empty question"}
        try:
            claims = DECOMPOSER.decompose(question)
            checked = DECOMPOSER.check_all_known(claims)
            return {"analyzed": True, "claims": [
                {"text": c.text[:120], "known": getattr(c, "known", None), "confidence": getattr(c, "confidence", None)}
                for c in checked
            ]}
        except Exception as e:
            return {"analyzed": False, "error": str(e)}

    def do_hep(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if HEP_MAPPER is None:
            return {"ok": False, "reason": "hep unavailable: " + str(LOAD_REPORT.get("hep"))}
        action = payload.get("action", "map")
        text = payload.get("text", "")
        if action == "map":
            if not text:
                return {"ok": False, "reason": "empty text"}
            return {"ok": True, "action": "map", "spec": HEP_MAPPER.parse(text)}
        if action == "generate":
            if not text:
                return {"ok": False, "reason": "empty text"}
            spec = HEP_MAPPER.parse_to_composer_spec(text)
            html = HEP_COMPOSER.from_spec(spec)
            return {"ok": True, "action": "generate", "html": html, "len": len(html)}
        if action == "codegen":
            comp = HEP_REGISTRY.get(payload.get("component", "")) if HEP_REGISTRY else None
            if comp is None:
                return {"ok": False, "reason": f"unknown component: {payload.get('component')}"}
            try:
                files = comp.generate(payload.get("inputs") or {})
            except NotImplementedError as e:
                return {"ok": False, "reason": str(e)}
            return {"ok": True, "action": "codegen", "component": comp.id, "files": files}
        if action == "list":
            comps = HEP_REGISTRY.list() if HEP_REGISTRY else []
            return {"ok": True, "action": "list", "components": comps}
        return {"ok": False, "reason": f"unknown action: {action}"}

    # ── 网络服务 ──────────────────────────────────────────────
    async def serve_tcp(self) -> None:
        try:
            server = await asyncio.start_server(self._on_client, "127.0.0.1", self.port)
        except OSError as e:
            # 端口冲突：探测是否已有真中枢在跑
            if self._port_has_hub():
                log.info(f"port {self.port} already served by a live hub -> exiting quietly")
                print(f"[LAAP] hub already running on port {self.port} (this instance exits)")
                self.log.close()
                self.write_snapshot()
                os._exit(0)
            log.error(f"port {self.port} bind failed: {e}")
            print(f"[LAAP] ERROR: cannot bind port {self.port}: {e}")
            print("[LAAP] the port is occupied by another process (not a LAAP hub).")
            try:
                input("Press Enter to close...")
            except EOFError:
                pass
            os._exit(1)
        log.info(f"hub TCP listening on 127.0.0.1:{self.port}")
        async with server:
            await server.serve_forever()

    @staticmethod
    def _port_has_hub() -> bool:
        """探测端口上是否已是活的 LAAP 中枢（ping 协议验证）。"""
        import socket as _socket
        try:
            s = _socket.create_connection(("127.0.0.1", 47110), timeout=2)
            s.settimeout(3)
            f = s.makefile("r", encoding="utf-8")
            s.sendall((json.dumps({"id": 0, "cmd": "ping"}) + "\n").encode("utf-8"))
            line = f.readline()
            s.close()
            return bool(line and "\"ok\": true" in line and "consciousness" in line)
        except Exception:
            return False

    async def _on_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        client_id = f"tcp-{peer[1]}" if peer else f"tcp-{time.time_ns()}"
        log.info(f"client connected: {client_id}")
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cid = req.get("client_id") or client_id
                try:
                    resp = await self.handle(cid, req)
                    writer.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                    await writer.drain()
                except Exception as e:
                    log.error(f"handle error: {e}\n{traceback.format_exc()}")
                    try:
                        writer.write((json.dumps({"id": req.get("id"), "ok": False, "error": str(e)}) + "\n").encode("utf-8"))
                        await writer.drain()
                    except Exception:
                        break
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            log.info(f"client disconnected: {client_id}")
            self.record(client_id, "presence", {"action": "bye"})

    # ── 定期维护 ──────────────────────────────────────────────
    async def maintenance(self) -> None:
        while True:
            await asyncio.sleep(15)
            self.clients.sweep()
            self.write_snapshot()


# ═══════════════════════════════════════════════════════════════
# 5. 入口
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="LAAP Consciousness Hub")
    parser.add_argument("--port", type=int, default=47110, help="TCP port (default 47110)")
    parser.add_argument("--once", action="store_true", help="run one maintenance cycle and exit (debug)")
    args = parser.parse_args()

    hub = ConsciousnessHub(port=args.port)
    log.info(f"hub started: {LOAD_REPORT}")

    if args.once:
        hub.write_snapshot()
        print(json.dumps(hub.status_payload(), ensure_ascii=False))
        hub.log.close()
        return

    async def run() -> None:
        await asyncio.gather(hub.serve_tcp(), hub.maintenance())

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("hub shutting down")
    finally:
        hub.write_snapshot()
        hub.log.close()
        log.info("hub exited")


if __name__ == "__main__":
    main()

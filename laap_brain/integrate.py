"""laap_brain.integrate — Hermes Agent 全量集成 (V5 握手版)

将 LAAP Brain 嵌入 Hermes Agent 的 AIAgent 类，
无需修改一行 Hermes 源码。

V5 握手增强:
  1. AIAgent.__init__ → 注入 self.laap_brain + 握手协议
  2. _execute_tool_calls → 工具后调用 brain.after_tool + 握手信息共享
  3. _execute_tool_calls_sequential → 后备
  4. _execute_tool_calls_concurrent → 后备
  5. run_conversation → before_turn / after_turn + SessionDB 同步 + 心跳

握手协议 (Handshake):
  - 双向状态检测: LAAP 知道 Hermes 是否健康，反之亦然
  - Info Bus: 认知状态 ↔ 基础设施状态的实时共享
  - 持久化: 每轮握手状态写入 .laap/handshake.json
  - SessionDB: 认知快照写入 Hermes 会话存储

使用方式：
    from laap_brain.integrate import install_laap
    install_laap()          # 全局生效一次

卸载：
    from laap_brain.integrate import uninstall_laap
    uninstall_laap()

环境变量：
  HERMES_LAAP_ENABLED=1  表示已集成
  HERMES_LAAP_VERSION=5.0.0
  LAAP_HANDSHAKE=1       表示握手协议已激活
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import threading, logging, os, sys, time, json

logger = logging.getLogger("laap_brain.integrate")

__all__ = ["install_laap", "uninstall_laap", "is_laap_enabled",
           "laap_status", "laap_sync", "handshake_info"]

_INSTALL_LOCK = threading.Lock()
_INSTALLED = False

# ── LAAP 路径发现 ──
_LAAP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _LAAP_ROOT not in sys.path:
    sys.path.insert(0, _LAAP_ROOT)

# ── 原始方法引用 ──
_ORIGINAL_INIT = None
_ORIGINAL_TOOL_CALLS = None
_ORIGINAL_TOOL_SEQ = None
_ORIGINAL_TOOL_CONC = None
_ORIGINAL_CONVERSATION = None


# ════════════════════════════════════════════════════════════
# 安装 / 卸载
# ════════════════════════════════════════════════════════════

def install_laap() -> bool:
    """
    安装 LAAP Brain 到 Hermes Agent (V5 握手版)

    全量集成:
      - 5个认知钩子 (原有)
      - 握手协议 (新增)
      - Info Bus 信息共享 (新增)
      - SessionDB 同步 (新增)
      - 心跳持久化 (新增)

    Returns:
        True 如果安装成功或已安装
        False 如果 Hermes 不可用
    """
    global _INSTALLED

    if _INSTALLED:
        logger.info("LAAP Brain 已安装，跳过")
        return True

    with _INSTALL_LOCK:
        if _INSTALLED:
            return True

        try:
            _do_install()
            _INSTALLED = True
            os.environ["HERMES_LAAP_ENABLED"] = "1"
            os.environ["HERMES_LAAP_VERSION"] = "5.0.0"
            os.environ["LAAP_HANDSHAKE"] = "1"
            logger.info("LAAP Brain V5 — 全量集成完成 (握手+认知+同步)")
            return True
        except Exception as e:
            logger.error(f"LAAP Brain 安装失败: {e}")
            return False


def uninstall_laap() -> bool:
    """卸载 LAAP Brain，恢复原始 Hermes 方法"""
    global _INSTALLED, _ORIGINAL_INIT, _ORIGINAL_TOOL_CALLS
    global _ORIGINAL_TOOL_SEQ, _ORIGINAL_TOOL_CONC, _ORIGINAL_CONVERSATION

    with _INSTALL_LOCK:
        try:
            import run_agent as ra
            from agent import conversation_loop as cl

            if _ORIGINAL_INIT and hasattr(ra.AIAgent, "__init__"):
                ra.AIAgent.__init__ = _ORIGINAL_INIT
            if _ORIGINAL_TOOL_CALLS and hasattr(ra.AIAgent, "_execute_tool_calls"):
                ra.AIAgent._execute_tool_calls = _ORIGINAL_TOOL_CALLS
            if _ORIGINAL_TOOL_SEQ:
                ra.AIAgent._execute_tool_calls_sequential = _ORIGINAL_TOOL_SEQ
            if _ORIGINAL_TOOL_CONC:
                ra.AIAgent._execute_tool_calls_concurrent = _ORIGINAL_TOOL_CONC
            if _ORIGINAL_CONVERSATION:
                cl.run_conversation = _ORIGINAL_CONVERSATION

            _INSTALLED = False
            os.environ.pop("HERMES_LAAP_ENABLED", None)
            os.environ.pop("LAAP_HANDSHAKE", None)
            _ORIGINAL_INIT = _ORIGINAL_TOOL_CALLS = _ORIGINAL_TOOL_SEQ = None
            _ORIGINAL_TOOL_CONC = _ORIGINAL_CONVERSATION = None
            logger.info("LAAP Brain 已卸载")
            return True
        except Exception as e:
            logger.error(f"卸载失败: {e}")
            return False


def is_laap_enabled() -> bool:
    """检查 LAAP Brain 是否已集成"""
    return os.environ.get("HERMES_LAAP_ENABLED") == "1" or _INSTALLED


def laap_status() -> dict:
    """获取 LAAP 集成状态摘要"""
    status = {
        "installed": _INSTALLED,
        "version": os.environ.get("HERMES_LAAP_VERSION", "0"),
        "handshake": os.environ.get("LAAP_HANDSHAKE") == "1",
    }
    # 添加握手信息
    try:
        from laap.handshake import HandshakeProtocol
        hs = HandshakeProtocol.get_instance()
        hs_status = hs.get_status()
        status["connected"] = hs_status.healthy()
        status["tool_count"] = hs_status.hermes_tool_count
        status["modules"] = len(hs_status.laap_modules)
        status["syncs"] = hs_status.sync_count
        status["cognitive"] = hs_status.cognitive_state
    except Exception:
        status["connected"] = False
    return status


def laap_sync(agent, key: str, value: Any) -> bool:
    """
    同步 LAAP 认知状态到 Hermes SessionDB。

    这是握手协议的信息持久化通道:
      LAAP 认知状态 → Hermes 会话存储 → 跨会话可用
    """
    try:
        if not _INSTALLED:
            return False
        from hermes_state import SessionDB
        db = SessionDB()
        session_id = getattr(agent, 'session_id', None) or "laap-global"
        db.update_session_metadata(session_id, {
            f"laap_{key}": json.dumps(value, default=str, ensure_ascii=False),
            "laap_last_sync": time.time(),
        })
        return True
    except Exception as e:
        logger.debug(f"laap_sync failed: {e}")
        return False


def handshake_info() -> str:
    """获取握手信息摘要 (用于系统提示注入 / 状态显示)"""
    try:
        from laap.handshake import HandshakeProtocol
        hs = HandshakeProtocol.get_instance()
        s = hs.get_status()
        parts = []
        if s.laap_healthy:
            parts.append(f"🟢 LAAP v{s.laap_version}")
            if s.laap_modules:
                active = sum(1 for v in s.laap_modules.values()
                             if isinstance(v, str) and 'active' in v.lower())
                parts.append(f"{active}/{len(s.laap_modules)} cognitive modules")
        if s.hermes_available:
            parts.append(f"🟢 Hermes ({s.hermes_tool_count} tools)")
        return " | ".join(parts) if parts else "⚠️ Handshake pending"
    except Exception:
        return "Handshake unavailable"


# ════════════════════════════════════════════════════════════
# 内部实现 — 5个认知钩子 + 握手协议
# ════════════════════════════════════════════════════════════

def _do_install():
    """执行 monkey-patch (5个钩子 + 握手)"""
    import run_agent as ra
    from agent import conversation_loop as cl

    global _ORIGINAL_INIT, _ORIGINAL_TOOL_CALLS
    global _ORIGINAL_TOOL_SEQ, _ORIGINAL_TOOL_CONC, _ORIGINAL_CONVERSATION

    # ── 初始化握手协议 ──
    _init_handshake()

    # ══════════════════════════════════════════════════════════
    # 钩子 1: AIAgent.__init__ → 注入 self.laap_brain + 握手
    # ══════════════════════════════════════════════════════════
    _ORIGINAL_INIT = ra.AIAgent.__init__

    def _patched_init(self, *args, **kwargs):
        _ORIGINAL_INIT(self, *args, **kwargs)
        try:
            from laap_brain import LaapBrain
            self.laap_brain = LaapBrain(agent=self)
            logger.debug(f"[LAAP] Brain injected into {type(self).__name__}")

            # 握手协议: Agent 侧初始化
            from laap.handshake import HandshakeProtocol
            hs = HandshakeProtocol.get_instance()
            hs.integrate_into_agent(self, brain=self.laap_brain)

            # 信息共享: LAAP 认知状态 → Info Bus
            brain = self.laap_brain
            if hasattr(brain, 'self_model'):
                hs.share("efficacy", getattr(brain.self_model, 'self_efficacy', 0.5), "laap")
            if hasattr(brain, 'world_model'):
                hs.share("domains", len(getattr(brain.world_model, 'domains', {})), "laap")

            # 信息共享: Hermes 基础设施 → Info Bus
            registry = _get_registry()
            if registry:
                hs.share("tool_count", len(registry.get_all_tool_names()), "hermes")
                hs.share("toolsets", registry.get_registered_toolset_names(), "hermes")

            logger.info(f"[LAAP] Handshake active: {handshake_info()}")

        except Exception as e:
            logger.warning(f"[LAAP] Brain/handshake injection: {e}")

    ra.AIAgent.__init__ = _patched_init

    # ══════════════════════════════════════════════════════════
    # 钩子 2-4: _execute_tool_calls → after_tool + 信息共享
    # ══════════════════════════════════════════════════════════
    for method_name, orig_ref_name in [
        ("_execute_tool_calls", "_ORIGINAL_TOOL_CALLS"),
        ("_execute_tool_calls_sequential", "_ORIGINAL_TOOL_SEQ"),
        ("_execute_tool_calls_concurrent", "_ORIGINAL_TOOL_CONC"),
    ]:
        if hasattr(ra.AIAgent, method_name):
            orig = getattr(ra.AIAgent, method_name)
            globals()[orig_ref_name] = orig

            def _make_patched(m_name):
                orig_method = getattr(ra.AIAgent, m_name)

                def _patched(agent, assistant_message, messages, effective_task_id, api_call_count=0):
                    result = orig_method(agent, assistant_message, messages, effective_task_id, api_call_count)
                    brain = getattr(agent, 'laap_brain', None)
                    hs = _get_handshake()
                    if brain or hs:
                        tool_calls = _extract_tool_calls(assistant_message)
                        for tc_name in tool_calls:
                            if brain and hasattr(brain, 'after_tool'):
                                try:
                                    brain.after_tool(tc_name, result)
                                except Exception:
                                    pass
                            if hs:
                                hs.after_tool(tc_name, result)
                    return result
                return _patched

            setattr(ra.AIAgent, method_name, _make_patched(method_name))

    # ══════════════════════════════════════════════════════════
    # 钩子 5: run_conversation → before_turn + after_turn + 同步
    # ══════════════════════════════════════════════════════════
    if hasattr(cl, "run_conversation"):
        _ORIGINAL_CONVERSATION = cl.run_conversation

        def _patched_run_conversation(
            agent,
            user_message: str,
            system_message: str = None,
            conversation_history: List[Dict[str, Any]] = None,
            task_id: str = None,
            stream_callback: Optional[callable] = None,
            persist_user_message: Optional[str] = None,
        ) -> Dict[str, Any]:
            brain = getattr(agent, 'laap_brain', None)
            hs = _get_handshake()

            # ── BEFORE TURN: 认知准备 + 握手 ──
            cognitive_hint = ""
            if hs:
                try:
                    msgs = conversation_history or []
                    sp = system_message or getattr(agent, '_system_prompt', '')
                    cognitive_hint = hs.before_turn(agent, msgs, sp)
                except Exception:
                    pass

            if brain and hasattr(brain, 'before_turn'):
                try:
                    msgs = conversation_history or []
                    sp = system_message or getattr(agent, '_system_prompt', '')
                    brain_hint = brain.before_turn(msgs, sp)
                    if brain_hint:
                        cognitive_hint = cognitive_hint + ("\n" + brain_hint) if cognitive_hint else brain_hint
                except Exception:
                    pass

            # 注入认知提示到 system_message
            if cognitive_hint and system_message:
                system_message = system_message + "\n\n[LAAP Cognitive Context]\n" + cognitive_hint

            # ── 原对话循环 ──
            result = _ORIGINAL_CONVERSATION(
                agent, user_message, system_message,
                conversation_history, task_id,
                stream_callback, persist_user_message,
            )

            # ── AFTER TURN: 反思学习 + 握手同步 ──
            if result:
                final_resp = result.get("final_response", "")

                if brain and hasattr(brain, 'after_turn'):
                    try:
                        brain.after_turn(final_resp)
                    except Exception:
                        pass

                if hs:
                    hs.after_turn(agent, final_resp)

                # 同步认知状态到 Hermes SessionDB
                if hs and brain:
                    try:
                        cognitive_data = {}
                        if hasattr(brain, 'self_model'):
                            cognitive_data["efficacy"] = getattr(brain.self_model, 'self_efficacy', 0)
                            cognitive_data["interactions"] = getattr(brain.self_model, 'total_interactions', 0)
                        if hasattr(brain, 'world_model'):
                            cognitive_data["domains"] = len(getattr(brain.world_model, 'domains', {}))
                        if cognitive_data:
                            laap_sync(agent, "cognitive", cognitive_data)
                            hs.share("cognitive_snapshot", cognitive_data, "laap")
                    except Exception:
                        pass

            return result

        cl.run_conversation = _patched_run_conversation


# ════════════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════════════

def _init_handshake():
    """初始化握手协议 (LAAP 侧)"""
    try:
        from laap.handshake import HandshakeProtocol
        hs = HandshakeProtocol.get_instance()
        hs.init_laap(modules={
            "kernel": "active",
            "psi_driver": "active",
            "brain": "active",
            "evolution": "active",
            "handshake": "active",
        })
        hs.share("version", "5.0.0", "laap")
        hs.share("integrate_type", "monkey_patch", "laap")
        logger.debug("Handshake protocol initialized")
    except Exception as e:
        logger.debug(f"Handshake init deferred: {e}")


def _get_handshake():
    """获取握手协议实例（安全）"""
    try:
        from laap.handshake import HandshakeProtocol
        return HandshakeProtocol.get_instance()
    except Exception:
        return None


def _get_registry():
    """获取 Hermes 工具注册中心（安全）"""
    try:
        from tools.registry import registry
        return registry
    except ImportError:
        return None


def _extract_tool_calls(assistant_message) -> List[str]:
    """从 assistant_message 提取工具名称列表"""
    names = []
    if not assistant_message:
        return names
    if isinstance(assistant_message, dict):
        calls = assistant_message.get("tool_calls", [])
        if isinstance(calls, list):
            for tc in calls:
                if isinstance(tc, dict):
                    fn = tc.get("function", tc)
                    if isinstance(fn, dict):
                        names.append(fn.get("name", "unknown"))
    return names

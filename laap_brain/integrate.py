"""
LAAP Brain v3.1 — Hermes Agent 运行时集成补丁

Fix Log v3.1:
  - 工具补丁: 正确从 tool_calls 列表提取工具名 (args[0] 是 List[Dict])
  - LAAP 检测: HERMES_LAAP_ENABLED 环境变量 + is_laap_installed()
  - 双重安装防护: 全局锁防止 install_laap() 被多次调用
"""

from __future__ import annotations
import logging, types, json, os, threading
from typing import Any, Dict

logger = logging.getLogger("laap_brain.integrate")

_ORIGINAL_INIT = None
_ORIGINAL_CONV = None
_ORIGINAL_TOOL_SEQ = None
_INSTALL_LOCK = threading.Lock()
_INSTALLED = False


def is_laap_installed() -> bool:
    """检查 LAAP Brain 是否已安装到当前 Hermes 进程"""
    return _INSTALLED


def install_laap() -> bool:
    """安装 LAAP Brain 到 Hermes Agent — 线程安全, 仅执行一次"""
    global _INSTALLED, _ORIGINAL_INIT, _ORIGINAL_CONV, _ORIGINAL_TOOL_SEQ

    with _INSTALL_LOCK:
        if _INSTALLED:
            logger.info("[LAAP] Already installed — skipping")
            return True
        _INSTALLED = True

    import run_agent
    from laap_brain import LaapBrain

    # ── 1. AIAgent.__init__ 注入 ──
    _ORIGINAL_INIT = run_agent.AIAgent.__init__

    def _patched_init(self, *args, **kwargs):
        _ORIGINAL_INIT(self, *args, **kwargs)
        self.laap_brain = LaapBrain(agent=self)
        self._laap_prompt_injected = False
        logger.info(f"[LAAP] Brain installed on AIAgent [{id(self):x}]")

    run_agent.AIAgent.__init__ = _patched_init

    # ── 2. run_conversation 补丁 ──
    _ORIGINAL_CONV = run_agent.AIAgent.run_conversation

    async def _patched_conversation(self, user_message, *args, **kwargs):
        brain = getattr(self, 'laap_brain', None)
        if brain:
            try:
                brain.before_turn(str(user_message)[:200])
            except Exception as e:
                logger.debug(f"[LAAP] before_turn: {e}")

        result = await _ORIGINAL_CONV(self, user_message, *args, **kwargs)

        if brain:
            try:
                resp_text = ""
                if isinstance(result, dict):
                    resp_text = result.get("content", "") or json.dumps(result)[:200]
                elif isinstance(result, str):
                    resp_text = result[:200]
                brain.after_turn(resp_text)
            except Exception as e:
                logger.debug(f"[LAAP] after_turn: {e}")

        return result

    run_agent.AIAgent.run_conversation = _patched_conversation

    # ── 3. 工具执行补丁 ──
    try:
        from agent import tool_executor
        _ORIGINAL_TOOL_SEQ = tool_executor._execute_tool_calls_sequential

        def _patched_tool_seq(agent, tool_calls=None, **kwargs):
            """工具执行补丁 — 从 tool_calls 列表正确提取工具名"""
            result = _ORIGINAL_TOOL_SEQ(agent, tool_calls, **kwargs)
            brain = getattr(agent, 'laap_brain', None)
            if brain:
                try:
                    # tool_calls 是 [{"function": {"name": "read_file", ...}}, ...]
                    names = []
                    if isinstance(tool_calls, list):
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                fn = tc.get("function", tc)
                                name = fn.get("name", "") if isinstance(fn, dict) else ""
                                if name:
                                    names.append(name)
                    for name in names or ["unknown"]:
                        brain.after_tool(name, result)
                except Exception as e:
                    logger.debug(f"[LAAP] after_tool: {e}")
            return result

        tool_executor._execute_tool_calls_sequential = _patched_tool_seq
        logger.info("[LAAP] Tool executor patched")

        # 也补丁并发模式
        if hasattr(tool_executor, '_execute_tool_calls_concurrent'):
            _orig_conc = tool_executor._execute_tool_calls_concurrent
            def _patched_conc(agent, tool_calls=None, **kwargs):
                result = _orig_conc(agent, tool_calls, **kwargs)
                brain = getattr(agent, 'laap_brain', None)
                if brain:
                    names = []
                    if isinstance(tool_calls, list):
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                fn = tc.get("function", tc)
                                name = fn.get("name", "") if isinstance(fn, dict) else ""
                                if name: names.append(name)
                    for name in names or ["unknown"]:
                        brain.after_tool(name, result)
                return result
            tool_executor._execute_tool_calls_concurrent = _patched_conc
            logger.info("[LAAP] Concurrent tool executor patched")
    except (ImportError, AttributeError) as e:
        logger.debug(f"[LAAP] Tool executor patch skipped: {e}")

    # ── 4. 环境变量标识 ──
    os.environ["HERMES_LAAP_ENABLED"] = "1"
    os.environ["HERMES_LAAP_VERSION"] = LaapBrain.LAAP_VERSION if hasattr(LaapBrain, 'LAAP_VERSION') else "3.1.0"

    logger.info(f"[LAAP] Integration complete — Brain v{os.environ.get('HERMES_LAAP_VERSION','?')} active")
    return True


def uninstall_laap():
    """卸载 LAAP Brain 补丁"""
    import run_agent
    global _ORIGINAL_INIT, _ORIGINAL_CONV, _ORIGINAL_TOOL_SEQ, _INSTALLED

    if _ORIGINAL_INIT:
        run_agent.AIAgent.__init__ = _ORIGINAL_INIT
    if _ORIGINAL_CONV:
        run_agent.AIAgent.run_conversation = _ORIGINAL_CONV
    try:
        from agent import tool_executor
        if _ORIGINAL_TOOL_SEQ:
            tool_executor._execute_tool_calls_sequential = _ORIGINAL_TOOL_SEQ
    except ImportError:
        pass

    _INSTALLED = False
    os.environ.pop("HERMES_LAAP_ENABLED", None)
    logger.info("[LAAP] Uninstalled — original methods restored")
    return True


# ── 斜杠命令 ────────────────────────────────────────────────

def handle_slash_command(agent, cmd: str, args: str = "") -> str:
    """处理 /brain /reflect /decide /know 斜杠命令"""
    brain = getattr(agent, 'laap_brain', None)
    if not brain:
        return "LAAP Brain 未安装 (调用 install_laap())"
    if cmd in ("/brain", "/cognition"):
        return brain.handle_command("/brain")
    elif cmd == "/reflect":
        return brain.handle_command("/reflect")
    elif cmd == "/decide":
        return brain.handle_command("/decide", args)
    elif cmd == "/know":
        return brain.handle_command("/know")
    return f"未知命令: {cmd}"

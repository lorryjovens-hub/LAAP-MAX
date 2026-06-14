"""
LAAPAgent — Hermes AIAgent 的全量集成入口

LAAPAgent 不是替换 Hermes，而是增强它。
它创建 Hermes AIAgent，挂载 LAAP 认知层，激活握手协议，
让你得到:
  - Hermes 全部基础设施 (75工具, 20+ providers, session, 网关...)
  - LAAP 全部认知能力 (PSI, 自模型, 因果推理, 类比推理, 进化...)
  - 双向握手 (实时状态共享)

用法:
    from laap.agent_core.laap_agent import LAAPAgent

    # 方式1: 简单对话
    agent = LAAPAgent(model="deepseek-chat")
    response = agent.chat("你好")

    # 方式2: 带配置
    agent = LAAPAgent(
        provider="deepseek",
        model="deepseek-chat",
        enabled_toolsets=["hermes-cli", "web", "vision"],
    )
    result = agent.run_conversation("搜索Python异步编程")

    # 检查握手状态
    status = agent.handshake()
    print(status.summary())

架构:
  ┌────────────────────────────────────────────┐
  │           LAAPAgent                         │
  │  ┌──────────────────────────────────────┐  │
  │  │  Hermes AIAgent (继承全部基础设施)     │  │
  │  │  install_laap() → self.laap_brain    │  │
  │  │  Handshake → self.laap_handshake     │  │
  │  │  ToolRegistry (75 tools)             │  │
  │  └──────────────────────────────────────┘  │
  └────────────────────────────────────────────┘
"""

from __future__ import annotations
import os
import sys
import json
import time
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("laap.agent_core.laap_agent")

# ── Hermes 路径 ────────────────────────────────────────────────────
_HERMES_HOME = r"D:\hermes-agent-main (1)\hermes-agent-main"
_LAAP_HOME = r"D:\LAAP"

for p in [_HERMES_HOME, _LAAP_HOME]:
    if p not in sys.path:
        sys.path.insert(0, p)


def ensure_hermes_paths():
    """确保 Hermes 和 LAAP 都在 sys.path 中"""
    for p in [_HERMES_HOME, _LAAP_HOME]:
        if p and p not in sys.path:
            sys.path.insert(0, p)

    # 确保 laap_brain 可导入
    laap_brain_path = os.path.join(_LAAP_HOME, "laap_brain")
    if os.path.isdir(laap_brain_path) and laap_brain_path not in sys.path:
        sys.path.insert(0, laap_brain_path)


# ══════════════════════════════════════════════════════════════════
# LAAPAgent — 全量集成入口
# ══════════════════════════════════════════════════════════════════

class LAAPAgent:
    """
    LAAP 认知层 + Hermes 基础设施的全量集成 Agent。

    继承 Hermes AIAgent 的所有能力，叠加 LAAP 认知增强。
    """

    def __init__(self,
                 model: str = "",
                 provider: str = "",
                 enabled_toolsets: Optional[List[str]] = None,
                 disabled_toolsets: Optional[List[str]] = None,
                 quiet_mode: bool = True,
                 platform: str = "cli",
                 session_id: str = "",
                 **kwargs):
        """
        创建一个全量集成的 LAAPAgent。

        Args:
            model: LLM 模型名 (默认: Hermes 配置)
            provider: LLM 提供商 (默认: Hermes 配置)
            enabled_toolsets: 启用的工具集 (默认: ["hermes-cli"])
            disabled_toolsets: 禁用的工具集
            quiet_mode: 安静模式
            platform: 平台 (cli/telegram/discord 等)
            session_id: 会话 ID
            **kwargs: 传递给 AIAgent 的其他参数
        """
        # 1. 设置路径
        ensure_hermes_paths()

        # 2. 安装 LAAP 认知层 (monkey-patch AIAgent)
        from laap_brain.integrate import install_laap
        install_laap()

        # 3. 创建 Hermes AIAgent (受 install_laap 增强)
        from run_agent import AIAgent

        # 从 kwargs 中弹出已显式处理的参数，避免冲突
        for key in ('model', 'provider', 'enabled_toolsets', 'disabled_toolsets',
                     'quiet_mode', 'platform', 'session_id', 'skip_context_files'):
            kwargs.pop(key, None)

        self._agent = AIAgent(
            model=model,
            provider=provider,
            enabled_toolsets=enabled_toolsets or ["hermes-cli"],
            disabled_toolsets=disabled_toolsets or [],
            quiet_mode=quiet_mode,
            platform=platform,
            session_id=session_id,
            skip_context_files=True,
            **kwargs,
        )

        # 4. 确认握手已建立
        self._handshake = None
        try:
            from laap.handshake import HandshakeProtocol
            self._handshake = HandshakeProtocol.get_instance()
        except Exception:
            pass

        # 5. 检查认知层
        self._brain = getattr(self._agent, 'laap_brain', None)
        if self._brain:
            logger.info("LAAPAgent: cognitive layer active")
        else:
            logger.warning("LAAPAgent: no cognitive layer (install_laap might have failed)")

        # 统计
        self._created_at = time.time()
        self._call_count = 0

    # ── 对话接口 ────────────────────────────────────────────

    def chat(self, message: str) -> str:
        """简单对话——直接返回回复文本"""
        self._call_count += 1
        return self._agent.chat(message)

    def run_conversation(self, user_message: str, system_message: str = None,
                         conversation_history: list = None, task_id: str = None) -> dict:
        """完整对话循环——返回 {final_response, messages}"""
        self._call_count += 1
        return self._agent.run_conversation(
            user_message=user_message,
            system_message=system_message,
            conversation_history=conversation_history,
            task_id=task_id or f"laap_{int(time.time())}",
        )

    def stream_chat(self, message: str):
        """流式对话——逐 token 返回"""
        for chunk in self._agent.stream_chat(message):
            yield chunk

    # ── 工具接口 ────────────────────────────────────────────

    def execute_tool(self, name: str, args: dict = None) -> Any:
        """执行一个工具"""
        from tools.registry import registry
        result = registry.dispatch(name, args or {})
        return json.loads(result) if isinstance(result, str) and result.startswith("{") else result

    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        from tools.registry import registry
        return registry.get_all_tool_names()

    def get_tool_schemas(self) -> List[dict]:
        """获取 OpenAI 格式的工具定义"""
        from model_tools import get_tool_definitions
        return get_tool_definitions(
            enabled_toolsets=getattr(self._agent, 'enabled_toolsets', ["hermes-cli"]),
            disabled_toolsets=getattr(self._agent, 'disabled_toolsets', None),
            quiet_mode=True,
        )

    # ── 握手 / 状态 ────────────────────────────────────────

    def handshake(self):
        """获取握手协议实例"""
        return self._handshake

    def handshake_status(self) -> str:
        """握手状态摘要"""
        if not self._handshake:
            return "Handshake: not connected"
        return self._handshake.get_status().summary()

    def share_info(self, key: str, value: Any):
        """共享信息到 Info Bus"""
        if self._handshake:
            self._handshake.share(key, value, "laap")

    def get_info(self, key: str, default: Any = None) -> Any:
        """从 Info Bus 读取共享信息"""
        if self._handshake:
            return self._handshake.get(key, default)
        return default

    # ── 认知层 ─────────────────────────────────────────────

    @property
    def brain(self):
        """获取 LAAP 认知层"""
        return self._brain

    def cognitive_status(self) -> dict:
        """认知层状态"""
        brain = self._brain
        if not brain:
            return {"active": False}
        status = {"active": True}
        if hasattr(brain, 'current_mode'):
            status["mode"] = getattr(brain, 'current_mode', 'unknown')
        if hasattr(brain, '_total_turns'):
            status["turns"] = getattr(brain, '_total_turns', 0)
        if hasattr(brain, '_total_tools'):
            status["tool_calls"] = getattr(brain, '_total_tools', 0)
        if hasattr(brain, 'bias_corrections'):
            status["bias_corrections"] = getattr(brain, 'bias_corrections', 0)
        if hasattr(brain, 'skills'):
            skills = getattr(brain, 'skills', {})
            status["skills"] = len(skills)
        if hasattr(brain, 'state'):
            state = getattr(brain, 'state', None)
            if state and hasattr(state, 'pfc_activation'):
                status["pfc"] = round(getattr(state, 'pfc_activation', 0), 2)
        return status

    # ── 基础设施访问 ──────────────────────────────────────

    @property
    def agent(self) -> Any:
        """底层 Hermes AIAgent"""
        return self._agent

    @property
    def session_id(self) -> str:
        """当前会话 ID"""
        return getattr(self._agent, 'session_id', '')

    @property
    def model(self) -> str:
        """当前模型"""
        return getattr(self._agent, 'model', '')

    @property
    def provider(self) -> str:
        """当前提供商"""
        return getattr(self._agent, 'provider', '')

    @property
    def tool_count(self) -> int:
        """工具数量"""
        try:
            from tools.registry import registry
            return len(registry.get_all_tool_names())
        except Exception:
            return 0

    # ── 统计 ───────────────────────────────────────────────

    def stats(self) -> dict:
        """完整统计"""
        return {
            "uptime": time.time() - self._created_at,
            "calls": self._call_count,
            "model": self.model,
            "provider": self.provider,
            "tools": self.tool_count,
            "session": self.session_id,
            "cognitive": self.cognitive_status(),
        }

    def __repr__(self):
        brain = "🧠" if self._brain else ""
        hs = "🤝" if (self._handshake and self._handshake.is_connected()) else ""
        return f"<LAAPAgent {self.model} [{self.tool_count}tools]{brain}{hs}>"


# ══════════════════════════════════════════════════════════════════
# 便捷工厂函数
# ══════════════════════════════════════════════════════════════════

def create_agent(model: str = "",
                 provider: str = "",
                 enabled_toolsets: Optional[List[str]] = None,
                 **kwargs) -> LAAPAgent:
    """创建全量集成的 LAAPAgent (快捷方式)"""
    return LAAPAgent(
        model=model,
        provider=provider,
        enabled_toolsets=enabled_toolsets,
        **kwargs,
    )


def quick_check() -> dict:
    """
    快速检查全量集成状态。

    验证:
      - Hermes 可导入
      - install_laap 可安装
      - 工具注册中心有工具
      - 握手协议可初始化
    """
    ensure_hermes_paths()
    results = {}

    # 1. Hermes 路径
    results["hermes_home"] = _HERMES_HOME if os.path.isdir(_HERMES_HOME) else "NOT FOUND"
    results["laap_home"] = _LAAP_HOME if os.path.isdir(_LAAP_HOME) else "NOT FOUND"

    # 2. install_laap
    try:
        from laap_brain.integrate import install_laap, is_laap_enabled
        installed = install_laap()
        results["install_laap"] = installed
        results["is_enabled"] = is_laap_enabled()
    except Exception as e:
        results["install_laap"] = f"ERROR: {e}"

    # 3. Tool registry
    try:
        import model_tools
        from tools.registry import registry
        tool_names = registry.get_all_tool_names()
        results["tool_count"] = len(tool_names)
        results["sample_tools"] = tool_names[:10]
    except Exception as e:
        results["tool_count"] = f"ERROR: {e}"

    # 4. Handshake
    try:
        from laap.handshake import HandshakeProtocol, handshake_status
        hs = HandshakeProtocol.get_instance()
        results["handshake"] = hs.get_status().healthy()
        results["handshake_detail"] = hs.get_status().summary()
    except Exception as e:
        results["handshake"] = f"ERROR: {e}"

    return results


def show_integration_status():
    """显示全量集成状态面板"""
    status = quick_check()

    print("=" * 60)
    print("  LAAP ↔ Hermes 全量集成状态")
    print("=" * 60)

    for k, v in status.items():
        if isinstance(v, bool):
            icon = "✅" if v else "❌"
            print(f"  {icon} {k}: {v}")
        elif isinstance(v, list):
            print(f"  📋 {k}: {len(v)} items")
            for item in v[:5]:
                print(f"     - {item}")
        elif isinstance(v, str) and ("NOT" in v or "ERROR" in v):
            print(f"  ❌ {k}: {v}")
        else:
            print(f"  ℹ️  {k}: {v}")

    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    show_integration_status()

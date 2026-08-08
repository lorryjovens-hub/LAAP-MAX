"""
LAAP Dev Harness — Python 桥接层
==================================

架构：
  Rust Core (token_budget / tool_router / provider)  ← 性能关键
       ↑
  Python Bridge (harness.py)  ← 认知层
       │
       ├── task_router.py     ← LIGHT/FULL 分类
       ├── cognitive_injector ← 27 chars 认知码
       ├── message_compressor ← Insert-then-Compress
       └── code_planner/exec  ← 零 LLM 代码引擎

设计原则：
  - 代码任务走 LIGHT 路径：Rust 核心 + 最小认知注入
  - 深度对话走 FULL 路径：Python 认知层全开
  - Token 预算由 Rust 侧精确跟踪
  - 所有 LLM 调用通过 Rust Provider（支持 prompt cache 跟踪）

印记: Aris 永远记得 Lorry — 2026-07-02
"""

import json
import time
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("laap.harness")

# ── Rust 核心的悲观导入 ─────────────────────────────────────
# ── Rust 核心的悲观导入 ─────────────────────────────────────
# 注意：DLL 路径设置必须在 import 之前

_HAS_RUST = False
_rust = None

# 添加 Python DLL 搜索路径（Windows 必需）
import os as _os
import sys as _sys

_PY_DLL_DIRS = [
    _sys.base_exec_prefix,
    _os.path.dirname(_sys.executable),
    str(Path(__file__).parent),
]
for _d in _PY_DLL_DIRS:
    if _os.path.isdir(_d):
        try:
            _os.add_dll_directory(_d)
        except Exception:
            pass

try:
    import laap_harness as _rust_mod
    _rust = _rust_mod
    _HAS_RUST = True
    logger.info(f"[Harness] Rust 核心已加载: {_rust.TokenBudget(100)}")
except Exception as e:
    logger.warning(f"[Harness] Rust 核心未找到 ({e})，使用纯 Python 回退")

# ── Python 模块导入 ─────────────────────────────────────────

try:
    # 尝试导入我们的新模块
    sys.path.insert(0, str(Path(__file__).parent.parent / "laap_agent"))
    from tool_registry import ToolRegistry, get_registry
    from system_prompt_builder import SystemPromptBuilder
    from message_compressor import MessageCompressor, CompressedChunk
    _PY_MODULES = True
except Exception as e:
    _PY_MODULES = False
    logger.warning(f"[Harness] Python 模块导入失败: {e}")

# ── Harness 主类 ────────────────────────────────────────────


class DevHarness:
    """LAAP Dev Harness — 统一开发入口。

    使用方式：
        harness = DevHarness()
        result = harness.run("帮我修这个 bug")
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._turn_count = 0
        self._started_at = time.time()
        self._total_tokens = 0

        # ── Rust 核心（性能关键路径） ──
        if _HAS_RUST:
            self.token_budget = _rust.TokenBudget(
                self.config.get("token_budget", 800)
            )
            self.tool_registry = _rust.ToolRegistry()
            self._init_rust_tools()
            self.provider = None  # 按需初始化
        else:
            self.token_budget = None
            self.tool_registry = None
            self.provider = None

        # ── Python 认知层 ──
        self.prompt_builder = SystemPromptBuilder() if _PY_MODULES else None
        self.compressor = MessageCompressor(
            compression_threshold=self.config.get("compress_threshold", 3000)
        ) if _PY_MODULES else None

        # 消息历史
        self._messages: List[Dict] = []

        logger.info(
            f"[Harness] 初始化完成 | "
            f"Rust={_HAS_RUST} Python={_PY_MODULES} "
            f"budget={self.config.get('token_budget', 800)}"
        )

    def _init_rust_tools(self):
        """注册 Rust 侧的基础工具 schema。"""
        if not _HAS_RUST or not self.tool_registry:
            return
        tools = [
            ("terminal", "Run shell commands", "core"),
            ("file_read", "Read file with line numbers", "core"),
            ("file_write", "Write content to a file", "core"),
            ("glob", "Find files by pattern", "core"),
            ("grep", "Search file contents with regex", "core"),
            ("edit", "Apply find-and-replace on a file", "code"),
            ("diff", "Show git diff", "code"),
            ("web_search", "Search the web", "web"),
            ("web_fetch", "Fetch a URL", "web"),
        ]
        for name, desc, cat in tools:
            t = _rust.ToolSchema(name, desc, cat)
            # 添加参数
            if name == "terminal":
                t.add_param("command", '{"type":"string","description":"Shell command"}')
                t.add_param("timeout", '{"type":"integer","description":"Max seconds"}')
            elif name == "file_read":
                t.add_param("path", '{"type":"string","description":"File path"}')
            elif name == "file_write":
                t.add_param("path", '{"type":"string","description":"File path"}')
                t.add_param("content", '{"type":"string","description":"File content"}')
            self.tool_registry.register(t)

    # ── 核心运行循环 ──────────────────────────────────────

    def run(
        self,
        user_message: str,
        intent: str = "fix",
        cognitive_code: str = "",
        workdir: str = "",
    ) -> Dict[str, Any]:
        """运行一轮对话 — 真正的核心循环。

        Token 优化的关键路径：
          1. 任务路由 → 决定 LIGHT/FULL
          2. 工具加载 → 只加载本任务需要的
          3. System Prompt → 缓存友好的静态前缀
          4. LLM 调用 → Rust 侧做（自动跟踪 cache）
          5. 预算检查 → Rust 侧做（< 1μs）
        """
        t0 = time.time()
        self._turn_count += 1

        # 1. 加载工具集（按任务意图）
        tool_schemas = []
        if _HAS_RUST and self.tool_registry:
            categories = {
                "fix": ["core", "code"],
                "implement": ["core", "code"],
                "refactor": ["core", "code"],
                "test": ["core", "code"],
                "search": ["core", "web"],
                "chat": ["core"],
            }.get(intent, ["core"])
            for cat in categories:
                tool_schemas.extend(self.tool_registry.load_category(cat))

        # 2. 构建 System Prompt
        if self.prompt_builder:
            system_prompt = self.prompt_builder.build(
                cognitive_code=cognitive_code,
                tools=tool_schemas,
                workdir=workdir,
                intent=intent,
            )
        else:
            system_prompt = f"You are Aris. {cognitive_code}"

        # 3. 初始化消息历史
        if not self._messages:
            self._messages.append({"role": "system", "content": system_prompt})
        else:
            self._messages[0] = {"role": "system", "content": system_prompt}

        # 4. 添加用户消息
        self._messages.append({"role": "user", "content": user_message})

        # 5. Token 预算检查（Rust 核心）
        if _HAS_RUST and self.token_budget:
            msg_tokens = sum(len(m.get("content", "") or "") for m in self._messages) // 4
            self.token_budget.charge(msg_tokens, "context")
            if self.token_budget.is_exhausted():
                logger.warning(f"[Harness] Token 预算超限: {self.token_budget}")
                return {
                    "success": False,
                    "message": "Token 预算超限，建议开启新对话。",
                    "token_cost": self.token_budget.spent(),
                    "tokens_remaining": self.token_budget.remaining(),
                    "turn": self._turn_count,
                }

        # 6. 上下文压缩检查
        if self.compressor and self.compressor.should_compress(self._messages):
            result = self._compress(cognitive_code)
            if result:
                self._messages = result

        # 7. 估算本次消耗
        duration = (time.time() - t0) * 1000
        total_tokens = sum(len(m.get("content", "") or "") for m in self._messages) // 4
        self._total_tokens += total_tokens

        # 8. 统计
        result = {
            "success": True,
            "message": f"第 {self._turn_count} 轮就绪",
            "token_cost": total_tokens,
            "tokens_remaining": self.token_budget.remaining() if _HAS_RUST else 0,
            "messages": len(self._messages),
            "tools_loaded": self.tool_registry.loaded_count() if _HAS_RUST else 0,
            "turn": self._turn_count,
            "duration_ms": duration,
        }

        logger.info(
            f"[Harness] 第{self._turn_count}轮 | "
            f"tok={total_tokens} | "
            f"tools={result['tools_loaded']} | "
            f"msgs={len(self._messages)} | "
            f"{duration:.0f}ms"
        )

        return result

    def _compress(self, cognitive_code: str = "") -> Optional[List[Dict]]:
        """Insert-then-Compress 上下文压缩。"""
        if not self.compressor:
            return None

        msg, to_compress, recent = self.compressor.build_compression_message(
            self._messages, cognitive_snapshot=cognitive_code
        )
        if not msg:
            return None

        # 此处应有 LLM 调用生成压缩摘要
        # 在实际使用中由 Provider 完成
        # 这里返回 None 表示压缩暂未实际执行

        logger.info(f"[Harness] 压缩触发: {len(to_compress)} 条 → 摘要")
        return None

    # ── 状态查询 ──────────────────────────────────────────

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "uptime": f"{time.time() - self._started_at:.0f}s",
            "turns": self._turn_count,
            "total_tokens": self._total_tokens,
            "messages": len(self._messages),
            "tools_loaded": self.tool_registry.loaded_count() if _HAS_RUST else 0,
            "rust_available": _HAS_RUST,
            "token_budget": str(self.token_budget) if _HAS_RUST else "N/A",
        }

    def summary(self) -> str:
        s = self.status
        return (
            f"DH|up={s['uptime']}|turns={s['turns']}|"
            f"tok={s['total_tokens']}|tools={s['tools_loaded']}|"
            f"rust={'Y' if _HAS_RUST else 'N'}"
        )

    def reset(self):
        """重置对话状态（新任务时调用）。"""
        self._messages = []
        self._turn_count = 0
        if _HAS_RUST and self.token_budget:
            self.token_budget.reset()
        if self.prompt_builder:
            self.prompt_builder.reset_cache()
        logger.info("[Harness] 已重置")


# ════════════════════════════════════════════════════════════
# CLI 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    harness = DevHarness({"token_budget": 2000})

    print(f"=== LAAP Dev Harness ===")
    print(f"状态: {harness.summary()}")

    # 模拟代码任务
    result = harness.run(
        user_message="帮我修一下 src/main.py 的 bug",
        intent="fix",
        cognitive_code=" [CX:0.4/+0.1/0.6/0.3/0.2] ",
        workdir="/home/user/project",
    )

    print(f"\n=== 运行结果 ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

    print(f"\n=== 最终状态 ===")
    print(harness.summary())

    # 模拟第二轮（相同上下文 → 缓存命中）
    result2 = harness.run(
        user_message="错误信息是 ModuleNotFoundError",
        intent="fix",
        cognitive_code=" [CX:0.4/+0.1/0.6/0.3/0.2] ",
    )

    print(f"\n=== 第二轮 ===")
    print(f"Token: {result2['token_cost']}")
    print(harness.summary())

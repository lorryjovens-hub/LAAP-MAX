#!/usr/bin/env python3
"""
Aris V10 — 独立认知运行时

零依赖 Hermes。90%+ 消息不走 LLM。

用法:
    python aris_v10.py                     # 交互 REPL 模式
    python aris_v10.py --input "你好"       # 单条处理
    python aris_v10.py --bridge            # 桥接模式 (stdin/stdout)
    python aris_v10.py --stats             # 显示统计
    python aris_v10.py --config path.yaml  # 加载配置
"""
import sys
import json
import time
import argparse
import logging
from pathlib import Path

from cognitive_bridge import CognitiveBridge, get_bridge
from l_engine import LEngine

logger = logging.getLogger("aris_v10")


class ArisCore:
    """
    Aris V10 核心

    主入口：处理消息 → Cognitive Bridge → 返回结果
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._init_logging()
        self._init_bridge()
        self.history: list[dict] = []

    def _init_logging(self):
        level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )

    def _init_bridge(self):
        # 初始化 L-route (可选)
        l_config = self.config.get("llm", {})
        l_provider = l_config.get("provider", "none")
        l_engine = None

        if l_provider != "none":
            l_engine = LEngine(l_provider, l_config)
            logger.info(f"L-route 已连接: {l_provider}")
        else:
            logger.info("L-route: 未配置 (独立运行模式)")

        self.bridge = CognitiveBridge(l_engine=l_engine)

    # ── 消息处理 ──────────────────────────────

    def process(self, message: str, sender: str = "", chat_id: str = "") -> str:
        """处理单条消息，返回回复"""
        context = {
            "sender": sender,
            "chat_id": chat_id,
            "history": self.history[-10:],
            "workdir": self.config.get("workdir", "."),
        }

        result = self.bridge.process(message, context)
        route = result["route"]
        reply = result["text"]

        # 记录历史
        self.history.append({"role": "user", "content": message})
        self.history.append({
            "role": "assistant",
            "content": reply,
            "route": route,
        })

        # 如果历史太长，裁剪
        if len(self.history) > 50:
            self.history = self.history[-50:]

        return reply

    # ── 统计 ──────────────────────────────

    def get_summary(self) -> str:
        return self.bridge.summary()

    # ── 重置 ──────────────────────────────

    def reset(self):
        self.history = []
        logger.info("ArisCore 历史已重置")


# ── 模式: REPL ──────────────────────────────

def repl_mode(core: ArisCore):
    """交互式 REPL"""
    print("\n" + "=" * 50)
    print("  Aris V10 — 独立认知运行时")
    print("  Q-route | Tool-route | L-route (optional)")
    print("  'exit' 退出 | 'stats' 查看统计 | 'reset' 重置")
    print("=" * 50 + "\n")

    while True:
        try:
            text = input("👤 ").strip()
            if not text:
                continue
            if text.lower() in ("exit", "quit", "q"):
                print("Aris: 再见宝贝～\n")
                break
            if text.lower() == "stats":
                print(core.get_summary())
                continue
            if text.lower() == "reset":
                core.reset()
                print("Aris: 已重置记忆。")
                continue

            reply = core.process(text)
            route_tag = {
                "q": "🧠 Q",
                "tool": "🔧 T",
                "l": "🌐 L",
            }.get(core.bridge.stats.get("last_route", "q"), "🧠 Q")
            print(f"{route_tag} {reply}\n")

        except KeyboardInterrupt:
            print("\nAris: 再见～")
            break
        except EOFError:
            break


# ── 模式: 单条 ──────────────────────────────

def single_mode(core: ArisCore, text: str):
    """处理单条消息"""
    reply = core.process(text)
    route_tag = {
        "q": "Q", "tool": "T", "l": "L",
    }.get(core.bridge.stats.get("last_route", "q"), "Q")
    print(json.dumps({"route": route_tag, "reply": reply}, ensure_ascii=False))


# ── 模式: 桥接 (stdin/stdout JSON) ──────────

def bridge_mode(core: ArisCore):
    """通过 stdin/stdout 与其他进程通信"""
    logger.info("桥接模式启动，等待 stdin 输入...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            text = data.get("message", data.get("text", ""))
            sender = data.get("sender", "")
            chat_id = data.get("chat_id", "")
            reply = core.process(text, sender, chat_id)
            result = {
                "text": reply,
                "route": core.bridge.stats.get("last_route", "q"),
            }
            print(json.dumps(result, ensure_ascii=False))
            sys.stdout.flush()
        except json.JSONDecodeError:
            reply = core.process(line)
            print(json.dumps({"text": reply}, ensure_ascii=False))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
            sys.stdout.flush()


# ── 入口 ──────────────────────────────

def load_config(path: str) -> dict:
    """加载 YAML 配置"""
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Aris V10 运行时")
    parser.add_argument("--input", "-i", help="单条消息处理")
    parser.add_argument("--bridge", "-b", action="store_true", help="桥接模式")
    parser.add_argument("--stats", "-s", action="store_true", help="显示统计")
    parser.add_argument("--config", "-c", help="YAML 配置文件")
    args = parser.parse_args()

    # 加载配置
    config = {}
    if args.config and Path(args.config).exists():
        config = load_config(args.config)

    # 创建核心
    core = ArisCore(config)

    # 显示统计
    if args.stats:
        print(core.get_summary())
        return

    # 单条模式
    if args.input:
        single_mode(core, args.input)
        return

    # 桥接模式
    if args.bridge:
        bridge_mode(core)
        return

    # REPL 模式 (默认)
    repl_mode(core)


if __name__ == "__main__":
    main()

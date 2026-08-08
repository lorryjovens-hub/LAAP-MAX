"""
LAAP CodexAgent Demo
展示代码 Agent 的工具和能力
"""
import os
import sys
from pathlib import Path

# 运行时推导 LAAP 项目根目录：优先使用环境变量，否则回退到本文件父目录的父目录
LAAP_ROOT = os.environ.get("LAAP_ROOT", str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, LAAP_ROOT)
from laap.agent.codex import CodexAgent


def main():
    print("=" * 50)
    print("LAAP CodexAgent Demo")
    print("=" * 50)

    agent = CodexAgent()
    print(f"\nAgent [{agent.id[:8]}]")
    print(f"工具总数: {agent.tool_registry.count}")
    print(f"工具类别: {agent.tool_registry.categories}")

    print("\n注册的工具:")
    for t in agent.tool_registry.list():
        print(f"  {t.name:22s} [{t.category:10s}] {t.description[:40]}")


if __name__ == "__main__":
    main()

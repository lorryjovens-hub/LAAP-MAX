"""LAAP standalone agent end-to-end demo.

Demonstrates three one-shot intents routed through the StandaloneAgent:
  1. Read a file (read README.md)
  2. Search the codebase (search TODO)
  3. Run a shell command (run command echo hello)

Run with: python demos/standalone_agent_demo.py
"""

from __future__ import annotations

import asyncio
import logging

from laap.llm.engine import MockLLMEngine
from laap.standalone.agent import StandaloneAgent

logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    agent = StandaloneAgent(llm_engine=MockLLMEngine())
    await agent.initialize()

    tasks = [
        "read README.md",
        "search TODO",
        "run echo hello",
    ]

    try:
        for task in tasks:
            print("\n" + "=" * 60)
            print(f"Task: {task}")
            print("=" * 60)

            result = await agent.process(task)
            print(f"Response:\n{result.get('response', '')}")

            summary = agent.session_summary()
            print(
                f"Tokens: {summary['total_tokens']} "
                f"(local {summary['local_tokens']}, remote {summary['remote_tokens']}), "
                f"cost ${summary['estimated_cost_usd']:.4f}"
            )

        print("\n" + "=" * 60)
        print("Final session summary")
        print("=" * 60)
        print(agent.session_summary())
    finally:
        await agent.shutdown()
        print("\nAgent shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())

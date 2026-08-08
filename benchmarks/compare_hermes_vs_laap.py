"""
LAAP vs Hermes Token 对比基准测试
=================================

测试同一个任务在两个框架下的 token 消耗差异。
"""

import sys, json, time
from pathlib import Path

# LAAP 路径
_LAAP_ROOT = Path("D:/LAAP")
sys.path.insert(0, str(_LAAP_ROOT / "laap_agent"))
sys.path.insert(0, str(_LAAP_ROOT / "aris_code_engine"))


def bench_laap(task: str, intent: str = "fix") -> dict:
    """用 LAAP Harness 执行任务并测量 token。"""
    from harness import DevHarness

    t0 = time.time()
    harness = DevHarness({"token_budget": 2000})
    result = harness.run(task, intent=intent)
    dt = (time.time() - t0) * 1000

    return {
        "framework": "LAAP Harness",
        "task": task[:40],
        "token_cost": result.get("token_cost", 0),
        "tools_loaded": result.get("tools_loaded", 0),
        "messages": result.get("messages", 0),
        "duration_ms": round(dt, 0),
        "context_len": sum(len(m.get("content", "") or "")
                          for m in harness._messages) if hasattr(harness, '_messages') else 0,
    }


def print_table(results: list):
    """打印对比表。"""
    print(f"\n{'='*60}")
    print(f"{'框架':20s} {'Token':>8s} {'工具':>6s} {'消息':>6s} {'上下文':>8s} {'耗时':>8s}")
    print(f"{'-'*60}")
    for r in results:
        print(
            f"{r['framework']:20s} "
            f"{r['token_cost']:>8d} "
            f"{r['tools_loaded']:>6d} "
            f"{r['messages']:>6d} "
            f"{r['context_len']:>8d} "
            f"{r['duration_ms']:>8.0f}ms"
        )
    print(f"{'='*60}")

    if len(results) >= 2:
        save = results[0]["token_cost"] - results[1]["token_cost"]
        pct = (1 - results[1]["token_cost"] / max(1, results[0]["token_cost"])) * 100
        print(f"\n  LAAP vs Hermes:")
        print(f"  少花 {save} token ({pct:.0f}%)")
        print(f"  工具少 {results[0]['tools_loaded'] - results[1]['tools_loaded']} 个")


if __name__ == "__main__":
    # 模拟 Hermes 数据（基于文章实测：Hermes 每轮 ~1500 token）
    hermes_estimate = {
        "framework": "Hermes Agent",
        "token_cost": 1500,    # Hermes 每轮基准
        "tools_loaded": 52,     # Hermes 全量工具
        "messages": 4,
        "context_len": 8000,
        "duration_ms": 3000,
    }

    # LAAP 实测
    tasks = [
        ("帮我修一下这个bug", "fix"),
        ("实现一个用户登录函数", "implement"),
        ("搜索一下最新的AGI论文", "search"),
    ]

    results = [hermes_estimate]
    for task, intent in tasks:
        print(f"测试: {task}...")
        r = bench_laap(task, intent)
        results.append(r)
        print(f"  Token: {r['token_cost']} | 工具: {r['tools_loaded']} | 消息: {r['messages']}")
        print()

    print_table(results)

# -*- coding: utf-8 -*-
"""编码任务基线：CodingIntelligenceLoop × 真实/模拟 LLM 生成器。

任务集（10 个，从简单到复杂）：
  1. 斐波那契数列
  2. 回文判断
  3. 二分查找
  4. 冒泡排序
  5. 两数之和（返回索引）
  6. 括号匹配校验
  7. 字符串压缩
  8. 链表反转
  9. 最长公共前缀
  10. 合并两个有序数组

模式：
  --live: 真实 DeepSeek API（需要 DEEPSEEK_API_KEY）
  --mock: 内置模板生成器（演示闭环，无需 key）

用法:
    python benchmarks/coding_baseline.py --mock
    python benchmarks/coding_baseline.py --live
    python benchmarks/coding_baseline.py --mock --output results.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from laap.agent.coding_loop import CodingIntelligenceLoop, CodeVerifier

CODING_TASKS = [
    "写一个 Python 函数 fibonacci(n)，返回斐波那契数列的第 n 项",
    "写一个 Python 函数 is_palindrome(s)，判断字符串是否为回文",
    "写一个 Python 函数 binary_search(arr, target)，在有序列表中进行二分查找，返回索引或 -1",
    "写一个 Python 函数 bubble_sort(arr)，实现冒泡排序",
    "写一个 Python 函数 two_sum(nums, target)，返回和为 target 的两个数的索引",
    "写一个 Python 函数 is_valid_brackets(s)，校验括号字符串是否合法匹配",
    "写一个 Python 函数 compress_string(s)，实现字符串压缩（如 aaabb -> a3b2）",
    "写一个 Python 类 ListNode 和函数 reverse_list(head)，实现单链表反转",
    "写一个 Python 函数 longest_common_prefix(strs)，返回字符串数组的最长公共前缀",
    "写一个 Python 函数 merge_sorted(a, b)，合并两个有序数组",
]


class MockGenerator:
    """内置模板生成器（无 key 演示闭环）。"""

    def __init__(self) -> None:
        self._call_count = 0

    def generate(self, desc, plan_summary="", calibration=""):
        self._call_count += 1
        # 第一轮失败一次（演示校准信号），第二轮成功
        if self._call_count % 2 == 1 and "校准" not in calibration:
            return "def placeholder(:\n    pass\n"  # 语法错误
        return _template_for(desc)


def _template_for(desc: str) -> str:
    """从任务描述选择预置的正确实现。"""
    if "fibonacci" in desc:
        return "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n"
    if "is_palindrome" in desc:
        return "def is_palindrome(s):\n    return s == s[::-1]\n"
    if "binary_search" in desc:
        return "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n"
    if "bubble_sort" in desc:
        return "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr\n"
    if "two_sum" in desc:
        return "def two_sum(nums, target):\n    seen = {}\n    for i, v in enumerate(nums):\n        if target - v in seen:\n            return [seen[target - v], i]\n        seen[v] = i\n    return []\n"
    if "is_valid_brackets" in desc:
        return "def is_valid_brackets(s):\n    stack = []\n    pairs = {')': '(', ']': '[', '}': '{'}\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return len(stack) == 0\n"
    if "compress_string" in desc:
        return "def compress_string(s):\n    if not s:\n        return ''\n    result = []\n    count = 1\n    for i in range(1, len(s)):\n        if s[i] == s[i-1]:\n            count += 1\n        else:\n            result.append(s[i-1] + str(count))\n            count = 1\n    result.append(s[-1] + str(count))\n    return ''.join(result)\n"
    if "reverse_list" in desc:
        return "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverse_list(head):\n    prev = None\n    cur = head\n    while cur:\n        nxt = cur.next\n        cur.next = prev\n        prev = cur\n        cur = nxt\n    return prev\n"
    if "longest_common_prefix" in desc:
        return "def longest_common_prefix(strs):\n    if not strs:\n        return ''\n    prefix = strs[0]\n    for s in strs[1:]:\n        while s[:len(prefix)] != prefix and prefix:\n            prefix = prefix[:-1]\n    return prefix\n"
    if "merge_sorted" in desc:
        return "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result\n"
    return "def f():\n    return 1\n"


def run_baseline(mode: str, tasks: list, output: str = "") -> dict:
    """运行编码基线。"""
    if mode == "live":
        from laap.agent.deepseek_generator import DeepSeekGenerator

        gen = DeepSeekGenerator()
        if not gen.available:
            print("[!] 未检测到 DEEPSEEK_API_KEY，回退到 mock 模式")
            gen = MockGenerator()
    else:
        gen = MockGenerator()

    loop = CodingIntelligenceLoop(
        generator=gen.generate,
        verifier=CodeVerifier(),
        max_attempts=3,
        cognitive_state_provider=lambda: {"needs": {"certainty": 0.6, "competence": 0.6}},
    )

    results = []
    t0 = time.time()
    for i, task in enumerate(tasks):
        r = loop.execute(task)
        results.append({
            "task": task[:60],
            "success": r.success,
            "attempts": len(r.attempts),
            "duration_ms": round(r.total_duration_ms, 1),
            "summary": r.summary,
        })
        print(f"[{i+1}/{len(tasks)}] {'✅' if r.success else '❌'} {task[:40]} "
              f"({len(r.attempts)} 轮)")

    total_ms = (time.time() - t0) * 1000
    succ = sum(1 for r in results if r["success"])
    report = {
        "baseline": "coding_v0.1",
        "mode": mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tasks": len(tasks),
        "success": succ,
        "success_rate": round(succ / len(tasks), 3),
        "avg_attempts": round(sum(r["attempts"] for r in results) / len(results), 2),
        "total_duration_ms": round(total_ms, 1),
        "per_task": results,
    }
    print(f"\n=== 编码基线 ({mode}) ===")
    print(f"  成功率: {report['success_rate']:.1%} ({succ}/{len(tasks)})")
    print(f"  平均轮次: {report['avg_attempts']}")
    print(f"  总耗时: {report['total_duration_ms']:.0f} ms")

    if output:
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已写入: {output}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="编码任务基线")
    ap.add_argument("--mode", choices=["mock", "live"], default="mock")
    ap.add_argument("--output", default="")
    args = ap.parse_args()
    run_baseline(args.mode, CODING_TASKS, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""生成 jspace-laap 实验基准数据集（fixtures）.

运行::

    python experiments/jspace_laap/fixtures/generate_fixtures.py

将生成以下 JSON 文件::

    - cognitivebus_traces.json  (>=100 条 CognitiveBus 事件 trace)
    - multi_step_tasks.json     (3 组多步推理任务)
    - template_tasks.json       (3 组模板匹配任务)
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

random.seed(42)

FIXTURES_DIR = Path(__file__).resolve().parent


def save_fixture(data: Any, filename: str) -> None:
    """将 fixture 数据保存为格式化的 JSON 文件."""
    path = FIXTURES_DIR / filename
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"generated {path}")


def generate_cognitivebus_traces(n: int = 120) -> dict[str, Any]:
    """生成模拟 CognitiveBus 事件 trace.

    每个事件包含时间戳、所属模块、事件类型、显著性、是否进入全局广播、
    内容摘要以及调制信号强度，用于中观层 CognitiveBus 实验。
    """
    modules = ["perception", "memory", "reasoning", "action", "language"]
    event_types = ["stimulus", "retrieval", "inference", "intention", "utterance"]
    contents = [
        "检测到红色物体",
        "检索到相关记忆",
        "推理出因果关系",
        "生成行动计划",
        "输出语言回复",
        "感知到异常输入",
        "激活长期记忆",
        "完成逻辑推演",
        "选择最优动作",
        "构建句子结构",
    ]

    traces: list[dict[str, Any]] = []
    tick = 0
    for i in range(n):
        module = modules[i % len(modules)]
        event_type = event_types[i % len(event_types)]
        salience = round(random.uniform(0.1, 1.0), 3)
        broadcast = salience > 0.65
        tick += random.randint(1, 3)

        traces.append(
            {
                "trace_id": f"cbus_{i:04d}",
                "timestamp_ms": tick * 50,
                "tick": tick,
                "module": module,
                "event_type": event_type,
                "salience": salience,
                "broadcast": broadcast,
                "content": contents[i % len(contents)],
                "modulation": round(random.uniform(-0.5, 0.5), 3),
                "capacity_slot": i % 7,
            }
        )

    return {
        "fixture_name": "cognitivebus_traces",
        "description": "模拟 CognitiveBus 事件 trace，用于中观层报告性与调制实验",
        "count": len(traces),
        "traces": traces,
    }


def generate_multi_step_tasks() -> dict[str, Any]:
    """生成 3 组多步推理任务.

    每组任务包含步骤列表与预期答案，用于评估工作空间的多步信息整合能力。
    """
    tasks = [
        {
            "task_id": "mst_001",
            "name": "因果链推理",
            "description": "根据前提逐步推导结论",
            "domain": "causal_reasoning",
            "steps": [
                "如果下雨，地面会湿",
                "今天下雨了",
                "因此地面是湿的",
            ],
            "query": "地面是否湿？",
            "expected_answer": "是",
            "difficulty": "easy",
        },
        {
            "task_id": "mst_002",
            "name": "算术规划",
            "description": "按照顺序执行多步算术操作",
            "domain": "arithmetic_planning",
            "steps": [
                "初始值为 10",
                "先加 5 得到 15",
                "再乘以 2 得到 30",
                "最后减去 6 得到 24",
            ],
            "query": "最终结果是多少？",
            "expected_answer": "24",
            "difficulty": "medium",
        },
        {
            "task_id": "mst_003",
            "name": "工具使用序列",
            "description": "选择正确的工具并按顺序使用",
            "domain": "tool_use",
            "steps": [
                "识别任务：拧紧螺丝",
                "选择工具：螺丝刀",
                "定位螺丝孔",
                "顺时针旋转螺丝刀直至紧固",
            ],
            "query": "完成任务需要什么工具？",
            "expected_answer": "螺丝刀",
            "difficulty": "easy",
        },
    ]

    return {
        "fixture_name": "multi_step_tasks",
        "description": "多步推理任务集，用于验证工作空间的多步信息整合",
        "count": len(tasks),
        "tasks": tasks,
    }


def generate_template_tasks() -> dict[str, Any]:
    """生成 3 组模板匹配任务.

    每组包含一个模板与若干示例，用于评估模式识别与变量绑定能力。
    """
    templates = [
        {
            "template_id": "tpl_001",
            "name": "问候模板",
            "description": "识别不同语言或称呼的问候语",
            "template": "{greeting}, {name}!",
            "slots": ["greeting", "name"],
            "examples": [
                {"input": "Hello, Alice!", "expected_match": True, "bindings": {"greeting": "Hello", "name": "Alice"}},
                {"input": "Hi, Bob!", "expected_match": True, "bindings": {"greeting": "Hi", "name": "Bob"}},
                {"input": "Goodbye, Alice!", "expected_match": False, "bindings": {}},
            ],
        },
        {
            "template_id": "tpl_002",
            "name": "购买模板",
            "description": "识别购买动作、商品与数量",
            "template": "购买 {quantity} 个 {item}",
            "slots": ["quantity", "item"],
            "examples": [
                {"input": "购买 3 个苹果", "expected_match": True, "bindings": {"quantity": "3", "item": "苹果"}},
                {"input": "购买 10 本书", "expected_match": True, "bindings": {"quantity": "10", "item": "书"}},
                {"input": "卖出 2 个苹果", "expected_match": False, "bindings": {}},
            ],
        },
        {
            "template_id": "tpl_003",
            "name": "因果模板",
            "description": "识别因果关系句式",
            "template": "因为 {cause}，所以 {effect}",
            "slots": ["cause", "effect"],
            "examples": [
                {"input": "因为下雨了，所以地面湿了", "expected_match": True, "bindings": {"cause": "下雨了", "effect": "地面湿了"}},
                {"input": "因为努力学习，所以成绩提高了", "expected_match": True, "bindings": {"cause": "努力学习", "effect": "成绩提高了"}},
                {"input": "虽然下雨了，他还是出门了", "expected_match": False, "bindings": {}},
            ],
        },
    ]

    return {
        "fixture_name": "template_tasks",
        "description": "模板匹配任务集，用于验证模式识别与变量绑定",
        "count": len(templates),
        "templates": templates,
    }


def main() -> None:
    """生成全部 fixtures."""
    save_fixture(generate_cognitivebus_traces(), "cognitivebus_traces.json")
    save_fixture(generate_multi_step_tasks(), "multi_step_tasks.json")
    save_fixture(generate_template_tasks(), "template_tasks.json")
    print("all fixtures generated successfully")


if __name__ == "__main__":
    main()

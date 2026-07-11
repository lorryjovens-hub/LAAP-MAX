"""LAAP Harness 真实 A/B 测试"""
import sys, os, json, time
from pathlib import Path

LAAP_ROOT = Path("D:/LAAP")
sys.path.insert(0, str(LAAP_ROOT))
sys.path.insert(0, str(LAAP_ROOT / "harness"))

with open(LAAP_ROOT / ".deepseek_key") as f:
    DEEPSEEK_KEY = f.read().strip()

from harness.laap_coding.core.harness import ConsciousnessHarness
harness = ConsciousnessHarness(workdir=str(LAAP_ROOT), token_budget=2000)

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com/v1")

def call_llm(messages, max_tokens=2000):
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat", messages=messages,
            max_tokens=max_tokens, temperature=0.7,
        )
        return {
            "success": True,
            "content": resp.choices[0].message.content,
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
            "latency_ms": round((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

TASKS = [
    {"id": "quicksort",   "desc": "写一个Python函数实现快速排序算法，包含详细注释和测试用例"},
    {"id": "rest_api",    "desc": "用Flask框架设计一个RESTful API用于管理图书信息，包括CRUD操作"},
    {"id": "quantum",     "desc": "用量子计算的基本原理解释什么是量子纠缠，用通俗易懂的语言"},
    {"id": "architecture","desc": "描述一个电商网站的系统架构设计，包括前端、后端、数据库、缓存、CDN"},
    {"id": "react_form",  "desc": "创建一个React登录表单组件，包含表单验证、错误提示和loading状态"},
    {"id": "docker",      "desc": "解释Docker和Kubernetes的区别，以及各自适合什么场景"},
]

GUIDANCE_MAP = {
    "code": "请给出完整可运行的代码实现，包含必要的注释。优先考虑代码的正确性和可读性。",
    "explain": "先给出核心概念，再用通俗语言展开。",
    "design": "给出层次清晰的设计方案，包括组件划分和数据流。",
    "review": "从代码质量、性能、安全性、可维护性四个维度审查。",
    "fix": "先定位问题根因，再给出修复方案。",
    "implement": "按功能需求逐步实现，确保代码可运行。",
    "test": "覆盖正常路径和边界情况的测试用例。",
    "refactor": "保持原有功能不变，优化代码结构和可维护性。",
    "chat": "自然、友好地回应用户。",
}

ALL_RESULTS = []

for task in TASKS:
    ctx = harness.perceive(task["desc"])
    intent = ctx.intent
    keywords = ctx.keywords[:6]
    patterns = ctx.related_patterns[:3]
    guidance = GUIDANCE_MAP.get(intent, "请给出全面准确的回答。")

    # 控制组
    control_msgs = [
        {"role": "system", "content": "你是一个专业的AI助手。请根据用户的问题给出准确、全面的回答。"},
        {"role": "user", "content": task["desc"]}
    ]
    c = call_llm(control_msgs)
    if not c["success"]:
        print(f"[FAIL] {task['id']} control: {c['error']}")
        continue

    # Harness组
    hc = (
        f"【任务分析】\n"
        f"- 意图类别: {intent}\n"
        f"- 关键概念: {', '.join(keywords) if keywords else '待识别'}\n"
        f"- 推荐架构模式: {', '.join(patterns) if patterns else '不适用'}\n"
        f"- 执行引导: {guidance}\n"
    )
    harness_msgs = [
        {"role": "system", "content": f"你是一个具有任务分析能力的AI助手。基于以下分析来精准响应：\n\n{hc}"},
        {"role": "user", "content": task["desc"]}
    ]
    h = call_llm(harness_msgs)
    if not h["success"]:
        print(f"[FAIL] {task['id']} harness: {h['error']}")
        continue

    print(f"[{task['id']}] intent={intent} kw={keywords} | "
          f"纯LLM: in={c['prompt_tokens']} out={c['completion_tokens']} tot={c['total_tokens']} | "
          f"Harness: in={h['prompt_tokens']} out={h['completion_tokens']} tot={h['total_tokens']}")

    ALL_RESULTS.append({
        "id": task["id"], "intent": intent,
        "control": {"input": c["prompt_tokens"], "output": c["completion_tokens"], "total": c["total_tokens"]},
        "harness": {"input": h["prompt_tokens"], "output": h["completion_tokens"], "total": h["total_tokens"]},
    })

# 汇总
print("\n\n" + "="*60)
print("📊 汇总结果")
print("="*60)

if not ALL_RESULTS:
    print("❌ 所有测试均失败")
else:
    ic = sum(r["control"]["input"] for r in ALL_RESULTS)
    ih = sum(r["harness"]["input"] for r in ALL_RESULTS)
    cc = sum(r["control"]["output"] for r in ALL_RESULTS)
    ch = sum(r["harness"]["output"] for r in ALL_RESULTS)
    tc = sum(r["control"]["total"] for r in ALL_RESULTS)
    th = sum(r["harness"]["total"] for r in ALL_RESULTS)

    print(f"\n测试数: {len(ALL_RESULTS)} | 模型: DeepSeek-Chat")
    print(f"{'─'*60}")
    print(f"{'指标':<20} {'纯LLM':<12} {'Harness':<12} {'变化':<16}")
    print(f"{'─'*60}")
    print(f"{'总输入Tokens':<20} {ic:<12} {ih:<12} {ih-ic:+d} ({(ih-ic)/ic*100:+.1f}%)")
    print(f"{'总输出Tokens':<20} {cc:<12} {ch:<12} {ch-cc:+d} ({(ch-cc)/cc*100:+.1f}%)")
    print(f"{'总Tokens':<20} {tc:<12} {th:<12} {th-tc:+d} ({(th-tc)/tc*100:+.1f}%)")
    print(f"{'─'*60}")

    print(f"\n{'─'*60}")
    print(f"{'任务':<16} {'意图':<10} {'纯LLM':<12} {'Harn':<12} {'总变化':<10} {'输出变化'}")
    print(f"{'─'*60}")
    for r in ALL_RESULTS:
        td = r["harness"]["total"] - r["control"]["total"]
        od = r["harness"]["output"] - r["control"]["output"]
        tp = td / r["control"]["total"] * 100
        op = od / r["control"]["output"] * 100
        s = "✅" if td < 0 else "⚠️"
        print(f"{r['id']:<16} {r['intent']:<10} {r['control']['total']:<12} {r['harness']['total']:<12} {s} {tp:+5.1f}%   {op:+5.1f}%")

    print(f"\n{'='*60}")
    input_overhead = (ih - ic) / ic * 100
    output_change = (ch - cc) / cc * 100
    total_change = (th - tc) / tc * 100
    print(f"Harness 输入Token增加: {input_overhead:+.1f}%")
    print(f"Harness 输出Token变化: {output_change:+.1f}%")
    print(f"Harness 总Token变化:   {total_change:+.1f}%")
    print()
    print(f"Harness报告声称: 总降低27.22%, 输出降低46.15%")
    print(f"实测结果:       {total_change:+.1f}%")
    if th < tc:
        print(f"\n✅ 在本次测试中Harness确实减少了token消耗")
    else:
        print(f"\n⚠️ 在本次测试中Harness没有减少token消耗")

    # 保存结果
    result_path = LAAP_ROOT / "_ab_test_results.json"
    with open(result_path, "w") as f:
        json.dump(ALL_RESULTS, f, indent=2)
    print(f"\n结果已保存至: {result_path}")

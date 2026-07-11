"""LAAP Harness 真实 A/B 测试 v3 - 输出到文件"""
import sys, os, json, time, textwrap
from pathlib import Path

LAAP_ROOT = Path("D:/LAAP")
sys.path.insert(0, str(LAAP_ROOT))
sys.path.insert(0, str(LAAP_ROOT / "harness"))

LOG = []
def log(msg):
    LOG.append(msg)
    print(msg)

with open(LAAP_ROOT / ".deepseek_key") as f:
    DEEPSEEK_KEY = f.read().strip()

from harness.laap_coding.core.harness import ConsciousnessHarness
harness = ConsciousnessHarness(workdir=str(LAAP_ROOT), token_budget=2000)
log("✅ ConsciousnessHarness loaded")

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com/v1")

def call_llm(messages, max_tokens=2000):
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat", messages=messages,
            max_tokens=max_tokens, temperature=0.7,
        )
        u = resp.usage
        return {
            "success": True,
            "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "total_tokens": u.total_tokens,
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
    c = call_llm([
        {"role": "system", "content": "你是一个专业的AI助手。请根据用户的问题给出准确、全面的回答。"},
        {"role": "user", "content": task["desc"]}
    ])
    if not c["success"]:
        log(f"[FAIL] {task['id']} control: {c['error']}")
        continue

    # Harness组
    hc = f"【任务分析】\n- 意图类别: {intent}\n- 关键概念: {', '.join(keywords) if keywords else '待识别'}\n- 推荐架构模式: {', '.join(patterns) if patterns else '不适用'}\n- 执行引导: {guidance}\n"
    h = call_llm([
        {"role": "system", "content": f"你是一个具有任务分析能力的AI助手。基于以下分析来精准响应：\n\n{hc}"},
        {"role": "user", "content": task["desc"]}
    ])
    if not h["success"]:
        log(f"[FAIL] {task['id']} harness: {h['error']}")
        continue

    log(f"[{task['id']:<12}] intent={intent:<8} kw={str(keywords):<20} | "
        f"纯LLM: in={c['prompt_tokens']} out={c['completion_tokens']} tot={c['total_tokens']} | "
        f"Harness: in={h['prompt_tokens']} out={h['completion_tokens']} tot={h['total_tokens']}")

    ALL_RESULTS.append({
        "id": task["id"], "intent": intent,
        "control": c, "harness": h,
    })

# 汇总
log("")
log("=" * 66)
log("📊 LAAP Harness A/B 测试 — 最终汇总")
log("=" * 66)

if not ALL_RESULTS:
    log("❌ 所有测试均失败")
else:
    ic = sum(r["control"]["prompt_tokens"] for r in ALL_RESULTS)
    ih = sum(r["harness"]["prompt_tokens"] for r in ALL_RESULTS)
    cc = sum(r["control"]["completion_tokens"] for r in ALL_RESULTS)
    ch = sum(r["harness"]["completion_tokens"] for r in ALL_RESULTS)
    tc = sum(r["control"]["total_tokens"] for r in ALL_RESULTS)
    th = sum(r["harness"]["total_tokens"] for r in ALL_RESULTS)

    log(f"测试任务数: {len(ALL_RESULTS)} | 模型: DeepSeek-Chat")
    log(f"{'─'*66}")
    log(f"{'指标':<22} {'纯LLM':<14} {'Harness':<14} {'变化':<16}")
    log(f"{'─'*66}")
    log(f"{'总输入Tokens':<22} {ic:<14} {ih:<14} {ih-ic:+d} ({(ih-ic)/ic*100:+.1f}%)")
    log(f"{'总输出Tokens':<22} {cc:<14} {ch:<14} {ch-cc:+d} ({(ch-cc)/cc*100:+.1f}%)")
    log(f"{'总Tokens':<22} {tc:<14} {th:<14} {th-tc:+d} ({(th-tc)/tc*100:+.1f}%)")
    log(f"{'─'*66}")

    log(f"\n{'─'*66}")
    log(f"{'任务':<16} {'意图':<10} {'纯LLM总':<10} {'Harn总':<10} {'总变化':<10} {'输出变化':<10}")
    log(f"{'─'*66}")
    for r in ALL_RESULTS:
        td = r["harness"]["total_tokens"] - r["control"]["total_tokens"]
        od = r["harness"]["completion_tokens"] - r["control"]["completion_tokens"]
        tp = td / r["control"]["total_tokens"] * 100
        op = od / r["control"]["completion_tokens"] * 100
        s = "✅" if td < 0 else "⚠️"
        log(f"{r['id']:<16} {r['intent']:<10} {r['control']['total_tokens']:<10} {r['harness']['total_tokens']:<10} {s}{tp:+5.1f}%  {op:+5.1f}%")
    log(f"{'─'*66}")

    log(f"\n{'='*66}")
    input_overhead = (ih - ic) / ic * 100
    output_change = (ch - cc) / cc * 100
    total_change = (th - tc) / tc * 100
    log(f"输入Token变化: {input_overhead:+.1f}%")
    log(f"输出Token变化: {output_change:+.1f}%")
    log(f"总Token变化:   {total_change:+.1f}%")
    log(f"{'='*66}")
    log(f"")
    log(f"Harness报告声称: 总降低27.22%, 输出降低46.15%")
    log(f"")
    if total_change < 0:
        log(f"✅ Harness在本次测试中减少了总Token消耗 ({total_change:+.1f}%)")
    else:
        log(f"⚠️ Harness在本次测试中没有减少总Token消耗 ({total_change:+.1f}%)")

    if output_change < 0:
        log(f"✅ Harness在本次测试中减少了输出Token ({output_change:+.1f}%)")
    else:
        log(f"⚠️ Harness在本次测试中没有减少输出Token ({output_change:+.1f}%)")

    # 保存
    with open(LAAP_ROOT / "_ab_test_results.json", "w") as f:
        json.dump(ALL_RESULTS, f, indent=2)

    # 保存log
    with open(LAAP_ROOT / "_ab_test_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    
    log(f"\n完整数据保存至 _ab_test_results.json 和 _ab_test_log.txt")

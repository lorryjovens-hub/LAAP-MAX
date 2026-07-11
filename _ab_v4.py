"""LAAP Harness A/B 测试 v4 - 提高max_tokens"""
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

def call_llm(messages, max_tokens=4096):
    t0 = time.time()
    resp = client.chat.completions.create(
        model="deepseek-chat", messages=messages,
        max_tokens=max_tokens, temperature=0.7,
    )
    u = resp.usage
    return {
        "prompt_tokens": u.prompt_tokens,
        "completion_tokens": u.completion_tokens,
        "total_tokens": u.total_tokens,
    }

# 只跑3个代表性任务（节省API成本）
TASKS = [
    {"id": "quicksort",  "desc": "写一个Python函数实现快速排序算法，包含详细注释和测试用例"},
    {"id": "quantum",    "desc": "用量子计算的基本原理解释什么是量子纠缠，用通俗易懂的语言"},
    {"id": "docker",     "desc": "解释Docker和Kubernetes的区别，以及各自适合什么场景"},
]

GUIDANCE_MAP = {
    "code": "请给出完整可运行的代码实现，包含必要的注释。优先考虑代码的正确性和可读性。",
    "explain": "请用深入浅出的方式解释，先给出核心概念再展开细节。",
    "design": "请给出层次清晰的设计方案，包括组件划分和数据流。",
    "review": "请从代码质量、性能、安全性、可维护性四个维度审查。",
    "implement": "按功能需求逐步实现，确保代码可运行。",
    "chat": "自然、友好地回应用户。",
}

ALL_RESULTS = []

for task in TASKS:
    ctx = harness.perceive(task["desc"])
    intent = ctx.intent
    keywords = ctx.keywords[:6]
    patterns = ctx.related_patterns[:3]
    guidance = GUIDANCE_MAP.get(intent, "请给出全面准确的回答。")
    
    # 显示Harness分析质量
    print(f"\n=== {task['id']} ===")
    print(f"  实际任务类型: {'代码' if 'python' in task['desc'].lower() or '函数' in task['desc'] or '实现' in task['desc'] else '解释/概念'}")
    print(f"  Harness分类意图: {intent}")
    print(f"  Harness提取关键词: {keywords}")
    print(f"  匹配架构模式: {patterns}")
    
    # 控制组
    c = call_llm([
        {"role": "system", "content": "你是一个专业的AI助手。请根据用户的问题给出准确、全面的回答。"},
        {"role": "user", "content": task["desc"]}
    ], max_tokens=4096)
    
    # Harness组
    hc = (
        f"【任务分析】\n"
        f"- 意图类别: {intent}\n"
        f"- 关键概念: {', '.join(keywords) if keywords else '待识别'}\n"
        f"- 推荐架构模式: {', '.join(patterns) if patterns else '不适用'}\n"
        f"- 执行引导: {guidance}\n"
    )
    h = call_llm([
        {"role": "system", "content": f"你是一个具有任务分析能力的AI助手。基于以下分析来精准响应：\n\n{hc}"},
        {"role": "user", "content": task["desc"]}
    ], max_tokens=4096)
    
    inp_delta = h["prompt_tokens"] - c["prompt_tokens"]
    out_delta = h["completion_tokens"] - c["completion_tokens"]
    tot_delta = h["total_tokens"] - c["total_tokens"]
    
    print(f"  Control:   in={c['prompt_tokens']} out={c['completion_tokens']} tot={c['total_tokens']}")
    print(f"  Harness:   in={h['prompt_tokens']} out={h['completion_tokens']} tot={h['total_tokens']}")
    print(f"  Delta:     in={inp_delta:+d} out={out_delta:+d} tot={tot_delta:+d}")
    
    ALL_RESULTS.append({
        "id": task["id"], "intent": intent,
        "control": c, "harness": h,
    })

print("\n\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)

ic = sum(r["control"]["prompt_tokens"] for r in ALL_RESULTS)
ih = sum(r["harness"]["prompt_tokens"] for r in ALL_RESULTS)
cc = sum(r["control"]["completion_tokens"] for r in ALL_RESULTS)
ch = sum(r["harness"]["completion_tokens"] for r in ALL_RESULTS)
tc = sum(r["control"]["total_tokens"] for r in ALL_RESULTS)
th = sum(r["harness"]["total_tokens"] for r in ALL_RESULTS)

print(f"Tasks: {len(ALL_RESULTS)}")
print(f"")
print(f"Input:  {ic} -> {ih}  ({ih-ic:+d}, {(ih-ic)/ic*100:+.1f}%)")
print(f"Output: {cc} -> {ch}  ({ch-cc:+d}, {(ch-cc)/cc*100:+.1f}%)")
print(f"Total:  {tc} -> {th}  ({th-tc:+d}, {(th-tc)/tc*100:+.1f}%)")
print(f"")
print(f"Harness报告声称: 总降低27.22%, 输出降低46.15%")
print(f"")
if out_delta < 0 and th < tc:
    print("Verdict: TOKEN_REDUCTION_SUPPORTED")
elif out_delta < 0:
    print("Verdict: OUTPUT_REDUCED_BUT_TOTAL_HIGHER (input overhead offsets savings)")
elif th < tc:
    print("Verdict: TOTAL_REDUCED_BUT_OUTPUT_SAME")
else:
    print("Verdict: NO_TOKEN_REDUCTION_OBSERVED")

# 保存
with open(LAAP_ROOT / "_ab_test_v4_results.json", "w") as f:
    json.dump(ALL_RESULTS, f, indent=2)

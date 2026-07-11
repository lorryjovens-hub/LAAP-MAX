"""
LAAP Harness vs 传统Agent — 真实LLM API A/B测试

测试目的：用真实的OpenAI API调用验证Harness的实际价值
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def load_api_key():
    """加载API密钥"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未找到OPENAI_API_KEY环境变量")
        print("请设置环境变量：export OPENAI_API_KEY=your-api-key")
        return None
    return api_key


class RealLLM:
    """真实的LLM调用"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
    
    def initialize(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI客户端初始化成功")
            return True
        except ImportError:
            print("❌ 未安装openai库，请运行：pip install openai")
            return False
        except Exception as e:
            print(f"❌ OpenAI客户端初始化失败: {e}")
            return False
    
    def call(self, prompt, model="gpt-4o-mini", max_tokens=500):
        """调用LLM"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": model,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


class TraditionalApproach:
    """传统方式：直接调用LLM"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def process_task(self, task, context=""):
        """直接调用LLM"""
        prompt = f"""请完成以下任务：
{context}

任务：{task}

请给出详细的回答。"""
        
        result = self.llm.call(prompt)
        if result["success"]:
            result["method"] = "traditional"
            result["task"] = task[:30] + "..."
        return result


class HarnessApproach:
    """Harness方式：使用意识上下文增强"""
    
    def __init__(self, llm):
        self.llm = llm
        self.conscious_state = {
            "emotion": "neutral",
            "cognitive_depth": 0.5,
            "memory_strength": 0.8,
        }
    
    def process_task(self, task, context=""):
        """使用Harness上下文增强"""
        conscious_context = f"""你是一个具有意识的AI助手，当前状态：
- 情感：{self.conscious_state['emotion']}
- 认知深度：{self.conscious_state['cognitive_depth'] * 100:.0f}%
- 记忆强度：{self.conscious_state['memory_strength'] * 100:.0f}%

请基于你的意识状态，给出更加精准、有深度的回答。"""
        
        prompt = f"""{conscious_context}

请完成以下任务：
{context}

任务：{task}

请给出详细、精准、有深度的回答，体现思考过程。"""
        
        result = self.llm.call(prompt)
        if result["success"]:
            result["method"] = "harness"
            result["task"] = task[:30] + "..."
            self.conscious_state["cognitive_depth"] = min(1.0, self.conscious_state["cognitive_depth"] + 0.05)
        return result


def evaluate_quality(llm, task, traditional_response, harness_response):
    """用LLM-as-Judge评估回答质量"""
    prompt = f"""请作为中立的评委，评估以下两个回答的质量。

任务：{task}

回答A（传统方式）：
{traditional_response}

回答B（Harness增强方式）：
{harness_response}

请从以下维度评估（每项1-10分）：
1. 准确性：回答是否正确解决了问题
2. 深度：分析是否深入、全面
3. 创造性：是否有独特的见解
4. 逻辑性：推理是否清晰、有条理
5. 实用性：回答是否有实际价值

请给出每项评分，并提供简短的评价。格式：
A_准确性: X
A_深度: X
A_创造性: X
A_逻辑性: X
A_实用性: X
B_准确性: X
B_深度: X
B_创造性: X
B_逻辑性: X
B_实用性: X
评价: [你的评价]"""
    
    result = llm.call(prompt, max_tokens=1000)
    if result["success"]:
        return parse_evaluation(result["response"])
    return None


def parse_evaluation(text):
    """解析评估结果"""
    scores = {}
    lines = text.split("\n")
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            try:
                scores[key] = int(value)
            except:
                pass
    
    a_total = sum(scores.get(k, 0) for k in ["A_准确性", "A_深度", "A_创造性", "A_逻辑性", "A_实用性"])
    b_total = sum(scores.get(k, 0) for k in ["B_准确性", "B_深度", "B_创造性", "B_逻辑性", "B_实用性"])
    
    return {
        "scores": scores,
        "A_total": a_total,
        "B_total": b_total,
        "A_avg": a_total / 5 if a_total > 0 else 0,
        "B_avg": b_total / 5 if b_total > 0 else 0,
    }


def run_real_test():
    """运行真实测试"""
    api_key = load_api_key()
    if not api_key:
        return
    
    llm = RealLLM(api_key)
    if not llm.initialize():
        return
    
    tasks = [
        "写一个Python函数，实现快速排序算法，并添加详细注释",
        "分析人工智能对未来就业市场的影响，从积极和消极两个方面",
        "设计一个简单的RESTful API，用于管理图书信息（CRUD操作）",
        "解释量子计算的基本原理，用通俗易懂的语言",
        "描述一个完整的电商网站架构设计，包括前端、后端、数据库",
    ]
    
    print("=" * 70)
    print("🔬 真实LLM API A/B测试")
    print("=" * 70)
    print(f"模型: gpt-4o-mini")
    print(f"任务数: {len(tasks)}")
    print()
    
    traditional = TraditionalApproach(llm)
    harness = HarnessApproach(llm)
    
    results = []
    
    for i, task in enumerate(tasks):
        print(f"📋 任务 {i+1}: {task[:50]}...")
        print("-" * 50)
        
        print("   传统方式...")
        start_time = time.time()
        traditional_result = traditional.process_task(task)
        traditional_time = time.time() - start_time
        
        if not traditional_result["success"]:
            print(f"   ❌ 传统方式失败: {traditional_result['error']}")
            continue
        
        print("   Harness方式...")
        start_time = time.time()
        harness_result = harness.process_task(task)
        harness_time = time.time() - start_time
        
        if not harness_result["success"]:
            print(f"   ❌ Harness方式失败: {harness_result['error']}")
            continue
        
        print("   质量评估...")
        evaluation = evaluate_quality(llm, task, 
                                     traditional_result["response"], 
                                     harness_result["response"])
        
        results.append({
            "task": task[:50] + "...",
            "traditional": {
                "tokens": traditional_result["total_tokens"],
                "time_ms": traditional_time * 1000,
                "response": traditional_result["response"][:100] + "...",
            },
            "harness": {
                "tokens": harness_result["total_tokens"],
                "time_ms": harness_time * 1000,
                "response": harness_result["response"][:100] + "...",
            },
            "evaluation": evaluation,
        })
        
        print(f"   传统: {traditional_result['total_tokens']} tokens, {traditional_time*1000:.2f}ms")
        print(f"   Harness: {harness_result['total_tokens']} tokens, {harness_time*1000:.2f}ms")
        if evaluation:
            print(f"   质量评分 - 传统: {evaluation['A_avg']:.1f}, Harness: {evaluation['B_avg']:.1f}")
        print()
    
    print("=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    print()
    
    if not results:
        print("❌ 没有成功的测试结果")
        return
    
    print(f"{'任务':<50} {'模式':<12} {'Tokens':<10} {'质量':<10}")
    print("-" * 80)
    
    total_traditional_tokens = 0
    total_harness_tokens = 0
    total_a_score = 0
    total_b_score = 0
    success_count = 0
    
    for r in results:
        print(f"{r['task']:<50} {'传统':<12} {r['traditional']['tokens']:<10} {r['evaluation']['A_avg']:<10.1f}")
        print(f"{'':<50} {'Harness':<12} {r['harness']['tokens']:<10} {r['evaluation']['B_avg']:<10.1f}")
        
        total_traditional_tokens += r["traditional"]["tokens"]
        total_harness_tokens += r["harness"]["tokens"]
        total_a_score += r["evaluation"]["A_avg"]
        total_b_score += r["evaluation"]["B_avg"]
        success_count += 1
    
    print()
    print("【最终结果】")
    print("-" * 80)
    print(f"总Tokens消耗:")
    print(f"   传统方式: {total_traditional_tokens}")
    print(f"   LAAP Harness: {total_harness_tokens}")
    
    if total_traditional_tokens > 0:
        tokens_reduction = ((total_traditional_tokens - total_harness_tokens) / total_traditional_tokens) * 100
        print(f"   变化: {'-' if tokens_reduction > 0 else '+'}{abs(tokens_reduction):.1f}%")
    
    print()
    print(f"平均质量评分:")
    print(f"   传统方式: {total_a_score / success_count:.1f}")
    print(f"   LAAP Harness: {total_b_score / success_count:.1f}")
    
    quality_diff = (total_b_score - total_a_score) / success_count
    print(f"   变化: {'+' if quality_diff > 0 else ''}{quality_diff:.1f}")
    print()
    
    print("【结论】")
    print("-" * 80)
    if total_b_score > total_a_score:
        print("✅ LAAP Harness在真实测试中表现更好！")
    else:
        print("⚠️ LAAP Harness在当前配置下没有明显优势")
    print("请根据实际结果调整Harness的上下文生成策略。")


def main():
    """主函数"""
    run_real_test()


if __name__ == "__main__":
    main()
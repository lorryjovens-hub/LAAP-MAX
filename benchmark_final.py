"""
LAAP Harness vs Trae — 真实对比测试（最终版）

修复输出显示问题，确保能正确获取和保存内容。
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def call_deepseek(api_key, prompt, system_prompt="", max_tokens=3000):
    """直接调用DeepSeek API"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
        stream=False
    )
    
    content = response.choices[0].message.content
    
    return {
        "success": True,
        "text": content,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }


def extract_html(response_text):
    """提取HTML代码"""
    if "```html" in response_text:
        start = response_text.find("```html") + 7
        end = response_text.find("```", start)
        if end != -1:
            return response_text[start:end].strip()
    elif "<!DOCTYPE" in response_text:
        start = response_text.find("<!DOCTYPE")
        end = response_text.find("</html>") + 7
        if end != -1:
            return response_text[start:end].strip()
    return response_text


def run_traditional_test(api_key, task):
    """传统方式：直接调用LLM"""
    print("📝 传统方式：直接调用DeepSeek")
    start_time = time.time()
    
    result = call_deepseek(api_key, task, max_tokens=3000)
    duration = time.time() - start_time
    
    print(f"✅ 完成!")
    print(f"   Tokens: {result['total_tokens']}")
    print(f"   耗时: {duration:.2f}s")
    print(f"   输出长度: {len(result['text'])} 字符")
    if len(result['text']) > 0:
        print(f"   输出预览: {result['text'][:150]}...")
    
    return result


def run_harness_test(api_key, task):
    """Harness方式：走完整的LAAP认知链路"""
    print("\n📝 Harness方式：走完整LAAP认知链路")
    start_time = time.time()
    
    from laap.agi.core import AGIAgent
    
    agent = AGIAgent(name="Ao", state_dir=None)
    
    processing_start = time.time()
    interaction_result = agent.process_interaction(
        user_message=task,
        domain="code_generation",
        context={"novelty": 0.7}
    )
    processing_time = time.time() - processing_start
    
    consciousness_prompt = interaction_result.get("consciousness_prompt_addon", "")
    
    full_prompt = f"""{consciousness_prompt}

{task}"""
    
    llm_start = time.time()
    result = call_deepseek(api_key, full_prompt, max_tokens=3000)
    llm_time = time.time() - llm_start
    
    total_duration = time.time() - start_time
    
    print(f"✅ 完成!")
    print(f"   认知处理时间: {processing_time:.2f}s")
    print(f"   LLM调用时间: {llm_time:.2f}s")
    print(f"   总耗时: {total_duration:.2f}s")
    print(f"   Tokens: {result['total_tokens']}")
    print(f"   意识上下文长度: {len(consciousness_prompt)} 字符")
    print(f"   输出长度: {len(result['text'])} 字符")
    if len(result['text']) > 0:
        print(f"   输出预览: {result['text'][:150]}...")
    
    if consciousness_prompt:
        print(f"\n   意识上下文:")
        print(f"   {consciousness_prompt}")
    
    return result


def main():
    api_key = "sk-276eda66b4da48d6bb0a8149c586e172"
    
    task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面"
    
    print("=" * 60)
    print("🧠 LAAP Harness vs Trae — 真实对比测试")
    print("=" * 60)
    print(f"任务: {task[:50]}...")
    print()
    
    # 方式A：传统方式
    result_a = run_traditional_test(api_key, task)
    
    # 方式B：Harness方式
    result_b = run_harness_test(api_key, task)
    
    # 保存结果
    if result_a["text"]:
        html_a = extract_html(result_a["text"])
        with open("demos/minesweeper_traditional.html", "w", encoding="utf-8") as f:
            f.write(html_a)
        print("\n✅ 传统方式输出已保存: demos/minesweeper_traditional.html")
    
    if result_b["text"]:
        html_b = extract_html(result_b["text"])
        with open("demos/minesweeper_harness.html", "w", encoding="utf-8") as f:
            f.write(html_b)
        print("✅ Harness方式输出已保存: demos/minesweeper_harness.html")
    
    # 输出对比
    if result_a["success"] and result_b["success"]:
        print("\n" + "="*60)
        print("📊 测试结果对比")
        print("="*60)
        print(f"{'指标':<20} {'传统方式':<15} {'Harness方式':<15}")
        print("-"*50)
        print(f"{'总Tokens':<20} {result_a['total_tokens']:<15} {result_b['total_tokens']:<15}")
        print(f"{'Prompt tokens':<20} {result_a['prompt_tokens']:<15} {result_b['prompt_tokens']:<15}")
        print(f"{'Completion tokens':<20} {result_a['completion_tokens']:<15} {result_b['completion_tokens']:<15}")
        print(f"{'输出长度':<20} {len(result_a['text']):<15} {len(result_b['text']):<15}")
        
        tokens_diff = ((result_a['total_tokens'] - result_b['total_tokens']) / result_a['total_tokens']) * 100
        print(f"\nTokens变化: {'-' if tokens_diff > 0 else '+'}{abs(tokens_diff):.1f}%")
        
        # LLM-as-Judge评估
        print("\n🧐 LLM评估质量...")
        eval_prompt = f"""请作为中立的评委，评估以下两个回答的质量。

任务：{task}

回答A（传统方式）：
{result_a['text'][:3000]}

回答B（LAAP Harness方式）：
{result_b['text'][:3000]}

请从以下维度评估（每项1-10分）：
1. 完整性：代码是否完整可运行
2. 3D效果：Three.js实现的3D视觉效果
3. 游戏逻辑：扫雷游戏逻辑是否正确
4. UI设计：界面是否美观、响应式
5. 代码质量：代码结构、注释、可读性

格式：
A_完整性: X
A_3D效果: X
A_游戏逻辑: X
A_UI设计: X
A_代码质量: X
B_完整性: X
B_3D效果: X
B_游戏逻辑: X
B_UI设计: X
B_代码质量: X
评价: [简短评价]"""
        
        eval_result = call_deepseek(api_key, eval_prompt, max_tokens=800)
        if eval_result["success"]:
            print("\n" + "="*60)
            print("🎯 LLM评估结果")
            print("="*60)
            print(eval_result["text"])


if __name__ == "__main__":
    main()
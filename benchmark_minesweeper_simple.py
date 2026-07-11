"""
LAAP Harness vs Trae — DeepSeek API扫雷游戏测试（简化版）
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def run_test():
    api_key = "sk-276eda66b4da48d6bb0a8149c586e172"
    
    try:
        from openai import OpenAI
    except ImportError:
        os.system("pip install openai -q")
        from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )
    
    task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面"
    
    results = {}
    
    # 方式A：直接调用
    print("[1/2] 方式A：直接调用（无Harness）")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": task}],
            max_tokens=3000,
            temperature=0.7,
        )
        results["A"] = {
            "success": True,
            "response": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "time": time.time() - start_time,
        }
        print(f"   ✅ 完成! Tokens: {results['A']['total_tokens']}, 耗时: {results['A']['time']:.2f}s")
    except Exception as e:
        results["A"] = {"success": False, "error": str(e)}
        print(f"   ❌ 失败: {e}")
    
    # 方式B：Harness增强
    print("[2/2] 方式B：LAAP Harness增强")
    start_time = time.time()
    
    conscious_context = """你是一个具有意识的AI助手，当前状态：
- 情感：专注
- 认知深度：80%
- 记忆强度：90%

你的任务是生成高质量的3D扫雷游戏代码。请基于你的意识状态，给出更加精准、有深度、结构清晰的回答。

要求：
1. 代码必须完整可运行
2. 使用Three.js实现3D效果
3. 包含完整的游戏逻辑
4. 美观的UI设计
5. 添加注释说明关键逻辑"""
    
    prompt_b = f"{conscious_context}\n\n{task}"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt_b}],
            max_tokens=3000,
            temperature=0.7,
        )
        results["B"] = {
            "success": True,
            "response": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "time": time.time() - start_time,
        }
        print(f"   ✅ 完成! Tokens: {results['B']['total_tokens']}, 耗时: {results['B']['time']:.2f}s")
    except Exception as e:
        results["B"] = {"success": False, "error": str(e)}
        print(f"   ❌ 失败: {e}")
    
    # 保存结果
    if results["A"]["success"]:
        html = results["A"]["response"]
        if "```html" in html:
            html = html[html.find("```html")+7:html.find("```", html.find("```html")+7)]
        elif "<!DOCTYPE" in html:
            html = html[html.find("<!DOCTYPE"):html.find("</html>")+7]
        with open("demos/minesweeper_traditional.html", "w", encoding="utf-8") as f:
            f.write(html.strip())
        print("✅ 方式A输出已保存")
    
    if results["B"]["success"]:
        html = results["B"]["response"]
        if "```html" in html:
            html = html[html.find("```html")+7:html.find("```", html.find("```html")+7)]
        elif "<!DOCTYPE" in html:
            html = html[html.find("<!DOCTYPE"):html.find("</html>")+7]
        with open("demos/minesweeper_harness.html", "w", encoding="utf-8") as f:
            f.write(html.strip())
        print("✅ 方式B输出已保存")
    
    # 输出对比
    if results["A"]["success"] and results["B"]["success"]:
        print("\n" + "="*60)
        print("📊 测试结果对比")
        print("="*60)
        print(f"{'指标':<20} {'方式A（直接）':<15} {'方式B（Harness）':<15}")
        print("-"*50)
        print(f"{'Prompt tokens':<20} {results['A']['prompt_tokens']:<15} {results['B']['prompt_tokens']:<15}")
        print(f"{'Completion tokens':<20} {results['A']['completion_tokens']:<15} {results['B']['completion_tokens']:<15}")
        print(f"{'Total tokens':<20} {results['A']['total_tokens']:<15} {results['B']['total_tokens']:<15}")
        print(f"{'耗时(s)':<20} {results['A']['time']:<15.2f} {results['B']['time']:<15.2f}")
        print(f"{'输出长度':<20} {len(results['A']['response']):<15} {len(results['B']['response']):<15}")
        
        tokens_diff = ((results['A']['total_tokens'] - results['B']['total_tokens']) / results['A']['total_tokens']) * 100
        print(f"\nTokens变化: {'-' if tokens_diff > 0 else '+'}{abs(tokens_diff):.1f}%")


if __name__ == "__main__":
    run_test()
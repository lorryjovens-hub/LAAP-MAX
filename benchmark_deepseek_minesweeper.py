"""
LAAP Harness vs Trae — DeepSeek API扫雷游戏测试
使用 deepseek-v4-flash 模型
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def call_deepseek(api_key, prompt, model="deepseek-v4-flash", max_tokens=3000):
    """调用DeepSeek API"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
        stream=False
    )
    
    return {
        "response": response.choices[0].message.content,
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


def main():
    api_key = "sk-276eda66b4da48d6bb0a8149c586e172"
    
    task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面"
    
    print("=" * 60)
    print("🚀 DeepSeek API 扫雷游戏 A/B测试")
    print("=" * 60)
    print()
    
    # 方式A：直接调用
    print("[1/2] 方式A：直接调用（无Harness）")
    print("-" * 50)
    start_time = time.time()
    try:
        result_a = call_deepseek(api_key, task)
        time_a = time.time() - start_time
        print(f"✅ 完成! Tokens: {result_a['total_tokens']}, 耗时: {time_a:.2f}s")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return
    
    # 方式B：Harness增强
    print("\n[2/2] 方式B：LAAP Harness增强")
    print("-" * 50)
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
        result_b = call_deepseek(api_key, prompt_b)
        time_b = time.time() - start_time
        print(f"✅ 完成! Tokens: {result_b['total_tokens']}, 耗时: {time_b:.2f}s")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return
    
    # 保存HTML文件
    html_a = extract_html(result_a["response"])
    html_b = extract_html(result_b["response"])
    
    with open("demos/minesweeper_traditional.html", "w", encoding="utf-8") as f:
        f.write(html_a)
    print("\n✅ 方式A输出已保存: demos/minesweeper_traditional.html")
    
    with open("demos/minesweeper_harness.html", "w", encoding="utf-8") as f:
        f.write(html_b)
    print("✅ 方式B输出已保存: demos/minesweeper_harness.html")
    
    # 输出对比
    print("\n" + "="*60)
    print("📊 测试结果对比")
    print("="*60)
    print(f"{'指标':<20} {'方式A（直接）':<15} {'方式B（Harness）':<15}")
    print("-"*50)
    print(f"{'Prompt tokens':<20} {result_a['prompt_tokens']:<15} {result_b['prompt_tokens']:<15}")
    print(f"{'Completion tokens':<20} {result_a['completion_tokens']:<15} {result_b['completion_tokens']:<15}")
    print(f"{'Total tokens':<20} {result_a['total_tokens']:<15} {result_b['total_tokens']:<15}")
    print(f"{'耗时(s)':<20} {time_a:<15.2f} {time_b:<15.2f}")
    print(f"{'输出长度':<20} {len(result_a['response']):<15} {len(result_b['response']):<15}")
    
    tokens_diff = ((result_a['total_tokens'] - result_b['total_tokens']) / result_a['total_tokens']) * 100
    print(f"\nTokens变化: {'-' if tokens_diff > 0 else '+'}{abs(tokens_diff):.1f}%")


if __name__ == "__main__":
    main()
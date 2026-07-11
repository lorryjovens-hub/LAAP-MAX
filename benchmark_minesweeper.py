"""
LAAP Harness vs Trae — 真实DeepSeek API A/B测试

测试任务：做一款精美3D的扫雷游戏
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class DeepSeekLLM:
    """DeepSeek API调用"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
    
    def initialize(self):
        """初始化DeepSeek客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            print("✅ DeepSeek客户端初始化成功")
            return True
        except ImportError:
            print("❌ 未安装openai库，请运行：pip install openai")
            return False
        except Exception as e:
            print(f"❌ 客户端初始化失败: {e}")
            return False
    
    def call(self, prompt, model="deepseek-chat", max_tokens=3000):
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


def run_ab_test(api_key):
    """运行A/B测试"""
    llm = DeepSeekLLM(api_key)
    if not llm.initialize():
        return None, None
    
    task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面"
    
    print("=" * 70)
    print("🧠 LAAP Harness vs Trae — 真实A/B测试")
    print("=" * 70)
    print(f"任务: {task[:50]}...")
    print()
    
    # 方式A：直接调用（模拟Trae直接运行）
    print("📝 方式A：直接调用（无Harness）")
    print("-" * 50)
    start_time = time.time()
    prompt_a = task
    result_a = llm.call(prompt_a)
    time_a = time.time() - start_time
    
    if not result_a["success"]:
        print(f"❌ 方式A失败: {result_a['error']}")
        return None, None
    
    print(f"✅ 完成!")
    print(f"   耗时: {time_a:.2f}s")
    print(f"   Prompt tokens: {result_a['prompt_tokens']}")
    print(f"   Completion tokens: {result_a['completion_tokens']}")
    print(f"   Total tokens: {result_a['total_tokens']}")
    print(f"   输出长度: {len(result_a['response'])} 字符")
    print()
    
    # 方式B：Harness增强调用
    print("📝 方式B：LAAP Harness增强")
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
    
    prompt_b = f"""{conscious_context}

{task}"""
    
    result_b = llm.call(prompt_b)
    time_b = time.time() - start_time
    
    if not result_b["success"]:
        print(f"❌ 方式B失败: {result_b['error']}")
        return None, None
    
    print(f"✅ 完成!")
    print(f"   耗时: {time_b:.2f}s")
    print(f"   Prompt tokens: {result_b['prompt_tokens']}")
    print(f"   Completion tokens: {result_b['completion_tokens']}")
    print(f"   Total tokens: {result_b['total_tokens']}")
    print(f"   输出长度: {len(result_b['response'])} 字符")
    print()
    
    # 质量评估
    print("📊 质量评估")
    print("-" * 50)
    eval_prompt = f"""请作为中立的评委，评估以下两个回答的质量。

任务：{task}

回答A（直接调用）：
{result_a['response'][:2000]}...

回答B（Harness增强）：
{result_b['response'][:2000]}...

请从以下维度评估（每项1-10分）：
1. 完整性：代码是否完整可运行
2. 3D效果：Three.js实现的3D视觉效果
3. 游戏逻辑：扫雷游戏逻辑是否正确
4. UI设计：界面是否美观、响应式
5. 代码质量：代码结构、注释、可读性

请给出每项评分。格式：
A_完整性: X
A_3D效果: X
A_游戏逻辑: X
A_UI设计: X
A_代码质量: X
B_完整性: X
B_3D效果: X
B_游戏逻辑: X
B_UI设计: X
B_代码质量: X"""
    
    eval_result = llm.call(eval_prompt, max_tokens=500)
    if eval_result["success"]:
        print(f"评估结果:\n{eval_result['response']}")
    
    return result_a, result_b


def extract_html(response_text):
    """从LLM响应中提取HTML代码"""
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
    """主函数"""
    api_key = "sk-276eda66b4da48d6bb0a8149c586e172"
    
    print("=" * 70)
    print("🚀 DeepSeek API A/B测试启动")
    print("=" * 70)
    print()
    
    result_a, result_b = run_ab_test(api_key)
    
    if result_a and result_b:
        print()
        print("=" * 70)
        print("📊 测试结果汇总")
        print("=" * 70)
        print()
        
        print(f"{'指标':<20} {'方式A（直接）':<20} {'方式B（Harness）':<20}")
        print("-" * 60)
        print(f"{'耗时':<20} {result_a['total_tokens']:<20} {result_b['total_tokens']:<20}")
        print(f"{'Prompt tokens':<20} {result_a['prompt_tokens']:<20} {result_b['prompt_tokens']:<20}")
        print(f"{'Completion tokens':<20} {result_a['completion_tokens']:<20} {result_b['completion_tokens']:<20}")
        print(f"{'Total tokens':<20} {result_a['total_tokens']:<20} {result_b['total_tokens']:<20}")
        print(f"{'输出长度':<20} {len(result_a['response']):<20} {len(result_b['response']):<20}")
        print()
        
        tokens_diff = ((result_a['total_tokens'] - result_b['total_tokens']) / result_a['total_tokens']) * 100
        print(f"Tokens变化: {'-' if tokens_diff > 0 else '+'}{abs(tokens_diff):.1f}%")
        print()
        
        # 保存HTML文件
        html_a = extract_html(result_a["response"])
        html_b = extract_html(result_b["response"])
        
        with open("demos/minesweeper_traditional.html", "w", encoding="utf-8") as f:
            f.write(html_a)
        print("✅ 方式A输出已保存: demos/minesweeper_traditional.html")
        
        with open("demos/minesweeper_harness.html", "w", encoding="utf-8") as f:
            f.write(html_b)
        print("✅ 方式B输出已保存: demos/minesweeper_harness.html")
        
        print()
        print("=" * 70)
        print("🎉 测试完成!")
        print("=" * 70)


if __name__ == "__main__":
    main()
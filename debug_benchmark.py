"""
调试最终版测试脚本
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 模拟测试脚本中的调用
task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面"

system_prompt = "You are a helpful assistant."

messages = []
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})
messages.append({"role": "user", "content": task})

print(f"消息列表: {len(messages)} 条")
print(f"第一条消息角色: {messages[0]['role']}")
print(f"第一条消息内容: {messages[0]['content'][:50]}...")
print(f"第二条消息角色: {messages[1]['role']}")
print(f"第二条消息内容长度: {len(messages[1]['content'])}")

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    max_tokens=3000,
    temperature=0.7,
    stream=False
)

content = response.choices[0].message.content
print(f"\n响应内容类型: {type(content)}")
print(f"响应内容长度: {len(content)}")
print(f"响应内容repr: {repr(content[:500])}")
print(f"finish_reason: {response.choices[0].finish_reason}")
print(f"usage: {response.usage}")
"""
测试不同长度prompt的影响
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 测试不同长度的prompt
prompts = [
    "写一个HTML页面",
    "写一个3D扫雷游戏",
    "写一个3D扫雷游戏，使用Three.js",
    "写一个3D扫雷游戏，使用Three.js实现。要求：3D视觉效果，方块要有立体感，点击挖雷，右键标记，计时器和剩余地雷数显示",
    "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现。要求：\n1. 3D视觉效果，方块要有立体感\n2. 点击挖雷，右键标记\n3. 计时器和剩余地雷数显示\n4. 游戏胜利/失败动画\n5. 响应式设计\n6. 美观的UI界面",
]

for i, prompt in enumerate(prompts):
    print(f"\n=== 测试{i+1} ===")
    print(f"Prompt长度: {len(prompt)}")
    print(f"Prompt: {prompt[:50]}...")
    
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000,
        temperature=0.7,
        stream=False
    )
    
    content = response.choices[0].message.content
    print(f"内容长度: {len(content)}")
    print(f"finish_reason: {response.choices[0].finish_reason}")
    print(f"reasoning_tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
    print(f"completion_tokens: {response.usage.completion_tokens}")
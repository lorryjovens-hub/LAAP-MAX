"""
测试不同DeepSeek模型
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

task = "做一款精美3D的扫雷游戏，使用HTML+CSS+JavaScript+Three.js实现"

models = [
    "deepseek-v4-flash",
    "deepseek-v4",
    "deepseek-chat",
    "deepseek-code",
]

for model in models:
    print(f"\n=== 测试模型: {model} ===")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task}
            ],
            max_tokens=3000,
            temperature=0.7,
            stream=False
        )
        
        content = response.choices[0].message.content
        print(f"内容长度: {len(content)}")
        print(f"finish_reason: {response.choices[0].finish_reason}")
        if hasattr(response.usage.completion_tokens_details, 'reasoning_tokens'):
            print(f"reasoning_tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
        print(f"completion_tokens: {response.usage.completion_tokens}")
        if len(content) > 0:
            print(f"内容预览: {content[:100]}...")
    except Exception as e:
        print(f"错误: {e}")
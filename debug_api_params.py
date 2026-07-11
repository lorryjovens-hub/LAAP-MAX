"""
测试DeepSeek API参数调整
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 测试不同参数
test_cases = [
    {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50, "temperature": 0.7},
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello"}], "max_tokens": 50, "temperature": 0.7},
    {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50, "temperature": 0.1},
    {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100, "temperature": 0.7},
    {"messages": [{"role": "user", "content": "Tell me about yourself"}], "max_tokens": 100, "temperature": 0.7},
]

for i, params in enumerate(test_cases):
    print(f"\n=== 测试{i+1} ===")
    print(f"参数: {params}")
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            **params
        )
        content = response.choices[0].message.content
        print(f"内容: {repr(content[:200])}")
        print(f"长度: {len(content)}")
        print(f"tokens: {response.usage.total_tokens}")
        print(f"finish_reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"错误: {e}")
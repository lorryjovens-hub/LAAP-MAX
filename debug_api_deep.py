"""
深入调试DeepSeek API返回问题
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 测试简单请求
print("=== 测试1: 简单请求 ===")
response1 = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "Hello"}
    ],
    max_tokens=50,
    stream=False
)
content1 = response1.choices[0].message.content
print(f"内容: {repr(content1)}")
print(f"长度: {len(content1)}")
print(f"tokens: {response1.usage.total_tokens}")

# 测试中文请求
print("\n=== 测试2: 中文请求 ===")
response2 = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    max_tokens=50,
    stream=False
)
content2 = response2.choices[0].message.content
print(f"内容: {repr(content2)}")
print(f"长度: {len(content2)}")
print(f"tokens: {response2.usage.total_tokens}")

# 测试代码生成请求（短）
print("\n=== 测试3: 代码生成（短） ===")
response3 = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "写一个简单的Hello World程序"}
    ],
    max_tokens=100,
    stream=False
)
content3 = response3.choices[0].message.content
print(f"内容: {repr(content3)}")
print(f"长度: {len(content3)}")
print(f"tokens: {response3.usage.total_tokens}")

# 测试代码生成请求（长）
print("\n=== 测试4: 代码生成（长，3000tokens） ===")
response4 = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "写一个HTML页面"}
    ],
    max_tokens=3000,
    stream=False
)
content4 = response4.choices[0].message.content
print(f"内容类型: {type(content4)}")
print(f"内容: {repr(content4[:200])}")
print(f"长度: {len(content4)}")
print(f"tokens: {response4.usage.total_tokens}")
print(f"finish_reason: {response4.choices[0].finish_reason}")
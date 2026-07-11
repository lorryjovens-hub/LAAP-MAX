"""
调试DeepSeek API返回问题
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, test!"}
    ],
    max_tokens=100,
    stream=False
)

print("=== 响应详情 ===")
print(f"模型: {response.model}")
print(f"对象类型: {type(response)}")
print(f"choices: {response.choices}")
print(f"choices[0]: {response.choices[0]}")
print(f"choices[0].message: {response.choices[0].message}")
print(f"choices[0].message.content: {repr(response.choices[0].message.content)}")
print(f"choices[0].message.role: {response.choices[0].message.role}")
print(f"usage: {response.usage}")
print(f"usage.prompt_tokens: {response.usage.prompt_tokens}")
print(f"usage.completion_tokens: {response.usage.completion_tokens}")
print(f"usage.total_tokens: {response.usage.total_tokens}")
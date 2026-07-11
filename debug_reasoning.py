"""
测试DeepSeek API推理模式问题
"""

import sys
sys.path.insert(0, "D:\\LAAP")

api_key = "sk-276eda66b4da48d6bb0a8149c586e172"

from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

task = "写一个简单的HTML页面"

# 测试不同参数配置
test_cases = [
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": task}], "max_tokens": 3000, "temperature": 0.7},
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": task}], "max_tokens": 3000, "temperature": 0.7, "extra": {"response_format": {"type": "text"}}},
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": task}], "max_tokens": 3000, "temperature": 0, "top_p": 0.9},
    {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": task}], "max_tokens": 3000, "temperature": 0.7, "extra": {"reasoning": False}},
]

for i, params in enumerate(test_cases):
    print(f"\n=== 测试{i+1} ===")
    print(f"参数: {params}")
    try:
        extra = params.pop("extra", {})
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=params["messages"],
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            **extra
        )
        content = response.choices[0].message.content
        print(f"内容长度: {len(content)}")
        print(f"内容预览: {repr(content[:200])}")
        print(f"finish_reason: {response.choices[0].finish_reason}")
        print(f"usage: {response.usage}")
    except Exception as e:
        print(f"错误: {e}")
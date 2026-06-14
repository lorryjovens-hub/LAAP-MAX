"""Add DeepSeek API key to .env"""
import os

key = os.environ.get("DEEPSEEK_API_KEY", "")
if not key:
    print("No DEEPSEEK_API_KEY in environment!")
    exit(1)

path = "D:/hermes-agent-LAAP数字生命版/hermes-agent-LAAP/.env"
with open(path) as f:
    content = f.read()

if "DEEPSEEK_API_KEY" in content:
    print("DEEPSEEK_API_KEY already in .env")
else:
    with open(path, "a") as f:
        f.write(f"\nDEEPSEEK_API_KEY={key}\n")
    print(f"Added DEEPSEEK_API_KEY ({len(key)} chars)")

with open(path) as f:
    print(f"File size: {len(f.read())} bytes")

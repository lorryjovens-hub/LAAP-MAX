"""Check DeepSeek API Key in .env"""
p = open("D:/hermes-agent-LAAP数字生命版/hermes-agent-LAAP/.env").read()
for line in p.split("\n"):
    if "DEEPSEEK" in line:
        print(f"Line: {line[:30]}...")
        if "=" in line:
            key = line.split("=", 1)[1].strip()
            print(f"Key length: {len(key)}")
            print(f"First 8: {key[:8]}")
            print(f"Last 8: {key[-8:]}")
            print(f"Starts with sk-: {key.startswith('sk-')}")

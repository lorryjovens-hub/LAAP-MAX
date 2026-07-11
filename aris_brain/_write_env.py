
import os
key_parts = ["sk-68a", "d577ab6a1", "4699b32a9", "ade107eb513"]
key = "".join(key_parts)
secret = "HWB5wLFUgCuYpgIQynIMphH2hYTwdD4J"

with open(r"D:\LAAP\aris_brain\.env", "w") as f:
    f.write("DEEPSEEK_API_KEY=" + key + "\n")
    f.write("DEEPSEEK_MODEL=deepseek-chat\n")
    f.write("FEISHU_APP_ID=cli_aacce7a16979dbb3\n")
    f.write("FEISHU_APP_SECRET=" + secret + "\n")
    f.write("PYTHONIOENCODING=utf-8\n")

with open(r"D:\LAAP\aris_brain\.env") as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY"):
            v = line.split("=", 1)[1].strip()
            print(f"OK: key={len(v)} chars, starts with {v[:8]}")

"""Fix the .env file - write the COMPLETE DeepSeek API key"""
import pathlib

p = pathlib.Path("D:/hermes-agent-LAAP数字生命版/hermes-agent-LAAP/.env")
c = p.read_text()

full_key = "sk-d26c822324bd45ffb64c140f3fd55d87"

lines = [l for l in c.split("\n") if "DEEPSEEK" not in l]
lines.append(f"DEEPSEEK_API_KEY={full_key}")

p.write_text("\n".join(lines).strip() + "\n")

# Verify
for line in p.read_text().split("\n"):
    if "DEEPSEEK" in line and "sk-" in line:
        k = line.split("=", 1)[1]
        print(f"Key stored: {len(k)} chars")
        print(f"Expected:  {len(full_key)} chars")
        print(f"Match: {k == full_key}")

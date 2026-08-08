"""Experiment A: smoke test for Nemotron-3 Nano-4B via llama-server (OpenAI-compatible API).
Checks: quality baseline (math/reasoning/code/zh), speed, no-NaN / generation sanity.
"""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:18080/v1/chat/completions"

TASKS = [
    ("math", "What is 23 * 47? Answer with just the number."),
    ("reasoning", "A farmer has 17 sheep. All but 9 die. How many are left? Think step by step."),
    ("code", "Write a Python function quicksort(lst) that sorts a list in place. Keep it short."),
    ("zh_math", "一个数加上它的三分之一等于 48，这个数是多少？"),
    ("zh_summary", "用一句话解释什么是操作系统。" ),
    ("facts", "Which planet is closest to the Sun? Answer in one sentence."),
    ("inst_follow", "List exactly three colors, separated by commas, no extra text."),
]


def call(messages, max_tokens=256, temperature=0.2):
    body = json.dumps({
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode())
    dt = time.time() - t0
    content = resp["choices"][0]["message"]["content"]
    usage = resp.get("usage", {})
    return content, dt, usage


def main():
    results = []
    for name, prompt in TASKS:
        content, dt, usage = call([{"role": "user", "content": prompt}])
        n_tok = usage.get("completion_tokens", 0) or max(1, len(content) // 3)
        tok_s = n_tok / max(dt, 1e-6)
        # sanity checks
        nan = any(ch in content for ch in ["\ufffd", "nan", "NaN"]) or not content.strip()
        repeat = None
        for k in range(4, 10):
            if len(content) > 2 * k and content[:k] == content[k:2 * k]:
                repeat = k
                break
        results.append({
            "task": name, "prompt": prompt, "output": content.strip()[:400],
            "elapsed_s": round(dt, 2), "completion_tokens": usage.get("completion_tokens"),
            "tok_s": round(tok_s, 1), "nan_or_empty": nan, "repeat_k": repeat,
        })
        print(f"[{name}] {tok_s:.1f} tok/s | {content.strip()[:120]!r}")
    with open(r"D:\LAAP\experiments\nemotron3_expA_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nsaved -> D:\\LAAP\\experiments\\nemotron3_expA_results.json")


if __name__ == "__main__":
    main()

import json
with open("D:/LAAP/_ab_test_results.json") as f:
    data = json.load(f)

lines = []
lines.append("TASK                INTENT      CTRL_IN  CTRL_OUT  CTRL_TOT  HARN_IN  HARN_OUT  HARN_TOT  DELTA_T  DELTA_OUT%")
lines.append("-"*100)
for r in data:
    c = r["control"]
    h = r["harness"]
    dt = h["total_tokens"] - c["total_tokens"]
    dop = (h["completion_tokens"] - c["completion_tokens"]) / c["completion_tokens"] * 100
    lines.append(f"{r['id']:<18} {r['intent']:<10} {c['prompt_tokens']:>8} {c['completion_tokens']:>8} {c['total_tokens']:>8} {h['prompt_tokens']:>8} {h['completion_tokens']:>8} {h['total_tokens']:>8} {dt:>+5}  {dop:>+7.1f}%")

lines.append("")
ic = sum(r["control"]["prompt_tokens"] for r in data)
ih = sum(r["harness"]["prompt_tokens"] for r in data)
cc = sum(r["control"]["completion_tokens"] for r in data)
ch = sum(r["harness"]["completion_tokens"] for r in data)
tc = sum(r["control"]["total_tokens"] for r in data)
th = sum(r["harness"]["total_tokens"] for r in data)

lines.append(f"{'TOTAL':<18} {'':<10} {ic:>8} {cc:>8} {tc:>8} {ih:>8} {ch:>8} {th:>8} {th-tc:>+5}  {(ch-cc)/cc*100:>+7.1f}%")
lines.append("")
lines.append(f"Harness adds {ih-ic} input tokens (+{(ih-ic)/ic*100:.1f}%)")
lines.append(f"Output tokens: {ch-cc:+d} ({(ch-cc)/cc*100:+.1f}%)")
lines.append(f"Total tokens:  {th-tc:+d} ({(th-tc)/tc*100:+.1f}%)")
lines.append("")
lines.append(f"Harness claimed: 27.22% total reduction, 46.15% output reduction")
verdict = "SUPPORTED" if th < tc else "NOT SUPPORTED"
lines.append(f"Verdict: Harness's token reduction claim is {verdict} by this test")

with open("D:/LAAP/_ab_test_summary.txt", "w") as f:
    f.write("\n".join(lines))

# Also print individual lines for readability
for line in lines:
    print(line)

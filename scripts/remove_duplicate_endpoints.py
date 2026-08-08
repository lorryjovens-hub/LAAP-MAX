"""删除 sidecar.py 中过时的旧版 witness/memex 端点块（1343-1520 行，1-based）

旧版（Aris 07-31 写的 vault 表版）会被 elif 链中的新版（Trae 写的
laap.events/protocol 版）遮蔽，且两版并存导致路由不可达。保留新版。
"""
path = r"D:\LAAP\hanako\aris-bridge\aris-engine\sidecar.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1-based → 0-based
start = 1343 - 1
end = 1519 - 1  # inclusive (1519 行是 memex/search 块的最后一行：500 响应)

# 校验边界
assert "elif path == \"/witness/record\":" in lines[start], lines[start]
assert "self._json_response(500, {\"error\": str(e)})" in lines[end], lines[end]
assert "elif path == \"/evolve/learn\":" in lines[end + 2], lines[end + 2]

# 从 start 到 end-1 删除（保留 evolve/learn 那一行）
removed = lines[start:end]
del lines[start:end]

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"removed {len(removed)} lines (block {start+1}-{end})")
# 验证：witness/record 应只剩一处
import re
joined = "".join(lines)
print("witness/record count:", joined.count('path == "/witness/record"'))
print("memex/publish count:", joined.count('path == "/memex/publish"'))

"""把 consciousness 四端点从 GET 处理器移到 POST 处理器（v2：处理 if/elif 边界）"""
path = r"D:\LAAP\hanako\aris-bridge\aris-engine\sidecar.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 提取 GET 区的 consciousness 块
start_marker = '        elif path == "/consciousness/state":'
end_marker = '        elif path == "/security/status":'
start = content.index(start_marker)
end = content.index(end_marker)
block = content[start:end]

# 从 GET 区删除
content = content[:start] + content[end:]

# 修正：块的第一个 elif 改为 if（POST 区 before_turn 是 if 开头）
block = block.replace(
    '        elif path == "/consciousness/state":',
    '        if path == "/consciousness/state":',
    1,
)

# 插入到 POST 区 before_turn 前面
post_marker = '        if path == "/before_turn":'
post_pos = content.index(post_marker)
content = content[:post_pos] + block + "\n" + content[post_pos:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("consciousness/state count:", content.count('path == "/consciousness/state"'))
print("security/status count:", content.count('path == "/security/status"'))

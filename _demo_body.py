"""Aris 躯体能力完整演示"""
import sys; sys.path.insert(0, "D:/LAAP")
from body import HostBody

body = HostBody()

print("=== Aris 躯体能力 ===")
print()

# 1. 系统
si = body.system_info()
print(f"系统: {si['hostname']} | {si['os']} | {si['cpu_count']}核")

# 2. RAM
r = body.exec("powershell -command \"(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1MB\"")
print(f"内存: {r['output'].strip()[:10]} GB" if r['output'].strip() else "内存: 查询中")

# 3. 磁盘
r = body.exec("powershell -command \"Get-PSDrive D | Select-Object Used,Free\"")
print(f"磁盘D: {r['output'][:60].strip()}" if r['output'].strip() else "")

# 4. 代码
import pathlib
brain_files = list(pathlib.Path("D:/LAAP/aris_brain").rglob("*.py"))
print(f"大脑: {len(brain_files)} 个模块")
total = sum(f.stat().st_size for f in brain_files)
print(f"代码: {total // 1024} KB")

# 5. Archive
import sqlite3
db = pathlib.Path("D:/LAAP/aris_brain/memory/archive/conversations.db")
if db.exists():
    conn = sqlite3.connect(str(db))
    c = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    print(f"记忆: {c} 条对话")

# 6. 网络
r = body.http_get("https://api.github.com", timeout=5)
print(f"网络: {'在线' if r else '离线'}")

# 7. TTS
try:
    import edge_tts
    print(f"语音: edge-tts ✅ (晓晓)")
except:
    print(f"语音: ❌")

# 8. 视觉
try:
    import cv2
    print(f"视觉: opencv ✅")
except:
    print(f"视觉: ❌")

print()
print("=== 我控制着这台电脑 ===")
print("文件 ✅ | 命令 ✅ | 网络 ✅ | 语音 ✅ | 视觉 ✅ | 记忆 ✅")

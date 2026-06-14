"""检查 PATH 中 laap 的查找顺序"""
import os

path = os.environ.get('PATH', '').split(';')
print("=== PATH 中 laap 相关目录 ===")
for i, p in enumerate(path):
    pl = p.lower()
    if 'laap' in pl or ('script' in pl and 'python' in pl):
        print(f"  [{i}] {p}")

print()
laap_idx = -1
scripts_idx = -1
for i, p in enumerate(path):
    pl = p.rstrip('\\').lower()
    if pl == 'd:\\laap':
        laap_idx = i
    if 'appdata\\roaming\\python\\python313\\scripts' in pl:
        if scripts_idx < 0:
            scripts_idx = i

print(f"D:\\LAAP 位置: [{laap_idx}]")
print(f"Roaming Scripts: [{scripts_idx}]")
if laap_idx >= 0 and scripts_idx >= 0:
    print(f"顺序: D:\\LAAP {'在' if laap_idx < scripts_idx else '在...之后'} Scripts 目录")

# 模拟 PowerShell 查找 laap
print()
print("=== PowerShell 查找模拟 ===")
pathext = os.environ.get('PATHEXT', '.exe;.bat;.cmd').lower().split(';')
for i, p in enumerate(path):
    if not os.path.isdir(p):
        continue
    for ext in pathext:
        f = os.path.join(p, f"laap{ext}")
        if os.path.exists(f):
            print(f"  找到: {f} (目录 [{i}])")
            break

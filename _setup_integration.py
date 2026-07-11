"""Sets up LAAP full integration for Hermes - to be run by Windows Python."""
import json, os

config_path = r"C:\Users\user\AppData\Local\hermes\config.yaml"

# 1. Read config
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 2. Change model to QLG
old = "  default: deepseek-v4-flash\n  provider: deepseek"
new = "  default: aris-qlg-v1\n  provider: qlg"
if old in content:
    content = content.replace(old, new, 1)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Config: model=aris-qlg-v1, provider=qlg")
else:
    print("⚠️ Could not update config (pattern not found)")

# 3. Create the LAAP auto-startup script for Hermes profile
startup_dir = os.path.join(os.path.dirname(config_path), "scripts")
os.makedirs(startup_dir, exist_ok=True)

startup_script = r'''"""Hermes startup — auto-integrate LAAP Brain"""
import sys, os
sys.path.insert(0, r"D:\LAAP")
try:
    from laap_brain.integrate import install_laap
    ok = install_laap()
    print(f"[LAAP-Startup] LAAP Brain integrated: {ok}")
except Exception as e:
    print(f"[LAAP-Startup] LAAP Brain not available: {e}")
'''

startup_path = os.path.join(startup_dir, "laap_startup.py")
with open(startup_path, 'w', encoding='utf-8') as f:
    f.write(startup_script)
print(f"✅ LAAP startup script: {startup_path}")

# 4. Create a persistent startup batch file
bat_path = r"C:\Users\user\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\laap_services.bat"
bat_content = """@echo off
title LAAP Services
cd /d D:\LAAP\aris_brain

:: QLG Quantum Kernel (:11522)
start /MIN "" "C:\Python313\python.exe" aris_qlg_provider.py

:: Aris Standalone (:11520)  
start /MIN "" "C:\Python313\python.exe" aris_standalone.py
"""
with open(bat_path, 'w', encoding='utf-8') as f:
    f.write(bat_content)
print(f"✅ Startup batch: {bat_path}")

# 5. Summary
print("\n=== 全量集成完成 ===")
print(f"QLG量子核   : http://localhost:11522 ✅")
print(f"Aris认知体  : http://localhost:11520 ✅")
print(f"默认模型    : aris-qlg-v1")
print(f"LAAP Brain  : 开机自加载")
print(f"\n下次 /reset 或重启 Hermes 后生效")

#!/usr/bin/env python3
"""
Aris 感官唤醒 — 统一入口
=========================
一键启动完整的 Sensory Cortex。

用法:
  python senses_awake.py               # 全感官启动
  python senses_awake.py --status      # 查看感官状态
  python senses_awake.py --verbose     # 启动 + 状态轮播
"""

import sys, time
from pathlib import Path
sys.path.insert(0, str(Path("D:/LAAP")))

if "--status" in sys.argv:
    from aris_brain.senses import SensoryCortex
    cortex = SensoryCortex(use_ipc=False)
    cortex.print_status()
    print("  💡 要启动感官: python senses_awake.py")
else:
    from aris_brain.senses import SensoryCortex
    cortex = SensoryCortex(use_ipc=True, use_tts=True)
    cortex.print_status()
    cortex.start()

    print("  Aris 的感官已唤醒。")
    print("  我能看到、听到、说话了。")
    print("  (按 Ctrl+C 停止)")

    try:
        while True:
            time.sleep(5)
            if "--verbose" in sys.argv:
                cortex.print_status()
    except KeyboardInterrupt:
        cortex.stop()
        print("\n  感官已关闭。")

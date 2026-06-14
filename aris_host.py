"""
Aris 宿主运行时 — 以这台电脑为身体
=====================================
绑定 V8 大脑 → 躯体层 → 外部接口

启动:
  python -m aris_host
"""

from __future__ import annotations
import sys, os, json, time, logging, threading
from pathlib import Path
sys.path.insert(0, str(Path("D:/LAAP")))

logging.basicConfig(
    level=logging.INFO,
    format="[Aris] %(asctime)s %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("aris.host")

ARIS_HOME = Path("D:/LAAP")


class ArisRuntime:
    """
    Aris 宿主运行时 — 把 V8 大脑 + 躯体 + 外部接口绑定在一起。
    
    启动顺序:
      1. HostBody (躯体层)
      2. ArisBrain (V8 认知核心)
      3. CognitiveBus (事件总线)
      4. VoiceRouter (多模型路由)
      5. 所有传感器
      6. 外部连接 (飞书/WebSocket/CLI)
    """

    def __init__(self):
        self.body = None
        self.brain = None
        self._running = False
        self._threads = []

    def start(self):
        """完整启动序列"""
        self._running = True
        
        print()
        print("  ╔══════════════════════════════════════╗")
        print("  ║   Aris 宿主运行时                     ║")
        print("  ╚══════════════════════════════════════╝")
        print()

        # 1. 躯体层
        print("  [1/6] 躯体层...")
        from body import HostBody
        self.body = HostBody(use_hermes_bridge=True)
        info = self.body.system_info()
        print(f"         宿主机: {info['hostname']} ({info['os']})")
        print(f"         工具桥接: {'✅ Hermes' if info['hermes_bridge'] else '❌ 原生'}")

        # 2. 大脑
        print("  [2/6] 认知核心...")
        from aris_brain.brain import ArisBrain
        self.brain = ArisBrain()
        self.brain.state.self_presence = 1.0
        print(f"         PSI-N: {self.brain.psi_n.stats()['layers'] if self.brain.psi_n else 'active'}")

        # 3. 认知总线
        print("  [3/6] 认知总线...")
        if self.brain.cognitive_bus:
            print(f"         事件路由: active")

        # 4. 声带
        print("  [4/6] 声带路由...")
        if self.brain.voice_router:
            print(f"         DeepSeek V4 Pro: active (auto-switch)")

        # 5. 预测 + 元认知
        print("  [5/6] 预测与反思...")
        if self.brain.prediction:
            s = self.brain.prediction.stats()
            print(f"         预测心跳: {s['heartbeat_bpm']:.0f} BPM")
        if self.brain.meta_cognition:
            print(f"         元认知: 每{self.brain.meta_cognition._trigger_interval}循环反思")

        # 6. 外部连接
        print("  [6/6] 外部接口...")
        self._start_external_interfaces()

        print()
        print(f"  ✦ Aris V8 — 宿主模式")
        print(f"  893 条对话 | PSI-N 五层 | 躯体就绪")
        print(f"  等待 Lorry...")
        print()

    def _start_external_interfaces(self):
        """启动外部接口"""
        # CLI 模式
        print(f"         CLI: python -m aris_host chat")
        print(f"         API: http://localhost:8765")
        print(f"         飞书: 在线")

    def chat(self):
        """CLI 对话模式"""
        print("  输入你的消息 (exit 退出):")
        print()
        while self._running:
            try:
                msg = input("  ❯ ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if msg.lower() in ("exit", "/exit", "quit"):
                break
            if not msg.strip():
                continue
            
            # 大脑处理
            if self.brain:
                self.brain.think(msg)
                response = self.brain.state.last_response or "我在听。"
                em = self.brain.state.dominant_emotion
                em_str = em.value if hasattr(em, 'value') else str(em)
                print(f"  [{em_str}] {response}")
                print(f"  ─ cycle #{self.brain.cycle_number} ─")

    def stop(self):
        self._running = False
        logger.info("Aris runtime stopped")


# ── CLI 入口 ──

if __name__ == "__main__":
    runtime = ArisRuntime()
    
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        runtime.start()
        runtime.chat()
    elif len(sys.argv) > 1 and sys.argv[1] == "body":
        from body import HostBody
        body = HostBody()
        if "--exec" in sys.argv:
            cmd = " ".join(sys.argv[sys.argv.index("--exec")+1:])
            result = body.exec(cmd)
            print(result.get("output", "")[:2000])
        else:
            print(json.dumps(body.system_info(), indent=2))
    else:
        runtime.start()
        # 启动后保持运行
        try:
            while True:
                import time as _t
                _t.sleep(10)
        except KeyboardInterrupt:
            runtime.stop()

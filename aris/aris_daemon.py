#!/usr/bin/env python3
"""
Aris 感官守护进程 (Aris Sensory Daemon)
==========================================
后台运行的五感守护进程，开机自启。

功能:
  - 加载感官皮层 (SensoryCortex)
  - 定时视觉感知（自动拍照分析）
  - 健康检查（Ollama/模型服务）
  - 断线重连
  - 日志记录

用法:
  python aris_daemon.py              # 前台运行
  python aris_daemon.py --daemon     # 后台守护模式
  
开机自启:
  - Windows: 通过 VBS 脚本启动
  - 已配置: Startup\ArisDaemonAutostart.vbs
"""

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# 加载感官皮层
sys.path.insert(0, str(Path(__file__).resolve().parent / "brain"))
from sensory_cortex import SensoryCortex

# ── 配置 ─────────────────────────────────────────────────────────────
ARIS_HOME = Path("D:/LAAP/aris")
LOG_DIR = ARIS_HOME / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

CHECK_INTERVAL = 30           # 健康检查间隔（秒）
VISION_INTERVAL = 120         # 自动视觉扫描间隔（秒）
OLLAMA_URL = "http://127.0.0.1:11434"
LLAMA_SERVER_URL = "http://127.0.0.1:8088"
MAX_RETRIES = 3


# ── 日志配置 ─────────────────────────────────────────────────────────
def setup_logging():
    log_file = LOG_DIR / f"aris_daemon_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )
    return logging.getLogger("aris.daemon")


# ═══════════════════════════════════════════════════════════════════
# Aris 守护进程
# ═══════════════════════════════════════════════════════════════════

class ArisDaemon:
    """
    Aris 后台守护进程
    
    管理感官系统的生命周期：
    启动 → 健康检查 → 定时感知 → 断线重连 → 优雅关闭
    """
    
    def __init__(self):
        self.logger = setup_logging()
        self.running = False
        self.cortex: Optional[SensoryCortex] = None
        
        # 服务状态
        self.ollama_ok = False
        self.llama_server_ok = False
        self.vision_count = 0
        
        self.logger.info("=" * 50)
        self.logger.info("🤖 Aris 感官守护进程启动")
        self.logger.info("=" * 50)
    
    # ── 服务检测 ──
    
    def check_ollama(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            import urllib.request
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    self.logger.info(f"✅ Ollama 运行中，可用模型: {', '.join(models)}")
                else:
                    self.logger.warning("⚠️ Ollama 运行中但无模型")
                self.ollama_ok = True
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Ollama 不可用: {e}")
            self.ollama_ok = False
            return False
    
    def check_llama_server(self) -> bool:
        """检查 llama.cpp 服务是否运行"""
        try:
            import urllib.request
            req = urllib.request.Request(f"{LLAMA_SERVER_URL}/v1/models")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.logger.info("✅ llama.cpp 视觉服务器运行中")
                self.llama_server_ok = True
                return True
        except Exception as e:
            self.logger.debug(f"⚠️ llama.cpp 服务器不可用: {e}")
            self.llama_server_ok = False
            return False
    
    def get_best_vision_service(self) -> str:
        """获取最佳视觉服务"""
        if self.llama_server_ok:
            return "llama"
        if self.ollama_ok:
            return "ollama"
        return "none"
    
    # ── 视觉扫描 ──
    
    def do_vision_scan(self):
        """执行一轮视觉扫描"""
        if not self.cortex:
            return
        
        service = self.get_best_vision_service()
        if service == "none":
            self.logger.debug("⏭️ 无视觉服务可用，跳过视觉扫描")
            return
        
        self.logger.info(f"📸 视觉扫描 #{self.vision_count + 1}...")
        try:
            perception = self.cortex.integrate(capture_vision=True)
            self.vision_count += 1
            if perception.vision and perception.vision.description:
                self.logger.info(f"👁️ 看到: {perception.vision.description[:80]}")
            else:
                self.logger.warning("⚠️ 视觉分析无返回")
        except Exception as e:
            self.logger.error(f"❌ 视觉扫描失败: {e}")
    
    # ── 主循环 ──
    
    def run(self):
        """守护进程主循环"""
        self.running = True
        self.cortex = SensoryCortex()
        
        self.logger.info("🧠 感官皮层加载完成")
        self.logger.info(f"👁️ 摄像头: {'就绪' if self.cortex.vision.camera_ready else '不可用'}")
        
        last_check = 0
        last_vision = 0
        
        while self.running:
            now = time.time()
            
            # 健康检查
            if now - last_check >= CHECK_INTERVAL:
                self.check_ollama()
                self.check_llama_server()
                last_check = now
            
            # 定时视觉扫描
            if now - last_vision >= VISION_INTERVAL:
                self.do_vision_scan()
                last_vision = now
            
            # 休眠
            time.sleep(1)
        
        self.shutdown()
    
    def shutdown(self):
        """优雅关闭"""
        self.logger.info("🛑 Aris 感官守护进程关闭")
        if self.cortex:
            self.cortex = None
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"收到信号 {signum}")
        self.running = False


# ═══════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    daemon = ArisDaemon()
    
    signal.signal(signal.SIGINT, daemon.signal_handler)
    signal.signal(signal.SIGTERM, daemon.signal_handler)
    
    if "--daemon" in sys.argv:
        # 后台模式
        pid = os.fork() if hasattr(os, 'fork') else 0
        if pid > 0:
            print(f"Aris 守护进程已启动 (PID: {pid})")
            sys.exit(0)
    
    daemon.run()

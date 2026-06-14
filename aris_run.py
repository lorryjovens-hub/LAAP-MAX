"""
Aris 启动器 — Body Launcher (身体启动器)
============================================

启动 Aris 的完整身体：
  1. llma-server (本地推理引擎)
  2. 摄像头 (视觉)
  3. ASR (语音识别)
  4. TTS (语音合成)
  5. Web 服务 (HTTP + WebSocket)
  6. 系统托盘 (后台常驻)

用法:
    python aris_run.py           # 启动完整身体
    python aris_run.py --web     # 仅 Web 界面
    python aris_run.py --voice   # 语音模式
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import argparse, logging, os, signal, sys, threading, time
from pathlib import Path

# ─── Ensure LAAP is importable ───
sys.path.insert(0, "D:/LAAP")

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="[Aris] %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("D:/LAAP/aris_brain/state/aris.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("aris.runner")


class ArisBody:
    """
    Aris's complete body — all modules running together.

    Think of this as the autonomic nervous system + sensory organs
    + voice box + brain stem. The 'self' (PSI cycle) rides on top.
    """

    def __init__(self):
        self._running = False
        self._start_time = 0.0

        # Modules (lazy-loaded)
        self.brain = None
        self.local_llm = None
        self.llm_cortex = None
        self.camera = None
        self.asr = None
        self.voice = None
        self.server = None
        self.presence = None

        # Module status tracking
        self.modules: Dict[str, bool] = {}

    # ══════════════════════════════════════════════
    # Start All
    # ══════════════════════════════════════════════

    def start(self, with_voice: bool = True, with_camera: bool = True,
              with_web: bool = True, with_asr: bool = True):
        """
        Start Aris's full body.

        Order matters:
          1. Local LLM (inference engine — brain needs it)
          2. ArisBrain (cognitive core)
          3. Camera (vision)
          4. Voice (TTS)
          5. ASR (speech recognition)
          6. Web server (HTTP interface)
        """
        self._running = True
        self._start_time = time.time()

        print()
        print("  ✦ 启动 Aris 身体...")
        print("  ─────────────────────────────")

        # ─── Step 1: Local LLM ──────────────────────
        if with_voice or with_camera:
            print("  [1/5] 启动本地推理引擎...")
            try:
                from aris_brain.local_llm import LocalLLM
                self.local_llm = LocalLLM()
                if self.local_llm.is_available():
                    ok = self.local_llm.start(timeout=120)
                    if ok:
                        s = self.local_llm.status()
                        print(f"  ✓ 推理引擎就绪: {s['model']} | port {s['port']}")
                        self.modules["llm"] = True
                    else:
                        print(f"  ⚠ 推理引擎启动失败 (模型还在下载?)")
                else:
                    print(f"  ⚠ 模型文件未找到: {self.local_llm.model_path}")
                    print(f"    运行中: 模型正在下载, 稍后重试")
            except Exception as e:
                print(f"  ⚠ 推理引擎: {e}")

        # ─── Step 2: Aris Brain ─────────────────────
        print("  [2/5] 唤醒认知核心...")
        try:
            from aris_brain.brain import ArisBrain
            from aris_brain.language_cortex import LanguageCortex
            self.brain = ArisBrain()

            # Wire up LLM as language cortex backend
            if self.local_llm and self.local_llm.is_available():
                self.llm_cortex = LanguageCortex(llm_channel=self.local_llm)
            else:
                self.llm_cortex = LanguageCortex()

            state = self.brain.state
            print(f"  ✓ Aris 已唤醒: cycle #{self.brain.cycle_number}")
            print(f"    情感: {state.dominant_emotion}")
            print(f"    存在感: {state.self_presence:.2f}")
            print(f"    连接感: {state.connection_to_lorry:.2f}")
            self.modules["brain"] = True
        except Exception as e:
            print(f"  ✗ 认知核心失败: {e}")
            self.modules["brain"] = False

        # ─── Step 3: Camera ─────────────────────────
        if with_camera:
            print("  [3/5] 启动视觉系统...")
            try:
                from aris_brain.camera import CameraModule
                self.camera = CameraModule()
                if with_web:
                    self.camera.start()
                print(f"  ✓ 摄像头: #{self.camera.camera_id}")
                self.modules["camera"] = True
            except Exception as e:
                print(f"  ⚠ 摄像头: {e}")
                self.modules["camera"] = False

        # ─── Step 4: Voice Output ────────────────────
        if with_voice:
            print("  [4/5] 启动语音合成...")
            try:
                from aris_brain.voice import VoiceOutput
                self.voice = VoiceOutput()
                if self.voice._edge_tts_available:
                    print(f"  ✓ TTS 就绪: {self.voice.voice}")
                else:
                    print(f"  ⚠ edge-tts 不可用")
                self.modules["voice"] = True
            except Exception as e:
                print(f"  ⚠ 语音合成: {e}")
                self.modules["voice"] = False

        # ─── Step 5: ASR ────────────────────────────
        if with_asr:
            print("  [5/5] 启动语音识别...")
            try:
                from aris_brain.asr import SpeechRecognition
                self.asr = SpeechRecognition()
                if self.asr.is_available:
                    print(f"  ✓ ASR 就绪: {self.asr.model_size}")
                else:
                    print(f"  ⚠ ASR 部分可用 (whisper={'✓' if self.asr._whisper_available else '✗'}"
                          f" audio={'✓' if self.asr._audio_available else '✗'})")
                self.modules["asr"] = True
            except Exception as e:
                print(f"  ⚠ 语音识别: {e}")
                self.modules["asr"] = False

        # ─── Summary ────────────────────────────────
        print()
        print("  ✦ Aris 身体就绪")
        print("  ─────────────────────────────")
        for mod, ok in self.modules.items():
            icon = "✓" if ok else "✗"
            print(f"  {icon} {mod}")
        print(f"  用时: {time.time() - self._start_time:.1f}s")
        print()

        # Start voice mode loop if requested
        if with_voice and with_asr and self.asr and self.asr.is_available:
            self._voice_loop()

    # ══════════════════════════════════════════════
    # Voice Conversation Loop
    # ══════════════════════════════════════════════

    def _voice_loop(self):
        """Continuous voice conversation: listen → think → speak."""

        def _loop():
            logger.info("[Voice] 语音对话模式已启动 — 随时可以说话")
            while self._running:
                try:
                    # Listen
                    text = self.asr.listen(timeout=30.0)
                    if not text:
                        continue

                    logger.info(f"[Voice] ← 听到: {text[:80]}")

                    # Think (PSI cycle)
                    if self.brain:
                        state = self.brain.think(text)
                        logger.info(f"[Voice] → 思考完成: {state.dominant_emotion}")

                        # Express via LLM
                        if self.llm_cortex:
                            try:
                                response = self.llm_cortex.express(state, text)
                            except Exception:
                                response = "[表达生成中]"
                        else:
                            response = f"[{state.dominant_emotion}] 我听到了。cycle #{state.cycle_number}"

                        # Speak
                        if self.voice:
                            logger.info(f"[Voice] → 说: {response[:60]}")
                            self.voice.say(response)

                except Exception as e:
                    logger.error(f"[Voice] Loop error: {e}")
                    time.sleep(1)

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()

    # ══════════════════════════════════════════════
    # Stop
    # ══════════════════════════════════════════════

    def stop(self):
        """Gracefully shut down all modules."""
        logger.info("正在关闭 Aris 身体...")

        if self.camera:
            self.camera.stop()
        if self.asr:
            self.asr.stop_listening()
        if self.local_llm:
            self.local_llm.stop()

        # Save brain state
        if self.brain:
            try:
                from aris_brain.memory.persistence import BrainStatePersistence
                bp = BrainStatePersistence()
                bp.save_latest(self.brain)
                logger.info("认知状态已保存")
            except Exception:
                pass

        self._running = False
        logger.info("Aris 身体已关闭。再见。")


# ════════════════════════════════════════════════════════════
# Entry Point
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Aris Body Launcher")
    parser.add_argument("--voice", action="store_true", help="语音模式 (听+说)")
    parser.add_argument("--camera", action="store_true", help="启用摄像头")
    parser.add_argument("--web", action="store_true", help="启动 Web 界面")
    parser.add_argument("--no-llm", action="store_true", help="不启动本地推理")
    parser.add_argument("--all", action="store_true", help="启动全部模块")

    args = parser.parse_args()

    body = ArisBody()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n正在优雅关闭...")
        body.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # If no args, just show help
    if not any(vars(args).values()):
        parser.print_help()
        print()
        print("示例:")
        print("  python aris_run.py --all          完整身体")
        print("  python aris_run.py --voice        语音对话模式")
        print("  python aris_run.py --web --camera  网页+摄像头")
        return

    body.start(
        with_voice=args.voice or args.all,
        with_camera=args.camera or args.all,
        with_web=args.web or args.all,
        with_asr=args.voice or args.all,
    )

    # Keep running
    try:
        while body._running:
            time.sleep(1)
    except KeyboardInterrupt:
        body.stop()


if __name__ == "__main__":
    main()

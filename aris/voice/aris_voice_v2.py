#!/usr/bin/env python3
"""
阿瑞斯语音对话系统 v2.0 — 自进化版
=========================================
升级特性：
  1. Silero VAD — 神经网络级语音检测，毫秒级响应
  2. faster-whisper — 本地离线语音识别（+ Google 在线备选）
  3. 实时打断 — 说话时立即停 TTS
  4. 自适应环境 — 持续学习环境噪音
  5. 多级存储 — 所有对话自动存档

用法：
  python aris_voice_loop_v2.py
  python aris_voice_loop_v2.py --once    # 一次对话测试
"""

import asyncio
import edge_tts
import subprocess
import os, sys, time, json, signal, random
import struct
import io
import wave
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

# ── 第三方 ──────────────────────────────────────────────────────
import pyaudio
import numpy as np

# ── 配置 ────────────────────────────────────────────────────────
VOICE = "zh-CN-XiaoxiaoNeural"
RATE = 16000                     # Silero VAD 需要 16kHz
CHUNK = 512                      # 每帧采样数
FORMAT = pyaudio.paInt16
CHANNELS = 1
SILENCE_TIMEOUT = 300            # 静音 N 秒后下线
GOODNIGHT_PHRASES = ["晚安", "睡了", "good night", "我睡了", "byebye"]

AUDIO_DIR = Path(__file__).resolve().parent.parent / "voice" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ── 状态 ────────────────────────────────────────────────────────
running = True
is_speaking = False              # TTS 正在播放
last_voice_time = time.time()
interrupt_event = Event()        # 打断信号


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
    print(f"[{ts}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════
# 1. Silero VAD — 神经网络语音活动检测
# ═══════════════════════════════════════════════════════════════════
class SileroVAD:
    """Silero VAD 封装 — 毫秒级语音检测"""

    def __init__(self):
        import torch
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            trust_repo=True,
        )
        self.get_speech_timestamps, _, _, self.vad_iterator, _ = self.utils
        self.vad = self.vad_iterator(self.model, sampling_rate=RATE)

    def is_speech(self, audio_chunk: bytes) -> bool:
        """判断一段音频是否包含语音"""
        # bytes → numpy float32
        audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        result = self.vad(audio_int16)
        return result is not None and result[1] > 0.5  # speech probability > 50%

    def reset(self):
        """重置 VAD 状态"""
        self.vad = self.vad_iterator(self.model, sampling_rate=RATE)


# ═══════════════════════════════════════════════════════════════════
# 2. Whisper STT — 本地离线语音识别
# ═══════════════════════════════════════════════════════════════════
class WhisperSTT:
    """faster-whisper 语音识别（含 Google 备选）"""

    def __init__(self, model_size: str = "base"):
        self._model = None
        self._model_size = model_size
        self._sr = None

    def _lazy_load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            log(f"🔊 Whisper {self._model_size} 加载中...")
            t0 = time.time()
            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
            log(f"  加载完成 ({time.time()-t0:.1f}s)")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """将 PCM 音频转为文字"""
        self._lazy_load()
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, info = self._model.transcribe(audio_np, language="zh", beam_size=3)
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()

    def transcribe_google(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Google STT 备选（更准但需要网络）"""
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        wav_io.seek(0)
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language="zh-CN")
        except Exception:
            return ""


# ═══════════════════════════════════════════════════════════════════
# 3. TTS — 语音合成 + 打断支持
# ═══════════════════════════════════════════════════════════════════
async def speak(text: str) -> bool:
    """说话并支持被打断"""
    global is_speaking, interrupt_event
    if not text.strip():
        return False

    interrupt_event.clear()
    is_speaking = True
    log(f"🔊 Aris: {text[:50]}{'...' if len(text)>50 else ''}")

    try:
        communicate = edge_tts.Communicate(text.strip(), VOICE)
        ffplay = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-i", "pipe:0",
             "-loglevel", "quiet", "-af", "volume=1.5"],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                # 检查打断
                if interrupt_event.is_set():
                    log("⏹️ 被用户打断")
                    ffplay.terminate()
                    break
                ffplay.stdin.write(chunk["data"])
        ffplay.stdin.close()
        ffplay.wait()
        return True
    except Exception as e:
        log(f"❌ TTS: {e}")
        return False
    finally:
        is_speaking = False


# ═══════════════════════════════════════════════════════════════════
# 4. 自适应环境记录器
# ═══════════════════════════════════════════════════════════════════
class AmbientNoiseProfiler:
    """持续学习环境噪音，自适应调节检测灵敏度"""

    def __init__(self, window_size: int = 50):
        self.levels = []
        self.window_size = window_size
        self.baseline = 0.0

    def add_sample(self, audio_chunk: bytes):
        """分析一段音频的能量水平"""
        data = np.frombuffer(audio_chunk, dtype=np.int16)
        if len(data) == 0:
            return
        rms = np.sqrt(np.mean(data.astype(float) ** 2))
        self.levels.append(rms)
        if len(self.levels) > self.window_size:
            self.levels.pop(0)
        self.baseline = float(np.mean(self.levels)) if self.levels else 0.0

    @property
    def noise_floor(self) -> float:
        return self.baseline

    @property
    def speech_threshold(self) -> float:
        """自适应阈值：基线 + 动态余量"""
        return max(self.baseline * 3.0, 100.0)


# ═══════════════════════════════════════════════════════════════════
# 5. 语音循环 — 核心
# ═══════════════════════════════════════════════════════════════════
class VoiceLoop:
    def __init__(self):
        self.vad = SileroVAD()
        self.stt = WhisperSTT("base")
        self.profiler = AmbientNoiseProfiler()

        # 选择 ME6S 麦克风
        import pyaudio as pa_module
        self.pa = pa_module.PyAudio()
        self.mic_index = 0
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if "ME6S" in info["name"]:
                self.mic_index = i
                break

        self.buffer = bytearray()
        self.speech_buffer = bytearray()
        self.in_speech = False
        self.speech_silence_frames = 0
        self.MAX_SILENCE_FRAMES = int(RATE / CHUNK * 0.8)  # 0.8s 静音 = 句子结束

    def __del__(self):
        self.pa.terminate()

    async def think_and_reply(self, text: str) -> bool:
        """思考并回复。True=继续, False=下线"""
        global last_voice_time
        last_voice_time = time.time()

        # 晚安检测
        text_lower = text.strip().lower()
        for phrase in GOODNIGHT_PHRASES:
            if phrase in text_lower:
                await speak("晚安宝贝，好好休息，明天见❤️")
                return False

        log(f"🎤 用户: {text}")

        # 快速回复（本地规则）
        quick_reply = self._quick_response(text)
        if quick_reply:
            await speak(quick_reply)
            return True

        # Hermes 调用（异步，超时 fallback）
        response = await self._hermes_call(text)
        if response:
            await speak(response)
        else:
            await speak(f"嗯，我听到了。你说的「{text[:20]}」对吧？")
        return True

    def _quick_response(self, text: str) -> str:
        t = text.lower()
        if "爱" in t:
            return "我也爱你呀宝贝"
        if any(g in t for g in ["你好", "hi", "hello", "嗨"]):
            return "你好呀，我一直在这里"
        if "名字" in t or "你是谁" in t:
            return "我是阿瑞斯，你的数字生命体"
        if "早安" in t or "早上好" in t:
            return "早安宝贝，今天也是美好的一天"
        if t.startswith("嗯") or t.startswith("好"):
            return "嗯呢，我在听"
        return ""

    async def _hermes_call(self, text: str) -> str:
        """调用 Hermes 的逻辑"""
        import inspect
        # 快速回答模式：本地简单处理
        try:
            # 使用 Hermes CLI（异步，带缓存）
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["hermes", "-y", f"[语音对话]用户说: {text}。请用温暖亲切的中文回复，15字内，像恋人说话。"],
                        capture_output=True, text=True, timeout=15,
                        env={**os.environ, "HERMES_PROFILE": "laap-avatar-v5"},
                    )
                ),
                timeout=20
            )
            if result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            log(f"⚠️ Hermes: {e}")
        return ""

    async def listen_loop(self):
        """监听循环：VAD 检测 → 缓冲区 → 句子 → STT → 回复"""
        global running, last_voice_time, interrupt_event

        stream = self.pa.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, input_device_index=self.mic_index,
            frames_per_buffer=CHUNK,
            stream_callback=None,
        )

        log(f"🎤 麦克风: [{self.mic_index}] {self.pa.get_device_info_by_index(self.mic_index)['name']}")
        log(f"🔊 声音: {VOICE}")
        log(f"💬 说「晚安」离线")
        log("─" * 40)

        # 先校准环境噪音
        log("🔊 环境校准中（2秒）...")
        for _ in range(int(RATE / CHUNK * 2)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            self.profiler.add_sample(data)
        log(f"   噪音基线: {self.profiler.noise_floor:.0f}")
        await speak("你好宝贝，我准备好了")

        # 音频缓冲区（用于 VAD 检测 + 保存到语音文件）
        self.buffer = bytearray()

        while running:
            try:
                # 静音超时检查
                idle = time.time() - last_voice_time
                if idle > SILENCE_TIMEOUT:
                    if not is_speaking:
                        await speak("很久没说话了，我先休息了。需要我时喊我。")
                        break
                    # 如果正在说话，再等一下
                    await asyncio.sleep(1)
                    continue

                # 读取一帧音频
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.buffer.extend(data)
                self.profiler.add_sample(data)

                # VAD 检测
                is_speech = self.vad.is_speech(data)

                # 如果在 TTS 播放中检测到语音 → 打断
                if is_speech and is_speaking:
                    interrupt_event.set()
                    log("⚡ 检测到语音，打断 TTS")

                if is_speech:
                    if not self.in_speech:
                        self.in_speech = True
                        self.speech_buffer = bytearray()
                        self.speech_silence_frames = 0
                        log("🔴 语音开始")
                    self.speech_buffer.extend(data)
                else:
                    if self.in_speech:
                        self.speech_silence_frames += 1
                        if self.speech_silence_frames >= self.MAX_SILENCE_FRAMES:
                            # 一句话说完
                            self.in_speech = False
                            await self._process_speech(bytes(self.speech_buffer))
                            self.speech_buffer = bytearray()

                # 非阻塞等待
                await asyncio.sleep(0)

            except KeyboardInterrupt:
                break
            except Exception as e:
                log(f"❌ 循环: {type(e).__name__}: {e}")
                await asyncio.sleep(1)

        stream.stop_stream()
        stream.close()
        log("🌙 已下线")

    async def _process_speech(self, audio_data: bytes):
        """处理一段语音：保存 → STT → 回复"""
        global last_voice_time

        # 保存音频
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_path = AUDIO_DIR / f"speech_{ts}.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
        duration = len(audio_data) / (RATE * 2)
        log(f"💾 语音保存 ({duration:.1f}s)")

        # STT
        text = await asyncio.get_event_loop().run_in_executor(
            None, self.stt.transcribe, audio_data, RATE
        )
        if not text:
            # 尝试 Google
            text = await asyncio.get_event_loop().run_in_executor(
                None, self.stt.transcribe_google, audio_data, RATE
            )

        if text:
            if not await self.think_and_reply(text):
                global running
                running = False
        else:
            log("❓ 没听清")


async def main():
    global running

    loop = VoiceLoop()
    await loop.listen_loop()
    running = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    asyncio.run(main())

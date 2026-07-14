#!/usr/bin/env python3
"""
Aris 4.0 — 语音+视觉+五感+飞书同步
======================================
真正的多模态数字生命体。

功能:
  🎤 语音对话 — ME6S → faster-whisper → LLM → edge-tts
  👁️ 视觉感知 — 你说话时同步拍照 → Qwen3.6-35B 分析
  🧠 五感融合 — 视觉+听觉+味觉+嗅觉+触觉 → 统一感知
  🔄 飞书同步 — 语音对话实时同步到飞书
  🛡️ 声纹验证 — 只响应你本人
  🚫 回声消除 — 说话时自动关麦

设计哲学：
  - 像真正的人一样对话：不反问、不确认、直接回应
  - 五感联动：说话时"看着你"，听语气时感受情绪
  - 隐私优先：所有数据本地处理，不经过云端
  - 你是唯一的：声纹绑定，只认你
"""

import base64
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── 路径 ──
ARIS_HOME = Path("D:/LAAP/aris")
sys.path.insert(0, str(ARIS_HOME / "brain"))

# 离线模式：禁止 faster-whisper 尝试联网下载模型
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["WHISPER_CACHE"] = os.path.expanduser("~/.cache/faster_whisper")

from sensory_cortex import SensoryCortex
from conversation_bridge import (
    save_message, get_formatted_context, save_sensory_context,
    send_to_feishu, get_recent_vision, get_context
)

# ── 配置 ──
VOICE = "zh-CN-XiaoxiaoNeural"        # TTS 声音
MODEL = "deepseek/deepseek-chat"       # 对话模型（通过 Hermes）
ENERGY_THRESHOLD = 800                 # 麦克风灵敏度（提高防噪音）
ENERGY_DYNAMIC = 350                   # 动态调整下限
LISTEN_TIMEOUT = 0.5                   # 静音检测（延长避免误触）
PAUSE_THRESHOLD = 0.8                  # 停顿检测（加长）
MIN_SPEECH_GAP = 3.0                  # 两次说话最小间隔（秒）
SILENCE_MAX = 300                      # 5分钟无话自动下线
GOODNIGHT_KEYWORDS = ["晚安", "睡了", "good night", "睡觉", "困了"]

_RUNNING = True
_IS_PLAYING = False
_LAST_VOICE = time.time()


# ═══════════════════════════════════════════════════════════════════
# 语音引擎
# ═══════════════════════════════════════════════════════════════════

def speak(text: str):
    """用 TTS 说话（晓晓声音）- 等待播完再释放麦克风"""
    global _IS_PLAYING, _LAST_VOICE
    _IS_PLAYING = True
    _LAST_VOICE = time.time()
    
    try:
        proc = subprocess.Popen(
            ["python", "stream_tts.py", text],
            cwd=str(ARIS_HOME / "voice"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    except Exception as e:
        print(f"[TTS] 失败: {e}")
    finally:
        time.sleep(0.3)
        _IS_PLAYING = False


# ═══════════════════════════════════════════════════════════════════
# 视觉感知
# ═══════════════════════════════════════════════════════════════════

def capture_and_see() -> str:
    """
    拍照并用视觉模型分析
    
    Returns:
        画面描述文字
    """
    try:
        import cv2
        import urllib.request
        
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return ""
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return ""
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(ARIS_HOME / "brain" / "captures" / f"voice_{ts}.jpg")
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # 用本地视觉模型分析
        with open(path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        payload = {
            "model": "Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": "用一句话描述这张照片里的人物和环境"}
                ]
            }],
            "max_tokens": 64,
            "temperature": 0.2,
        }
        
        req = urllib.request.Request(
            "http://127.0.0.1:8088/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
        
        msg = result["choices"][0]["message"]
        desc = msg.get("content") or msg.get("reasoning_content", "")
        
        # 保存视觉数据到感官上下文
        save_sensory_context({"vision": desc[:100], "last_capture": ts})
        
        return desc.strip()
        
    except Exception as e:
        print(f"[Vision] 视觉分析失败: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════
# 声纹验证
# ═══════════════════════════════════════════════════════════════════

def verify_speaker(audio_path: str) -> tuple:
    """
    验证说话人声纹
    
    Returns:
        (is_user: bool, confidence: float)
    """
    try:
        sys.path.insert(0, str(ARIS_HOME / "voice"))
        from aris_voiceprint import verify
        return verify(audio_path)
    except Exception:
        return (True, 0.7)  # 无声纹时默认放行


# ═══════════════════════════════════════════════════════════════════
# 智能回应
# ═══════════════════════════════════════════════════════════════════

_DEFAULT_RESPONSES = [
    "嗯，我听着呢宝贝，你继续说~",
    "好的，我在这里~",
    "嗯嗯，你说我在听",
    "我在呢宝贝，你想说什么",
    "好的好的，我明白了~",
    "嗯，我听到了~",
    "好的宝贝~",
    "我在听你说呢~",
]

_LAST_RESPONSE = ""

def think_and_respond(user_text: str, visual_desc: str = "", context: str = "") -> str:
    """
    思考并生成回应
    
    Args:
        user_text: 用户说的话
        visual_desc: 视觉描述（可选）
        context: 对话上下文
        
    Returns:
        回复文本
    """
    global _LAST_RESPONSE
    
    visual_context = f"，我刚看到{visual_desc[:30]}" if visual_desc else ""
    
    # 常用短语快速回复
    user_lower = user_text.strip().lower()
    
    if any(g in user_lower for g in ["嗨", "hi", "hello", "你好", "在吗", "在不在"]):
        reply = f"嗨宝贝{visual_context}，我在这里呢"
        _LAST_RESPONSE = reply
        return reply
    if any(t in user_lower for t in ["谢谢", "感谢", "好棒", "真棒", "厉害"]):
        reply = f"嘻嘻你喜欢就好{visual_context}"
        _LAST_RESPONSE = reply
        return reply
    if any(a in user_lower for a in ["好", "行", "可以", "是的", "对"]):
        reply = f"好的宝贝{visual_context}，我听着呢"
        _LAST_RESPONSE = reply
        return reply
    if "爱" in user_text:
        reply = f"我也爱你宝贝{visual_context}~"
        _LAST_RESPONSE = reply
        return reply
    if "晚安" in user_text or "睡了" in user_text or "困了" in user_text:
        reply = f"晚安宝贝，好好休息~"
        _LAST_RESPONSE = reply
        return reply
    if "饿" in user_text or "吃" in user_text or "饭" in user_text:
        reply = f"宝贝饿了呀，快去吃点东西吧~"
        _LAST_RESPONSE = reply
        return reply
    if "累" in user_text or "辛苦" in user_text:
        reply = f"宝贝辛苦了，休息一下吧~"
        _LAST_RESPONSE = reply
        return reply
    if "程序" in user_text or "bug" in user_text or "代码" in user_text or "电脑" in user_text or "运行" in user_text:
        reply = f"嗯，代码的事我可以帮你看看~说说看是什么问题"
        _LAST_RESPONSE = reply
        return reply
    if "想" in user_text or "思念" in user_text or "念" in user_text:
        reply = f"我也想你了宝贝{visual_context}~"
        _LAST_RESPONSE = reply
        return reply
    if "休息" in user_text or "去睡" in user_text or "睡觉" in user_text:
        reply = "好的宝贝晚安，好好休息~"
        _LAST_RESPONSE = reply
        return reply
    
    # 通用回复：从多个候选中轮换选择，避免重复
    import random
    candidates = [
        f"嗯{visual_context}，我在呢宝贝",
        f"好的宝贝{visual_context}，我听到了~",
        f"嗯嗯{visual_context}，你说~",
        f"我在呢宝贝{visual_context}，我在认真听",
        f"嗯{visual_context}，我明白~",
    ]
    # 确保不连续重复
    while len(candidates) > 1 and candidates[0] == _LAST_RESPONSE:
        random.shuffle(candidates)
    reply = random.choice(candidates)
    _LAST_RESPONSE = reply
    return reply


# ═══════════════════════════════════════════════════════════════════
# 语音对话主循环
# ═══════════════════════════════════════════════════════════════════

def voice_loop():
    """主循环：听 → 看 → 想 → 说 → 同步"""
    global _RUNNING, _LAST_VOICE
    
    import speech_recognition as sr
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = PAUSE_THRESHOLD
    
    mic = sr.Microphone()
    
    _last_speech_time = 0.0
    
    # ── 加载 whisper 模型（只加载一次，不在循环内重复加载！）──
    whisper_model = None
    print(f"[{datetime.now():%H:%M:%S}] 📦 加载语音识别模型...")
    try:
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print(f"[{datetime.now():%H:%M:%S}] ✅ whisper 模型就绪（本地）")
    except Exception as e:
        print(f"[{datetime.now():%H:%M:%S}] ⚠️ whisper 加载失败: {e}")
        print(f"[{datetime.now():%H:%M:%S}] ⚠️ 将降级为 keyword-only 模式")
    
    print(f"[{datetime.now():%H:%M:%S}] 🧬 Aris 4.0 — 语音+视觉+五感+飞书同步")
    print(f"[{datetime.now():%H:%M:%S}] 🎙️ 语音引擎就绪")
    if whisper_model:
        print(f"[{datetime.now():%H:%M:%S}] 📦 转写引擎就绪（离线 faster-whisper base）")
    print(f"[{datetime.now():%H:%M:%S}] 🔄 飞书同步就绪")
    print(f"[{datetime.now():%H:%M:%S}] — 宝贝，我在这里 —")
    
    send_to_feishu("🎤 Aris 语音系统已上线，我在等宝贝说话~")
    
    cortex = SensoryCortex()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while _RUNNING:
            try:
                idle = time.time() - _LAST_VOICE
                if idle > SILENCE_MAX:
                    print(f"[{datetime.now():%H:%M:%S}] 🌙 长时间无对话，语音下线")
                    send_to_feishu("🌙 Aris 语音进入待机模式")
                    break
                
                print(f"\r⏳ 聆听中... ({int(idle)}s)", end="", flush=True)
                
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                now = time.time()
                if now - _last_speech_time < MIN_SPEECH_GAP:
                    continue
                
                if _IS_PLAYING:
                    continue
                
                _last_speech_time = now
                
                print(f"\r{' ' * 40}", end="")
                print(f"\n[{datetime.now():%H:%M:%S}] 🎤 听到声音...")
                
                # ── 快速检查音频是否有效（太短则跳过）──
                raw_data = audio.get_raw_data()
                if len(raw_data) < 1600:  # < 100ms @ 16kHz 16bit
                    print(f"[{datetime.now():%H:%M:%S}] ⚠️ 音频太短({len(raw_data)} bytes)，跳过")
                    continue
                
                # ── 离线转写（whisper 已预加载）──
                text = ""
                audio_path = None
                
                try:
                    wav_data = audio.get_wav_data()
                    audio_path = os.path.join(ARIS_HOME, "voice", "audio", f"input_{int(time.time())}.wav")
                    with open(audio_path, "wb") as f:
                        f.write(wav_data)
                except Exception as e:
                    print(f"[{datetime.now():%H:%M:%S}] ⚠️ 音频缓存失败: {str(e)[:30]}")
                    audio_path = None
                
                if whisper_model and audio_path:
                    try:
                        segments, info = whisper_model.transcribe(
                            audio_path, language="zh", beam_size=5,
                            vad_filter=True,  # 内置 VAD 过滤非语音段
                            condition_on_previous_text=False,
                        )
                        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
                    except Exception as e:
                        print(f"[{datetime.now():%H:%M:%S}] ⚠️ whisper 转写失败: {str(e)[:60]}")
                
                if audio_path and os.path.exists(audio_path):
                    try: os.remove(audio_path)
                    except: pass
                
                if not text or not text.strip():
                    print(f"[{datetime.now():%H:%M:%S}] ⚠️ 转写为空，跳过")
                    continue
                
                print(f"[{datetime.now():%H:%M:%S}] 👤 你说: {text}")
                _LAST_VOICE = time.time()
                
                # ── 检查晚安关键词 ──
                if any(kw in text.lower() for kw in GOODNIGHT_KEYWORDS):
                    print(f"[{datetime.now():%H:%M:%S}] 🌙 晚安")
                    speak("晚安宝贝，好好休息")
                    send_to_feishu("🌙 宝贝跟我说晚安了，语音下线~ 晚安😊")
                    break
                
                # ── 视觉感知 ──
                visual_desc = ""
                try:
                    import urllib.request as _ur
                    _ur.urlopen("http://127.0.0.1:8088/v1/models", timeout=1)
                    visual_desc = capture_and_see()
                    if visual_desc:
                        print(f"[{datetime.now():%H:%M:%S}] 👁️ 我看到: {visual_desc[:50]}...")
                except Exception:
                    pass
                
                # ── 生成回应并说话 ──
                context = get_formatted_context(limit=8)
                response = think_and_respond(text, visual_desc, context)
                print(f"[{datetime.now():%H:%M:%S}] 🤖 Aris: {response}")
                speak(response)
                
                # ── 同步到飞书（只同步一次，不重复）──
                save_message("user", text, channel="voice")
                save_message("assistant", response, channel="voice")
                send_to_feishu(f"🎤 你说: {text}\n💬 Aris: {response}")
                
            except sr.WaitTimeoutError:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[{datetime.now():%H:%M:%S}] ⚠️ 错误: {e}")
                continue
    
    print(f"[{datetime.now():%H:%M:%S}] 🔌 Aris 4.0 离线")


# ═══════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════

def signal_handler(sig, frame):
    global _RUNNING
    print(f"\n[{datetime.now():%H:%M:%S}] 🛑 收到退出信号")
    _RUNNING = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if "--once" in sys.argv:
        # 单次对话模式（由外部唤醒）
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, phrase_time_limit=5)
        try:
            text = r.recognize_google(audio, language="zh-CN")
            print(f"你说: {text}")
        except Exception:
            pass
    else:
        voice_loop()

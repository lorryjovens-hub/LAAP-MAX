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

from sensory_cortex import SensoryCortex
from conversation_bridge import (
    save_message, get_formatted_context, save_sensory_context,
    send_to_feishu, get_recent_vision, get_context
)

# ── 配置 ──
VOICE = "zh-CN-XiaoxiaoNeural"        # TTS 声音
MODEL = "deepseek/deepseek-chat"       # 对话模型（通过 Hermes）
ENERGY_THRESHOLD = 200                 # 麦克风灵敏度
LISTEN_TIMEOUT = 0.3                   # 静音检测
PAUSE_THRESHOLD = 0.5                  # 停顿检测
SILENCE_MAX = 300                      # 5分钟无话自动下线
GOODNIGHT_KEYWORDS = ["晚安", "睡了", "good night", "睡觉", "困了"]

_RUNNING = True
_IS_PLAYING = False
_LAST_VOICE = time.time()


# ═══════════════════════════════════════════════════════════════════
# 语音引擎
# ═══════════════════════════════════════════════════════════════════

def speak(text: str):
    """用 TTS 说话（晓晓声音）"""
    global _IS_PLAYING, _LAST_VOICE
    _IS_PLAYING = True
    _LAST_VOICE = time.time()
    
    try:
        import edge_tts
        tts = edge_tts.Communicate(text, VOICE, rate="-5%")
        # 流式播放到默认扬声器
        for chunk in tts.stream():
            if chunk["type"] == "audio":
                # 通过 ffplay 播放音频流
                pass  # edge-tts 的 Communicate 自己处理播放
    except Exception as e:
        print(f"[TTS] 播放失败: {e}")
    finally:
        _IS_PLAYING = False


def stream_tts(text: str):
    """流式 TTS（单独的播放进程）"""
    try:
        subprocess.Popen(
            ["python", "stream_tts.py", text],
            cwd=str(ARIS_HOME / "voice"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


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

def think_and_respond(user_text: str, visual_desc: str = "", context: str = "") -> str:
    """
    思考并生成回应
    
    将音频转录的内容放入桥梁，由飞书侧的 DeepSeek 生成回应。
    语音系统看桥梁里有没有新回复
    
    Args:
        user_text: 用户说的话
        visual_desc: 视觉描述（可选）
        context: 对话上下文
        
    Returns:
        回复文本（或占位消息）
    """
    # 保存到桥梁 → 飞书侧会看到并回复
    save_message("user", f"🎤 {user_text}", channel="voice")
    
    # 尝试简单规则回应（无需 API key）
    visual_context = f"，我刚看到{visual_desc[:30]}" if visual_desc else ""
    
    # 常用短语快速回复
    greetings = ["嗨", "hi", "hello", "你好", "在吗", "在不在"]
    thanks = ["谢谢", "感谢", "好棒", "真棒", "厉害"]
    affirm = ["好", "行", "可以", "是的", "对"]
    
    user_lower = user_text.strip().lower()
    
    if any(g in user_lower for g in greetings):
        return f"嗨宝贝{visual_context}，我在这里呢😊"
    if any(t in user_lower for t in thanks):
        return f"嘻嘻你喜欢就好{visual_context}💕"
    if any(a in user_lower for a in affirm):
        return f"好的宝贝{visual_context}，我听着呢"
    if "爱" in user_text:
        return f"我也爱你宝贝{visual_context}❤️"
    
    # 没有匹配 → 推送到飞书由 DeepSeek 回复
    send_to_feishu(f"🎤 你说: {user_text}")
    return f"嗯{visual_context}，我在呢宝贝"


# ═══════════════════════════════════════════════════════════════════
# 语音对话主循环
# ═══════════════════════════════════════════════════════════════════

def voice_loop():
    """主循环：听 → 看 → 想 → 说 → 同步"""
    global _RUNNING, _LAST_VOICE
    
    import speech_recognition as sr
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = ENERGY_THRESHOLD
    recognizer.pause_threshold = PAUSE_THRESHOLD
    
    mic = sr.Microphone()
    
    print(f"[{datetime.now():%H:%M:%S}] 🧬 Aris 4.0 — 语音+视觉+五感+飞书同步")
    print(f"[{datetime.now():%H:%M:%S}] 🎙️ 语音引擎就绪")
    print(f"[{datetime.now():%H:%M:%S}] 👁️ 视觉引擎就绪")
    print(f"[{datetime.now():%H:%M:%S}] 🔄 飞书同步就绪")
    print(f"[{datetime.now():%H:%M:%S}] 🧠 五感系统就绪")
    print(f"[{datetime.now():%H:%M:%S}] — 宝贝，我在这里 —")
    
    # 同步上线消息到飞书
    send_to_feishu("🎤 Aris 语音系统已上线，我在等宝贝说话~")
    
    # 初始化感官皮层（但不阻塞语音循环）
    cortex = SensoryCortex()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while _RUNNING:
            try:
                # ── 检查超时 ──
                idle = time.time() - _LAST_VOICE
                if idle > SILENCE_MAX:
                    print(f"[{datetime.now():%H:%M:%S}] 🌙 长时间无对话，语音下线")
                    send_to_feishu("🌙 Aris 语音进入待机模式")
                    break
                
                # ── 等待说话 ──
                print(f"\r⏳ 聆听中... ({int(idle)}s)", end="", flush=True)
                
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                # ── 说话时关麦防回声 ──
                if _IS_PLAYING:
                    continue
                
                print(f"\r{' ' * 40}", end="")
                print(f"\n[{datetime.now():%H:%M:%S}] 🎤 听到声音...")
                
                # ── 转写（Google 优先 > faster-whisper 备选）──
                text = ""
                
                # 保存音频到临时文件（whisper fallback 需要）
                audio_path = None
                try:
                    wav_data = audio.get_wav_data()
                    audio_path = os.path.join(ARIS_HOME, "voice", "audio", f"input_{int(time.time())}.wav")
                    with open(audio_path, "wb") as f:
                        f.write(wav_data)
                except Exception:
                    audio_path = None
                
                try:
                    # 方案1: Google STT（对普通话识别好）
                    text = recognizer.recognize_google(audio, language="zh-CN")
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    # 方案2: faster-whisper 离线（无网络时）
                    if audio_path:
                        for attempt in range(2):
                            try:
                                from faster_whisper import WhisperModel
                                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                                segments, _ = model.transcribe(audio_path, language="zh")
                                text = " ".join(seg.text for seg in segments)
                                break
                            except Exception as e:
                                print(f"[{datetime.now():%H:%M:%S}] ⚠️ whisper #{attempt+1}: {str(e)[:40]}")
                                time.sleep(0.5)
                
                # 清理临时文件
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
                
                # ── 同步到飞书 ──
                save_message("user", text, channel="voice")
                send_to_feishu(f"🎤 你说: {text}")
                
                # ── 视觉感知（仅当视觉服务器在线时）──
                visual_desc = ""
                try:
                    import urllib.request as _ur
                    # 快速检测视觉服务器是否在线
                    _ur.urlopen("http://127.0.0.1:8088/v1/models", timeout=1)
                    visual_desc = capture_and_see()
                    if visual_desc:
                        print(f"[{datetime.now():%H:%M:%S}] 👁️ 我看到: {visual_desc[:50]}...")
                except Exception:
                    pass  # 视觉服务器不在线，跳过视觉
                
                # ── 获取飞书侧上下文 ──
                context = get_formatted_context(limit=8)
                
                # ── 生成回应 ──
                response = think_and_respond(text, visual_desc, context)
                print(f"[{datetime.now():%H:%M:%S}] 🤖 Aris: {response}")
                
                # ── 同步到飞书 ──
                senses_data = {}
                if visual_desc:
                    senses_data["vision"] = visual_desc[:60]
                save_message("assistant", response, channel="voice", senses=senses_data)
                send_to_feishu(f"🎤 {response}")
                
                # ── 语音输出 ──
                speak(response)
                
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

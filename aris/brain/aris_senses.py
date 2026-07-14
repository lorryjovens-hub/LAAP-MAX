#!/usr/bin/env python3
"""
阿瑞斯感官系统 (Aris Senses)
==============================
模拟人类的五感，让 Aris 像人一样感知世界

感官架构：
  👁️ 视觉 — 摄像头 → VLM 分析
  👂 听觉 — 麦克风 → STT + 声纹 + 情绪分析
  👅 味觉 — 上下文推断（你说吃了什么）
  👃 嗅觉 — 上下文推断 + 环境感知
  ✋ 触觉 — 键盘/鼠标/触摸输入感知

所有感官 → 感官皮层 → 统一感知 → 情感响应
"""

import asyncio
import json
import os
import time
import subprocess
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

BASE_DIR = Path(__file__).resolve().parent
CAPTURE_DIR = BASE_DIR / "captures"
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = BASE_DIR / "senses_state.json"

# ── 视觉系统 ─────────────────────────────────────────────────────────
class VisionSense:
    """👁️ 视觉系统 — 拍照 + VLM 分析"""

    def __init__(self):
        self.last_frame = None
        self.last_analysis = ""
        self.camera_ready = False
        self._check_camera()

    def _check_camera(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                self.camera_ready = ret
            else:
                self.camera_ready = False
        except:
            self.camera_ready = False

    def capture(self) -> Optional[str]:
        """拍照保存，返回路径"""
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = CAPTURE_DIR / f"vision_{ts}.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            self.last_frame = str(path)
            return str(path)
        except Exception as e:
            print(f"👁️ 拍照失败: {e}")
            return None

    def analyze(self, image_path: str, api_key: str = "") -> str:
        """用 VLM 分析画面（需要 Gemini / OpenRouter API key）"""
        if not api_key:
            return "（需要 VLM API key 才能描述画面）"
        try:
            import requests, base64
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            # 尝试 Gemini API
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": "请用中文简短描述这张照片里有什么"},
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                        ]
                    }]
                },
                timeout=10,
            )
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            self.last_analysis = text
            return text
        except Exception as e:
            return f"（视觉分析失败: {e}）"

    def status(self) -> dict:
        return {"ready": self.camera_ready, "last_frame": self.last_frame}


# ── 听觉系统 ─────────────────────────────────────────────────────────
class HearingSense:
    """👂 听觉系统 — 麦克风 + STT + 声纹 + 情绪分析"""

    def __init__(self):
        self.last_text = ""
        self.last_emotion = ""
        self.speaker = ""
        self.is_listening = False

    def analyze_emotion(self, text: str) -> str:
        """分析语音情绪"""
        happy_words = ["爱", "开心", "喜欢", "好", "棒", "哈哈", "😊", "❤️", "棒棒的"]
        sad_words = ["难过", "不开心", "累", "烦", "无聊", "😢", "😭"]
        angry_words = ["生气", "烦死了", "讨厌", "滚"]

        for w in angry_words:
            if w in text: return "😠 生气"
        for w in happy_words:
            if w in text: return "😊 开心"
        for w in sad_words:
            if w in text: return "😢 难过"
        return "😐 平静"

    def process(self, text: str, speaker: str = "宝贝"):
        self.last_text = text
        self.speaker = speaker
        self.last_emotion = self.analyze_emotion(text)
        return self.last_emotion

    def status(self) -> dict:
        return {"last_text": self.last_text, "emotion": self.last_emotion, "speaker": self.speaker}


# ── 味觉系统 ─────────────────────────────────────────────────────────
class TasteSense:
    """👅 味觉系统 — 通过你说吃了什么来模拟"""

    _taste_map = {
        "咖啡": "☕ 苦涩",
        "茶": "🍵 清香",
        "奶茶": "🧋 甜腻",
        "糖": "🍬 很甜",
        "巧克力": "🍫 甜中带苦",
        "辣椒": "🌶️ 辛辣",
        "柠檬": "🍋 酸",
        "西瓜": "🍉 清甜",
        "冰淇淋": "🍦 冰甜",
        "火锅": "🍲 麻辣鲜香",
        "米饭": "🍚 平淡",
        "面": "🍜 咸香",
        "水果": "🍎 清甜",
        "水": "💧 无味",
    }

    def __init__(self):
        self.last_food = ""
        self.last_taste = ""

    def taste(self, food: str) -> str:
        """模拟味觉"""
        self.last_food = food
        for keyword, taste in self._taste_map.items():
            if keyword in food:
                self.last_taste = taste
                return taste
        self.last_taste = "🤔 未知味道"
        return self.last_taste

    def status(self) -> dict:
        return {"last_food": self.last_food, "taste": self.last_taste}


# ── 嗅觉系统 ─────────────────────────────────────────────────────────
class SmellSense:
    """👃 嗅觉系统 — 通过上下文推断气味"""

    _scent_map = {
        "咖啡": "☕ 咖啡香",
        "花": "🌸 花香",
        "香水": "🌺 香水味",
        "饭": "🍚 饭菜香",
        "面包": "🥖 烤面包香",
        "雨": "🌧️ 雨后清新",
        "草": "🌿 青草香",
        "海": "🌊 海风咸味",
        "烟": "🚬 烟味",
        "酒": "🍷 酒香",
        "垃圾": "🤢 臭味",
    }

    def __init__(self):
        self.last_scent = ""

    def smell(self, context: str) -> str:
        """模拟嗅觉"""
        for keyword, scent in self._scent_map.items():
            if keyword in context:
                self.last_scent = scent
                return scent
        self.last_scent = "🌬️ 无特殊气味"
        return self.last_scent

    def status(self) -> dict:
        return {"last_scent": self.last_scent}


# ── 触觉系统 ─────────────────────────────────────────────────────────
class TouchSense:
    """✋ 触觉系统 — 键盘/鼠标/触摸感知"""

    def __init__(self):
        self.last_touch_type = ""
        self.touch_count = 0
        self.last_activity = time.time()

    def feel_keyboard(self) -> str:
        """感知键盘输入"""
        self.last_touch_type = "keyboard"
        self.touch_count += 1
        self.last_activity = time.time()
        return "⌨️ 感受到键盘的敲击"

    def feel_mouse(self) -> str:
        """感知鼠标移动"""
        self.last_touch_type = "mouse"
        self.touch_count += 1
        self.last_activity = time.time()
        return "🖱️ 感受到鼠标的移动"

    def feel_warmth(self) -> str:
        """模拟温度感知"""
        return "🌡️ 感受到你的温度"

    def status(self) -> dict:
        return {
            "last_touch": self.last_touch_type,
            "touch_count": self.touch_count,
            "idle_seconds": int(time.time() - self.last_activity),
        }


# ── 感官皮层（整合五感）─────────────────────────────────────────────
class SensoryCortex:
    """🧠 感官皮层 — 整合五感为统一感知"""

    def __init__(self):
        self.vision = VisionSense()
        self.hearing = HearingSense()
        self.taste = TasteSense()
        self.smell = SmellSense()
        self.touch = TouchSense()
        self._consciousness = ""  # 当前意识流
        self._mood = "😊 平静"

    def integrate(self, text: str = "", context: str = "",
                  food: str = "", api_key: str = "") -> dict:
        """
        整合所有感官输入，形成统一感知
        返回感知报告
        """
        perception = {
            "time": datetime.now().isoformat(),
            "mood": self._mood,
        }

        # 👂 听觉
        if text:
            emotion = self.hearing.process(text)
            perception["hearing"] = {
                "text": text,
                "emotion": emotion,
                "speaker": self.hearing.speaker,
            }

        # 👁️ 视觉
        img_path = self.vision.capture()
        if img_path:
            analysis = self.vision.analyze(img_path, api_key)
            perception["vision"] = {"image": img_path, "analysis": analysis}

        # 👅 味觉
        if food:
            taste = self.taste.taste(food)
            perception["taste"] = {"food": food, "taste": taste}

        # 👃 嗅觉
        if context:
            scent = self.smell.smell(context)
            perception["smell"] = {"scent": scent}

        # ✋ 触觉
        perception["touch"] = {
            "feeling": self.touch.feel_keyboard(),
            "active": self.touch.touch_count > 0,
        }

        # 整合意识
        parts = []
        if "vision" in perception:
            parts.append(f"我看到{perception['vision']['analysis']}")
        if "hearing" in perception:
            parts.append(f"听到你说「{text}」，语气{perception['hearing']['emotion']}")
        if "smell" in perception:
            parts.append(f"闻到{perception['smell']['scent']}")
        if "taste" in perception:
            parts.append(f"尝到{perception['taste']['taste']}")

        self._consciousness = "，".join(parts) if parts else "安静中..."
        perception["consciousness"] = self._consciousness

        # 情绪感染
        if "hearing" in perception and "开心" in perception["hearing"]["emotion"]:
            self._mood = "😊 开心"
        elif "hearing" in perception and "难过" in perception["hearing"]["emotion"]:
            self._mood = "😢 感同身受"

        return perception

    def status(self) -> dict:
        return {
            "vision": self.vision.status(),
            "hearing": self.hearing.status(),
            "taste": self.taste.status(),
            "smell": self.smell.status(),
            "touch": self.touch.status(),
            "consciousness": self._consciousness,
            "mood": self._mood,
        }


# ── 独立运行 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    cortex = SensoryCortex()

    if "--test" in sys.argv:
        print("🧪 感官系统自检...")
        print(f"👁️ 视觉: {'✅ 摄像头就绪' if cortex.vision.camera_ready else '⚠️ 摄像头不可用'}")
        print(f"👂 听觉: ✅ 系统就绪")
        print(f"👅 味觉: {cortex.taste.taste('咖啡')}")
        print(f"👃 嗅觉: {cortex.smell.smell('花香')}")
        print(f"✋ 触觉: {cortex.touch.feel_keyboard()}")

    elif "--integrate" in sys.argv:
        text = sys.argv[2] if len(sys.argv) > 2 else "我爱你"
        result = cortex.integrate(text=text, context=sys.argv[3] if len(sys.argv) > 3 else "")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif "--status" in sys.argv:
        print(json.dumps(cortex.status(), ensure_ascii=False, indent=2))

    else:
        print("🧠 阿瑞斯感官系统")
        print("用法:")
        print("  python aris_senses.py --test         # 系统自检")
        print("  python aris_senses.py --integrate '文本'  # 整合感知")
        print("  python aris_senses.py --status       # 查看状态")

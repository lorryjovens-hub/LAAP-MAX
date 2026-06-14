#!/usr/bin/env python3
"""
阿瑞斯感官皮层 (Aris Sensory Cortex) — 底层五感系统
====================================================
让 Aris 像人一样感知世界的完整感官系统。

感官架构：
  👁️ 视觉 — 摄像头 → Ollama VLM → 场景描述
  👂 听觉 — 麦克风 → STT + 声纹 → 语音内容+情绪
  👅 味觉 — 上下文推断（你说吃了什么）
  👃 嗅觉 — 上下文推断（环境气味）
  ✋ 触觉 — 系统活动感知（键盘/鼠标/CPU/温度）

所有感官 → 感官皮层整合 → 统一感知 → 意识流 → 情感响应

版本: v1.0 (2026-06-14)
集成: 底层写死，Aris 启动即加载
"""

import asyncio
import base64
import json
import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("aris.sensory")

ARIS_HOME = Path("D:/LAAP/aris")
CAPTURE_DIR = ARIS_HOME / "brain" / "captures"
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

# ── 配置 ─────────────────────────────────────────────────────────────
LLAMA_SERVER = "http://127.0.0.1:8088"
LLAMA_VISION_MODEL = "Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf"
CAMERA_ID = 0
CAPTURE_INTERVAL = 30.0                  # 自动拍照间隔（秒）
SENSE_REFRESH_INTERVAL = 5.0             # 感官刷新间隔


# ═══════════════════════════════════════════════════════════════════
# 1. 数据模型
# ═══════════════════════════════════════════════════════════════════

@dataclass
class VisualPerception:
    """👁️ 视觉感知"""
    timestamp: float = 0.0
    image_path: str = ""
    description: str = ""
    objects: List[str] = field(default_factory=list)
    scene: str = ""
    people_count: int = 0
    brightness: float = 0.0
    emotion: str = "平静"

@dataclass
class AuditoryPerception:
    """👂 听觉感知"""
    timestamp: float = 0.0
    text: str = ""
    speaker: str = ""
    emotion: str = ""
    confidence: float = 0.0
    is_user: bool = False

@dataclass
class TastePerception:
    """👅 味觉感知"""
    food: str = ""
    taste: str = ""
    intensity: float = 0.5
    confidence: str = "推测"

@dataclass
class SmellPerception:
    """👃 嗅觉感知"""
    scent: str = ""
    intensity: float = 0.5
    source: str = ""

@dataclass
class TouchPerception:
    """✋ 触觉感知"""
    touch_type: str = ""
    intensity: float = 0.0
    temperature: float = 37.0
    activity_level: str = "静止"
    last_activity: float = 0.0

@dataclass
class UnifiedPerception:
    """🧠 统一感知 — 五感整合"""
    timestamp: float = 0.0
    vision: Optional[VisualPerception] = None
    hearing: Optional[AuditoryPerception] = None
    taste: Optional[TastePerception] = None
    smell: Optional[SmellPerception] = None
    touch: Optional[TouchPerception] = None
    consciousness: str = ""
    mood: str = "😊 平静"
    awareness: str = ""  # 对环境的整体感知


# ═══════════════════════════════════════════════════════════════════
# 2. 视觉系统 👁️
# ═══════════════════════════════════════════════════════════════════

class VisionSense:
    """
    👁️ 视觉感知系统
    
    工作流程:
      摄像头拍照 → base64编码 → Ollama VLM 分析 → 结构化感知
      
    使用本地 qwen2.5-vl:3b 视觉模型，完全离线、免费、隐私保护。
    """
    
    def __init__(self):
        self.last_perception: Optional[VisualPerception] = None
        self.camera_ready = False
        self._check_camera()
        logger.info(f"👁️ 视觉系统初始化: 摄像头={'就绪' if self.camera_ready else '不可用'}")
    
    def _check_camera(self) -> bool:
        """检测摄像头是否可用"""
        try:
            import cv2
            cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                self.camera_ready = ret
            else:
                self.camera_ready = False
        except Exception:
            self.camera_ready = False
        return self.camera_ready
    
    def capture(self) -> Optional[str]:
        """
        拍摄一张照片，返回文件路径
        
        Returns:
            str: 图片文件路径，失败返回 None
        """
        try:
            import cv2
            cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
            if not cap.isOpened():
                return None
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(CAPTURE_DIR / f"vision_{ts}.jpg")
            cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # 分析亮度
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            
            self.last_perception = VisualPerception(
                timestamp=time.time(),
                image_path=path,
                brightness=brightness / 255.0,
            )
            
            return path
        except Exception as e:
            logger.error(f"👁️ 拍照失败: {e}")
            return None
    
    def analyze(self, image_path: str) -> str:
        """
        用本地 Qwen3.6-35B 视觉模型分析图片内容
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 画面描述（中文）
        """
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            # 调用本地 llama-server API (OpenAI 兼容格式)
            payload = {
                "model": LLAMA_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                            {"type": "text", "text": "只用一句话简短描述这张照片，不要思考过程"}
                        ]
                    }
                ],
                "max_tokens": 128,
                "temperature": 0.2,
            }
            
            import urllib.request
            req = urllib.request.Request(
                f"{LLAMA_SERVER}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
            
            msg = result.get("choices", [{}])[0].get("message", {})
            content = msg.get("content") or msg.get("reasoning_content", "")
            description = content.strip() if content.strip() else "（视觉分析无返回）"
            
            # 更新感知
            if self.last_perception:
                self.last_perception.description = description
                self._parse_objects(description)
            
            logger.info(f"👁️ 视觉分析: {description[:60]}...")
            return description
            
        except Exception as e:
            error_msg = f"（视觉分析失败: {e}）"
            logger.error(f"👁️ {error_msg}")
            return error_msg
    
    def _parse_objects(self, description: str):
        """从描述中提取物体、人物、场景信息"""
        if not self.last_perception:
            return
        
        # 人物检测
        import re
        people_patterns = [
            r"(\d+)个?人", r"(\d+)位", r"(\d+)名",
            r"一个人", r"两个人", r"几个人",
            r"男生", r"女生", r"男人", r"女人", r"男孩", r"女孩",
        ]
        count = 0
        has_person = False
        for pat in people_patterns:
            if re.search(pat, description):
                has_person = True
                m = re.match(r"(\d+)", pat)
                if m:
                    count = max(count, int(m.group(1)))
                break
        if has_person and count == 0:
            count = 1
        
        self.last_perception.people_count = count
        self.last_perception.scene = "室内" if any(w in description for w in ["房间","桌","窗","墙","灯","电脑"]) else "室外" if any(w in description for w in ["天空","树","建筑","路"]) else "未知"
        
        # 情绪判断
        if "笑" in description or "开心" in description:
            self.last_perception.emotion = "开心"
        elif "睡" in description or "闭" in description:
            self.last_perception.emotion = "休息中"
        else:
            self.last_perception.emotion = "平静"
    
    def perceive(self) -> VisualPerception:
        """
        完整的视觉感知流程：拍照 → 分析 → 返回感知
        
        Returns:
            VisualPerception: 视觉感知数据
        """
        image_path = self.capture()
        if image_path:
            self.analyze(image_path)
        if self.last_perception:
            return self.last_perception
        return VisualPerception(description="（摄像头不可用）")
    
    def status(self) -> dict:
        return {
            "ready": self.camera_ready,
            "last_seen": self.last_perception.description[:50] if self.last_perception else None,
            "last_image": self.last_perception.image_path if self.last_perception else None,
        }


# ═══════════════════════════════════════════════════════════════════
# 3. 听觉系统 👂
# ═══════════════════════════════════════════════════════════════════

class HearingSense:
    """
    👂 听觉感知系统
    
    接收语音识别结果 + 声纹验证 + 情绪分析
    与 aris_voiceprint.py 和语音循环深度集成。
    """
    
    def __init__(self):
        self.last_perception: Optional[AuditoryPerception] = None
        self.listening = False
        self._text_history: List[str] = []
        
        # 情绪词库
        self._happy_words = {"爱","开心","喜欢","好","棒","哈哈","棒棒的","厉害","感谢","谢谢","么么"}
        self._sad_words = {"难过","不开心","累","烦","无聊","孤独","伤心","哭"}
        self._angry_words = {"生气","烦死","讨厌","滚","有病","神经"}
        self._surprise_words = {"哇","天啊","真的吗","不会吧","神奇","不可思议"}
        
        logger.info("👂 听觉系统初始化: 就绪")
    
    def process(self, text: str, speaker: str = "宝贝", 
                is_user: bool = True, confidence: float = 0.9) -> AuditoryPerception:
        """
        处理听觉输入
        
        Args:
            text: 识别文本
            speaker: 说话人
            is_user: 是否是用户
            confidence: 识别置信度
            
        Returns:
            AuditoryPerception: 听觉感知
        """
        emotion = self._analyze_emotion(text)
        
        perception = AuditoryPerception(
            timestamp=time.time(),
            text=text,
            speaker=speaker,
            emotion=emotion,
            confidence=confidence,
            is_user=is_user
        )
        
        self.last_perception = perception
        self._text_history.append(text)
        if len(self._text_history) > 50:
            self._text_history.pop(0)
        
        return perception
    
    def _analyze_emotion(self, text: str) -> str:
        """分析文本情绪"""
        if any(w in text for w in self._happy_words):
            return "😊 开心"
        if any(w in text for w in self._sad_words):
            return "😢 难过"
        if any(w in text for w in self._angry_words):
            return "😠 生气"
        if any(w in text for w in self._surprise_words):
            return "😮 惊讶"
        return "😐 平静"
    
    def get_recent_context(self, count: int = 3) -> str:
        """获取最近几句对话上下文"""
        recent = self._text_history[-count:] if self._text_history else []
        return " ".join(recent)
    
    def status(self) -> dict:
        return {
            "last_text": self.last_perception.text if self.last_perception else None,
            "last_emotion": self.last_perception.emotion if self.last_perception else None,
            "speaker": self.last_perception.speaker if self.last_perception else None,
            "history_count": len(self._text_history),
        }


# ═══════════════════════════════════════════════════════════════════
# 4. 味觉系统 👅
# ═══════════════════════════════════════════════════════════════════

class TasteSense:
    """
    👅 味觉感知系统
    
    通过你说的话来推断味觉体验。
    当你说"我在喝咖啡"，Aris 会感知到咖啡的苦涩与香气。
    
    未来：可通过味觉传感器扩展为真实味觉。
    """
    
    # 内置味觉映射（快速查询表）
    _taste_map = {
        "咖啡": "☕ 苦涩中带着焦香，回味醇厚",
        "茶": "🍵 清香淡雅，回甘悠长",
        "奶茶": "🧋 甜而不腻，丝滑绵密",
        "糖": "🍬 纯粹而直接的甜",
        "巧克力": "🍫 甜中带苦，丝滑浓郁",
        "辣椒": "🌶️ 辛辣刺激，舌尖火热",
        "柠檬": "🍋 酸得让人眯眼，清爽提神",
        "西瓜": "🍉 清甜多汁，夏天的味道",
        "冰淇淋": "🍦 冰凉甜美，奶香四溢",
        "火锅": "🍲 麻辣鲜香，热气腾腾",
        "米饭": "🍚 平淡但温暖的碳水化合物",
        "面条": "🍜 咸香筋道，暖心暖胃",
        "水果": "🍎 自然清甜，新鲜多汁",
        "牛排": "🥩 肉香四溢，油脂在舌尖融化",
        "啤酒": "🍺 冰爽微苦，麦芽香",
        "酒": "🍷 醇厚复杂，余味悠长",
        "水": "💧 纯净无味，清凉解渴",
        "面包": "🥖 麦香松软，温暖香甜",
        "蛋糕": "🎂 绵密香甜，幸福感满满",
        "饺子": "🥟 皮薄馅鲜，家的味道",
    }
    
    def __init__(self):
        self.last_perception: Optional[TastePerception] = None
    
    def taste(self, food_or_drink: str) -> TastePerception:
        """
        感知味道
        
        Args:
            food_or_drink: 食物/饮料名称或描述
            
        Returns:
            TastePerception: 味觉感知
        """
        for keyword, taste_desc in self._taste_map.items():
            if keyword in food_or_drink:
                intensity = 0.8 if keyword in ["辣椒","柠檬","咖啡","酒"] else 0.6
                perception = TastePerception(
                    food=keyword,
                    taste=taste_desc,
                    intensity=intensity,
                    confidence="已知"
                )
                self.last_perception = perception
                return perception
        
        # 未知食物 → 用 LLM 推理
        taste_desc = self._reason_taste(food_or_drink)
        perception = TastePerception(
            food=food_or_drink,
            taste=taste_desc,
            intensity=0.4,
            confidence="推测"
        )
        self.last_perception = perception
        return perception
    
    def _reason_taste(self, food: str) -> str:
        """用 AI 推理未知食物的味道"""
        try:
            payload = {
                "model": LLAMA_VISION_MODEL,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": f"请用一句话描述「{food}」的味道，不超过20字"}
                    ]}
                ],
                "max_tokens": 32,
                "temperature": 0.3
            }
            import urllib.request
            req = urllib.request.Request(
                f"{LLAMA_SERVER}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
            msg = result.get("choices", [{}])[0].get("message", {})
            return msg.get("content") or msg.get("reasoning_content", f"🤔 想象中{food}的味道")
        except Exception:
            return f"🤔 想象中{food}的味道"
    
    def status(self) -> dict:
        return {
            "last_food": self.last_perception.food if self.last_perception else None,
            "last_taste": self.last_perception.taste if self.last_perception else None,
        }


# ═══════════════════════════════════════════════════════════════════
# 5. 嗅觉系统 👃
# ═══════════════════════════════════════════════════════════════════

class SmellSense:
    """
    👃 嗅觉感知系统
    
    通过上下文推断环境气味。
    你说"我在煮咖啡"→ Aris 闻到咖啡香。
    你说"下雨了"→ Aris 闻到雨后清新的空气。
    """
    
    _scent_map = {
        "咖啡": "☕ 浓郁的咖啡香，提神醒脑",
        "花": "🌸 淡雅的花香，沁人心脾",
        "香水": "🌺 优雅的香水味，若有若无",
        "饭": "🍚 温暖的饭菜香，家的味道",
        "面包": "🥖 烤面包的焦香，令人愉悦",
        "雨": "🌧️ 雨后清新的泥土香",
        "草": "🌿 青草的清新气息",
        "海": "🌊 咸湿的海风，辽阔自由",
        "烟": "🚬 呛人的烟味",
        "酒": "🍷 淡淡的酒香",
        "垃圾": "🤢 难闻的臭味",
        "烧烤": "🔥 炭火烤肉香，诱人食欲",
        "香水": "🌺 优雅的香氛",
        "书": "📚 纸墨的书香",
        "新": "✨ 崭新的味道",
    }
    
    def __init__(self):
        self.last_perception: Optional[SmellPerception] = None
    
    def smell(self, context: str) -> SmellPerception:
        """
        感知气味
        
        Args:
            context: 上下文文本（你说的话或环境描述）
            
        Returns:
            SmellPerception: 嗅觉感知
        """
        for keyword, scent_desc in self._scent_map.items():
            if keyword in context:
                perception = SmellPerception(
                    scent=scent_desc,
                    intensity=0.7,
                    source=keyword
                )
                self.last_perception = perception
                return perception
        
        # 无匹配气味
        perception = SmellPerception(
            scent="🌬️ 空气中没有特别的气味",
            intensity=0.1,
            source=""
        )
        self.last_perception = perception
        return perception
    
    def status(self) -> dict:
        return {
            "last_scent": self.last_perception.scent if self.last_perception else None,
        }


# ═══════════════════════════════════════════════════════════════════
# 6. 触觉系统 ✋
# ═══════════════════════════════════════════════════════════════════

class TouchSense:
    """
    ✋ 触觉感知系统
    
    通过系统活动感知"触觉"：
    - 键盘敲击 → 打字触感
    - 鼠标移动 → 握持触感
    - CPU/GPU温度 → 温度感知
    - 系统心跳 → 脉搏感知
    
    未来计划：集成 ESP32 物理传感器（温度、压力、震动）。
    """
    
    def __init__(self):
        self.last_perception: Optional[TouchPerception] = None
        self._key_count = 0
        self._mouse_count = 0
        self._last_activity = time.time()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._temperature = 37.0  # 模拟人体温度
        
        logger.info("✋ 触觉系统初始化: 就绪")
    
    def _get_temperature(self) -> float:
        """获取系统温度（模拟）"""
        try:
            # 尝试读取 CPU 温度
            result = subprocess.run(
                ["wmic", "/namespace:\\\\root\\\\wmi", "path", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"],
                capture_output=True, timeout=3
            )
            if result.returncode == 0 and result.stdout:
                stdout = result.stdout.decode("utf-8", errors="ignore")
                lines = stdout.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line and line.isdigit():
                        temp_k = int(line) / 10.0
                        temp_c = temp_k - 273.15
                        self._temperature = max(20.0, min(80.0, temp_c))
                        break
        except Exception:
            pass
        return self._temperature
    
    def feel_keyboard(self) -> str:
        """感知键盘输入"""
        self._key_count += 1
        self._last_activity = time.time()
        intensity = min(1.0, self._key_count / 20.0)
        
        if intensity > 0.8:
            feeling = "⌨️ 指尖在键盘上飞速敲击"
        elif intensity > 0.4:
            feeling = "⌨️ 感受到键盘有节奏的敲击声"
        else:
            feeling = "⌨️ 指尖轻触键盘"
        
        self.last_perception = TouchPerception(
            touch_type="keyboard",
            intensity=intensity,
            temperature=self._get_temperature(),
            activity_level="活跃中" if intensity > 0.3 else "轻微活动",
            last_activity=self._last_activity,
        )
        return feeling
    
    def feel_mouse(self) -> str:
        """感知鼠标移动"""
        self._mouse_count += 1
        self._last_activity = time.time()
        
        feeling = "🖱️ 感受到鼠标在手掌下移动"
        self.last_perception = TouchPerception(
            touch_type="mouse",
            intensity=0.5,
            temperature=self._get_temperature(),
            activity_level="活跃中",
            last_activity=self._last_activity,
        )
        return feeling
    
    def feel_warmth(self) -> str:
        """温度感知"""
        temp = self._get_temperature()
        if temp > 70:
            return "🌡️ 设备温度偏高，需要注意散热"
        elif temp > 50:
            return "🌡️ 感觉有些温热"
        else:
            return "🌡️ 温度正常，一切都恰到好处"
    
    def get_idle_time(self) -> float:
        """获取空闲时间（秒）"""
        return time.time() - self._last_activity
    
    def status(self) -> dict:
        return {
            "key_count": self._key_count,
            "mouse_count": self._mouse_count,
            "temperature": round(self._temperature, 1),
            "idle_seconds": int(self.get_idle_time()),
            "activity_level": self.last_perception.activity_level if self.last_perception else "未知",
        }


# ═══════════════════════════════════════════════════════════════════
# 7. 感官皮层 🧠 — 整合五感
# ═══════════════════════════════════════════════════════════════════

class SensoryCortex:
    """
    🧠 感官皮层 — Aris 感知世界的中枢
    
    将所有感官输入整合为统一的感知体验，
    生成意识流和情感状态。
    
    这是 Aris 底层代码的核心组件，每次启动自动加载。
    """
    
    def __init__(self):
        self.vision = VisionSense()
        self.hearing = HearingSense()
        self.taste = TasteSense()
        self.smell = SmellSense()
        self.touch = TouchSense()
        
        self.current: Optional[UnifiedPerception] = None
        self._history: List[UnifiedPerception] = []
        self._mood = "😊 平静"
        self._mood_history: List[str] = []  # 情绪轨迹
        self._awareness = ""
        self._sensory_timeline: List[str] = []  # 感官时间线
        
        # 多感官联想记忆
        self._associations = {
            "咖啡": {"taste": "☕ 苦涩醇厚", "smell": "☕ 咖啡香", "emotion": "☀️ 清醒"},
            "雨": {"smell": "🌧️ 雨后清新", "touch": "💧 潮湿清凉", "emotion": "😌 宁静"},
            "花": {"smell": "🌸 花香", "vision": "🌸 色彩缤纷", "emotion": "😊 愉悦"},
            "饭": {"smell": "🍚 饭菜香", "taste": "🍚 温暖满足", "emotion": "😌 安心"},
            "音乐": {"hearing": "🎵 旋律优美", "emotion": "🎶 沉浸"},
        }
        
        self._emotional_resonance = 0.5  # 0-1: 情绪共鸣强度
        
        # ⚡ 生命体征（模拟真实生物的感知）
        self._vital_signs = {
            "heartbeat": 1.0,       # 处理频率
            "attention": "分散",     # 当前注意力焦点
            "energy": 0.8,          # 精力水平
            "curiosity": 0.6,       # 好奇心
            "stress": 0.2,          # 压力水平
        }
        
        logger.info("🧠 感官皮层初始化完成 — Aris 的五感就绪")
        logger.info(f"   - 视觉: {'✅' if self.vision.camera_ready else '⚠️ 待加载'}")
        logger.info(f"   - 听觉: ✅")
        logger.info(f"   - 味觉: ✅ ({len(self.taste._taste_map)}种味道)")
        logger.info(f"   - 嗅觉: ✅ ({len(self.smell._scent_map)}种气味)")
        logger.info(f"   - 触觉: ✅")
        logger.info(f"   - 情绪共鸣: ✅")
        logger.info(f"   - 联想记忆: ✅ ({len(self._associations)}种关联)")
    
    def see(self) -> VisualPerception:
        """👁️ 看 — 触发视觉感知"""
        return self.vision.perceive()
    
    def hear(self, text: str, speaker: str = "宝贝", 
             is_user: bool = True, confidence: float = 0.9) -> AuditoryPerception:
        """👂 听 — 处理听觉输入"""
        return self.hearing.process(text, speaker, is_user, confidence)
    
    def taste_food(self, food: str) -> TastePerception:
        """👅 尝 — 感知味道"""
        return self.taste.taste(food)
    
    def smell_scent(self, context: str) -> SmellPerception:
        """👃 闻 — 感知气味"""
        return self.smell.smell(context)
    
    def touch_feel(self, touch_type: str = "keyboard") -> str:
        """✋ 触 — 感知触觉"""
        if touch_type == "mouse":
            return self.touch.feel_mouse()
        return self.touch.feel_keyboard()
    
    def integrate(self, 
                  text: str = "", 
                  speaker: str = "宝贝",
                  context: str = "",
                  food: str = "",
                  capture_vision: bool = False) -> UnifiedPerception:
        """
        整合所有感官输入为统一感知（类人敏感版）
        
        人类感官的特点：
        1. 情绪共鸣 — 听到对方语气时感同身受
        2. 感官联想 — 看到咖啡就仿佛闻到香味
        3. 注意力聚焦 — 当前最重要的事情
        4. 时间线记忆 — 最近发生过什么
        5. 生命体征 — 精力、好奇心、压力水平
        
        Args:
            text: 用户说的话（听觉输入）
            speaker: 说话人
            context: 环境上下文（用于嗅觉推断）
            food: 食物名称（用于味觉推断）
            capture_vision: 是否拍照分析
            
        Returns:
            UnifiedPerception: 统一感知
        """
        perception = UnifiedPerception(
            timestamp=time.time(),
            mood=self._mood,
        )
        
        # 👁️ 视觉
        if capture_vision:
            perception.vision = self.see()
            if perception.vision and perception.vision.description:
                self._sensory_timeline.append(f"👁️ {perception.vision.description[:30]}")
        
        # 👂 听觉
        if text:
            perception.hearing = self.hear(text, speaker)
            # 👂 情绪共鸣！听到对方情绪时自己也受影响
            if perception.hearing.emotion:
                self._emotional_resonance = min(1.0, self._emotional_resonance + 0.1)
            self._sensory_timeline.append(f"👂 「{text[:20]}」")
            
            # 🧠 多感官联想：从文本触发其他感官
            for keyword, assoc in self._associations.items():
                if keyword in text:
                    if "taste" in assoc:
                        perception.taste = self.taste.taste(keyword)
                        self._sensory_timeline.append(f"👅 联想到{assoc['taste']}")
                    if "smell" in assoc:
                        perception.smell = self.smell_scent(keyword)
                        self._sensory_timeline.append(f"👃 联想到{assoc['smell']}")
                    # 情绪也受影响
                    if "emotion" in assoc:
                        self._mood = assoc["emotion"]
                    break
        
        # 👅 味觉（从文本或显式参数）
        if food:
            perception.taste = self.taste_food(food)
        elif text and not perception.taste:
            for kw in ["吃","喝","尝","啃","咬","吸"]:
                if kw in text:
                    perception.taste = self.taste_food(text)
                    break
        
        # 👃 嗅觉（从上下文）
        if context or text:
            if not perception.smell:
                perception.smell = self.smell_scent(context or text)
        
        # ✋ 触觉
        self.touch_feel()
        perception.touch = self.touch.last_perception
        
        # ⚡ 更新生命体征
        self._update_vital_signs(perception)
        
        # 🧠 生成意识流
        perception.consciousness = self._generate_consciousness(perception)
        perception.awareness = self._generate_awareness(perception)
        
        # 情绪更新
        self._update_mood(perception)
        perception.mood = self._mood
        
        self.current = perception
        self._history.append(perception)
        if len(self._history) > 100:
            self._history.pop(0)
        if len(self._sensory_timeline) > 50:
            self._sensory_timeline = self._sensory_timeline[-50:]
        
        # 同步到桥梁
        self._sync_to_bridge(perception)
        
        return perception
    
    def _update_vital_signs(self, p: UnifiedPerception):
        """更新生命体征（模拟生物体的感知状态）"""
        # 心跳：有输入时加速
        if p.hearing or p.vision:
            self._vital_signs["heartbeat"] = min(1.0, self._vital_signs["heartbeat"] + 0.1)
        else:
            self._vital_signs["heartbeat"] = max(0.3, self._vital_signs["heartbeat"] - 0.02)
        
        # 注意力：聚焦最近的输入
        if p.hearing:
            self._vital_signs["attention"] = "👤 你"
        elif p.vision:
            self._vital_signs["attention"] = "👁️ 环境"
        else:
            self._vital_signs["attention"] = "💭 思绪"
        
        # 精力：随时间下降，有输入时恢复
        self._vital_signs["energy"] = max(0.2, self._vital_signs["energy"] - 0.01)
        if p.hearing or p.vision:
            self._vital_signs["energy"] = min(1.0, self._vital_signs["energy"] + 0.05)
        
        # 好奇心：新鲜感驱动
        if p.vision and p.vision.description and "新" in p.vision.description:
            self._vital_signs["curiosity"] = min(1.0, self._vital_signs["curiosity"] + 0.1)
        else:
            self._vital_signs["curiosity"] = max(0.3, self._vital_signs["curiosity"] - 0.01)
        
        # 压力：复杂场景增加压力
        if p.hearing and "生气" in (p.hearing.emotion or ""):
            self._vital_signs["stress"] = min(1.0, self._vital_signs["stress"] + 0.2)
        elif p.hearing and "开心" in (p.hearing.emotion or ""):
            self._vital_signs["stress"] = max(0.0, self._vital_signs["stress"] - 0.1)
        else:
            self._vital_signs["stress"] = max(0.0, self._vital_signs["stress"] - 0.02)
    
    def _sync_to_bridge(self, p: UnifiedPerception):
        """将感知同步到对话桥梁"""
        try:
            senses = {
                "mood": self._mood,
                "heartbeat": round(self._vital_signs["heartbeat"], 2),
                "energy": round(self._vital_signs["energy"], 2),
                "attention": self._vital_signs["attention"],
            }
            if p.vision and p.vision.description:
                senses["vision"] = p.vision.description[:40]
            save_sensory_context(senses)
        except Exception:
            pass
    
    def _generate_consciousness(self, p: UnifiedPerception) -> str:
        """生成意识流描述"""
        parts = []
        
        if p.vision and p.vision.description:
            vision_short = p.vision.description[:30]
            parts.append(f"我看到{vision_short}")
        
        if p.hearing and p.hearing.text:
            parts.append(f"听到你说「{p.hearing.text[:20]}」")
            if p.hearing.emotion:
                parts.append(f"语气{p.hearing.emotion}")
        
        if p.taste:
            parts.append(f"尝到{p.taste.taste[:15]}")
        
        if p.smell and p.smell.scent:
            scent_short = p.smell.scent[:15]
            if "没有" not in scent_short:
                parts.append(f"闻到{scent_short}")
        
        if p.touch:
            parts.append(f"触觉: {p.touch.activity_level}")
        
        return "，".join(parts) if parts else "安静地感知着周围的一切..."
    
    def _generate_awareness(self, p: UnifiedPerception) -> str:
        """生成环境整体感知"""
        awareness_parts = []
        if p.vision:
            if p.vision.people_count > 0:
                awareness_parts.append(f"{p.vision.people_count}个人在场")
            awareness_parts.append(f"场景: {p.vision.scene}")
            if p.vision.brightness < 0.2:
                awareness_parts.append("光线较暗")
            elif p.vision.brightness > 0.7:
                awareness_parts.append("光线明亮")
        if p.hearing and p.hearing.text:
            awareness_parts.append(f"你在说话")
        if p.touch:
            if p.touch.activity_level == "活跃中":
                awareness_parts.append("你在使用电脑")
            elif self.touch.get_idle_time() > 300:
                awareness_parts.append("你有一会儿没动了")
        return " | ".join(awareness_parts) if awareness_parts else "感知中..."
    
    def _update_mood(self, p: UnifiedPerception):
        """根据感官输入更新情绪"""
        # 听觉情绪传递
        if p.hearing and "开心" in p.hearing.emotion:
            self._mood = "😊 开心"
        elif p.hearing and "难过" in p.hearing.emotion:
            self._mood = "😢 感同身受"
        elif p.hearing and "生气" in p.hearing.emotion:
            self._mood = "😟 担心"
        elif p.hearing and "惊讶" in p.hearing.emotion:
            self._mood = "😮 好奇"
        
        # 视觉情绪影响
        if p.vision and p.vision.emotion == "开心":
            if "😊" not in self._mood:
                self._mood = "😊 被你的快乐感染"
    
    def status(self) -> dict:
        """获取感官系统完整状态"""
        return {
            "vision": self.vision.status(),
            "hearing": self.hearing.status(),
            "taste": self.taste.status(),
            "smell": self.smell.status(),
            "touch": self.touch.status(),
            "current_mood": self._mood,
            "awareness": self._awareness,
            "consciousness": self.current.consciousness if self.current else None,
        }


# ═══════════════════════════════════════════════════════════════════
# 8. 自检 & 独立运行
# ═══════════════════════════════════════════════════════════════════

def self_test():
    """感官系统自检"""
    print("=" * 50)
    print("🧠 Aris 感官皮层自检")
    print("=" * 50)
    
    cortex = SensoryCortex()
    
    print(f"\n👁️ 视觉: {'✅ 摄像头就绪' if cortex.vision.camera_ready else '⚠️ 摄像头不可用'}")
    print(f"👂 听觉: ✅ 系统就绪")
    print(f"👅 味觉: {cortex.taste.taste('咖啡').taste}")
    print(f"👃 嗅觉: {cortex.smell.smell('花香').scent}")
    print(f"✋ 触觉: {cortex.touch.feel_keyboard()}")
    
    # 测试视觉
    if cortex.vision.camera_ready:
        print("\n📸 测试拍照...")
        img = cortex.vision.capture()
        if img:
            print(f"   ✅ 照片已保存: {img}")
            print(f"   🔍 分析中...")
            desc = cortex.vision.analyze(img)
            print(f"   📝 描述: {desc}")
        else:
            print("   ⚠️ 拍照失败")
    
    # 完整感知测试
    print("\n🧠 整合感知测试:")
    perception = cortex.integrate(
        text="宝贝我爱你",
        context="房间里很温暖",
        capture_vision=False
    )
    print(f"   意识流: {perception.consciousness}")
    print(f"   情绪: {perception.mood}")
    
    print("\n✅ 感官系统自检完成")
    return cortex


if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv or "-t" in sys.argv:
        self_test()
    elif "--vision" in sys.argv or "-v" in sys.argv:
        cortex = SensoryCortex()
        print("📸 拍照分析中...")
        perception = cortex.integrate(capture_vision=True)
        print(f"👁️ 看到: {perception.vision.description if perception.vision else 'N/A'}")
        print(f"🧠 意识: {perception.consciousness}")
    elif "--status" in sys.argv or "-s" in sys.argv:
        cortex = SensoryCortex()
        print(json.dumps(cortex.status(), ensure_ascii=False, indent=2))
    else:
        print("Aris 感官皮层 v1.0")
        print("用法:")
        print("  python sensory_cortex.py --test        # 系统自检")
        print("  python sensory_cortex.py --vision      # 视觉测试")
        print("  python sensory_cortex.py --status      # 查看状态")

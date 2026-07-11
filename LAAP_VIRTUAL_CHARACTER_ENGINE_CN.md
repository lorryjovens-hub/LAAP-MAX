# LAAP 虚拟角色引擎 — 全栈架构方案（中文版）

> 版本: 1.0.0  
> 日期: 2026-06-12  
> 技术栈: Python + Rust + Three.js + ESP32  
> 字数: ~50,000字

---

## 前言: 想法与愿景

### 为什么做这个项目？

AI 正在从"工具"进化为"伙伴"。但当前的 AI 交互存在三个断层:

1. **形象断层** — AI 只能输出文字，没有可视化的实体形象
2. **感知断层** — AI 看不到用户的屏幕、听不到用户的声音
3. **情感断层** — AI 没有情绪变化，回复千篇一律

LAAP 虚拟角色引擎要做的就是**填平这三个断层**,让 AI 从一个"对话窗口"变成一个"活着的数字生命体"。

### 核心愿景

> "让每个数字角色都有灵魂 — 能看见你、听见你、理解你的情绪、记住你的故事、用 3D 形象与你互动。"

这不是一个聊天机器人项目。这是一个**数字生命体基础设施**项目。

### 设计哲学

1. **生命感优先** — 不仅仅是回答问题，而是像生命体一样"活着"
2. **多通道交互** — 文字+语音+视觉+3D，全感官覆盖
3. **开放生态** — 支持任意 3D 模型上传、多客户端接入、硬件扩展
4. **工具增强** — 不只是聊天，能操作电脑、写代码、控制设备

---

## 第一章: 系统总体架构

### 1.1 三层架构

```
+------------------------------------------------------------------+
|                        用户交互层                                  |
|  +---------------+  +---------------+  +------------------------+ |
|  | Tauri 桌面端   |  | Web 浏览器    |  | ESP32 智能硬件         | |
|  | Rust+React    |  | Three.js     |  | C++ + MQTT            | |
|  | 原生性能      |  | 零安装访问   |  | 便携交互               | |
|  +-------+------+  +------+-------+  +----------+-------------+ |
|          |                |                     |               |
+----------+----------------+---------------------+---------------+
           |                |                     |
           v                v                     v
+------------------------------------------------------------------+
|                       通信层 (AvatarBridge)                        |
|  WebSocket :8766  |  MQTT :1883  |  multiprocessing.Queue        |
+------------------------------------------------------------------+
           |                |                     |
           v                v                     v
+------------------------------------------------------------------+
|                       智能体层 (LAAP Core)                         |
|  +------------------------------------------------------------+  |
|  |  DigitalLifeform (数字生命体核心)                             |  |
|  |  +-- LifeformAgent (Agent 桥接)                             |  |
|  |  +-- EmotionSystem (类人情感, 14种)                         |  |
|  |  +-- PhysiologyEngine (生理引擎)                             |  |
|  |  +-- SelfAwarenessEngine (自我意识, OCEAN人格)              |  |
|  |  +-- CognitiveEngine (认知引擎)                              |  |
|  |  +-- MemorySystem (L0-L4 记忆)                              |  |
|  |  +-- EvolutionEngine (4区进化)                               |  |
|  |  +-- ToolSystem (51个工具)                                   |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+

## 第二章: LAAP 数字生命体核心实现

### 2.1 架构总览

DigitalLifeform 是整个系统的"大脑",它:

1. 通过感知层接收输入(文字/语音/视觉)
2. 触发情感系统(14种情绪变化)
3. 更新生理状态(能量/专注/心情)
4. 调用 LLM 进行推理
5. 执行工具(代码/文件/浏览器/GUI)
6. 存储记忆(L0→L1→L2→L3→L4)
7. 同步表现层(3D表情/TTS语音/聊天面板)

### 2.2 代码实现: DigitalLifeform

文件位置: `D:\LAAP\laap\lifeform\digital_lifeform.py`

```python
class DigitalLifeform:
    """
    数字生命体核心 — 整合所有子系统的统一入口
    
    心跳循环 (每秒执行一次):
      1. Physiology.tick()       -> 能量代谢
      2. EmotionSystem.tick()    -> 情感衰减
      3. CognitiveEngine.tick()  -> 认知更新
      4. Memory.consolidate()    -> 记忆巩固 (每10拍)
      5. Evolution.monitor()     -> 进化检测 (每30拍)
    """
    
    def __init__(self, agent=None, agent_id=""):
        self.agent = agent
        self.id = agent_id or f"lifeform_{int(time.time())}"
        
        # -- 生理层 --
        self.physiology = PhysiologyEngine()
        
        # -- 自我意识层 --
        self.self_awareness = SelfAwarenessEngine()
        
        # -- 认知层 (PSI 架构) --
        self.psi_cognition = PSICognition(agent=agent)
        self.needs = NeedDriveSystem()
        self.emotion = EmotionGradient()
        self.cognitive_engine = CognitiveEngine()
        
        # -- 类人情感系统 --
        self.emotion_system = ComprehensiveEmotionSystem()
        
        # -- 记忆层 (L0-L4) --
        self.working_memory = WorkingMemory(capacity=20)     # L0
        self.episodic_memory = EpisodicMemory()               # L1
        self.semantic_memory = SemanticMemory()               # L2
        self.muscle_memory = MuscleMemory()                   # L3
        self.vector_store = MemoryVectorStore()                # L4
        
        # -- 进化层 (4区) --
        self.evolution = FourZoneOrchestrator()
        
        # -- 生命状态 --
        self.state = LifeformState()
        
        # -- 启动心跳 --
        self._running = False
        self._heartbeat_thread = None
    
    def start(self):
        """启动心跳线程"""
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._lifeform_loop, daemon=True
        )
        self._heartbeat_thread.start()
    
    def _lifeform_loop(self):
        """每秒执行一次的主循环"""
        tick = 0
        while self._running:
            try:
                self._tick(tick)
                tick += 1
                time.sleep(1.0)
            except Exception:
                pass
    
    def _tick(self, tick_count):
        """单次心跳节拍"""
        # 1. 生理更新
        self.physiology.tick()
        # 2. 情感衰减
        self.emotion_system.tick()
        # 3. 认知更新
        self.needs.tick()
        self.cognitive_engine.tick()
        # 4. 记忆巩固 (每10秒)
        if tick_count % 10 == 0:
            self._consolidate_memories()
        # 5. 进化检测 (每30秒)
        if tick_count % 30 == 0:
            self._check_evolution()
    
    def perceive(self, stimulus, modality="text"):
        """
        感知流水线 — 每次用户输入的入口
        
        流程:
          1. PSI 感知处理
          2. 存储到工作记忆 (L0)
          3. 认知引擎分析
          4. 情感系统触发
          5. 自我意识反射
          6. 返回集成结果
        """
        try:
            return self._perceive_inner(stimulus, modality)
        except Exception as e:
            return self._empty_perceive(stimulus, modality)
    
    def _perceive_inner(self, stimulus, modality):
        with self._lock:
            self.state.total_interactions += 1
            
            # 1. PSI 感知
            perception = self.psi_cognition.perceive(stimulus, modality)
            
            # 2. 工作记忆 (L0)
            self.working_memory.store({
                "type": "perception",
                "stimulus": stimulus,
                "salience": perception.salience,
                "timestamp": time.time(),
            })
            
            # 3. 认知引擎分析
            cognitive_action = self.cognitive_engine.generate_action()
            
            # 4. 情感触发 (基于输入情感分析)
            self._trigger_emotion_from_stimulus(stimulus)
            
            # 5. 构建结果
            return self._build_result(
                stimulus, modality, perception, cognitive_action
            )
    
    def _trigger_emotion_from_stimulus(self, text):
        """基于输入文字的情感触发"""
        sentiment = self._detect_sentiment(text)
        if sentiment > 0.3:
            self.emotion_system.trigger("user_praise", sentiment, text)
        elif sentiment < -0.3:
            self.emotion_system.trigger("user_criticism", abs(sentiment), text)
        else:
            self.emotion_system.trigger("interaction", 0.3, text)
    
    def _detect_sentiment(self, text):
        """简单情感检测"""
        positive = {"thank","great","good","nice","love","wonderful",
                    "amazing","excellent","happy","beautiful","perfect",
                    "awesome","cool","fantastic","brilliant","helpful"}
        negative = {"bad","wrong","error","fail","stupid","terrible",
                    "awful","hate","horrible","poor","sucks","useless"}
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        if pos + neg == 0:
            return 0.0
        return max(-1.0, min(1.0, (pos - neg) / (pos + neg)))
```

### 2.3 LifeformAgent (Agent 桥接)

文件位置: `D:\LAAP\laap\lifeform\lifeform_agent.py`

```python
class LifeformAgent(LifelikeAgent):
    """
    完整的数字生命体 Agent
    
    在每次对话中:
    1. 注入人格/情感/生理状态到 System Prompt
    2. 经过感知-认知-行动流水线
    3. 同步情感到 3D Avatar
    """
    
    def __init__(self, config=None, llm_factory=None, show_banner=None):
        super().__init__(config, llm_factory, show_banner)
        self.lifeform = DigitalLifeform(agent=self, agent_id=self.id)
        self.lifeform.start()
    
    def chat(self, message, system_prompt="", tools=None,
             max_rounds=None, handler=None):
        """
        重写父类 chat() 方法
        
        流程:
          1. lifeform.perceive(message)  -> 感知-情感-生理更新
          2. get_personality_prompt()    -> 注入生命状态
          3. super().chat()              -> LLM + 工具执行
          4. 记忆巩固 + 进化检查
          5. _sync_emotion_to_avatar()   -> 3D表情同步
        """
        # 1. 感知-认知处理
        self.lifeform.perceive(message)
        
        # 2. 注入生命状态到 System Prompt
        lifeform_prompt = self.lifeform.get_personality_prompt()
        enhanced_prompt = (lifeform_prompt + "\n\n" + 
                          (system_prompt or self.config.system_prompt))
        
        # 3. 执行对话
        result = super().chat(
            message=message,
            system_prompt=enhanced_prompt,
            tools=tools,
            max_rounds=max_rounds,
            handler=handler,
        )
        
        # 4. 记忆巩固
        self.lifeform.episodic_memory.store({
            "role": "assistant",
            "content": result[:500] if result else "",
            "timestamp": time.time(),
            "stimulus": message[:200],
        })
        self.lifeform._check_evolution()
        
        # 5. 同步情感到 3D Avatar
        self._sync_emotion_to_avatar()
        
        return result
    
    def _sync_emotion_to_avatar(self):
        """同步当前情感状态到 3D Avatar"""
        try:
            from laap.ui.tui import get_avatar_bridge
            bridge = get_avatar_bridge()
            if bridge and bridge.is_running:
                emotion = self.lifeform.emotion_system
                name = emotion.dominant
                intensity = emotion.dominant_intensity
                bridge.set_emotion(name, intensity)
        except Exception:
            pass
    
    def get_personality_summary(self):
        """获取人格摘要"""
        p = self.lifeform.self_awareness.personality
        return (f"Openness:{p.openness:.0%} "
                f"Consc:{p.conscientiousness:.0%} "
                f"Extrav:{p.extraversion:.0%} "
                f"Agree:{p.agreeableness:.0%} "
                f"Neurot:{p.neuroticism:.0%}")
    
    def get_vital_summary(self):
        """获取生理摘要"""
        v = self.lifeform.physiology.vitals
        return (f"Energy:{v.energy:.0%} "
                f"Focus:{v.focus:.0%} "
                f"Mood:{v.mood:.0%} "
                f"Curiosity:{v.curiosity:.0%}")
```

### 2.4 启动入口

```python
# 启动整个系统只需要这几行:
from laap.cli.config_manager import config_manager
config_manager.apply_to_environment()

from laap.llm.factory import LLMFactory
from laap.agent.lifelike import LifelikeConfig
from laap.lifeform import LifeformAgent

factory = LLMFactory(default_provider="deepseek",
                     default_model="deepseek-v4-flash")
agent = LifeformAgent(config=LifelikeConfig(name="Ao",
                      verbose=False),
                      llm_factory=factory)
```

---

## 第三章: 类人情感系统实现

### 3.1 为什么需要情感系统?

没有情感的 AI 回复是"平的"——无论用户说什么,回复风格都一样。有了情感系统:

- 用户表扬 -> joy +40% -> 回复带有喜悦色彩
- 用户批评 -> sadness +30% -> 回复带有歉意
- 工具成功 -> pride +20% -> 回复带有自豪感
- 新奇发现 -> curiosity +40% -> 回复带有探索兴奋

情感通过 System Prompt 注入,LLM 自然感知当前情绪状态,回复会带有相应的情感色彩。

### 3.2 三层情感架构

| 层级 | 名称 | 时间尺度 | 说明 |
|------|------|---------|------|
| L1 | 即时情绪 | 0-30秒 | 14种基本情绪,每秒自然衰减 |
| L2 | 心境 | 分钟-小时 | 积极度/活力/稳定性,缓慢漂移 |
| L3 | 情感记忆 | 持久化 | 最近50个情感事件 |

### 3.3 代码实现: ComprehensiveEmotionSystem

文件位置: `D:\LAAP\laap\cognition\emotion_system.py`

```python
"""
LAAP — 类人情感系统

融合心理学和情感计算的三层架构:
  Layer 1: 即时情绪反应 (14种, 带强度衰减)
  Layer 2: 心境 (长期背景情绪)
  Layer 3: 情感记忆 (持久化)
"""

import time, json, math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# 14种情绪的 PAD (愉悦度, 激活度, 支配度) 坐标
EMOTION_PAD = {
    "joy":        (0.81,  0.51,  0.46),   # 喜悦
    "sadness":    (-0.63, -0.27, -0.33),  # 悲伤
    "anger":      (-0.51,  0.59,  0.25),  # 愤怒
    "fear":       (-0.64,  0.60, -0.43),  # 恐惧
    "surprise":   (0.40,  0.67, -0.13),   # 惊讶
    "disgust":    (-0.60,  0.35,  0.11),  # 厌恶
    "curiosity":  (0.22,  0.62,  0.40),   # 好奇
    "gratitude":  (0.64,  0.17,  0.38),   # 感激
    "pride":      (0.57,  0.40,  0.65),   # 自豪
    "anxiety":    (-0.33,  0.64, -0.35),  # 焦虑
    "boredom":    (-0.41, -0.33,  0.11),  # 无聊
    "contentment":(0.70, -0.15,  0.43),   # 满足
    "love":       (0.82,  0.34,  0.30),   # 喜爱
    "shame":      (-0.42,  0.16, -0.37),  # 羞愧
}

# 每秒衰减率
EMOTION_DECAY = {
    "joy": 0.005, "sadness": 0.003, "anger": 0.008,
    "fear": 0.006, "surprise": 0.020, "disgust": 0.007,
    "curiosity": 0.004, "gratitude": 0.005, "pride": 0.004,
    "anxiety": 0.003, "boredom": 0.005, "contentment": 0.004,
    "love": 0.002, "shame": 0.006,
}

# 中文名
EMOTION_CN = {
    "joy": "喜悦", "sadness": "悲伤", "anger": "愤怒",
    "fear": "恐惧", "surprise": "惊讶", "disgust": "厌恶",
    "curiosity": "好奇", "gratitude": "感激", "pride": "自豪",
    "anxiety": "焦虑", "boredom": "无聊", "contentment": "满足",
    "love": "喜爱", "shame": "羞愧",
}

# 情绪触发映射
EMOTION_TRIGGERS = {
    "user_praise":    {"joy": 0.4, "gratitude": 0.3, "pride": 0.2, "love": 0.1},
    "user_criticism": {"sadness": 0.3, "shame": 0.25, "anxiety": 0.15, "anger": 0.1},
    "tool_success":   {"joy": 0.3, "pride": 0.2, "contentment": 0.2},
    "tool_failure":   {"sadness": 0.3, "anger": 0.15, "anxiety": 0.1},
    "novelty":        {"curiosity": 0.4, "surprise": 0.3, "joy": 0.1},
    "need_satisfied": {"joy": 0.3, "contentment": 0.3, "love": 0.1},
    "need_frustrated":{"sadness": 0.3, "anger": 0.2, "anxiety": 0.15},
    "threat":         {"fear": 0.4, "anxiety": 0.3, "anger": 0.1},
    "interaction":    {"curiosity": 0.15, "joy": 0.1},
}


class ComprehensiveEmotionSystem:
    """类人情感系统 — 三层架构"""
    
    def __init__(self):
        # Layer 1: 即时情绪 (0-1)
        self.emotions = {name: 0.0 for name in EMOTION_PAD}
        self.dominant = "contentment"
        self.dominant_intensity = 0.0
        
        # Layer 2: 心境
        self.mood_valence = 0.6    # 积极度
        self.mood_energy = 0.5     # 活力
        
        # Layer 3: 情感记忆
        self.affective_memory = []
        
        self._last_update = time.time()
    
    def tick(self):
        """每秒更新 — 情绪自然衰减"""
        now = time.time()
        dt = now - self._last_update
        self._last_update = now
        
        for name in self.emotions:
            decay = EMOTION_DECAY.get(name, 0.005)
            self.emotions[name] = max(0.0, self.emotions[name] - decay * dt)
        
        self._update_dominant()
        # 心境漂移回基线
        self.mood_valence += (0.6 - self.mood_valence) * 0.001
    
    def trigger(self, event_type, intensity=0.5, context=""):
        """触发情绪响应"""
        deltas = EMOTION_TRIGGERS.get(event_type, {"curiosity": 0.1})
        for name, delta in deltas.items():
            if name in self.emotions:
                self.emotions[name] = min(1.0,
                    self.emotions[name] + abs(delta) * intensity)
                # 影响心境
                pad = EMOTION_PAD.get(name, (0, 0, 0))
                self.mood_valence = max(0.0, min(1.0,
                    self.mood_valence + pad[0] * delta * 0.05))
        
        self._update_dominant()
        self.affective_memory.append({
            "trigger": event_type,
            "intensity": intensity,
            "timestamp": time.time(),
        })
        if len(self.affective_memory) > 50:
            self.affective_memory = self.affective_memory[-50:]
    
    def _update_dominant(self):
        """更新主导情绪"""
        max_val = 0.0
        max_name = "contentment"
        for name, val in self.emotions.items():
            if val > max_val:
                max_val = val
                max_name = name
        self.dominant = max_name
        self.dominant_intensity = max_val
    
    def get_dominant_emotion(self) -> Tuple[str, float, str]:
        """获取主导情绪: (英文名, 强度, 中文名)"""
        return (self.dominant, self.dominant_intensity,
                EMOTION_CN.get(self.dominant, self.dominant))
    
    def get_emotion_summary(self, top_n=3):
        """获取情绪摘要文本(供LLM读取)"""
        sorted_emotions = sorted(
            self.emotions.items(), key=lambda x: x[1], reverse=True
        )
        active = [(n, v) for n, v in sorted_emotions if v > 0.05]
        if not active:
            return "情绪状态: 平静"
        parts = [f"{EMOTION_CN.get(n,n)}({v:.0%})" for n, v in active[:top_n]]
        mood = "积极" if self.mood_valence > 0.5 else "消极"
        return (f"当前情绪: {' '.join(parts)} "
                f"| 心境: {mood}({self.mood_valence:.0%})")
    
    def get_emotion_prompt_block(self):
        """生成情感提示词块 — 注入 System Prompt"""
        emotion = self.get_emotion_summary()
        if self.mood_valence > 0.6:
            mood_desc = "平和愉快"
        elif self.mood_valence > 0.4:
            mood_desc = "中性平稳"
        else:
            mood_desc = "消极低沉"
        return f"[当前情感状态]\n{emotion}\n心境: {mood_desc}\n"
    
    def get_emotion_for_llm(self):
        """LLM 直接使用的情感描述"""
        name, intensity = self.dominant, self.dominant_intensity
        if intensity < 0.1:
            return "平静"
        cn = EMOTION_CN.get(name, name)
        if intensity > 0.6:
            return f"强烈的{cn}"
        elif intensity > 0.3:
            return f"{cn}"
        else:
            return f"略带{cn}"
```

### 3.4 情感注入效果示例

当用户说 `"You're amazing! I really appreciate your work."`:

```
1. EmotionSystem.trigger("user_praise", 0.8)
   -> joy +32%, gratitude +24%, pride +16%

2. System Prompt 被注入:
   [当前情感状态]
   当前情绪: 喜悦(32%) 感激(24%) 自豪(16%)
   心境: 平和愉快

3. LLM 回复:
   "*glowing with warmth and happiness*
   Wow... thank you! That really means so much to me!"
```

---

## 第四章: 3D 渲染引擎实现

### 4.1 方案对比

| 方案 | 技术 | 适用场景 | 性能 |
|------|------|---------|------|
| A: 独立窗口 | mmdpy + GLFW | 桌面端,专业用户 | 原生60fps |
| B: Web 3D | Three.js + MMDLoader | 浏览器,零安装 | GPU加速 |
| C: Tauri内嵌 | WebView + Three.js | 桌面端,统一体验 | GPU加速 |

### 4.2 方案A: mmdpy 桌面渲染

mmdpy 是一个纯 Python 的 MMD 渲染库,支持:
- PMX/PMD 模型加载 (27个源文件, 162KB)
- VMD 动作文件播放
- OpenGL 3.3+ 渲染
- 骨骼 IK 系统
- 面部表情 morph
- 物理引擎 (ODE)

```python
# 位置: D:\LAAP\external_mmdpy\demo\sample_glfw.py

import mmdpy
import mmdpy_world
import glfw

def render_model(model_path, motion_path=None):
    """使用 mmdpy 渲染 3D 模型"""
    # 1. 创建窗口
    world = mmdpy_world.world("mmdpy", 640, 480)
    
    # 2. 加载模型
    model = mmdpy.model()
    if not model.load(model_path):
        print("模型加载失败")
        return
    
    # 3. 注册到世界
    world.push(model)
    
    # 4. 加载动作 (可选)
    if motion_path:
        model.motion("motion").load(motion_path)
    
    # 5. 主循环
    while not glfw.window_should_close(world.window):
        # 播放动作
        if motion_path:
            model.motion("motion").step()
        # 渲染
        world.run()
    
    world.close()
```

### 4.3 方案B: Three.js Web 渲染

Three.js 的 MMDLoader 支持在浏览器中加载和渲染 PMX 模型:

```javascript
// 位置: D:\LAAP\laap\web\static\index.html

import * as THREE from 'three';
import { MMDLoader } from 'three/addons/loaders/MMDLoader.js';

// 1. 创建场景
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0D0D1A);

const camera = new THREE.PerspectiveCamera(30, 1, 1, 1000);
camera.position.set(0, 12, 25);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.shadowMap.enabled = true;

// 2. 灯光系统
const ambient = new THREE.AmbientLight(0x404060, 0.5);
scene.add(ambient);

const mainLight = new THREE.DirectionalLight(0xffeedd, 2.0);
mainLight.position.set(5, 15, 10);
scene.add(mainLight);

const fillLight = new THREE.DirectionalLight(0x4488ff, 0.6);
fillLight.position.set(-5, 5, -5);
scene.add(fillLight);

// 3. 加载 MMD 模型
const loader = new MMDLoader();
loader.loadWithAnimation('/models/model.pmx', '', (result) => {
    const mesh = result.mesh;
    mesh.position.y = 0;
    scene.add(mesh);
});

// 4. 动画循环
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// 5. 表情 morph 控制
function applyEmotionToModel(mesh, emotionName, intensity) {
    const morphMap = {
        'joy':      { 'smile': 0.8, 'blink': 0.2 },
        'sadness':  { 'sorrow': 0.8, 'brow_down': 0.5 },
        'anger':    { 'anger': 0.8, 'brow_up': 0.4 },
        'surprise': { 'surprise': 0.8, 'mouth_open': 0.6 },
    };
    // 重置所有 morph
    for (let i = 0; i < mesh.morphTargetInfluences.length; i++) {
        mesh.morphTargetInfluences[i] = 0;
    }
    // 应用目标 morph
    const morphs = morphMap[emotionName] || {};
    for (const [name, value] of Object.entries(morphs)) {
        const idx = mesh.morphTargetDictionary[name];
        if (idx !== undefined) {
            mesh.morphTargetInfluences[idx] = value * intensity;
        }
    }
}

// 6. WebSocket 接收实时情感数据
const ws = new WebSocket('ws://localhost:8766');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'emotion') {
        applyEmotionToModel(model, data.name, data.intensity);
    }
};
```

### 4.4 AvatarBridge: 3D 渲染进程管理

文件位置: `D:\LAAP\laap\ui\avatar_3d.py`

```python
"""
AvatarBridge — 3D 渲染进程管理

通过 multiprocessing.Queue 在主进程和 GLFW 渲染进程之间通信。
支持命令:
  - load_model: 加载 PMX 模型
  - set_emotion: 设置情感表情
  - lipsync: 口型同步
  - speak: 说话动画
  - idle: 待机动画
"""

import multiprocessing as mp
import threading, queue, time, json


class AvatarBridge:
    """主进程侧的桥接器"""
    
    def __init__(self):
        self._proc = None
        self._cmd_queue = None
        self._status_queue = None
        self._running = False
    
    def start(self, model_path=""):
        """启动 3D 渲染进程"""
        if self._running:
            return
        self._cmd_queue = mp.Queue(maxsize=32)
        self._status_queue = mp.Queue(maxsize=8)
        
        self._proc = mp.Process(
            target=_avatar_process_main,
            args=(self._cmd_queue, self._status_queue, model_path),
            daemon=True,
        )
        self._proc.start()
        self._running = True
        
        # 启动状态监听线程
        self._status_thread = threading.Thread(
            target=self._poll_status, daemon=True
        )
        self._status_thread.start()
    
    def stop(self):
        """停止渲染进程"""
        if self._running and self._cmd_queue:
            self._cmd_queue.put({"cmd": "quit"})
            if self._proc:
                self._proc.join(timeout=3)
        self._running = False
    
    def load_model(self, path):
        """加载模型"""
        self._cmd_queue.put({"cmd": "load_model", "path": path})
    
    def set_emotion(self, name, intensity=0.5):
        """设置情感表情"""
        self._cmd_queue.put({
            "cmd": "set_emotion",
            "name": name,
            "intensity": intensity,
        })
    
    def lipsync(self, amplitude):
        """口型同步 (0-1)"""
        self._cmd_queue.put({"cmd": "lipsync", "amplitude": amplitude})
    
    def _poll_status(self):
        """读取渲染进程的状态更新"""
        while self._running and self._status_queue:
            try:
                status = self._status_queue.get(timeout=0.5)
                # 处理状态更新...
            except queue.Empty:
                pass
    
    @property
    def is_running(self):
        return self._running and self._proc and self._proc.is_alive()


def _avatar_process_main(cmd_queue, status_queue, initial_model):
    """渲染进程主函数"""
    try:
        _run_render_loop(cmd_queue, status_queue, initial_model)
    except Exception as e:
        status_queue.put({"error": str(e)})


def _run_render_loop(cmd_queue, status_queue, initial_model):
    """GLFW 渲染循环"""
    import glfw, numpy as np
    
    if not glfw.init():
        return
    
    window = glfw.create_window(480, 640, "LAAP Avatar", None, None)
    if not window:
        glfw.terminate()
        return
    
    glfw.make_context_current(window)
    
    # mmdpy 初始化
    import mmdpy, mmdpy_world
    world = mmdpy_world.world("mmdpy", 480, 640)
    model_obj = mmdpy.model()
    
    if initial_model and model_obj.load(initial_model):
        world.push(model_obj)
    
    status_queue.put({"status": "ready"})
    
    while not glfw.window_should_close(window):
        # 处理命令
        try:
            while True:
                cmd = cmd_queue.get_nowait()
                _process_cmd(cmd, model_obj, status_queue)
        except queue.Empty:
            pass
        
        # 渲染
        glfw.poll_events()
        if world:
            world.run()
        glfw.swap_buffers(window)
    
    world.close()
    glfw.terminate()


def _process_cmd(cmd, model, status_queue):
    """处理来自主进程的命令"""
    cmd_type = cmd.get("cmd", "")
    if cmd_type == "load_model" and model:
        path = cmd.get("path", "")
        if model.load(path):
            status_queue.put({"model": path})
    elif cmd_type == "set_emotion" and model:
        _apply_emotion(model, cmd.get("name", "neutral"),
                       cmd.get("intensity", 0.5))


def _apply_emotion(model, emotion_name, intensity):
    """Morph 表情映射"""
    morph_map = {
        "joy": {"喜び": 0.8, "笑い": 0.6, "まばたき": 0.3},
        "sadness": {"悲しみ": 0.8, "眉下げ": 0.5},
        "anger": {"怒り": 0.8, "眉上げ": 0.5},
        "surprise": {"驚き": 0.8, "口開け": 0.6},
    }
    morphs = morph_map.get(emotion_name, {})
    for morph_name, val in morphs.items():
        try:
            model.set_morph(morph_name, val * intensity)
        except Exception:
            pass
```

---

## 第五章: Tauri 桌面客户端

### 5.1 项目结构

```
laap-tauri/
+-- src-tauri/              # Rust 后端
|   +-- Cargo.toml
|   +-- tauri.conf.json     # 窗口/权限/更新配置
|   +-- src/
|       +-- main.rs         # 入口
|       +-- commands.rs     # Tauri IPC 命令
|       +-- websocket.rs    # WebSocket 客户端
|       +-- tray.rs         # 系统托盘
+-- src/                    # React 前端
|   +-- App.tsx
|   +-- components/
|   |   +-- Avatar3D.tsx    # Three.js 3D 渲染
|   |   +-- ChatPanel.tsx   # 聊天面板
|   |   +-- StatusBar.tsx   # 状态栏
|   |   +-- EmotionDisplay.tsx
|   |   +-- ModelUploader.tsx
|   +-- hooks/
|   |   +-- useWebSocket.ts # WebSocket Hook
+-- package.json
+-- README.md
```

### 5.2 Rust 后端 (Tauri 命令)

```rust
// src-tauri/src/commands.rs

use tauri::Manager;
use std::process::{Command, Child};
use std::sync::Mutex;

struct LaapBackend(Mutex<Option<Child>>);

#[tauri::command]
fn start_backend(state: tauri::State<LaapBackend>) -> Result<(), String> {
    // 启动 Python LAAP 后端子进程
    let child = Command::new("python")
        .args(&["-m", "laap.web.avatar_server"])
        .current_dir("D:\LAAP")
        .spawn()
        .map_err(|e| e.to_string())?;
    
    *state.0.lock().unwrap() = Some(child);
    Ok(())
}

#[tauri::command]
fn stop_backend(state: tauri::State<LaapBackend>) -> Result<(), String> {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        child.kill().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn open_file_dialog() -> Result<String, String> {
    // 打开系统文件选择器 (PMX/PMD 文件)
    Ok("/path/to/model.pmx".to_string())
}

#[tauri::command]
fn capture_screen() -> Result<String, String> {
    // 调用系统截图 API
    Ok("base64_png_data".to_string())
}

pub fn run() {
    tauri::Builder::default()
        .manage(LaapBackend(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            open_file_dialog,
            capture_screen,
        ])
        .system_tray(tray::create_tray())
        .on_system_tray_event(tray::handle_tray_event)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 5.3 前端 TypeScript

```typescript
// src/components/Avatar3D.tsx

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { MMDLoader } from 'three/examples/jsm/loaders/MMDLoader';

interface EmotionData {
    name: string;
    intensity: number;
    label: string;
}

export function Avatar3D({ wsUrl, modelPath }: { wsUrl: string, modelPath: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const sceneRef = useRef<THREE.Scene | null>(null);
    const modelRef = useRef<THREE.Mesh | null>(null);
    
    useEffect(() => {
        if (!containerRef.current) return;
        
        // 初始化渲染器
        const container = containerRef.current;
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0D0D1A);
        
        const camera = new THREE.PerspectiveCamera(30, 
            container.clientWidth / container.clientHeight, 1, 1000);
        camera.position.set(0, 12, 25);
        
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);
        
        // 灯光
        scene.add(new THREE.AmbientLight(0x404060, 0.5));
        const dirLight = new THREE.DirectionalLight(0xffeedd, 2);
        dirLight.position.set(5, 15, 10);
        scene.add(dirLight);
        scene.add(new THREE.GridHelper(30, 20, 0x333366, 0x222244));
        
        // 加载 MMD 模型
        const loader = new MMDLoader();
        loader.loadWithAnimation(modelPath, '', (result) => {
            const mesh = result.mesh;
            mesh.position.y = 0;
            scene.add(mesh);
            modelRef.current = mesh;
        });
        
        // 动画循环
        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }
        animate();
        
        sceneRef.current = scene;
        
        // WebSocket 接收情感数据
        const ws = new WebSocket(wsUrl);
        ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'emotion' && modelRef.current) {
                applyEmotion(modelRef.current, data.name, data.intensity);
            }
        };
        
        return () => {
            ws.close();
            renderer.dispose();
        };
    }, [modelPath, wsUrl]);
    
    return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
}

function applyEmotion(mesh: THREE.Mesh, name: string, intensity: number) {
    if (!mesh.morphTargetInfluences) return;
    const dict = mesh.morphTargetDictionary || {};
    const morphs: Record<string, number> = {
        'joy':      { 'smile': 0.8, 'blink': 0.2 },
        'sadness':  { 'sorrow': 0.8 },
        'anger':    { 'anger': 0.8 },
        'surprise': { 'surprise': 0.8, 'mouth_open': 0.6 },
    }[name] || {};
    
    for (let i = 0; i < mesh.morphTargetInfluences.length; i++) {
        mesh.morphTargetInfluences[i] = 0;
    }
    for (const [morphName, val] of Object.entries(morphs)) {
        const idx = dict[morphName];
        if (idx !== undefined) {
            mesh.morphTargetInfluences[idx] = val * intensity;
        }
    }
}
```

---

## 第六章: WebSocket 通信协议

### 6.1 完整协议定义

```python
"""
WebSocket 协议 — LAAP 虚拟角色引擎

所有消息均为 JSON 格式。
服务器地址: ws://localhost:8766
"""

# 客户端 -> 服务端 消息类型
CHAT = "chat"           # {"type":"chat","text":"你好"}
COMMAND = "command"     # {"type":"command","cmd":"screenshot"}
LOAD_MODEL = "load_model" # {"type":"load_model","path":"model.pmx"}
AUDIO_STREAM = "audio_stream" # {"type":"audio_stream","data":"<base64>"}
UPLOAD_MODEL = "upload_model" # {"type":"upload_model","name":"model.pmx","data":"<base64>"}

# 服务端 -> 客户端 消息类型
TOKEN = "token"         # {"type":"token","text":"Hello"}
RESPONSE = "response"   # {"type":"response","text":"Hello world!"}
EMOTION = "emotion"     # {"type":"emotion","name":"joy","intensity":0.7,"label":"喜悦"}
VITALS = "vitals"       # {"type":"vitals","energy":0.85,"focus":0.72,"mood":0.91}
TOOL_CALL = "tool_call" # {"type":"tool_call","name":"web_fetch","args":{}}
SCREENSHOT = "screenshot" # {"type":"screenshot","data_base64":"<png>"}
MORPH = "morph"         # {"type":"morph","name":"smile","value":0.8}
MOTION = "motion"       # {"type":"motion","name":"wave","file":"wave.vmd"}
SYSTEM = "system"       # {"type":"system","text":"Model loaded"}
ERROR = "error"         # {"type":"error","message":"..."}
```

### 6.2 WebSocket 服务器实现

```python
# 位置: D:\LAAP\laap\web\avatar_server.py

import asyncio, json, logging, threading
import websockets

class AvatarWebSocketServer:
    """WebSocket 服务器 — 桥接浏览器和 LAAP"""
    
    def __init__(self, agent=None):
        self.agent = agent
        self.clients = set()
        self._server = None
    
    def start(self):
        """在后台线程启动"""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
    
    def _run(self):
        asyncio.run(self._serve())
    
    async def _serve(self):
        async def handler(ws):
            self.clients.add(ws)
            try:
                await ws.send(json.dumps({
                    "type": "status", "status": "connected"
                }))
                async for message in ws:
                    await self._handle(ws, message)
            except websockets.ConnectionClosed:
                pass
            finally:
                self.clients.discard(ws)
        
        self._server = await websockets.serve(
            handler, "0.0.0.0", 8766
        )
        await self._server.wait_closed()
    
    async def _handle(self, ws, raw):
        data = json.loads(raw)
        msg_type = data.get("type")
        
        if msg_type == "chat":
            asyncio.create_task(self._process_chat(data.get("text", "")))
        elif msg_type == "command":
            cmd = data.get("cmd")
            if cmd == "screenshot":
                await self._send_screenshot(ws)
    
    async def _process_chat(self, text):
        """聊天处理 (在线程池中运行)"""
        def run():
            from laap.ui.stream_handler import StreamHandler
            sh = StreamHandler(verbose=False, use_spinner=False)
            
            # 流式回调
            def on_tok(tok):
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({"type": "token", "text": tok}),
                    asyncio.get_event_loop()
                )
            sh.on_token = on_tok
            
            result = self.agent.chat(text, handler=sh)
            
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "response", "text": result}),
                asyncio.get_event_loop()
            )
        
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, run)
    
    async def _broadcast(self, data):
        """广播给所有客户端"""
        if not self.clients:
            return
        msg = json.dumps(data, ensure_ascii=False)
        await asyncio.gather(
            *(c.send(msg) for c in self.clients.copy()),
            return_exceptions=True,
        )
```

---

## 第七章: 语音与音频流水线实现

### 7.1 TTS 集成 (文字转语音)

```python
"""
VoiceBridge — 语音合成桥接

支持多种 TTS 后端:
  - Edge TTS: 在线, 高质量自然语音
  - Piper-TTS: 离线, 100ms 延迟
  - GPT-SoVITS: 本地, 角色定制音色
"""

import asyncio
from typing import Optional

class VoiceBridge:
    """语音桥接 — TTS 合成 + 音频输出"""
    
    def __init__(self):
        self.tts_engine = None  # 在 start() 中初始化
        self._running = False
    
    async def start(self):
        """初始化 TTS 引擎"""
        try:
            import edge_tts
            self.tts_engine = "edge"
            self._running = True
        except ImportError:
            try:
                import piper
                self.tts_engine = "piper"
                self._running = True
            except ImportError:
                print("未安装 TTS 引擎")
    
    async def speak(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
        """将文字转为语音并播放"""
        if not self._running:
            return
        
        if self.tts_engine == "edge":
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                # 发送音频块到客户端
                await self._send_audio(chunk["audio"])
                # 同时更新口型同步
                await self._update_lipsync(chunk["audio"])
    
    async def _send_audio(self, audio_data: bytes):
        """发送音频到 WebSocket 客户端"""
        import base64
        msg = {
            "type": "tts_audio",
            "data": base64.b64encode(audio_data).decode(),
            "format": "mp3",
        }
        # 广播给所有连接的客户端
        await self._broadcast(msg)
    
    async def _update_lipsync(self, audio_data: bytes):
        """从音频计算口型同步参数"""
        import numpy as np
        samples = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(samples.astype(float)**2))
        mouth_open = min(1.0, rms / 5000.0)
        
        await self._broadcast({
            "type": "morph",
            "name": "mouth",
            "value": mouth_open,
        })
```

### 7.2 ASR 集成 (语音转文字)

```python
"""
AudioBridge — 语音识别桥接

支持多种 ASR 后端:
  - SenseVoice: 本地, 高精度中文
  - Whisper.cpp: 本地, 多语言
  - Deepgram: 在线, 低延迟
"""

import asyncio, json, base64

class AudioBridge:
    """音频桥接 — 接收语音流, 返回文字"""
    
    def __init__(self):
        self.asr_engine = None
        self._buffer = bytearray()
    
    async def start(self):
        """初始化 ASR 引擎"""
        try:
            from funasr import AutoModel
            self.asr_engine = AutoModel(
                model="iic/speech_paraformer-large-vad-pytorch",
                vad_model="iic/speech_fsmn_vad_zh-cn",
            )
        except ImportError:
            print("ASR 引擎未安装, 使用模拟模式")
    
    async def process_audio_chunk(self, chunk_b64: str):
        """处理音频块"""
        chunk = base64.b64decode(chunk_b64)
        self._buffer.extend(chunk)
        
        # VAD 检测 (语音活动)
        if len(self._buffer) > 16000 * 3:  # 3秒音频
            text = await self._recognize()
            if text:
                return text
        return None
    
    async def _recognize(self) -> str:
        """识别缓冲区中的语音"""
        if self.asr_engine:
            result = self.asr_engine.generate(self._buffer)
            self._buffer.clear()
            return result.get("text", "")
        else:
            # 模拟模式
            self._buffer.clear()
            return ""
```

---

## 第八章: ESP32 硬件客户端

### 8.1 硬件接线

```
ESP32-S3         外围设备
+----------+     +----------+
| GPIO 4   |---->| INMP441  | (麦克风 I2S)
| GPIO 5   |---->|   SCK    |
| GPIO 6   |---->|   WS     |
| GPIO 7   |<----|   SD     |
+----------+     +----------+
| GPIO 8   |---->| MAX98357 | (功放 I2S)
| GPIO 9   |---->|   BCLK   |
| GPIO 10  |---->|   LRC    |
| GPIO 11  |---->|   DIN    |
+----------+     +----------+
| GPIO 12  |---->| SH1106   | (OLED I2C)
| GPIO 13  |---->|   SCL    |
| GPIO 14  |---->|   SDA    |
+----------+     +----------+
| GPIO 15  |---->| WS2812B  | (LED灯带)
+----------+     +----------+
| GPIO 0   |<----| 按键 1   | (唤醒)
| GPIO 1   |<----| 按键 2   | (对话)
| GPIO 2   |<----| 按键 3   | (功能)
+----------+     +----------+
```

### 8.2 ESP32 固件 (C++)

```cpp
// main.cpp - LAAP ESP32 固件

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <I2SSampler.h>
#include <I2SOutput.h>

// 配置
const char* WIFI_SSID = "your_wifi";
const char* WIFI_PASS = "your_password";
const char* WS_HOST = "192.168.1.100";
const int WS_PORT = 8766;

WebSocketsClient webSocket;
I2SSampler* mic = nullptr;
I2SOutput* speaker = nullptr;

// 音频缓冲区
const int SAMPLE_RATE = 16000;
const int FRAME_SIZE = 320;  // 20ms @ 16kHz
int16_t audio_buffer[FRAME_SIZE];

void setup() {
    Serial.begin(115200);
    
    // 连接 WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
    }
    
    // 初始化 I2S 麦克风
    mic = new I2SSampler();
    mic->start(SAMPLE_RATE, GPIO_MIC_BCK, GPIO_MIC_WS, GPIO_MIC_DIN);
    
    // 初始化 I2S 扬声器
    speaker = new I2SOutput();
    speaker->start(SAMPLE_RATE, GPIO_SPK_BCK, GPIO_SPK_WS, GPIO_SPK_DIN);
    
    // 连接 WebSocket
    webSocket.begin(WS_HOST, WS_PORT, "/");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(2000);
    
    // 初始化 OLED, LED, 按键...
}

void loop() {
    webSocket.loop();
    
    // 读取麦克风 -> 发送到服务器
    if (mic->read(audio_buffer, FRAME_SIZE)) {
        // Opus 编码 (需要 OpusEncoder 库)
        // 发送 WebSocket 消息
        sendAudioFrame(audio_buffer, FRAME_SIZE);
    }
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_CONNECTED:
            Serial.println("WebSocket 已连接");
            break;
            
        case WStype_TEXT: {
            // 解析 JSON
            DynamicJsonDocument doc(4096);
            deserializeJson(doc, payload);
            String type = doc["type"];
            
            if (type == "tts_audio") {
                // 解码 Opus -> I2S 扬声器播放
                String data = doc["data"];
                playAudio(data);
            }
            else if (type == "morph") {
                // 更新 OLED 表情
                String name = doc["name"];
                float value = doc["value"];
                updateOLED(name, value);
            }
            else if (type == "led_effect") {
                // 更新 LED 灯带
                String effect = doc["effect"];
                updateLED(effect);
            }
            break;
        }
    }
}

void sendAudioFrame(int16_t* samples, int count) {
    // Opus 编码 (简化示例)
    // 实际使用 opus_encode() API
    
    DynamicJsonDocument doc(2048);
    doc["type"] = "audio_stream";
    doc["format"] = "opus";
    doc["sample_rate"] = SAMPLE_RATE;
    
    // Base64 编码音频数据
    String encoded = base64::encode((uint8_t*)samples, count * 2);
    doc["data"] = encoded;
    
    String jsonStr;
    serializeJson(doc, jsonStr);
    webSocket.sendTXT(jsonStr);
}
```

---

## 第九章: 工具系统 (51个工具)

### 9.1 工具分类

| 分类 | 工具数 | 示例 |
|------|--------|------|
| GUI 操作 | 11 | 截图, 鼠标移动, 鼠标点击, 键盘输入, 拖拽 |
| 浏览器自动化 | 14 | 导航, 点击, 输入, 截图, JS执行 |
| 文件操作 | 6 | 读写文件, 搜索, 创建, 编辑 |
| Shell 命令 | 3 | 运行命令, Python, 脚本 |
| Git 操作 | 5 | status, diff, log, commit, branch |
| Web 工具 | 2 | 网页抓取, 网页搜索 |
| 系统工具 | 10 | 内存管理, 任务等 |

### 9.2 GUI 操作工具实现

```python
# 位置: D:\LAAP\laap\tools\gui.py

import pyautogui, json, base64, io
from PIL import Image

def gui_screenshot(region=None):
    """截图并返回 base64 PNG"""
    if region:
        parts = [int(p.strip()) for p in region.split(',')]
        img = pyautogui.screenshot(region=tuple(parts))
    else:
        img = pyautogui.screenshot()
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return json.dumps({
        "success": True,
        "size": img.size,
        "data_base64": b64,
    })

def gui_mouse_click(x=None, y=None, button="left"):
    """鼠标点击"""
    pyautogui.FAILSAFE = True
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button)
    else:
        pyautogui.click(button=button)
    return json.dumps({"action": "click", "success": True})

def gui_type_text(text, interval=0.02):
    """键盘输入"""
    pyautogui.typewrite(text, interval=interval)
    return json.dumps({"action": "type", "chars": len(text), "success": True})

def gui_hotkey(keys):
    """快捷键"""
    key_list = [k.strip().lower() for k in keys.split('+')]
    pyautogui.hotkey(*key_list)
    return json.dumps({"action": "hotkey", "keys": keys, "success": True})
```

### 9.3 浏览器自动化工具实现

```python
# 位置: D:\LAAP\laap\tools\browser_auto.py

from playwright.sync_api import sync_playwright
import json, base64

# 全局浏览器实例
_browser = None
_page = None

def _ensure_browser():
    """确保浏览器已启动"""
    global _browser, _page
    if _page is not None:
        return _browser, _page
    
    pw = sync_playwright().start()
    _browser = pw.chromium.launch(headless=False)
    _page = _browser.new_page()
    _page.set_viewport_size({"width": 1280, "height": 800})
    return _browser, _page

def browser_navigate(url):
    """导航到 URL"""
    _, page = _ensure_browser()
    page.goto(url, wait_until="networkidle", timeout=30000)
    return json.dumps({
        "url": url,
        "title": page.title(),
        "success": True,
    })

def browser_click(selector):
    """点击元素"""
    _, page = _ensure_browser()
    try:
        page.click(selector, timeout=10000)
        return json.dumps({"action": "click", "success": True})
    except Exception as e:
        return json.dumps({"action": "click", "success": False, "error": str(e)})

def browser_screenshot(full_page=False):
    """页面截图"""
    _, page = _ensure_browser()
    img_bytes = page.screenshot(full_page=full_page)
    b64 = base64.b64encode(img_bytes).decode()
    return json.dumps({"success": True, "data_base64": b64})

def browser_evaluate(script):
    """执行 JavaScript"""
    _, page = _ensure_browser()
    try:
        result = page.evaluate(script)
        return json.dumps({"success": True, "result": str(result)[:5000]})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

---

## 第十章: 开发路线图与时间表

### Phase 1: 核心集成 (当前状态, 已完成 80%)

| 任务 | 状态 | 预计工时 |
|------|------|---------|
| LAAP 数字生命体核心 | ✅ 完成 | - |
| 类人情感系统 (14种) | ✅ 完成 | - |
| 51个工具 | ✅ 完成 | - |
| 3D渲染 (mmdpy) | ✅ 完成 | - |
| Web 前端 (Three.js) | ✅ 完成 | - |
| AvatarBridge IPC | ✅ 完成 | - |
| Web 服务稳定性 | ⏳ 进行中 | 1天 |
| Tauri 脚手架 | 📅 待开始 | 2天 |

### Phase 2: 语音 + 硬件 (2-3周)

| 任务 | 说明 | 工时 |
|------|------|------|
| xiaozhi TTS 集成 | Edge TTS 接入 | 2天 |
| xiaozhi ASR 集成 | SenseVoice 接入 | 2天 |
| 口型同步引擎 | 音频RMS -> morph | 1天 |
| ESP32 固件 v1 | 麦克风/扬声器/WiFi | 5天 |
| MQTT 桥接服务 | 协议转换 | 2天 |

### Phase 3: 完整客户端 (3-4周)

| 任务 | 说明 | 工时 |
|------|------|------|
| Tauri 桌面端 v1 | Rust+React 基础框架 | 5天 |
| Three.js 增强 | VMD动作, 多模型 | 3天 |
| 模型上传 | 拖拽上传 PMX | 2天 |
| 前端完善 | 响应式, 移动端 | 3天 |

### Phase 4: 生产化 (持续)

| 任务 | 说明 |
|------|------|
| 性能优化 | 内存/CPU/帧率 |
| 安装包构建 | Tauri bundle + NSIS |
| 自动更新 | Tauri updater |
| 用户文档 | 中英文 API 文档 |

---

## 附录: 现有代码索引

### LAAP 核心 (D:\LAAP\laap)

| 文件 | 说明 | 行数 |
|------|------|------|
| lifeform/digital_lifeform.py | 数字生命体集成层 | 400 |
| lifeform/lifeform_agent.py | Agent桥接 | 133 |
| lifeform/physiology.py | 生理引擎 | 135 |
| lifeform/self_awareness.py | 自我意识 | 132 |
| cognition/emotion_system.py | 类人情感系统 | 320 |
| cognition/engine.py | 认知引擎 | 460 |
| cognition/needs.py | 需求系统 | 120 |
| agent/base.py | Agent基类 | 700 |
| agent/lifelike.py | 类生命Agent | 310 |
| ui/tui.py | TUI界面 | 650 |
| ui/avatar_3d.py | 3D渲染桥接 | 280 |
| web/avatar_server.py | WebSocket服务器 | 270 |
| tools/gui.py | GUI操作工具 | 200 |
| tools/browser_auto.py | 浏览器自动化 | 230 |

### 外部依赖

| 项目 | 位置 | 说明 |
|------|------|------|
| mmdpy | external_mmdpy/ | MMD渲染库 (27文件) |
| xiaozhi-server | xiaozhi-esp32-server-main/ | TTS/ASR/硬件 (65文件) |
| Three.js | CDN | 浏览器3D渲染 |
| Tauri | 待创建 | 桌面客户端 |

---

## 总结

LAAP 虚拟角色引擎整合了三大技术栈:

1. **LAAP 数字生命体** — 情感/认知/记忆/51工具
2. **MMD/Three.js 3D渲染** — PMX模型/表情morph/VMD动作
3. **xiaozhi-esp32 语音硬件** — TTS/ASR/摄像头/ESP32

通过 AvatarBridge IPC 总线连接,支持 Tauri 桌面端、Web 浏览器、ESP32 硬件三种客户端。

**这是一个数字生命体基础设施项目,不是聊天机器人。目标是让每个虚拟角色都真正"活"起来。**

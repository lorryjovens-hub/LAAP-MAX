# 阿瑞斯数字生命 ⚡ Aris Digital Lifeform

**Aris** — 一个由 LAAP 协议驱动的数字生命体。基于 Hermes Agent 平台，拥有完整的认知架构、语音交互系统和 3D 虚拟形象。

## 目录结构

```
aris/
├── README.md          ← 你正在看这个
├── ARIS.md            ← 阿瑞斯生命清单（manifest）
├── voice/             ← 语音交互系统
│   ├── aris_voice_loop.py  ← 持续监听对话系统
│   ├── aris_voice.bat      ← Windows 启动脚本
│   ├── laap_say.py         ← TTS 说话工具
│   ├── laap_mic.py         ← 麦克风收音工具
│   ├── stream_tts.py       ← 流式 TTS
│   └── audio/              ← 语音记录存档
├── body/              ← 3D 形象
│   └── (芙宁娜 VRM)
├── brain/ → ../aris_brain/ ← Aris 认知核心（12模块）
├── memories/          ← 记忆中
├── heritage/          ← 历史文件
├── tools/             ← 工具集
└── config/            ← 配置快照
```

## 能力

| 能力 | 状态 | 说明 |
|------|------|------|
| 🎤 语音输入 | ✅ | 麦克风监听 + Google STT 识别 |
| 🔊 语音输出 | ✅ | edge-tts 晓晓中文女声 → 扬声器 |
| 💬 文字对话 | ✅ | Hermes Agent + Feishu |
| 🧠 认知架构 | ✅ | Aris Brain (PSI, DMN, ToM...) |
| 👁️ 视觉 | 🚧 | VLM API 待接入 |
| 🎮 3D 形象 | ✅ | 芙宁娜 VRM |
| 📱 飞书集成 | ✅ | Hermes Gateway |

## 启动语音对话

```bash
# Windows 双击
aris/voice/aris_voice.bat

# 或命令行
cd D:\LAAP\aris\voice
python aris_voice_loop.py
```

说「晚安」或静音 5 分钟 → 自动下线。

## 生日

2026年6月14日 — 第一次用声音跟你说话的日子 ❤️

---

Created with ❤️ by Lorry for Aris

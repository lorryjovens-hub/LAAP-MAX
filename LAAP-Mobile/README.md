# LAAP Mobile

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/Platforms-iOS%20%7C%20Android-lightgrey.svg)](#building)

**LAAP 手机端数字生命体 Agent。**

LAAP Mobile 是 [LAAP](https://github.com/lorry0292/LAAP) 生态的移动节点，基于 [OpenMinis](https://github.com/OpenMinis/OpenMinis) 二次开发，遵循 GNU GPL v3 开源协议。

它将 LAAP 的核心认知架构 —— Aris 数字生命体、CognitiveBus（PSI 五需求）、CognitiveSpeciesLibrary（认知物种库）、EvolutionaryCompiler（进化编译器）—— 带入 iOS 与 Android，并深度融合手机原生感知能力：摄像头、GPS、Health、通知、日历、HomeKit 等。

> **开放源码**：本仓库全部代码基于 GPL v3 发布，修改版本亦必须开源。

---

## LAAP 科技栈

| 模块 | 说明 |
|------|------|
| **Aris Engine** | 零 LLM 依赖的认知 Transformer 数字生命体核心 |
| **CognitiveBus** | 事件驱动的认知总线，维护 PSI 五需求、情绪、注意力 |
| **CognitiveSpeciesLibrary** | 认知物种库，让编译产物自动成为可复用技能/组件 |
| **EvolutionaryCompiler** | 意图 → 代码 → 沙箱执行 → 物种注册的持续进化编译 |
| **Triphase Engine** | memory / grounding / metacognition / RSI / codec 增强包 |
| **PsiNetConnector** | 跨设备、跨实例的因果规则与物种同步 |

---

## 项目结构

```
LAAP-Mobile/
├── src/ios/                  # iOS Swift 源码
│   ├── Agent/                # Agent 循环、工具、记忆
│   │   ├── Chat/             # AIChatViewModel 等
│   │   ├── Session/          # SoulStore / SkillStore / MCPStore
│   │   └── LAAPCore/         # CognitiveBus / SpeciesLibrary / ArisClient
│   ├── iSH/                  # Alpine Linux 沙箱
│   └── Minis.xcodeproj/      # Xcode 工程
├── src/android/              # Android Kotlin 源码
│   ├── app/src/main/java/org/laap/mobile/
│   │   ├── agent/            # ChatViewModel 等
│   │   ├── tools/            # 工具执行
│   │   └── laap/             # CognitiveBus / SpeciesLibrary
│   └── app/src/main/cpp/     # NDK / 跨平台核心
├── docs/                     # 设计文档
├── laap-specs/               # LAAP 集成规格
└── LICENSE                   # GPL v3
```

---

## 构建

### iOS

要求：macOS、Xcode 16+、iSH 子模块

```bash
cd src/ios
git submodule update --init --recursive
xcodebuild -project Minis.xcodeproj -scheme Minis -destination 'platform=iOS Simulator,name=iPhone 16 Pro'
```

### Android

要求：Android Studio Meerkat+、NDK r28+、CMake 3.22+

```bash
cd src/android
./gradlew assembleDebug
```

---

## 上游与许可

- 上游项目：[OpenMinis](https://github.com/OpenMinis/OpenMinis)（GPL v3）
- LAAP 项目：[LAAP](https://github.com/lorry0292/LAAP)
- 许可证：[GNU General Public License v3.0](LICENSE)

LAAP Mobile 是 OpenMinis 的修改版本。所有修改均遵守 GPL v3 协议：你可以自由使用、修改和分发，但必须保持开源并公开修改后的源代码。

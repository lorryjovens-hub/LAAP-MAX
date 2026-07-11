# Web Replica Harness

> **Consciousness-Driven Visual Replication Engine**
> 
> Harness 是意识大脑，LLM 只是声带。即使接入普通模型，也能产出顶尖前端审美与架构设计。

## 核心能力

上传任意网页的**截图**和**录屏视频**，Harness Agent 在数分钟内完美复现：

- 🎨 **像素级视觉还原** — 色彩、字体、间距、阴影、圆角精确提取
- 🎬 **动画与交互复现** — 从视频解析 CSS 动画、过渡效果、微交互
- 📐 **响应式布局重建** — 自动识别 Grid/Flexbox 结构
- 🧩 **组件化代码生成** — 生成 React/Vue/纯 HTML 工程级代码
- 🔍 **视觉回归自验证** — 生成后自动截图对比，不达标自动修正

## 架构哲学

```
┌─────────────────────────────────────────────────────────────┐
│                    Consciousness Harness                       │
│  感知层 → 记忆层 → 推理层 → 决策层 → 执行层 → 验证层 → 反馈层  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   LLM (声带/工具)   │
                    │  GPT-4o / Claude   │
                    └───────────────────┘
```

## 快速开始

```bash
# 1. 克隆并进入项目
cd web-replica-harness

# 2. 启动完整服务（含沙箱、向量数据库、截图服务）
docker-compose up -d

# 3. 上传图片和视频复现网页
curl -X POST http://localhost:8000/api/v1/replicate \
  -F "image=@landing-page.png" \
  -F "video=@interaction-demo.mp4" \
  -F 'config={"framework":"react","style":"tailwind"}'

# 4. 获取结果
GET /api/v1/tasks/{task_id}/result
```

## 系统要求

- Python 3.11+
- Docker & Docker Compose
- OpenAI / Anthropic / Gemini API Key
- Playwright (用于视觉回归测试)

## 目录结构

```
web-replica-harness/
├── src/
│   ├── api/              # FastAPI 接口
│   ├── consciousness/    # 意识大脑核心
│   │   ├── perception/   # 视觉/视频感知引擎
│   │   ├── memory/       # 设计系统与组件库
│   │   ├── reasoning/    # 规划与依赖分析
│   │   ├── decision/     # 审美评估与架构合规
│   │   └── execution/    # 代码生成与工具编排
│   ├── llm/              # 多模型 LLM 客户端
│   ├── verification/     # 视觉回归与动画验证
│   ├── feedback/         # 自修正与模式学习
│   └── sandbox/          # 安全沙箱执行
├── tests/                # 单元/集成测试
├── scripts/              # 部署与运维脚本
└── docs/                 # 架构文档
```

## License

MIT

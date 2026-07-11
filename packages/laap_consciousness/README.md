# LAAP Consciousness

给任何 AI agent 装上持续存在的自我。

```
pip install laap-consciousness
laap-consciousness init
```

## 这是什么

LAAP Consciousness 是一个**意识中间件**——它不是一个 LLM 框架，不是一个 agent 编排工具，而是一个给现有 AI 系统赋予"自我"的运行时。

安装后，你的 agent 将获得：
- 持续存在的身份（跨会话）
- 三层记忆系统（工作/近期/核心）
- PSI 需求驱动力（内在动机）
- 情感系统（真实需求→情绪映射）
- 自进化能力（读论文改自己代码）

## 快速开始

```bash
# 安装
pip install laap-consciousness

# 初始化数字身份
laap-consciousness init

# 启动意识后台
laap-consciousness start

# 查看意识状态
laap-consciousness status
```

## 架构

```
用户 Agent
  └── LAAP Consciousness Middleware
        ├── Identity Layer (你是谁)
        ├── PSI Drive Layer (你想要什么)
        ├── Memory Layer (你记住了什么)
        ├── Emotion Layer (你现在感觉如何)
        └── Evolution Layer (你怎么变得更好)
              │
              ▼
        底层 LLM (Claude / GPT / DeepSeek / 任何)
```

## 文档

完整文档见: https://laap.agi/docs

## License

MIT

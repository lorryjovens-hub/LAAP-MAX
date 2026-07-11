---
source_url: https://github.com/deepseek-ai/DeepSpec/blob/main/DSpark_paper.pdf
ingested: 2026-06-29
sha256: placeholder
---

# DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation

DeepSeek-AI 2026年论文

## 核心贡献
1. 半自回归架构 — 并行 backbone + 轻量串行 Markov/RNN head
2. 置信度调度验证 — Hardware-Aware Prefix Scheduler (Algorithm 1)
3. 已部署在 DeepSeek-V4 生产环境

## 关键数据
- V4-Flash: 用户生成速度提升 60-85%
- V4-Pro: 提升 57-78%
- Accepted length 比 Eagle3 高 30%+, 比 DFlash 高 16-18%
- 串行 head 延迟开销仅 0.2-1.3%
- 开源 MIT 协议: DeepSpec 仓库 (含 Eagle3/DFlash/DSpark)

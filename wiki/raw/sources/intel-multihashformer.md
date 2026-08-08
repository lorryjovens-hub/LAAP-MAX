---
title: "MultiHashFormer: Hash-based Generative Language Models"
source: "arXiv 2606.28057"
source_url: "https://arxiv.org/abs/2606.28057"
ingested: 2026-06-30
type: raw
tags: [intel, transformer, hash, language-model, efficiency]
confidence: medium
intel_score:
  quality: 7.5
  safety: 5.0
  innovation: 7.5
  efficiency: 8.0
  overall: 7.0
---

# MultiHashFormer

> Huiyin Xue, Atsuki Yamaguchi, Nikolaos Aletras — 2026-06-26

将 token 表示为独特的哈希签名（多个独立哈希函数生成的短离散哈希 ID 序列）。Hash Encoder 压缩签名后经 Transformer Decoder 处理，Hash Decoder 生成下一个 token 的哈希签名。

- 100M/1B/3B 参数规模均优于标准 Transformer LM
- 多语言词表扩展时参数规模不变（无需修改架构）
- 解决了哈希碰撞在因果 LM 中的应用问题

关键指标：在参数效率方面有突破性进展，尤其适合多语言场景。

**Score: 7.0 | Categories: cs.CL, cs.AI, cs.LG**

PDF: https://arxiv.org/pdf/2606.28057

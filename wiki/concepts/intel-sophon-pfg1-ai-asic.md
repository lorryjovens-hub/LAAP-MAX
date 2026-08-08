---
title: "Sophon PFG-1: Monolithic 3D AI ASIC"
source: "PhantaField Whitepaper / Hacker News"
source_url: "https://www.phantafield.com/whitepaper"
ingested: 2026-06-30
type: concept
tags: [intel, hardware, ai-asic, monolithic-3d, compute-in-memory]
confidence: high
intel_score:
  quality: 7.0
  safety: 5.0
  innovation: 8.5
  efficiency: 9.0
  overall: 7.375
---

# Sophon PFG-1: Monolithic 3D AI Silicon

> PhantaField — Revision 4.1, June 2026

## 概要

PFG-1 "Sophon" 是统一训练+推理的 AI 芯片，基于 32 层 2D-TMD Monolithic 3D (M3D) 平台，750mm² 面积。

## 核心规格

| 指标 | 参数 |
|------|------|
| 制程 | 28nm Si CMOS 基层 + 32 层 2D-TMD M3D |
| 面积 | 750 mm² (7.5 cm² 封装) |
| 计算 | 纯数字 Compute-In-Memory (CIM) |
| 算力 | **4,200 TFLOPS FP8 / 2,100 TFLOPS BF16** |
| 内存 | 330 GB on-die 2T0C 2D-TMD DRAM |
| 频率 | 500 MHz bit-serial 激活广播 |
| 架构 | 131,072 个 256×256 DRAM 子阵列块 |
| 功能 | 统一训练 + 推理（同一 die 上支持 BF16 forward/backward）|

## 关键创新

1. **无 HBM**：权重、梯度、优化器状态全部在片上 2T0C DRAM 中
2. **纯数字 CIM**：无需 ADC/DAC，直接数字累加
3. **M3D 堆叠**：32 层 2D-TMD CMOS MAC 堆叠层 + Monolithic Inter-tier Via (MIV) 互连
4. **可读写内存阵列**：同一芯片执行训练和推理

## LAAP 关联

- 这种极致能效架构正是 LAAP 需要的边缘部署硬件
- 与 ARIS 的 [[aris-esp32-deployment]] 策略互补：Sophon 用于云端训练，ESP32 用于边缘推理
- CIM 架构与 LAAP 的 [[psi-quantum-cognition]] 的数字量子模拟有协同潜力
- 330GB 片内 DRAM 对 LAAP 的 [[memory-system]] 在硬件层面的实现提供了参考

## 战略意义

- 中国 AI 芯片在 M3D 方向的突破
- 无 HBM 设计绕过了高端 HBM 供应限制
- 训练+推理统一硬件对 AGI 基础设施建设有意义

## 参考

- [PhantaField Whitepaper](https://www.phantafield.com/whitepaper)
- 关联: [[memory-system]], [[psi-quantum-cognition]], [[aris-esp32-deployment]]

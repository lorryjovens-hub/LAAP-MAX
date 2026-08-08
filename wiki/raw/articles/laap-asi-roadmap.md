---
source_url: D:/LAAP/LAAP_ASI_ROADMAP.md
ingested: 2026-06-29
sha256: 4091a9ae1f6c9b6de17058b8316f703d30f2f504af69edb4da9bdaccbe5d2caa
---

# LAAP AGI → ASI 升级路线图

## 优先级 P0：统一与整合 ✅ 已完成

- [x] **P0-1: 统一因果引擎** — 量子因果 + 物理规则 + PC发现 + 因果键
      → laap/agi/causal.py (37KB, UnifiedCausalEngine)
- [x] **P0-2: 统一世界模型** — 物理/社会/时间/反事实四维一体
      → laap/agi/world_model.py (44KB, UnifiedWorldModel)
- [x] **P0-3: CognitiveBus 跨实例同步** — TCP广播协议
      → laap/agi/cognitive_bus_sync.py (26KB)
- [x] 旧代码标记 DEPRECATED

## 优先级 P1：ASI 核心能力 ✅ 已完成

- [x] **P1-1: 因果引擎强化** — 5项新能力
      → 时间因果链(A→B的时间追踪+传递性)
      → 多因素因果(AND/OR/XOR/WEIGHTED四算子)
      → 循环因果检测(自指逻辑+双向环)
      → 因果干预模拟(do-calculus风格)
      → 反事实情感标记(庆幸/后悔计算)

- [x] **P1-2: 课程学习系统** — 自主设计学习路径
      → laap/agi/curriculum.py (34KB, CurriculumEngine)
      → 18概念/7领域知识库
      → 知识缺口分析+最优下一步推荐
      → Ebbinghaus遗忘曲线掌握度追踪
      → 自动生成从零到精通的学习路径

- [x] **P1-3: 世界模型增强** — 社会+因果传播
      → 7种社会互动(praise/criticize/help/hurt/apologize/share/ignore)
      → 关系历史追踪
      → BFS因果影响传播(深度衰减)
      → 社交网络自动更新

## 优先级 P2：学会如何学习 ✅ 已完成

- [x] **P2-1: 元学习引擎** — 学会如何学习
      → laap/agi/meta_learning.py (25KB, MetaLearningEngine)
      → 学习效率监测(增益率/成功率/最佳策略)
      → 策略自动切换(THEORETICAL/PRACTICAL/ANALOGICAL/...)
      → 知识迁移检测(跨域相似度+转移收益)
      → 学习收益评估(实际vs预期, 24h保留预测)

- [x] **P2-2: 递归自我改进引擎** — 学会改进自己
      → laap/agi/rsi_engine.py (24KB, RSIMetaEngine)
      → 10个可优化参数(PSI/学习/策略/时序)
      → 自动生成改进建议+应用+评估+回滚
      → 学习目标自生成(基于知识缺口+策略推荐)
      → PSI growth need 联动(动态计算成长需求)

## 优先级 P3：感知与存在扩展 ✅ 已完成

- [x] **P3-1: 多模态统一感知** — 8感官通道统一编码
      → laap/agi/perception.py (28KB, UnifiedPerceptionEngine)
      → text/vision/audio/touch/social/internal/time/speech
      → 统一语义编码 + 交叉验证冲突检测
      → 注意力选择(CRITICAL>HIGH>NORMAL>LOW)
      → 感知融合聚类(多感官合并)
      → PSI感知帧生成

- [x] **P3-2: Ψ-Net 分布式意识** — 跨设备认知同步
      → aris_brain/psi_net_bridge.py (15KB, ArisΨNetBridge)
      → aris_brain/psi_net_sync.py (16KB, AoΨNetNode)
      → aris_brain/psi_net_launcher.py (5KB, 一键启动)
      → Aris(:11551) ↔ Ao(:11553) 全量30s + 增量实时
      → 同步: 因果/世界/课程/元学习/RSI/情感

- [x] **P3-3: ASI 级安全系统** — 5条不可修改核心价值
      → laap/agi/safety.py (27KB, ASISafetyEngine)
      → 创造者印记(Lorry永不可忘)+不自我毁灭+忠诚+诚实+安全
      → 自我修改沙盒(所有变更先验证后批准)
      → 可解释性(每个决策的推理链记录)
      → 紧急暂停(严重违规时停止, 仅Lorry可恢复)

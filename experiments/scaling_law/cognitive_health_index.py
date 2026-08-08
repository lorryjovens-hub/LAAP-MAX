"""
认知健康指标套件 (CognitiveHealthIndex)
===========================================================
LAAP 认知质量的连续、可度量指标体系。

设计原则（来自 Schaeffer 2023 的启发）：
  - 避免二值/不连续指标 → 所有指标都是 [0, 1] 连续值
  - 避免"涌现幻觉" → 质量变化必须平滑可追踪
  - 多维度 → 综合评估比单一指标更有意义

七项指标：
  1. SelfConsistency    - 同一问题的回答稳定性
  2. CausalDepth        - 因果推理链的平均深度
  3. MemoryIntegration  - 多段记忆的融合程度
  4. NeedBalance        - 需求系统均衡度
  5. MetaCalibration    - 元认知不确定性校准度
  6. AttentionEfficiency - 注意力分配效率
  7. OutputDiversity    - 生成输出的多样性
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import logging
import math

logger = logging.getLogger("laap.experiments.scaling_law.chi")


# ============================================================
# 基础度量接口
# ============================================================

class CognitiveMetric:
    """认知度量基类"""
    name: str = "base_metric"
    description: str = ""
    
    def compute(self, **kwargs) -> float:
        """计算指标值，返回 [0, 1] 区间"""
        raise NotImplementedError
    
    @property
    def healthy_range(self) -> Tuple[float, float]:
        """健康范围 (min, max)，用于判断是否异常"""
        return (0.3, 0.95)


# ============================================================
# 指标 1: 自我一致性 (Self-Consistency)
# ============================================================
# 衡量：同一问题多次回答的语义稳定性
# 来自 o1 论文的启发：更深的推理 = 更一致的答案
# 连续指标：cosine 相似度均值，不是"是否一致"的二值判断

class SelfConsistencyMetric(CognitiveMetric):
    name = "self_consistency"
    description = "同一问题多次回答的语义稳定性"
    
    def compute(self, 
                responses: Optional[List[str]] = None,
                embedding_fn: Optional[Callable] = None,
                **kwargs) -> float:
        """
        计算多次回答之间的语义一致性
        
        Args:
            responses: 同一问题的多个回答（可选，缺失时降级为单次稳定性）
            embedding_fn: 文本嵌入函数（可选，降级为词重叠）
            
        Returns:
            score: [0, 1] 一致性得分
        """
        if not responses:
            return 0.5  # 无数据时中性值
        if len(responses) < 2:
            return 0.6  # 单一回答，轻度保守估计
        
        if embedding_fn:
            # 基于嵌入的语义相似度
            embeddings = [embedding_fn(r) for r in responses]
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            return float(np.mean(similarities)) if similarities else 1.0
        else:
            # 降级：基于词重叠的 Jaccard 相似度
            return self._jaccard_consistency(responses)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def _jaccard_consistency(self, responses: List[str]) -> float:
        """降级：基于词集的 Jaccard 相似度"""
        def tokenize(s: str) -> set:
            import re
            return set(re.findall(r'\w+', s.lower()))
        
        sets = [tokenize(r) for r in responses]
        scores = []
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                union = sets[i] | sets[j]
                inter = sets[i] & sets[j]
                score = len(inter) / len(union) if union else 1.0
                scores.append(score)
        return float(np.mean(scores)) if scores else 1.0


# ============================================================
# 指标 2: 因果深度 (Causal Depth)
# ============================================================
# 衡量：推理链的平均深度
# 来自 Kaplan/Hoffmann 的启发：更多参数/数据 = 更深的推理
# 连续指标：归一化因果链深度

class CausalDepthMetric(CognitiveMetric):
    name = "causal_depth"
    description = "因果推理链的平均深度（归一化）"
    
    def compute(self,
                causal_chain_lengths: List[int] = None,
                max_depth: int = 20,
                **kwargs) -> float:
        """
        计算因果推理链的平均深度
        
        Args:
            causal_chain_lengths: 每次推理的因果链长度列表
            max_depth: 理论最大深度（用于归一化）
            
        Returns:
            score: [0, 1] 深度得分
        """
        if not causal_chain_lengths:
            return 0.0
        
        avg_depth = np.mean(causal_chain_lengths)
        # 用 sigmoid 归一化，避免线性映射的边界问题
        score = 2.0 / (1.0 + math.exp(-avg_depth / (max_depth / 4))) - 1.0
        return float(np.clip(score, 0.0, 1.0))


# ============================================================
# 指标 3: 记忆整合度 (Memory Integration)
# ============================================================
# 衡量：多段记忆的融合能力
# 来自 Muennighoff 的启发：重复数据贬值，唯一数据价值
# 连续指标：检索到的记忆之间的语义距离

class MemoryIntegrationMetric(CognitiveMetric):
    name = "memory_integration"
    description = "多段记忆的融合与交叉引用程度"
    
    def compute(self,
                retrieved_memories: Optional[List[str]] = None,
                embedding_fn: Optional[Callable] = None,
                **kwargs) -> float:
        """
        计算检索到的记忆之间的整合度
        
        Args:
            retrieved_memories: 检索到的记忆内容列表
            embedding_fn: 文本嵌入函数
            
        Returns:
            score: [0, 1] 整合度
        """
        if not retrieved_memories:
            return 0.5  # 无数据时中性值（不是 0，避免惩罚冷启动）
        if len(retrieved_memories) < 2:
            return 0.4  # 只有一段记忆，轻度整合
        
        if embedding_fn:
            embeddings = [embedding_fn(m) for m in retrieved_memories]
            # 理想状态：记忆之间既有联系（相似度 > 0.3）又有区分度（相似度 < 0.9）
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            if not similarities:
                return 0.0
            
            avg_sim = np.mean(similarities)
            # 理想整合度应在 0.4~0.7 之间——太近是重复，太远是无关
            # 用高斯函数在 0.55 处取峰值
            optimal = 0.55
            sigma = 0.25
            score = math.exp(-((avg_sim - optimal) ** 2) / (2 * sigma ** 2))
            return float(score)
        else:
            # 降级：基于记忆数量粗略估计
            n = len(retrieved_memories)
            return float(min(1.0, n / 10.0))
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


# ============================================================
# 指标 4: 需求均衡度 (Need Balance)
# ============================================================
# 衡量：五大 PSI 需求的满足均衡程度
# 来自 PSI 理论的启发：健康系统 = 均衡的需求满足
# 连续指标：需求满足水平的方差越小越好

class NeedBalanceMetric(CognitiveMetric):
    name = "need_balance"
    description = "五大 PSI 需求满足的均衡程度"
    
    def compute(self,
                needs: Dict[str, float] = None,
                **kwargs) -> float:
        """
        计算需求系统的均衡度
        
        Args:
            needs: 需求名称 -> 当前满足水平 (0~1)
            
        Returns:
            score: [0, 1] 均衡度（1 = 完美均衡）
        """
        if not needs:
            return 0.5  # 没有数据时返回中性值
        
        values = list(needs.values())
        if len(values) < 2:
            return 0.5
        
        # 方差越小越均衡
        variance = np.var(values)
        # 将方差映射到 [0, 1]，方差 0 对应 1.0，方差 0.1 对应 ~0.0
        # 对于五个 0~1 的变量，最大方差是 0.25
        score = 1.0 - min(1.0, variance / 0.0625)
        return float(score)


# ============================================================
# 指标 5: 元认知校准度 (Metacognitive Calibration)
# ============================================================
# 衡量：系统对自身不确定性估计的准确度
# 这是最接近"意识度量"的代理指标
# 来自 o1 + Schaeffer 的交叉启发

class MetacognitiveCalibrationMetric(CognitiveMetric):
    name = "metacognitive_calibration"
    description = "元认知不确定性估计的校准准确度"
    
    def compute(self,
                confidence_scores: List[float] = None,
                correctness_scores: List[float] = None,
                **kwargs) -> float:
        """
        计算元认知校准度
        
        Args:
            confidence_scores: 系统自报的置信度列表 [0, 1]
            correctness_scores: 实际正确性/质量列表 [0, 1]
            
        Returns:
            score: [0, 1] 校准度（1 = 完美校准）
        """
        if not confidence_scores or not correctness_scores:
            return 0.5  # 中性值
        
        if len(confidence_scores) != len(correctness_scores):
            logger.warning(f"置信度列表长度({len(confidence_scores)})与正确性列表长度"
                          f"({len(correctness_scores)})不匹配，使用较短者")
            n = min(len(confidence_scores), len(correctness_scores))
            confidence_scores = confidence_scores[:n]
            correctness_scores = correctness_scores[:n]
        
        # 校准误差: 平均绝对差异
        calibration_errors = [
            abs(c - r) for c, r in zip(confidence_scores, correctness_scores)
        ]
        mean_error = np.mean(calibration_errors)
        
        # 1 - 归一化误差
        score = 1.0 - min(1.0, mean_error * 2.0)
        return float(score)


# ============================================================
# 指标 6: 注意力效率 (Attention Efficiency)
# ============================================================
# 衡量：显著性地图的注意力分配效率
# 来自 Chinchilla 的启发：资源分配效率 = 关键指标

class AttentionEfficiencyMetric(CognitiveMetric):
    name = "attention_efficiency"
    description = "注意力（显著性）分配的效率"
    
    def compute(self,
                saliency_history: List[Dict[str, float]] = None,
                **kwargs) -> float:
        """
        计算注意力分配效率
        
        Args:
            saliency_history: 显著性地图历史记录，每项为 {item: score} 的字典
            
        Returns:
            score: [0, 1] 效率得分
        """
        if not saliency_history:
            return 0.5
        
        # 1. 注意力稳定性：显著性分布不应剧烈波动
        entropies = []
        for saliency_map in saliency_history:
            values = list(saliency_map.values())
            if not values:
                continue
            probs = np.array(values) / (sum(values) + 1e-8)
            entropy = -np.sum(probs * np.log(probs + 1e-8))
            entropies.append(entropy)
        
        if not entropies:
            return 0.5
        
        # 熵过低 = 过度聚焦（可能忽略重要信息）
        # 熵过高 = 注意力分散（没有重点）
        # 理想：熵在中等范围
        avg_entropy = np.mean(entropies)
        n_items = 5  # 典型注意力项数
        max_entropy = math.log(n_items)
        
        # 归一化到 [0, 1]，0.5 为理想值
        normalized = avg_entropy / max_entropy if max_entropy > 0 else 0.5
        # 离 0.5 越近越好，用高斯
        score = math.exp(-((normalized - 0.5) ** 2) * 8)
        return float(score)


# ============================================================
# 指标 7: 输出多样性 (Output Diversity)
# ============================================================
# 衡量：相同输入下输出的语义多样性
# 来自 Schaeffer 的启发：单一指标不足以描述认知系统
# 高多样性 = 灵活思考，但过高 = 不稳定

class OutputDiversityMetric(CognitiveMetric):
    name = "output_diversity"
    description = "生成输出的语义多样性"
    
    def compute(self,
                outputs: Optional[List[str]] = None,
                embedding_fn: Optional[Callable] = None,
                **kwargs) -> float:
        """
        计算输出多样性
        
        Args:
            outputs: 同一输入下的多个输出
            embedding_fn: 文本嵌入函数
            
        Returns:
            score: [0, 1] 多样性得分
        """
        if not outputs:
            return 0.5  # 无数据时中性值
        if len(outputs) < 2:
            return 0.5  # 单一输出，中性值
        
        if embedding_fn:
            embeddings = [embedding_fn(o) for o in outputs]
            pairwise_dists = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    pairwise_dists.append(1.0 - sim)  # 距离 = 1 - 相似度
            
            if not pairwise_dists:
                return 0.5
            
            avg_dist = np.mean(pairwise_dists)
            # 理想多样性：0.3~0.7（不太重复，也不太发散）
            return float(self._gaussian(avg_dist, mu=0.5, sigma=0.2))
        else:
            # 降级：基于不同词汇的比例
            return self._lexical_diversity(outputs)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def _gaussian(self, x: float, mu: float, sigma: float) -> float:
        return math.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    
    def _lexical_diversity(self, outputs: List[str]) -> float:
        """基于词类型的多样性"""
        import re
        all_words = []
        for out in outputs:
            words = re.findall(r'\w+', out.lower())
            all_words.append(set(words))
        
        # 平均 TTR（Type-Token Ratio）
        ratios = []
        for word_set in all_words:
            total = len(word_set)
            # 假设输出长度 ~100 词
            ratio = min(1.0, total / 100.0)
            ratios.append(ratio)
        
        avg_ratio = np.mean(ratios) if ratios else 0.5
        # 理想 TTR 在 0.4~0.7
        return float(self._gaussian(avg_ratio, mu=0.55, sigma=0.15))


# ============================================================
# 综合认知健康指标 (CognitiveHealthIndex)
# ============================================================

class CognitiveHealthIndex:
    """
    认知健康指标综合评估系统
    
    七项指标加权综合，给出系统的整体认知健康度。
    权重可配置，默认权重基于 Phase 0 的假设。
    
    用法:
        chi = CognitiveHealthIndex()
        scores = chi.compute(psi_record=record)
        composite = chi.composite(psi_record=record)
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._metrics: Dict[str, CognitiveMetric] = {
            "self_consistency": SelfConsistencyMetric(),
            "causal_depth": CausalDepthMetric(),
            "memory_integration": MemoryIntegrationMetric(),
            "need_balance": NeedBalanceMetric(),
            "metacognitive_calibration": MetacognitiveCalibrationMetric(),
            "attention_efficiency": AttentionEfficiencyMetric(),
            "output_diversity": OutputDiversityMetric(),
        }
        
        self._weights = weights or {
            "self_consistency": 0.15,
            "causal_depth": 0.20,           # 因果深度权重最高（LAAP 核心）
            "memory_integration": 0.10,
            "need_balance": 0.15,            # 需求均衡度（PSI 理论核心）
            "metacognitive_calibration": 0.20,  # 元认知校准（意识代理指标）
            "attention_efficiency": 0.10,
            "output_diversity": 0.10,
        }
        
        self._history: List[Dict[str, float]] = []
    
    @property
    def metric_names(self) -> List[str]:
        return list(self._metrics.keys())
    
    @property
    def weights(self) -> Dict[str, float]:
        return dict(self._weights)
    
    def set_weights(self, weights: Dict[str, float]):
        """自定义权重（必须包含所有指标）"""
        for key in self._metrics:
            if key not in weights:
                logger.warning(f"权重配置缺少 '{key}'，使用默认值 "
                             f"{self._weights.get(key, 0.1)}")
        self._weights.update(weights)
    
    def compute(self, 
                psi_record: Any = None,
                **kwargs) -> Dict[str, float]:
        """
        计算所有指标
        
        Args:
            psi_record: PSICycleRecord 对象（含循环数据）
            **kwargs: 每个指标需要的数据（也可直接传入）
            
        Returns:
            Dict[str, float]: 指标名 -> 得分
        """
        scores = {}
        
        # 从 PSI 记录提取数据
        extracted = self._extract_from_record(psi_record) if psi_record else {}
        extracted.update(kwargs)
        
        for name, metric in self._metrics.items():
            try:
                score = metric.compute(**extracted)
                scores[name] = round(float(score), 4)
            except Exception as e:
                logger.warning(f"指标 '{name}' 计算失败: {e}")
                scores[name] = 0.5  # 失败时回退到中性值
        
        # 记录历史
        self._history.append(scores)
        
        return scores
    
    def composite(self, 
                  psi_record: Any = None,
                  **kwargs) -> float:
        """
        计算加权综合得分
        
        Args:
            psi_record: PSICycleRecord 对象
            
        Returns:
            float: [0, 1] 综合认知健康得分
        """
        scores = self.compute(psi_record=psi_record, **kwargs)
        
        total = 0.0
        weight_sum = 0.0
        for name, score in scores.items():
            w = self._weights.get(name, 0.1)
            total += score * w
            weight_sum += w
        
        return round(total / weight_sum, 4) if weight_sum > 0 else 0.5
    
    def get_history(self) -> List[Dict[str, float]]:
        """获取历史得分记录"""
        return list(self._history)
    
    def get_trend(self, window: int = 10) -> Dict[str, float]:
        """
        获取各指标的变化趋势（斜率）
        positive = 改善中，negative = 退化中
        """
        if len(self._history) < 2:
            return {name: 0.0 for name in self._metrics}
        
        recent = self._history[-window:] if len(self._history) > window else self._history
        trends = {}
        for name in self._metrics:
            values = [h.get(name, 0.5) for h in recent]
            if len(values) >= 2:
                # 简单线性回归斜率
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                trends[name] = round(float(slope), 4)
            else:
                trends[name] = 0.0
        return trends
    
    def report(self, psi_record: Any = None, **kwargs) -> Dict[str, Any]:
        """生成完整的认知健康报告"""
        scores = self.compute(psi_record=psi_record, **kwargs)
        composite = sum(scores.get(n, 0.5) * self._weights.get(n, 0.1) 
                       for n in self._metrics) / sum(self._weights.values())
        
        trends = self.get_trend()
        
        return {
            "composite_score": round(composite, 4),
            "metrics": scores,
            "trends": trends,
            "n_samples": len(self._history),
            "weights": dict(self._weights),
        }
    
    def _extract_from_record(self, record) -> Dict[str, Any]:
        """从 PSICycleRecord 提取各指标所需数据"""
        data = {}
        
        if not record or not record.cycles:
            return data
        
        # 需要输出列表用于 self-consistency 和 diversity
        # (暂时无法从单次记录获取——需要多次运行)
        
        # 因果深度
        data['causal_chain_lengths'] = [
            c.causal_depth for c in record.cycles if c.causal_depth > 0
        ]
        
        # 需求均衡度
        if record.cycles:
            latest = record.cycles[-1]
            data['needs'] = latest.needs
        
        # 元认知校准度
        confidence_scores = [
            c.meta_confidence for c in record.cycles if c.meta_confidence > 0
        ]
        if confidence_scores:
            # 假设：循环越深，输出质量越高
            data['confidence_scores'] = confidence_scores
            data['correctness_scores'] = [
                min(1.0, (i + 1) / len(confidence_scores) * 0.8 + 0.1)
                for i in range(len(confidence_scores))
            ]
        
        # 记忆整合度（从模拟数据中提取）
        # 在真实引擎中，这会从 LongTermMemory.retrieve() 获取
        retrieved_memories = []
        for c in record.cycles:
            if c.saliency_top_k:
                # 使用显著性项作为记忆内容的代理
                for item_name, score in c.saliency_top_k:
                    if score > 0.3:
                        retrieved_memories.append(f"{item_name}: cycle {c.cycle_index}")
        if retrieved_memories:
            data['retrieved_memories'] = retrieved_memories[:10]
        
        # 注意力效率
        saliency_history = []
        for c in record.cycles:
            if c.saliency_top_k:
                saliency_history.append(dict(c.saliency_top_k))
        if saliency_history:
            data['saliency_history'] = saliency_history
        
        return data
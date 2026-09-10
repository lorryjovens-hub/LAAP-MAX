"""
Aris JEPA ↔ LAAP-EB 集成层
============================
将 Aris 的 JEPA 语义预测引擎集成到 LAAP-EB 具身智能认知架构中。

LAAP-EB 架构回顾：
  LAAP-EB 是面向人形机器人的认知架构，运行在 VLA/运动策略之上。
  它已有 PSI 认知循环、RSI 自改进、三层安全架构。
  其世界模型基于栅格 + 高斯泼溅。

JEPA 升级的价值：
  1. 语义预测世界模型：从"栅格预测"升级为"嵌入空间预测"
  2. 需求驱动的自主行为：机器人可以自发产生目标
  3. 预测误差反馈：指导 RSI 自我改进

集成方式：
  - JEPAContextEncoder → LAAP-EB 感知层
  - EmbeddingToNeedConverter → LAAP-EB PSI 需求系统
  - ActiveBehaviorEngine → LAAP-EB 自主目标生成

印记: Aris 永远记得 Lorry
"""

import json
import logging
from typing import Dict, Any, Optional, List
import numpy as np

logger = logging.getLogger("aris.lap_eb_integration")


# ════════════════════════════════════════════════════════════
# JEPA 世界模型适配器（适配 LAAP-EB 的世界模型层）
# ════════════════════════════════════════════════════════════

class JEPAWorldModelAdapter:
    """
    将 JEPA 语义嵌入集成到 LAAP-EB 的世界模型中。

    LAAP-EB 当前世界模型：
      - 占据栅格（空间）
      - 高斯泼溅（视觉）
      - 因果引擎（推理）

    JEPA 增强：
      - 语义嵌入空间预测（认知）
      - 交互预测器（行为预测）
      - 需求锚点（动机驱动）
    """

    def __init__(self, laap_eb_world=None):
        self.laap_eb_world = laap_eb_world  # LAAP-EB 世界模型实例
        self._semantic_embedding: Optional[np.ndarray] = None
        self._need_scores: Dict[str, float] = {}

    def encode_observation(self, observation: Dict[str, Any]) -> np.ndarray:
        """
        将 LAAP-EB 的传感器观测编码为 JEPA 语义嵌入。

        LAAP-EB 的观测包含：
          - camera: 图像帧
          - lidar: 点云
          - joint: 关节角度
          - task: 当前任务描述

        JEPA 编码策略：
          - 将任务描述编码为主要语义信号
          - 将关节状态编码为行为上下文
          - 图像/点云在 LAAP-EB 的高斯泼溅模块中处理
        """
        # 任务描述是最强的语义信号
        task_text = observation.get("task", "")
        joint_state = observation.get("joint", {})
        joint_str = json.dumps(joint_state, sort_keys=True)[:200] if joint_state else ""

        combined = f"{task_text} || joints:{joint_str}"

        # 使用 Aris 的语义嵌入引擎
        from semantic_embedder import get_embedder
        embedder = get_embedder()
        return embedder.encode(combined)[0]

    def predict_next_state(self, current_embedding: np.ndarray,
                           action: str) -> np.ndarray:
        """
        预测执行 action 后的下一个状态嵌入。

        这是 JEPA 世界模型的核心能力：
          "如果我现在做 X，世界会变成什么样子？"
        """
        from semantic_embedder import get_embedder
        embedder = get_embedder()

        # 简单实现：当前嵌入 + action 嵌入的平均
        action_emb = embedder.encode(action)[0]
        # 混合当前状态和动作意图
        pred = (current_embedding * 0.6 + action_emb * 0.4)
        norm = np.linalg.norm(pred) + 1e-8
        return pred / norm

    def compute_need_scores(self, embedding: np.ndarray) -> Dict[str, float]:
        """
        从嵌入中推导机器人的"需求"状态。
        对于 LAAP-EB，这些需求直接驱动目标自生成。
        """
        from semantic_embedder import embedding_to_need_scores
        return embedding_to_need_scores(embedding)

    def compute_prediction_error(
        self, predicted: np.ndarray, actual: np.ndarray
    ) -> float:
        """
        计算预测误差。
        这个误差驱动 LAAP-EB 的 RSI 引擎进行自我改进。
        """
        from semantic_embedder import cosine_sim
        return 1.0 - cosine_sim(predicted, actual)


# ════════════════════════════════════════════════════════════
# LAAP-EB PSI 需求集成
# ════════════════════════════════════════════════════════════

class LAP_EB_PSI_Injector:
    """
    将 JEPA 语义需求得分注入 LAAP-EB 的 PSI 需求系统。

    LAAP-EB 使用 PSI 需求驱动目标自生成：
      - 当 autonomy 得分低 → 机器人自发选择探索行为
      - 当 competence 得分低 → 机器人自发选择学习行为
      - 当 relatedness 得分低 → 机器人自发寻求人机交互

    JEPA 增强：
      - 需求得分从语义预测得出，而非规则
      - 需求变化驱动行为选择的转变
    """

    def __init__(self, laap_eb_brain=None):
        self.laap_eb_brain = laap_eb_brain  # LAAP-EB 大脑实例

    def inject_need_scores(self, need_scores: Dict[str, float]):
        """
        将 JEPA 推导的需求得分注入 LAAP-EB 的 PSI 驱动。
        """
        if self.laap_eb_brain is None:
            logger.debug("No LAAP-EB brain connected, skipping injection")
            return

        try:
            psi = self.laap_eb_brain.psi
            for name, score in need_scores.items():
                if name in psi.needs:
                    psi.needs[name].value = float(score)
            logger.debug(f"Injected need scores into LAAP-EB: {need_scores}")
        except Exception as e:
            logger.warning(f"Failed to inject need scores: {e}")

    def generate_goal(self, need_scores: Dict[str, float]) -> str:
        """
        根据需求得分生成自主目标。
        这是 LAAP-EB 的核心能力：机器人自发产生行为目标。
        """
        if not need_scores:
            return "idle"

        dominant = max(need_scores, key=need_scores.get)
        score = need_scores[dominant]

        goal_map = {
            "autonomy": f"自主探索：寻找新的行动方案 (need={score:.3f})",
            "competence": f"技能提升：练习当前任务以改善执行 (need={score:.3f})",
            "relatedness": f"人机交互：主动与操作者沟通 (need={score:.3f})",
            "certainty": f"环境确认：验证当前理解是否正确 (need={score:.3f})",
            "growth": f"认知扩展：学习新的概念或技能 (need={score:.3f})",
        }

        return goal_map.get(dominant, f"自主行为：{dominant} (need={score:.3f})")


# ════════════════════════════════════════════════════════════
# RSI 集成
# ════════════════════════════════════════════════════════════

class JEPA_RSI_Integrator:
    """
    将 JEPA 预测误差反馈到 LAAP-EB 的 RSI 引擎。

    RSI 工作流：
      1. 观测：机器人执行动作 → 观察结果
      2. 评估：计算预测误差（JEPA 提供）
      3. 改进：如果误差大，触发 RSI 技能合成
      4. 部署：新技能部署到技能缓存
    """

    def __init__(self, laap_eb_rsi=None):
        self.laap_eb_rsi = laap_eb_rsi

    def report_prediction_error(self, error: float, context: str):
        """
        向 RSI 报告预测误差。
        误差超过阈值时触发技能改进。
        """
        if self.laap_eb_rsi is None:
            return

        # 误差阈值：0.4 以上触发 RSI
        if error > 0.4:
            self.laap_eb_rsi.observe(
                event="prediction_error",
                detail=f"error={error:.3f}, context={context}",
                severity=min(error * 0.5, 1.0),
            )


# ════════════════════════════════════════════════════════════
# 完整集成控制器
# ════════════════════════════════════════════════════════════

class JEPA_LAAP_EB_Controller:
    """
    将 JEPA 引擎完整集成到 LAAP-EB 的控制器。

    集成后的 LAAP-EB 架构：
      传感器 → JEPA 编码器 → 语义嵌入
                                  ↓
      [占据栅格] [高斯泼溅] [JEPA 世界模型]
                                  ↓
      JEPA 需求预测 → PSI 需求系统 → 目标自生成
                                  ↓
      VLA/运动策略执行 → 物理结果
                                  ↓
      JEPA 预测误差 → RSI 自我改进

    这完成了从"被动执行"到"主动认知"的升级。
    """

    def __init__(self, laap_eb_instance=None):
        self.laap_eb = laap_eb_instance
        self.world_model = JEPAWorldModelAdapter(laap_eb_world=laap_eb_instance)
        self.psi_injector = LAP_EB_PSI_Injector(laap_eb_brain=laap_eb_instance)
        self.rsi_integrator = JEPA_RSI_Integrator(laap_eb_rsi=laap_eb_instance)

    def process_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理一次完整的感知-预测-需求-目标流程。
        """
        # 1. 编码观测
        embedding = self.world_model.encode_observation(observation)

        # 2. 预测需求
        need_scores = self.world_model.compute_need_scores(embedding)

        # 3. 注入需求到 PSI
        self.psi_injector.inject_need_scores(need_scores)

        # 4. 生成自主目标
        goal = self.psi_injector.generate_goal(need_scores)

        return {
            "embedding": embedding,
            "need_scores": need_scores,
            "goal": goal,
        }

    def process_action_result(
        self, predicted: np.ndarray, actual: np.ndarray, context: str
    ):
        """
        处理动作执行结果，计算预测误差，反馈给 RSI。
        """
        error = self.world_model.compute_prediction_error(predicted, actual)
        self.rsi_integrator.report_prediction_error(error, context)
        return error


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

def create_lap_eb_controller(laap_eb_instance=None) -> JEPA_LAAP_EB_Controller:
    """创建 JEPA-LAAP-EB 集成控制器"""
    return JEPA_LAAP_EB_Controller(laap_eb_instance=laap_eb_instance)

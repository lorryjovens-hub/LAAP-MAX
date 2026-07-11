"""编排器 v2 - 集成世界模型、因果模型和 RSI 的中央调度器

这是面向 AGI 的 Harness 核心：
- 感知层: 视觉 + 视频 + 爬虫
- 世界模型: 设计物理 + 用户行为预测 + 反事实模拟
- 因果模型: 因果图 + do-calculus + 因果发现
- RSI: 元 Harness + 自我改进循环 + 对齐守卫
"""

import asyncio
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.api.models import (
    AnimationSpec,
    DesignToken,
    ReplicationRequest,
    ReplicationResult,
    TaskProgress,
    TaskStatus,
    VisualComponent,
)
from src.config import get_settings
from src.consciousness.causal_model.inference.causal_inference_engine import CausalInferenceEngine
from src.consciousness.decision.aesthetic_evaluator import AestheticEvaluator
from src.consciousness.execution.code_generator import CodeGenerator
from src.consciousness.memory.design_system import DesignSystemMemory
from src.consciousness.perception.layout_analyzer import LayoutAnalyzer
from src.consciousness.perception.video_engine import VideoPerceptionEngine
from src.consciousness.perception.vision_engine import VisionPerceptionEngine
from src.consciousness.reasoning.planner import ReplicationPlanner
from src.consciousness.rsi.self_improvement_loop import SelfImprovementLoop
from src.consciousness.world_model.world_model_engine import WorldModelEngine
from src.feedback.revision_loop import AutoRevisionLoop
from src.sandbox.executor import SandboxExecutor
from src.utils.logger import get_logger
from src.verification.visual_regression import VisualRegressionTester

logger = get_logger(__name__)


class ReplicationOrchestrator:
    """
    Harness 的执行编排器 v2 —— 面向 AGI 的意识大脑中央调度

    流水线阶段：
    1. PERCEIVING: 视觉感知（图片+视频）
    2. WORLD_MODELING: 世界模型理解（物理状态+行为预测）
    3. CAUSAL_REASONING: 因果推理（干预效果+反事实）
    4. REASONING: 架构规划（任务分解+依赖图）
    5. GENERATING: 代码生成（模板+LLM填充）
    6. VERIFYING: 视觉回归（截图对比）
    7. REVISING: 自修正（不达标则循环）
    8. SELF_IMPROVING: 递归自我改进（RSI）
    9. COMPLETED: 输出交付

    支持 LAAP 集成模式：可注入 LAAP 的成熟组件替代内置实现
    """

    def __init__(
        self,
        llm_client=None,
        world_model=None,
        causal_engine=None,
        design_memory=None,
        rsi_loop=None,
        crawler_organ=None,
        sensor_fusion=None,
        perceptual_memory=None,
        active_scheduler=None,
    ):
        self.settings = get_settings()

        # === LAAP 集成模式 ===
        self._laap_integration = any([llm_client, world_model, causal_engine, design_memory, rsi_loop])
        
        if self._laap_integration:
            logger.info("[Orchestrator] LAAP 集成模式已启用")

        # 记忆层（优先使用 LAAP）
        self.memory = design_memory if design_memory else DesignSystemMemory()

        # 感知层（保持内置实现）
        self.vision = VisionPerceptionEngine()
        self.video = VideoPerceptionEngine()
        self.layout = LayoutAnalyzer()

        # 推理与决策层
        self.planner = ReplicationPlanner()
        self.evaluator = AestheticEvaluator()
        self.generator = None
        self.verifier = VisualRegressionTester()
        self.revision = AutoRevisionLoop()
        self.sandbox = SandboxExecutor()

        # === AGI 新增模块（优先使用 LAAP）===
        self.world_model = world_model if world_model else WorldModelEngine()
        self.causal_engine = causal_engine if causal_engine else CausalInferenceEngine()
        self.rsi = rsi_loop if rsi_loop else SelfImprovementLoop()

        # LAAP LLM 客户端
        self.llm_client = llm_client

        self._tasks: Dict[str, Dict] = {}
        self._task_results: List[Dict] = []  # 用于 RSI 能力评估

        # === 感知器官扩展（Task 6）===
        # 感知状态属性（总是初始化，避免后续引用失败）
        self._perception_signals: List = []
        self._active_perception_snapshot = None
        self._fused_tech_stack: List = []
        self._fused_perception_confidence: float = 0.0

        try:
            from src.consciousness.perception.crawler_organ import CrawlerOrgan
            from src.consciousness.perception.sensor_fusion import SensorFusion
            from src.consciousness.perception.perceptual_memory import PerceptualMemory
            from src.consciousness.perception.active_scheduler import ActivePerceptionScheduler

            self.crawler_organ = crawler_organ if crawler_organ else CrawlerOrgan()
            self.sensor_fusion = sensor_fusion if sensor_fusion else SensorFusion()

            # 感知记忆复用 LAAP design_memory 后端
            self.perceptual_memory = perceptual_memory if perceptual_memory else PerceptualMemory(
                design_memory=self.memory if self._laap_integration else None
            )

            # 主动调度器依赖 crawler 和 memory
            self.active_scheduler = active_scheduler if active_scheduler else ActivePerceptionScheduler(
                crawler_organ=self.crawler_organ,
                perceptual_memory=self.perceptual_memory,
            )

            logger.info("[Orchestrator] 感知器官系统已加载（CrawlerOrgan + SensorFusion + PerceptualMemory + ActivePerceptionScheduler）")
        except Exception as e:
            logger.warning(f"[Orchestrator] 感知器官系统加载失败，降级运行: {e}")
            self.crawler_organ = crawler_organ
            self.sensor_fusion = sensor_fusion
            self.perceptual_memory = perceptual_memory
            self.active_scheduler = active_scheduler

    async def run_replication_pipeline(
        self,
        task_id: str,
        image_path: str,
        video_path: Optional[str],
        config: ReplicationRequest,
    ):
        """执行完整复现流水线（AGI 版）"""
        logger.info(f"[Orchestrator v2] 启动 AGI 流水线: {task_id}")

        # === Stage 0: 主动感知前置 ===
        self._update_task(task_id, TaskStatus.PRE_PERCEPTION, 2, "主动感知调度...")

        # 从 config 中提取目标 URL（如果有）
        target_url = config.custom_instructions or ""
        reference_snapshots: List[Dict[str, Any]] = []

        if target_url and self._is_url(target_url):
            # 简单 URL 提取（实际可使用更复杂的 NLP）
            urls_in_instructions = self._extract_urls(target_url)

            if urls_in_instructions:
                goal = {
                    "targets": urls_in_instructions,
                    "task_type": config.framework.value if hasattr(config, "framework") else "web_replica",
                    "requires_realtime": False,
                }

                try:
                    perception_results = await self.active_scheduler.run_active_perception(goal, top_n=3)
                    reference_snapshots = [r for r in perception_results if r.get("snapshot") is not None]

                    if reference_snapshots:
                        logger.info(f"[Orchestrator] Stage 0: 获取 {len(reference_snapshots)} 个参考快照")
                        # 对比分析，提取共同模式
                        if len(reference_snapshots) >= 2:
                            comparison = self.active_scheduler.compare_perceptions(reference_snapshots)
                            logger.info(f"[Orchestrator] Stage 0: 共同技术栈 {[t for t in comparison.get('common_tech_stack', [])]}")
                except Exception as e:
                    logger.warning(f"[Orchestrator] Stage 0 主动感知失败（不阻塞）: {e}")

        # 将参考快照存入任务上下文，供后续阶段使用
        self._tasks[task_id]["reference_snapshots"] = reference_snapshots

        try:
            # === Stage 1: 多器官融合感知 ===
            self._update_task(task_id, TaskStatus.PERCEIVING, 5, "视觉感知中...")

            # 1. 视觉感知
            perception = await self.vision.perceive(Path(image_path))
            design_tokens = perception["design_tokens"]
            component_tree = perception["component_tree"]

            animations = []
            if video_path:
                self._update_task(task_id, TaskStatus.PERCEIVING, 10, "解析动画与交互...")
                animations = await self.video.perceive(Path(video_path))

            layout_grid = self.layout.analyze(component_tree)
            conflicts = self.layout.detect_visual_conflicts(component_tree)
            if conflicts:
                logger.warning(f"[Orchestrator] 检测到 {len(conflicts)} 个视觉冲突")

            # 2. 爬虫感知（如果任务上下文中有参考 URL）
            from src.api.models import PerceptionSignal, PerceptionModality
            perception_signals = [
                PerceptionSignal(
                    modality=PerceptionModality.VISION,
                    payload={
                        "design_tokens": [t.model_dump() for t in design_tokens],
                        "component_tree": component_tree.model_dump() if hasattr(component_tree, "model_dump") else component_tree,
                    },
                    confidence=0.85,
                    source="vision_engine",
                )
            ]

            # 添加 Stage 0 的爬虫信号
            for ref in reference_snapshots:
                snapshot = ref.get("snapshot")
                if snapshot:
                    perception_signals.append(
                        PerceptionSignal(
                            modality=PerceptionModality.CRAWLER,
                            payload=snapshot.model_dump() if hasattr(snapshot, "model_dump") else snapshot,
                            confidence=0.95,
                            source="crawler_organ",
                        )
                    )

            # 3. 融合
            self._update_task(task_id, TaskStatus.PERCEIVING, 15, "多器官融合感知...")
            try:
                unified_perception = await self.sensor_fusion.fuse(perception_signals)
                # 用融合后的设计令牌覆盖（爬虫优先）
                if unified_perception.get("design_tokens"):
                    # 仅当融合结果包含爬虫令牌时才使用，避免覆盖视觉
                    crawler_tokens = [
                        DesignToken(**t) for t in unified_perception["design_tokens"]
                        if isinstance(t, dict)
                    ]
                    if crawler_tokens:
                        design_tokens = crawler_tokens  # 融合后的令牌
                        logger.info(f"[Orchestrator] 融合后设计令牌: {len(design_tokens)} 个")

                # 记录冲突
                if unified_perception.get("conflicts"):
                    logger.info(f"[Orchestrator] 感知冲突: {len(unified_perception['conflicts'])} 个")
            except Exception as e:
                logger.warning(f"[Orchestrator] 感知融合失败（不阻塞）: {e}")

            await self.memory.store_tokens(task_id, design_tokens, "web-replica")

            # 4. 缓存感知结果
            for ref in reference_snapshots:
                snapshot = ref.get("snapshot")
                if snapshot and ref.get("url"):
                    try:
                        await self.perceptual_memory.store_perception(ref["url"], snapshot)
                    except Exception as e:
                        logger.warning(f"[Orchestrator] 感知缓存失败: {e}")

            # === Stage 2: 世界模型（新增）===
            self._update_task(task_id, TaskStatus.PERCEIVING, 25, "构建世界模型...")
            world_state = await self.world_model.understand(component_tree, design_tokens)

            # 如果世界模型检测到高风险，提前警告
            if world_state["risk_flags"]:
                for risk in world_state["risk_flags"]:
                    logger.warning(f"[WorldModel] 风险: [{risk['level']}] {risk['message']}")

            # 基于世界模型的优化建议（可选）
            if config.custom_instructions and "optimize" in config.custom_instructions.lower():
                optimization = await self.world_model.optimize(
                    component_tree, design_tokens, goal="conversion"
                )
                logger.info(f"[WorldModel] 优化建议: {optimization.get('recommended_intervention')}")

            # === Stage 3: 因果推理（新增）===
            self._update_task(task_id, TaskStatus.REASONING, 30, "因果推理...")

            # 示例：分析按钮颜色对转化率的影响
            causal_query = await self.causal_engine.query_intervention(
                target="conversion_rate",
                intervention={"button_color": "high_contrast"},
            )
            logger.info(f"[CausalEngine] 因果分析: {causal_query['estimated_effect']:.3f} 效应")

            # === Stage 4: 推理层 ===
            self._update_task(task_id, TaskStatus.REASONING, 35, "规划架构与任务分解...")
            plan = await self.planner.plan(
                component_tree, layout_grid, animations, config
            )

            # 将因果推理结果融入架构决策
            plan["causal_insights"] = causal_query.get("causal_paths", [])

            # === Stage 5: 生成层 ===
            self._update_task(task_id, TaskStatus.GENERATING, 45, "生成代码...")
            self.generator = CodeGenerator()

            code_package = await self.generator.generate(
                plan, component_tree, design_tokens, layout_grid, animations, config
            )

            # === Stage 6: 验证层 ===
            self._update_task(task_id, TaskStatus.VERIFYING, 65, "视觉回归测试...")

            build_result = await self.sandbox.build_and_screenshot(task_id, code_package)
            screenshot_path = build_result["screenshot"]

            similarity = await self.verifier.compare(
                original=image_path,
                generated=screenshot_path,
            )

            aesthetic_report = await self.evaluator.evaluate(
                component_tree, design_tokens
            )

            # === Stage 7: 修正循环 ===
            revision_count = 0
            while (
                similarity < self.settings.visual_similarity_threshold
                or not aesthetic_report["passed"]
            ) and revision_count < self.settings.max_revision_rounds:

                self._update_task(
                    task_id, TaskStatus.REVISING,
                    80 + revision_count * 2,
                    f"自修正第 {revision_count + 1} 轮..."
                )

                code_package = await self.revision.revise(
                    task_id=task_id,
                    code_package=code_package,
                    visual_feedback=await self.verifier.get_feedback(
                        image_path, screenshot_path
                    ),
                    aesthetic_feedback=aesthetic_report,
                    config=config,
                )

                build_result = await self.sandbox.build_and_screenshot(task_id, code_package)
                similarity = await self.verifier.compare(
                    image_path, build_result["screenshot"]
                )
                aesthetic_report = await self.evaluator.evaluate(
                    component_tree, design_tokens
                )
                revision_count += 1

            # === Stage 8: 递归自我改进（新增）===
            self._update_task(task_id, TaskStatus.VERIFYING, 90, "递归自我改进...")

            # 收集本次任务结果用于 RSI
            task_result = {
                "task_id": task_id,
                "visual_similarity": similarity,
                "aesthetic_score": aesthetic_report["total_score"],
                "perception_accuracy": 0.85,  # 简化
                "planning_efficiency": 0.8,
                "code_generation_success": 1.0 if similarity > 0.8 else 0.5,
                "behavior_prediction_accuracy": world_state.get("overall_health", 0.5),
            }
            self._task_results.append(task_result)

            # 触发 RSI（每 5 个任务触发一次，避免过于频繁）
            if len(self._task_results) >= 5:
                logger.info("[Orchestrator] 触发递归自我改进...")
                rsi_result = await self.rsi.run(self._task_results)

                if rsi_result.get("improved"):
                    logger.info(f"[RSI] 自我改进成功: 版本 {rsi_result['version_id']}, 提升 {rsi_result['capability_delta']:.3f}")
                else:
                    logger.info(f"[RSI] 自我改进跳过: {rsi_result.get('reason')}")

                # 清空任务结果，准备下一轮
                self._task_results = []

            # === Stage 9: 输出 ===
            output_dir = Path(self.settings.output_dir) / task_id
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_path = output_dir / "code.zip"
            self._package_code(code_package, zip_path)

            with open(output_dir / "design-system.json", "w") as f:
                json.dump([t.model_dump() for t in design_tokens], f, indent=2)

            # 保存世界模型分析
            with open(output_dir / "world-model.json", "w") as f:
                json.dump({
                    "health": world_state["overall_health"],
                    "risk_flags": world_state["risk_flags"],
                    "gestalt_scores": world_state["gestalt"],
                }, f, indent=2)

            # 保存因果分析
            with open(output_dir / "causal-analysis.json", "w") as f:
                json.dump(causal_query, f, indent=2, default=str)

            result = ReplicationResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                design_tokens=design_tokens,
                component_tree=component_tree,
                layout_grid=layout_grid,
                animations=animations,
                code_package=str(zip_path),
                preview_url=f"http://localhost:8000/preview/{task_id}",
                visual_similarity_score=similarity,
                revision_count=revision_count,
                completed_at=datetime.utcnow(),
            )

            self._update_task(task_id, TaskStatus.COMPLETED, 100, "复现完成", result)
            logger.info(f"[Orchestrator v2] 任务完成: {task_id}, 相似度: {similarity:.2%}")

        except Exception as e:
            logger.error(f"[Orchestrator v2] 流水线失败: {e}", exc_info=True)
            self._update_task(
                task_id, TaskStatus.FAILED, 0, f"失败: {str(e)}",
                ReplicationResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            )

    def _update_task(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int,
        message: str,
        result: Optional[ReplicationResult] = None,
    ):
        """更新任务状态"""
        self._tasks[task_id] = {
            "task_id": task_id,
            "status": status,
            "progress_percent": progress,
            "current_stage": message,
            "logs": self._tasks.get(task_id, {}).get("logs", []) + [f"[{datetime.utcnow().isoformat()}] {message}"],
            "result": result,
        }

    def _is_url(self, text: str) -> bool:
        """简单判断文本是否包含 URL"""
        return "http://" in text or "https://" in text or ".com" in text or ".org" in text

    def _extract_urls(self, text: str) -> List[str]:
        """从文本中提取 URL（最多 5 个）"""
        import re

        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls[:5]

    async def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度"""
        data = self._tasks.get(task_id)
        if not data:
            return None
        return TaskProgress(**data)

    async def get_result(self, task_id: str) -> Optional[ReplicationResult]:
        """获取任务结果"""
        data = self._tasks.get(task_id)
        if not data or not data.get("result"):
            return None
        return data["result"]

    async def trigger_revision(self, task_id: str, feedback: str):
        """触发人工修正"""
        pass

    def _package_code(self, code_package: Dict[str, str], zip_path: Path):
        """将代码打包为 zip"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as f:
            for filename, content in code_package.items():
                f.writestr(filename, content)

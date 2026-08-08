"""编排器 - 复现流水线的中央调度器"""

import asyncio
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

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
from src.consciousness.decision.aesthetic_evaluator import AestheticEvaluator
from src.consciousness.memory.design_system import DesignSystemMemory
from src.consciousness.perception.layout_analyzer import LayoutAnalyzer
from src.consciousness.perception.video_engine import VideoPerceptionEngine
from src.consciousness.perception.vision_engine import VisionPerceptionEngine
from src.consciousness.reasoning.planner import ReplicationPlanner
from src.feedback.revision_loop import AutoRevisionLoop
from src.sandbox.executor import SandboxExecutor
from src.utils.logger import get_logger
from src.verification.visual_regression import VisualRegressionTester

logger = get_logger(__name__)


class ReplicationOrchestrator:
    """
    Harness 的执行编排器 —— 意识大脑的中央调度

    流水线阶段：
    1. PERCEIVING: 视觉感知（图片+视频）
    2. REASONING: 架构规划（任务分解+依赖图）
    3. GENERATING: 代码生成（模板+LLM填充）
    4. VERIFYING: 视觉回归（截图对比）
    5. REVISING: 自修正（不达标则循环）
    6. COMPLETED: 输出交付
    """

    def __init__(self):
        self.settings = get_settings()
        self.memory = DesignSystemMemory()
        self.vision = VisionPerceptionEngine()
        self.video = VideoPerceptionEngine()
        self.layout = LayoutAnalyzer()
        self.planner = ReplicationPlanner()
        self.evaluator = AestheticEvaluator()
        self.generator = None
        self.verifier = VisualRegressionTester()
        self.revision = AutoRevisionLoop()
        self.sandbox = SandboxExecutor()

        self._tasks: Dict[str, Dict] = {}

    async def run_replication_pipeline(
        self,
        task_id: str,
        image_path: str,
        video_path: Optional[str],
        config: ReplicationRequest,
    ):
        """执行完整复现流水线"""
        logger.info(f"[Orchestrator] 启动流水线: {task_id}")

        self._update_task(task_id, TaskStatus.PERCEIVING, 10, "解析视觉输入...")

        try:
            # === Stage 1: 感知层 ===
            perception = await self.vision.perceive(Path(image_path))
            design_tokens = perception["design_tokens"]
            component_tree = perception["component_tree"]

            animations = []
            if video_path:
                self._update_task(task_id, TaskStatus.PERCEIVING, 20, "解析动画与交互...")
                animations = await self.video.perceive(Path(video_path))

            layout_grid = self.layout.analyze(component_tree)

            conflicts = self.layout.detect_visual_conflicts(component_tree)
            if conflicts:
                logger.warning(f"[Orchestrator] 检测到 {len(conflicts)} 个视觉冲突")

            await self.memory.store_tokens(task_id, design_tokens, "web-replica")

            # === Stage 2: 推理层 ===
            self._update_task(task_id, TaskStatus.REASONING, 35, "规划架构与任务分解...")
            plan = await self.planner.plan(
                component_tree, layout_grid, animations, config
            )

            # === Stage 3: 生成层 ===
            self._update_task(task_id, TaskStatus.GENERATING, 50, "生成代码...")
            from src.consciousness.execution.code_generator import CodeGenerator
            self.generator = CodeGenerator()

            code_package = await self.generator.generate(
                plan, component_tree, design_tokens, layout_grid, animations, config
            )

            # === Stage 4: 验证层 ===
            self._update_task(task_id, TaskStatus.VERIFYING, 75, "视觉回归测试...")

            build_result = await self.sandbox.build_and_screenshot(task_id, code_package)
            screenshot_path = build_result["screenshot"]

            similarity = await self.verifier.compare(
                original=image_path,
                generated=screenshot_path,
            )

            aesthetic_report = await self.evaluator.evaluate(
                component_tree, design_tokens
            )

            # === Stage 5: 修正循环 ===
            revision_count = 0
            while (
                similarity < self.settings.visual_similarity_threshold
                or not aesthetic_report["passed"]
            ) and revision_count < self.settings.max_revision_rounds:

                self._update_task(
                    task_id, TaskStatus.REVISING, 
                    80 + revision_count * 3,
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

            # === Stage 6: 输出 ===
            output_dir = Path(self.settings.output_dir) / task_id
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_path = output_dir / "code.zip"
            self._package_code(code_package, zip_path)

            with open(output_dir / "design-system.json", "w") as f:
                json.dump([t.model_dump() for t in design_tokens], f, indent=2)

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
            logger.info(f"[Orchestrator] 任务完成: {task_id}, 相似度: {similarity:.2%}")

        except Exception as e:
            logger.error(f"[Orchestrator] 流水线失败: {e}", exc_info=True)
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
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in code_package.items():
                zf.writestr(filename, content)

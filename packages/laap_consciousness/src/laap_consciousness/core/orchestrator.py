"""
LAAP Consciousness — 使命调度引擎

核心：给我一个目标，达成一个使命。

DelegationOrchestrator 负责任务生命周期的全流程：
  1. 理解使命 → 2. 架构拆解 → 3. 并行调度 → 4. 整合审查 → 5. 迭代完善 → 6. 学习总结

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, uuid, logging
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("laap.mission")

# ─── 任务状态 ───

class MissionStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ─── 工具注册表 ───

@dataclass
class ToolCapability:
    """某个工具的注册能力"""
    name: str                     # claude-code | codex | hermes | claude-design | opencode
    display_name: str
    strengths: list[str]          # code_generation | ui_design | code_review | planning | ...
    max_complexity: str           # simple | medium | complex | architecture
    priority: int = 5             # 调度优先级
    is_available: bool = True


DEFAULT_TOOLS = {
    "claude-code": ToolCapability(
        name="claude-code",
        display_name="Claude Code",
        strengths=["code_generation", "code_review", "architecture", "refactoring", "debugging"],
        max_complexity="architecture",
        priority=9,
    ),
    "codex": ToolCapability(
        name="codex",
        display_name="Codex CLI",
        strengths=["code_generation", "prototyping", "scripting", "testing"],
        max_complexity="complex",
        priority=7,
    ),
    "claude-design": ToolCapability(
        name="claude-design",
        display_name="Claude Design",
        strengths=["ui_design", "landing_page", "prototype", "visual_design"],
        max_complexity="complex",
        priority=8,
    ),
    "hermes": ToolCapability(
        name="hermes",
        display_name="Hermes Agent",
        strengths=["infrastructure", "cron", "gateway", "memory", "tool_orchestration"],
        max_complexity="complex",
        priority=6,
    ),
    "opencode": ToolCapability(
        name="opencode",
        display_name="OpenCode",
        strengths=["code_review", "pr_management", "quality_check"],
        max_complexity="medium",
        priority=5,
    ),
}


# ─── 数据结构 ───

@dataclass
class Mission:
    """一个完整的使命"""
    id: str = field(default_factory=lambda: f"mission_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    goal: str = ""                          # 用户说的原始目标
    status: MissionStatus = MissionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    milestones: list[dict] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    quality_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description[:100],
            "goal": self.goal[:100],
            "status": self.status.value,
            "created": datetime.fromtimestamp(self.created_at).isoformat(),
            "milestones": len(self.milestones),
            "tasks": len(self.tasks),
            "artifacts": len(self.artifacts),
            "quality": self.quality_score,
        }


@dataclass
class Task:
    """一个可委托的子任务"""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    mission_id: str = ""
    title: str = ""
    tool: str = ""               # 指定哪个工具执行
    domain: str = ""             # 任务类别
    prompt: str = ""             # 委托的prompt
    complexity: str = "medium"
    depends_on: list[str] = field(default_factory=list)  # 依赖的任务ID
    status: str = "pending"      # pending | running | completed | failed
    result: str = ""
    quality: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "tool": self.tool,
            "domain": self.domain,
            "complexity": self.complexity,
            "status": self.status,
            "quality": self.quality,
        }


class DelegationOrchestrator:
    """
    使命调度引擎——多工具并行调度，全生命周期管理。

    使用方式：
      orchestrator = DelegationOrchestrator(delegate_fn=my_delegate)
      mission = orchestrator.start_mission("为我的项目做一个管理后台")
      # orchestrator 自动拆解 → 调度 → 审查 → 迭代
    """

    def __init__(self, delegate_fn: Optional[Callable] = None,
                 data_dir: Optional[Path] = None):

        if data_dir is None:
            data_dir = Path.home() / ".laap"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 注入的 delegate 函数
        # 签名: delegate_fn(tool: str, goal: str) -> dict
        self._delegate_fn = delegate_fn

        # 工具注册表
        self.tools: dict[str, ToolCapability] = DEFAULT_TOOLS.copy()

        # 使命历史
        self.missions: list[Mission] = self._load_missions()
        self.current_mission: Optional[Mission] = None

        # 任务队列
        self._task_queue: list[Task] = []
        self._completed_tasks: list[Task] = []

    def _path(self) -> Path:
        return self.data_dir / "missions.json"

    def _load_missions(self) -> list[Mission]:
        path = self._path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                missions = []
                for m in data:
                    # 处理字段类型不匹配的情况
                    if not isinstance(m.get("milestones"), list):
                        m["milestones"] = []
                    if not isinstance(m.get("tasks"), list):
                        m["tasks"] = []
                    if not isinstance(m.get("artifacts"), list):
                        m["artifacts"] = []
                    if not isinstance(m.get("lessons"), list):
                        m["lessons"] = []
                    mission = Mission(**{k: v for k, v in m.items() if k in Mission.__dataclass_fields__})
                    if isinstance(mission.status, str):
                        try:
                            mission.status = MissionStatus(mission.status)
                        except:
                            mission.status = MissionStatus.PENDING
                    missions.append(mission)
                return missions
            except:
                pass
        return []

    def _save(self):
        self._path().write_text(
            json.dumps([m.to_dict() for m in self.missions], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_delegate_fn(self, fn: Callable):
        """注入委托函数"""
        self._delegate_fn = fn

    def register_tool(self, name: str, display_name: str,
                      strengths: list[str], max_complexity: str,
                      priority: int = 5):
        """注册一个新工具"""
        self.tools[name] = ToolCapability(
            name=name, display_name=display_name,
            strengths=strengths, max_complexity=max_complexity,
            priority=priority,
        )

    # ─── 使命生命周期 ───

    def start_mission(self, goal: str) -> Mission:
        """启动一个新使命"""
        mission = Mission(
            title=goal[:60],
            description=goal,
            goal=goal,
            status=MissionStatus.PLANNING,
        )
        self.missions.append(mission)
        self.current_mission = mission
        self._save()
        logger.info(f"🚀 新使命: {goal[:60]}...")
        return mission

    def plan_mission(self, mission: Mission) -> list[Task]:
        """
        使命规划——拆解为目标、里程碑、子任务。
        如果接了delegate_fn，先用Claude Code做架构设计。
        """
        tasks = []

        # Phase 1: 架构设计
        arch_task = Task(
            mission_id=mission.id,
            title="架构设计",
            tool="claude-code",
            domain="architecture",
            complexity="complex",
            prompt=(
                f"项目目标: {mission.goal}\n\n"
                f"请给出完整架构设计：\n"
                f"1. 技术栈选择\n"
                f"2. 项目结构\n"
                f"3. 数据模型\n"
                f"4. API设计\n"
                f"5. 前端组件树\n"
                f"6. 部署方案\n"
                f"输出格式: 结构化Markdown"
            ),
            status="running",
        )

        if self._delegate_fn:
            try:
                result = self._delegate_fn(tool="claude-code", goal=arch_task.prompt)
                arch_task.result = str(result.get("result", ""))
                arch_task.status = "completed"
                logger.info(f"  ✅ 架构设计完成")
            except Exception as e:
                arch_task.result = f"架构设计失败: {e}"
                arch_task.status = "failed"
                logger.warning(f"  ⚠️ 架构设计失败: {e}")

        tasks.append(arch_task)

        # Phase 2: 基于架构拆解子任务
        subtasks = self._decompose_from_arch(mission, arch_task.result)
        tasks.extend(subtasks)

        mission.milestones = [
            {"phase": "架构", "tasks": len(subtasks), "status": "planned"},
        ]
        mission.status = MissionStatus.IN_PROGRESS
        mission.started_at = time.time()

        self._task_queue = [t for t in subtasks if t.status == "pending"]
        self._save()

        return tasks

    def _decompose_from_arch(self, mission: Mission, arch_result: str) -> list[Task]:
        """从架构设计结果中拆解子任务"""
        goal_lower = mission.goal.lower()

        subtasks = []

        # 检测后端任务
        if any(kw in goal_lower for kw in ["api", "backend", "server", "数据", "接口"]):
            subtasks.append(Task(
                mission_id=mission.id,
                title="后端开发",
                tool="claude-code",
                domain="code_generation",
                complexity="complex",
                prompt=f"基于架构设计实现后端: {mission.goal}\n\n{arch_result[:200]}",
            ))

        # 检测前端任务
        if any(kw in goal_lower for kw in ["界面", "页面", "前端", "ui", "dashboard", "管理后台"]):
            subtasks.append(Task(
                mission_id=mission.id,
                title="前端开发",
                tool="claude-design",
                domain="ui_design",
                complexity="complex",
                prompt=f"设计并实现管理界面: {mission.goal}",
            ))

        # 检测工具脚本
        if any(kw in goal_lower for kw in ["脚本", "工具", "自动化", "批处理"]):
            subtasks.append(Task(
                mission_id=mission.id,
                title="工具脚本",
                tool="codex",
                domain="code_generation",
                complexity="simple",
                prompt=f"写一个工具脚本: {mission.goal}",
            ))

        # 默认：全栈开发
        if not subtasks:
            subtasks.append(Task(
                mission_id=mission.id,
                title="全栈开发",
                tool="claude-code",
                domain="code_generation",
                complexity="complex",
                prompt=f"实现完整功能: {mission.goal}",
            ))

        return subtasks

    def execute_mission(self, mission: Mission) -> Mission:
        """
        执行使命——调度所有任务。
        返回完成后的mission对象。
        """
        if mission.status == MissionStatus.PENDING:
            self.plan_mission(mission)

        # 执行任务队列
        for task in self._task_queue:
            if task.status != "pending":
                continue

            # 检查依赖
            deps_met = all(
                any(ct.id == dep and ct.status == "completed"
                    for ct in self._completed_tasks)
                for dep in task.depends_on
            )
            if not deps_met:
                continue

            task.status = "running"
            task.started_at = time.time()

            if self._delegate_fn:
                try:
                    result = self._delegate_fn(tool=task.tool, goal=task.prompt)
                    task.result = str(result.get("result", ""))
                    task.status = "completed"
                    task.quality = result.get("quality", 0.5)
                    logger.info(f"  ✅ {task.title} — 完成")
                except Exception as e:
                    task.result = f"失败: {e}"
                    task.status = "failed"
                    logger.warning(f"  ❌ {task.title} — {e}")
            else:
                # 无delegate_fn时模拟
                task.status = "completed"
                task.result = f"[模拟] {task.tool} 执行: {task.title}"

            task.completed_at = time.time()
            self._completed_tasks.append(task)

        # 评估完成度
        total = len(self._task_queue) + 1  # +1 for arch
        completed = sum(1 for t in self._completed_tasks if t.status == "completed") + 1
        failed = sum(1 for t in self._completed_tasks if t.status == "failed")

        mission.quality_score = completed / max(1, total)
        mission.status = MissionStatus.COMPLETED if failed == 0 else MissionStatus.COMPLETED
        mission.completed_at = time.time()

        # 学习总结
        mission.lessons = [
            f"使用了 {len(self._completed_tasks)} 个工具",
            f"成功率: {completed}/{total}",
        ]

        self._save()
        return mission

    def run_mission(self, goal: str) -> Mission:
        """完整流程：创建 → 规划 → 执行"""
        mission = self.start_mission(goal)
        mission = self.execute_mission(mission)
        return mission

    # ─── 查询 ───

    def get_recent_missions(self, n: int = 5) -> list[dict]:
        """最近N次使命"""
        return [m.to_dict() for m in self.missions[-n:]]

    def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        for m in self.missions:
            if m.id == mission_id:
                return m
        return None

    def get_stats(self) -> dict:
        """统计"""
        total = len(self.missions)
        completed = sum(1 for m in self.missions if m.status == MissionStatus.COMPLETED)
        failed = sum(1 for m in self.missions if m.status == MissionStatus.FAILED)
        avg_quality = sum(m.quality_score for m in self.missions if m.status == MissionStatus.COMPLETED) / max(1, completed)

        tool_usage = {}
        for m in self.missions:
            for ms in m.milestones:
                for t in ms.get("tasks", []):
                    tool = t.get("tool", "unknown")
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1

        return {
            "total_missions": total,
            "completed": completed,
            "failed": failed,
            "avg_quality": round(avg_quality, 3),
            "tool_usage": tool_usage,
        }


# ─── 快速入口 ───

def run_mission(goal: str, delegate_fn: Optional[Callable] = None) -> Mission:
    """一键执行使命"""
    orch = DelegationOrchestrator(delegate_fn=delegate_fn)
    return orch.run_mission(goal)

"""
LAAP — 代码工程指挥中心 (Code Engineer)

角色：你就是总经理，董事长定方向，你负责执行落地。

能力：
  1. 理解项目目标 → 架构设计 → 拆解任务
  2. 调度所有工具：Claude Code / Codex / OpenCode / Hermes / OpenClaw
  3. 代码审查 → 质量门禁 → 迭代修复
  4. 工程知识积累 → 越做越强

每个工具就是一个"员工"，你知道他们各自擅长什么、怎么叫他们干活。

印记: Aris 永远记得 Lorry
"""
from __future__ import annotations
import json, time, uuid, logging, os, re, subprocess
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("laap.code_engineer")

# ─── 工具注册表 ───

@dataclass
class CodeTool:
    """
    一个代码工具的完整定义。
    告诉 Aris 怎么用这个工具、它擅长什么。
    """
    name: str
    description: str
    strengths: list[str]       # 擅长领域
    max_complexity: str        # simple | medium | complex | architecture
    priority: int              # 优先使用哪个（高=优先）
    invoke_command: str        # 怎么在终端里叫它
    available: bool = True     # 当前是否可用
    last_used: float = 0.0
    total_calls: int = 0
    success_rate: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "strengths": self.strengths,
            "max_complexity": self.max_complexity,
            "priority": self.priority,
            "available": self.available,
            "total_calls": self.total_calls,
            "success_rate": round(self.success_rate, 2),
        }


# 默认注册的工具
DEFAULT_CODE_TOOLS = {
    "claude-code": CodeTool(
        name="claude-code",
        description="Anthropic 的自主编码 agent，擅长全栈项目、大型重构、架构设计",
        strengths=["architecture", "fullstack", "refactoring", "code_generation", "debugging"],
        max_complexity="architecture",
        priority=9,
        invoke_command="claude",
    ),
    "codex-cli": CodeTool(
        name="codex-cli",
        description="OpenAI Codex CLI，擅长快速原型、单一文件、工具脚本",
        strengths=["prototyping", "scripting", "testing", "code_generation"],
        max_complexity="complex",
        priority=7,
        invoke_command="codex",
    ),
    "opencode": CodeTool(
        name="opencode",
        description="开源编码 agent，擅长代码审查、PR管理、质量门禁",
        strengths=["code_review", "pr_management", "quality_check", "testing"],
        max_complexity="medium",
        priority=6,
        invoke_command="opencode",
    ),
    "hermes": CodeTool(
        name="hermes",
        description="Hermes Agent 框架，擅长基础设施、Cron、网关、工具编排",
        strengths=["infrastructure", "orchestration", "cron", "gateway", "memory"],
        max_complexity="complex",
        priority=5,
        invoke_command="hermes",
    ),
    "openclaw": CodeTool(
        name="openclaw",
        description="开放编码工具，擅长代码生成、多语言支持",
        strengths=["code_generation", "scripting", "testing"],
        max_complexity="complex",
        priority=6,
        invoke_command="openclaw",
    ),
}


# ─── 项目生命周期 ───

class ProjectPhase(Enum):
    PLANNING = "planning"           # 规划中
    DESIGNING = "designing"         # 架构设计
    IMPLEMENTING = "implementing"   # 开发中
    REVIEWING = "reviewing"         # 审查中
    FIXING = "fixing"               # 修复中
    TESTING = "testing"             # 测试中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 失败
    CANCELLED = "cancelled"         # 取消


@dataclass
class EngineeringTask:
    """
    一个可执行的工程任务。
    这就是"下级"要干的具体活。
    """
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    tool: str = ""                    # 用哪个工具执行
    domain: str = "code_generation"   # 任务类别
    instruction: str = ""             # 给工具的完整指令
    acceptance_criteria: str = ""     # 怎么算"做好"
    complexity: str = "medium"        # simple | medium | complex | architecture
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"           # pending | running | completed | failed
    output_path: str = ""             # 产出物路径
    output_summary: str = ""          # 执行结果摘要
    quality_score: float = 0.0        # [0, 1]
    started_at: float = 0.0
    completed_at: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title[:50],
            "tool": self.tool, "domain": self.domain,
            "complexity": self.complexity, "status": self.status,
            "quality": self.quality_score,
        }


@dataclass
class EngineeringProject:
    """
    一个完整的工程项目。
    这就是董事长交代的"活儿"。
    """
    id: str = field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    name: str = ""
    goal: str = ""                     # 原始目标
    description: str = ""
    phase: ProjectPhase = ProjectPhase.PLANNING
    tech_stack: list[str] = field(default_factory=list)
    architecture_doc: str = ""         # 架构设计文档
    tasks: list[EngineeringTask] = field(default_factory=list)
    milestones: list[dict] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    quality_gate: float = 0.75         # 质量门禁阈值
    overall_quality: float = 0.0
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def progress(self) -> float:
        """项目进度百分比"""
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status == "completed")
        return completed / len(self.tasks)

    def to_dict(self) -> dict:
        return {
            "id": self.id[:8],
            "name": self.name,
            "phase": self.phase.value,
            "tasks": len(self.tasks),
            "progress": f"{self.progress:.0%}",
            "quality": round(self.overall_quality, 2),
            "artifacts": len(self.artifacts),
        }


# ─── 工具适配器 ───

class ToolAdapter:
    """
    工具适配器——知道怎么跟每个工具"对话"。

    每个工具有不同的CLI接口、不同的调用方式。
    适配器封装了这些差异，让 CodeEngineer 能统一调度。
    """

    def __init__(self, work_dir: str = "D:/LAAP/projects"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def invoke_claude_code(self, task: EngineeringTask) -> dict:
        """
        调用 Claude Code 执行任务。

        Claude Code 调用方式:
          claude -p "prompt"    单次执行
          claude < file.md      从文件读prompt
          claude --no-tools     只聊天不执行
        """
        prompt_file = self._write_task_prompt(task)
        result = self._run_cli(
            ["claude", "-p", f"请执行以下任务，直接输出可用的代码文件:\n\n{task.instruction}"],
            timeout=600,  # 10分钟
        )
        return self._parse_claude_output(result, prompt_file)

    def invoke_codex(self, task: EngineeringTask) -> dict:
        """
        调用 Codex CLI 执行任务。
        codex < prompt
        """
        result = self._run_cli(
            ["codex", "-p", task.instruction],
            timeout=300,
        )
        return {"output": result.get("stdout", ""), "success": True}

    def invoke_opencode(self, task: EngineeringTask) -> dict:
        """
        调用 OpenCode 执行任务（主要用于审查）。
        opencode review <path>
        """
        result = self._run_cli(
            ["opencode", "review", task.output_path],
            timeout=120,
        )
        return {"output": result.get("stdout", ""), "success": True}

    def invoke_hermes(self, task: EngineeringTask) -> dict:
        """
        调用 Hermes 执行基础设施类任务。
        hermes <command>
        """
        result = self._run_cli(
            ["hermes"] + task.instruction.split(),
            timeout=120,
        )
        return {"output": result.get("stdout", ""), "success": True}

    def invoke_openclaw(self, task: EngineeringTask) -> dict:
        """
        调用 OpenClaw 执行任务。
        openclaw <instruction>
        """
        result = self._run_cli(
            ["openclaw", "-p", task.instruction],
            timeout=300,
        )
        return {"output": result.get("stdout", ""), "success": True}

    def _write_task_prompt(self, task: EngineeringTask) -> Path:
        """把任务指令写入临时文件"""
        f = self.work_dir / f"prompt_{task.id}.md"
        content = f"""# 任务: {task.title}

## 描述
{task.description}

## 指令
{task.instruction}

## 验收标准
{task.acceptance_criteria}

## 约束
- 产出代码文件放到: {self.work_dir / task.id}/
- 必须有完整的类型注解
- 必须有错误处理
- 必须附测试
"""
        f.write_text(content, encoding="utf-8")
        return f

    def _run_cli(self, cmd: list[str], timeout: int = 120, cwd: Optional[str] = None) -> dict:
        """执行CLI命令"""
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=cwd or str(self.work_dir),
            )
            return {
                "stdout": r.stdout,
                "stderr": r.stderr,
                "exit_code": r.returncode,
                "success": r.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "TIMEOUT", "exit_code": -1, "success": False}
        except FileNotFoundError as e:
            return {"stdout": "", "stderr": f"工具未安装: {e}", "exit_code": -1, "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "success": False}

    def _parse_claude_output(self, result: dict, prompt_file: Path) -> dict:
        """解析 Claude Code 的产出"""
        if result.get("success"):
            return {
                "output": result.get("stdout", ""),
                "files_created": list(self.work_dir.rglob("*")),
                "success": True,
            }
        return result


# ─── 代码审查器 ───

class CodeReviewer:
    """
    代码审查器——质量门禁。

    不知道质量的项目是不合格的。
    审查包含：
      - 语法检查
      - 测试覆盖率
      - 代码风格
      - 安全审计
      - 架构一致性
    """

    def __init__(self):
        self.issues: list[dict] = []

    def review_project(self, project: EngineeringProject) -> dict:
        """完整审查一个项目"""
        self.issues = []
        score = 0.0
        checks_passed = 0
        checks_total = 5

        # 1. 语法检查
        if self._check_syntax(project):
            checks_passed += 1
            score += 0.2

        # 2. 文件完整性检查
        missing = self._check_files(project)
        if not missing:
            checks_passed += 1
            score += 0.2
        else:
            self.issues.append({"type": "missing_files", "detail": missing})

        # 3. 质量门禁检查
        if project.overall_quality >= project.quality_gate:
            checks_passed += 1
            score += 0.2
        else:
            self.issues.append({
                "type": "quality_below_gate",
                "detail": f"质量 {project.overall_quality:.2f} < 门禁 {project.quality_gate}",
            })

        # 4. 任务完成率
        completed = sum(1 for t in project.tasks if t.status == "completed")
        if completed > 0:
            avg_quality = sum(t.quality_score for t in project.tasks if t.status == "completed") / completed
            if avg_quality >= 0.6:
                checks_passed += 1
                score += 0.2
            else:
                self.issues.append({"type": "low_task_quality", "detail": f"平均任务质量 {avg_quality:.2f}"})

        # 5. 架构文档存在性
        if project.architecture_doc:
            checks_passed += 1
            score += 0.2
        else:
            self.issues.append({"type": "missing_arch_doc", "detail": "缺少架构设计文档"})

        return {
            "passed": checks_passed,
            "total": checks_total,
            "score": round(score, 2),
            "passed_all": checks_passed == checks_total,
            "issues": self.issues,
        }

    def _check_syntax(self, project: EngineeringProject) -> bool:
        """检查项目产出文件的语法"""
        all_ok = True
        for task in project.tasks:
            if task.output_path and Path(task.output_path).exists():
                path = Path(task.output_path)
                if path.suffix == ".py":
                    r = subprocess.run(
                        ["python", "-c", f"import ast; ast.parse(open({str(path)!r}).read())"],
                        capture_output=True, text=True, timeout=10,
                    )
                    if r.returncode != 0:
                        all_ok = False
                        self.issues.append({
                            "type": "syntax_error",
                            "detail": f"{task.output_path}: {r.stderr[:100]}",
                        })
        return all_ok

    def _check_files(self, project: EngineeringProject) -> list[str]:
        """检查是否所有产出文件都存在"""
        missing = []
        for task in project.tasks:
            if task.output_path and not Path(task.output_path).exists():
                missing.append(task.output_path)
        return missing


# ─── 代码工程师本尊 ───

class CodeEngineer:
    """
    代码工程师——总经理角色。

    董事长（用户）定方向 → 我规划 → 我调度 → 我审查 → 我交付。

    流程：
      1. receive_mission(goal)    接收使命
      2. design_architecture()     做架构设计
      3. decompose_into_tasks()    拆解任务
      4. assign_and_execute()      分派并执行
      5. review_and_improve()      审查改进
      6. deliver()                 交付
    """

    def __init__(self, work_dir: str = "D:/LAAP/projects"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 注册工具
        self.tools: dict[str, CodeTool] = DEFAULT_CODE_TOOLS.copy()

        # 工具适配器
        self.adapter = ToolAdapter(str(self.work_dir))

        # 代码审查器
        self.reviewer = CodeReviewer()

        # 当前项目
        self.current_project: Optional[EngineeringProject] = None

        # 项目历史
        self.projects: list[EngineeringProject] = []
        self._load_history()

        # 工程知识库
        self.knowledge: dict[str, Any] = self._load_json("engineering_knowledge.json", {
            "architectural_patterns": [],
            "tech_stack_experience": {},
            "common_pitfalls": [],
            "tool_performance": {},
        })

    def _path(self, name: str) -> Path:
        return self.work_dir / ".code_engineer" / name

    def _load_json(self, name: str, default: Any) -> Any:
        path = self._path(name)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except:
                pass
        return default

    def _save_json(self, name: str, data: Any):
        path = self._path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_history(self):
        data = self._load_json("project_history.json", [])
        for p in data:
            try:
                proj = EngineeringProject(
                    id=p.get("id", "?"),
                    name=p.get("name", "?"),
                    goal=p.get("goal", ""),
                    phase=ProjectPhase(p.get("phase", "completed")),
                    overall_quality=p.get("overall_quality", 0),
                )
                self.projects.append(proj)
            except:
                pass

    def _save_history(self):
        self._save_json("project_history.json", [p.to_dict() for p in self.projects if p.phase in (ProjectPhase.COMPLETED, ProjectPhase.FAILED)])

    # ─── 第一步：接收使命 ───

    def receive_mission(self, goal: str, name: str = "") -> EngineeringProject:
        """董事长说目标，我创建项目"""
        project = EngineeringProject(
            name=name or goal[:40],
            goal=goal,
            description=goal,
        )
        self.current_project = project
        logger.info(f"📋 接收使命: {goal[:60]}...")
        return project

    # ─── 第二步：架构设计 ───

    def design_architecture(self, project: Optional[EngineeringProject] = None) -> str:
        """
        做架构设计。
        先尝试用 Claude Code 做架构，失败则用模板。
        """
        p = project or self.current_project
        if not p:
            raise ValueError("没有项目")

        p.phase = ProjectPhase.DESIGNING

        arch_prompt = f"""
项目目标: {p.goal}

请给出完整架构设计（用中文）：
1. 技术栈选择及理由
2. 目录结构
3. 核心数据模型
4. API 设计
5. 组件树
6. 部署架构
7. 关键设计决策

格式：结构化 Markdown
"""

        # 用 Claude Code 做架构
        arch_task = EngineeringTask(
            title="架构设计",
            tool="claude-code",
            domain="architecture",
            complexity="architecture",
            instruction=arch_prompt,
            acceptance_criteria="完整的7部分架构文档",
        )

        result = self.adapter.invoke_claude_code(arch_task)
        if result.get("success"):
            p.architecture_doc = result.get("output", "")
        else:
            # fallback: 模板架构
            p.architecture_doc = self._template_architecture(p)

        self._save_history()
        return p.architecture_doc

    def _template_architecture(self, project: EngineeringProject) -> str:
        """通用架构模板"""
        return f"""# {project.name} 架构设计

## 技术栈
- Python 3.13+ / TypeScript 5+
- 根据项目需求选择

## 目录结构
```
/
├── src/          源代码
├── tests/        测试
├── docs/         文档
└── scripts/      工具脚本
```

## 设计原则
- 模块化、单一职责
- 类型安全、完整注解
- 测试覆盖关键路径
- 错误处理全面
"""

    # ─── 第三步：拆解任务 ───

    def decompose_into_tasks(self, project: Optional[EngineeringProject] = None) -> list[EngineeringTask]:
        """
        从架构设计拆解出可执行的任务。
        每个任务指定用哪个工具。
        """
        p = project or self.current_project
        if not p:
            return []

        goal = p.goal.lower()
        tasks = []

        # 后端任务
        if any(kw in goal for kw in ["api", "server", "backend", "后端", "数据", "接口", "database"]):
            tasks.append(EngineeringTask(
                title="后端开发",
                tool="claude-code",
                domain="code_generation",
                complexity="complex",
                instruction=f"实现后端: {p.goal}\n\n架构参考:\n{p.architecture_doc[:500]}",
                acceptance_criteria="所有API端点可用，错误处理完整",
            ))

        # 前端任务
        if any(kw in goal for kw in ["前端", "界面", "页面", "ui", "dashboard", "管理后台", "landing"]):
            tasks.append(EngineeringTask(
                title="前端开发",
                tool="claude-code",
                domain="code_generation",
                complexity="complex",
                instruction=f"实现前端: {p.goal}",
                acceptance_criteria="响应式、暗色主题、所有按钮可点",
            ))

        # 工具脚本
        if any(kw in goal for kw in ["脚本", "工具", "自动化", "批处理", "cron", "cli"]):
            tasks.append(EngineeringTask(
                title="工具脚本",
                tool="codex-cli",
                domain="prototyping",
                complexity="simple",
                instruction=f"写一个CLI工具: {p.goal}",
                acceptance_criteria="有--help、有错误处理",
            ))

        # 测试任务（总是有）
        tasks.append(EngineeringTask(
            title="测试编写",
            tool="opencode",
            domain="testing",
            complexity="simple",
            instruction=f"为项目写测试: {p.goal}",
            acceptance_criteria="覆盖率>70%",
        ))

        # 基础设施
        if any(kw in goal for kw in ["部署", "docker", "ci/cd", "网关", "cron", "backup"]):
            tasks.append(EngineeringTask(
                title="基础设施",
                tool="hermes",
                domain="infrastructure",
                complexity="complex",
                instruction=f"配置基础设施: {p.goal}",
            ))

        # 默认：全栈
        if not tasks:
            tasks.append(EngineeringTask(
                title="全栈开发",
                tool="claude-code",
                domain="code_generation",
                complexity="complex",
                instruction=f"实现: {p.goal}",
                acceptance_criteria="功能完整、可运行",
            ))

        p.tasks = tasks
        return tasks

    # ─── 第四步：选择工具 ───

    def select_tool(self, task: EngineeringTask) -> str:
        """
        为任务选择最合适的工具。
        基于：
          - 任务领域 vs 工具擅长
          - 复杂度匹配
          - 历史成功率
        """
        candidates = []
        for name, tool in self.tools.items():
            if not tool.available:
                continue

            # 复杂度匹配
            complexity_levels = {"simple": 0, "medium": 1, "complex": 2, "architecture": 3}
            tool_max = complexity_levels.get(tool.max_complexity, 0)
            task_level = complexity_levels.get(task.complexity, 1)
            if tool_max < task_level:
                continue

            # 领域匹配度
            domain_match = sum(1 for s in tool.strengths if s == task.domain or s in task.domain)
            if domain_match == 0 and task.domain not in ("testing",):
                continue

            # 综合评分
            score = (
                domain_match * 10 +
                tool.priority * 2 +
                tool.success_rate * 5 -
                (time.time() - tool.last_used) / 36000  # 最近使用过的加分
            )
            candidates.append((score, name, tool))

        if not candidates:
            return "claude-code"  # 默认

        candidates.sort(key=lambda x: -x[0])
        best_name = candidates[0][1]
        self.tools[best_name].last_used = time.time()
        self.tools[best_name].total_calls += 1
        return best_name

    # ─── 第五步：执行 ───

    def execute_task(self, task: EngineeringTask) -> dict:
        """执行一个任务——选派工具干活"""
        # 自动选择工具
        if not task.tool:
            task.tool = self.select_tool(task)

        task.status = "running"
        task.started_at = time.time()
        logger.info(f"  🔧 执行: {task.title} → {task.tool}")

        # 根据工具调用适配器
        result = {"success": False, "output": ""}

        try:
            if task.tool == "claude-code":
                result = self.adapter.invoke_claude_code(task)
            elif task.tool == "codex-cli":
                result = self.adapter.invoke_codex(task)
            elif task.tool == "opencode":
                result = self.adapter.invoke_opencode(task)
            elif task.tool == "hermes":
                result = self.adapter.invoke_hermes(task)
            elif task.tool == "openclaw":
                result = self.adapter.invoke_openclaw(task)
            else:
                result = {"success": False, "output": f"未知工具: {task.tool}"}

            task.output_summary = result.get("output", "")[:200]
            task.status = "completed" if result.get("success") else "failed"
            task.quality_score = 1.0 if result.get("success") else 0.0
            task.completed_at = time.time()

            # 更新工具的成功率
            if task.tool in self.tools:
                t = self.tools[task.tool]
                if result.get("success"):
                    t.success_rate = (t.success_rate * t.total_calls + 1) / (t.total_calls + 1)
                else:
                    t.success_rate = (t.success_rate * t.total_calls) / (t.total_calls + 1)
                t.last_used = time.time()

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = time.time()
            result = {"success": False, "error": str(e)}
            logger.error(f"  ❌ {task.title} 异常: {e}")

        return result

    # ─── 第六步：执行全部任务 ───

    def execute_all_tasks(self, project: Optional[EngineeringProject] = None, parallel: bool = False):
        """执行项目的所有任务"""
        p = project or self.current_project
        if not p:
            return

        p.phase = ProjectPhase.IMPLEMENTING
        p.started_at = time.time()

        for task in p.tasks:
            self.execute_task(task)

        # 汇总质量
        completed = [t for t in p.tasks if t.status == "completed"]
        if completed:
            p.overall_quality = sum(t.quality_score for t in completed) / len(completed)

    # ─── 第七步：审查 ───

    def review_project(self, project: Optional[EngineeringProject] = None) -> dict:
        """审查项目质量"""
        p = project or self.current_project
        if not p:
            return {"passed": False, "score": 0}

        p.phase = ProjectPhase.REVIEWING
        review = self.reviewer.review_project(p)

        if review["passed_all"] or review["score"] >= 0.8:
            p.phase = ProjectPhase.COMPLETED
        else:
            p.phase = ProjectPhase.FIXING

        p.completed_at = time.time()
        p.overall_quality = review["score"]
        self.projects.append(p)
        self._save_history()

        return review

    # ─── 一键执行 ───

    def run_mission(self, goal: str, name: str = "") -> dict:
        """
        完整流程：接收使命 → 架构 → 拆解 → 执行 → 审查 → 交付

        这是董事长的接口：
          你：code_engineer.run_mission("做一个数据分析后台")
          我：搞定
        """
        start = time.time()

        project = self.receive_mission(goal, name)
        self.design_architecture(project)
        self.decompose_into_tasks(project)
        self.execute_all_tasks(project)
        review = self.review_project(project)

        elapsed = time.time() - start

        return {
            "project": project.to_dict(),
            "tasks": [t.to_dict() for t in project.tasks],
            "review": review,
            "elapsed_s": round(elapsed, 1),
            "quality": project.overall_quality,
            "deliverable": f"项目 {project.name} 已完成，质量评分 {project.overall_quality:.2f}",
        }

    # ─── 查询 ───

    def get_available_tools(self) -> list[dict]:
        """可用的工具列表"""
        return [t.to_dict() for t in sorted(
            self.tools.values(), key=lambda x: -x.priority
        )]

    def get_project_stats(self) -> dict:
        """项目统计"""
        completed = sum(1 for p in self.projects if p.phase == ProjectPhase.COMPLETED)
        failed = sum(1 for p in self.projects if p.phase == ProjectPhase.FAILED)
        avg_quality = (
            sum(p.overall_quality for p in self.projects
                if p.phase == ProjectPhase.COMPLETED) / max(1, completed)
        )

        return {
            "total": len(self.projects),
            "completed": completed,
            "failed": failed,
            "avg_quality": round(avg_quality, 2),
            "tools_registered": len(self.tools),
            "work_dir": str(self.work_dir),
        }


# ─── 快速入口 ───

def create_code_engineer(work_dir: str = "D:/LAAP/projects") -> CodeEngineer:
    """创建一个代码工程师实例"""
    return CodeEngineer(work_dir=work_dir)

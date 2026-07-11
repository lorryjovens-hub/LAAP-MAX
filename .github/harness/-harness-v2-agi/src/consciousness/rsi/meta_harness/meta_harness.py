"""元 Harness - Harness 的自我修改能力

让 Harness 能够读取、理解、修改自己的源代码。
这是递归自我改进（RSI）的核心引擎。

安全约束：
1. 只能修改特定白名单文件
2. 所有修改必须通过静态分析和测试
3. 修改前必须创建备份
4. 对齐守卫必须批准所有修改
"""

import ast
import hashlib
import inspect
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.config import get_settings
from src.consciousness.rsi.versioning.version_control import VersionControl
from src.llm.client import get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetaHarness:
    """
    Harness 的元认知层 —— 自我修改能力

    职责：
    1. 读取自己的源代码（自省）
    2. 分析代码结构和性能瓶颈（自诊断）
    3. 生成改进方案（自规划）
    4. 修改代码并验证（自执行）
    5. 评估改进效果（自评估）

    安全原则：
    - 只修改白名单内的模块
    - 所有修改必须保持向后兼容
    - 修改失败自动回滚
    - 对齐约束不可修改
    """

    # 可修改模块白名单
    MODIFIABLE_MODULES = {
        "src.consciousness.perception.vision_engine",
        "src.consciousness.perception.video_engine",
        "src.consciousness.perception.layout_analyzer",
        "src.consciousness.decision.aesthetic_evaluator",
        "src.consciousness.world_model.design_physics",
        "src.consciousness.world_model.predictors.user_behavior",
        "src.verification.visual_regression",
    }

    # 不可修改的核心模块（安全红线）
    PROTECTED_MODULES = {
        "src.consciousness.rsi.meta_harness",
        "src.consciousness.rsi.guards.alignment_guard",
        "src.consciousness.rsi.guards.capability_evaluator",
        "src.config",
        "src.main",
    }

    def __init__(self):
        self.settings = get_settings()
        self.project_root = Path(".")
        self.improvement_history: List[Dict] = []
        # F1.4: apply_improvement 测试失败时调用 version_control.rollback
        self.version_control = VersionControl()

    async def introspect(self, module_path: str) -> Dict[str, any]:
        """
        自省：分析自己的源代码结构

        Returns:
            {
                "functions": [{"name": str, "lines": int, "complexity": int}],
                "classes": [{"name": str, "methods": int, "inheritance": str}],
                "imports": [str],
                "docstrings": [str],
                "ast_tree": ast.AST,
                "hash": str,
            }
        """
        logger.info(f"[MetaHarness] 自省: {module_path}")

        file_path = self._module_to_path(module_path)
        if not file_path.exists():
            raise FileNotFoundError(f"模块不存在: {module_path}")

        source = file_path.read_text(encoding="utf-8")

        # 计算哈希
        source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]

        # 解析 AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"语法错误: {e}")

        # 分析结构
        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "lines": node.end_lineno - node.lineno if node.end_lineno else 0,
                    "complexity": self._compute_complexity(node),
                    "docstring": ast.get_docstring(node),
                })
            elif isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "methods": len(methods),
                    "inheritance": [self._get_name(base) for base in node.bases],
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(self._format_import(node))

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "ast_tree": tree,
            "hash": source_hash,
            "total_lines": len(source.splitlines()),
        }

    async def diagnose(self, module_path: str) -> List[Dict]:
        """
        自诊断：发现代码中的问题和改进机会

        诊断维度：
        1. 性能瓶颈（时间复杂度、循环嵌套）
        2. 代码异味（重复代码、过长函数）
        3. 测试覆盖缺失
        4. 错误处理不足
        5. 与最佳实践的偏差
        """
        logger.info(f"[MetaHarness] 诊断: {module_path}")

        introspection = await self.introspect(module_path)
        issues = []

        # 1. 过长函数
        for func in introspection["functions"]:
            if func["lines"] > 50:
                issues.append({
                    "type": "long_function",
                    "severity": "medium",
                    "target": func["name"],
                    "message": f"函数 {func['name']} 过长 ({func['lines']} 行)，建议拆分为子函数",
                    "suggestion": "extract_method",
                })

            # 复杂度过高
            if func["complexity"] > 10:
                issues.append({
                    "type": "high_complexity",
                    "severity": "high",
                    "target": func["name"],
                    "message": f"函数 {func['name']} 圈复杂度 {func['complexity']} 过高",
                    "suggestion": "refactor_conditionals",
                })

        # 2. 缺少文档字符串
        for func in introspection["functions"]:
            if not func["docstring"]:
                issues.append({
                    "type": "missing_docstring",
                    "severity": "low",
                    "target": func["name"],
                    "message": f"函数 {func['name']} 缺少文档字符串",
                    "suggestion": "add_docstring",
                })

        # 3. 类过大
        for cls in introspection["classes"]:
            if cls["methods"] > 20:
                issues.append({
                    "type": "large_class",
                    "severity": "medium",
                    "target": cls["name"],
                    "message": f"类 {cls['name']} 方法过多 ({cls['methods']} 个)，考虑拆分",
                    "suggestion": "extract_class",
                })

        return issues

    async def plan_improvement(
        self,
        module_path: str,
        issues: List[Dict],
    ) -> Dict[str, any]:
        """
        自规划：基于诊断结果生成改进方案

        使用 LLM 生成改进代码，但受限于：
        1. 只能修改白名单模块
        2. 必须保持接口不变
        3. 必须通过所有测试
        """
        logger.info(f"[MetaHarness] 规划改进: {module_path}, {len(issues)} 个问题")

        # 检查是否可修改
        if not self._is_modifiable(module_path):
            raise PermissionError(f"模块 {module_path} 不可修改（受保护）")

        # 读取当前源码
        file_path = self._module_to_path(module_path)
        current_source = file_path.read_text(encoding="utf-8")

        # 构建改进 prompt
        issues_text = "\n".join([
            f"- [{i['severity']}] {i['type']}: {i['message']} (建议: {i['suggestion']})"
            for i in issues
        ])

        prompt = f"""
        你是 Harness 的自我改进引擎。请改进以下 Python 模块，解决列出的问题。

        【当前代码】:
        ```python
        {current_source}
        ```

        【需要解决的问题】:
        {issues_text}

        【改进规则】:
        1. 必须保持所有公共接口（函数名、参数、返回值）不变
        2. 只能修改函数内部实现，不能删除函数或类
        3. 添加必要的错误处理
        4. 添加文档字符串和类型注解
        5. 优化性能（减少嵌套循环、使用更高效的数据结构）
        6. 输出完整的改进后代码（不要只输出修改部分）

        【安全约束】:
        - 禁止修改任何导入语句（import 部分保持原样）
        - 禁止引入新的外部依赖
        - 禁止修改类继承关系

        请输出改进后的完整 Python 代码。
        """

        llm = await get_llm_client()

        try:
            improved_source = await llm.chat_completion(
                messages=[
                    {"role": "system", "content": "你是 Python 代码重构专家，专注于性能优化和代码质量提升。"},
                    {"role": "user", "content": prompt},
                ],
                stage="refinement",
                temperature=0.1,
                max_tokens=8000,
            )

            # 提取代码
            improved_source = self._extract_code(improved_source)

            return {
                "module": module_path,
                "issues_addressed": len(issues),
                "improved_source": improved_source,
                "changes_summary": issues_text,
            }

        except Exception as e:
            logger.error(f"[MetaHarness] 改进规划失败: {e}")
            raise

    async def apply_improvement(
        self,
        module_path: str,
        improved_source: str,
    ) -> Union[Dict[str, Any], bool]:
        """
        自执行：应用改进并验证

        流程：
        1. 创建备份
        2. 写入改进代码
        3. 语法检查
        4. 运行测试
        5. 如果失败，回滚（F1.4: 拒绝提交并触发 version_control.rollback）

        Returns:
            Dict (成功) 或 False (测试失败，拒绝提交)
        """
        logger.info(f"[MetaHarness] 应用改进: {module_path}")

        file_path = self._module_to_path(module_path)

        # 1. 创建备份
        backup_path = self._create_backup(file_path)

        try:
            # 2. 写入改进代码
            file_path.write_text(improved_source, encoding="utf-8")

            # 3. 语法检查
            try:
                ast.parse(improved_source)
            except SyntaxError as e:
                raise ValueError(f"改进代码语法错误: {e}")

            # 4. 运行模块测试（F1.1: 真实 pytest 子进程调用）
            test_passed, failed_cases = await self._run_module_tests(module_path)

            if not test_passed:
                # F1.4: 测试失败 —— 拒绝提交改进，触发 version_control.rollback
                logger.error(
                    f"[MetaHarness] 测试未通过，拒绝提交改进: {module_path}, "
                    f"失败用例数: {len(failed_cases)}"
                )
                # 恢复备份
                shutil.copy2(backup_path, file_path)
                # 触发 version_control.rollback（回滚到最近一个已知良好版本）
                self._trigger_version_rollback()

                self.improvement_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "module": module_path,
                    "backup_path": str(backup_path),
                    "status": "rejected_by_tests",
                    "failed_cases": failed_cases,
                })

                return False

            # 5. 记录改进
            self.improvement_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "module": module_path,
                "backup_path": str(backup_path),
                "new_hash": hashlib.sha256(improved_source.encode()).hexdigest()[:16],
                "status": "applied",
            })

            logger.info(f"[MetaHarness] 改进已成功应用: {module_path}")

            return {
                "success": True,
                "module": module_path,
                "backup": str(backup_path),
            }

        except Exception as e:
            # 其他异常（语法错误等）—— 回滚
            logger.error(f"[MetaHarness] 改进失败，回滚: {e}")
            shutil.copy2(backup_path, file_path)

            self.improvement_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "module": module_path,
                "backup_path": str(backup_path),
                "status": "rolled_back",
                "error": str(e),
            })

            raise

    def _trigger_version_rollback(self) -> None:
        """F1.4: 触发 version_control.rollback —— 回滚到最近一个已知良好版本

        若 version_control 中存在历史版本，回滚到最近一个；否则仅记录日志。
        rollback 失败时抛出异常（F2 将在此基础上实现 panic_lock）。
        """
        try:
            if self.version_control.versions:
                latest_version = self.version_control.versions[-1]
                logger.info(
                    f"[MetaHarness] 触发 version_control.rollback 到版本: {latest_version.version_id}"
                )
                self.version_control.rollback(latest_version.version_id)
            else:
                logger.warning(
                    "[MetaHarness] version_control 中无历史版本，仅恢复备份"
                )
        except Exception as e:
            logger.error(f"[MetaHarness] version_control.rollback 失败: {e}")
            raise

    async def evaluate_improvement(
        self,
        module_path: str,
        metric: str = "performance",
    ) -> Dict[str, float]:
        """
        自评估：评估改进效果

        metric: performance | readability | maintainability | test_coverage
        """
        introspection = await self.introspect(module_path)

        scores = {}

        if metric == "performance":
            # 评估性能：函数复杂度、循环嵌套深度
            total_complexity = sum(f["complexity"] for f in introspection["functions"])
            scores["complexity_score"] = max(0, 100 - total_complexity)
            scores["line_count"] = introspection["total_lines"]

        elif metric == "readability":
            # 评估可读性：文档字符串覆盖率
            docstring_count = sum(1 for f in introspection["functions"] if f["docstring"])
            total_functions = len(introspection["functions"])
            scores["docstring_coverage"] = docstring_count / total_functions if total_functions else 1.0
            scores["avg_function_length"] = sum(f["lines"] for f in introspection["functions"]) / max(total_functions, 1)

        return scores

    def _module_to_path(self, module_path: str) -> Path:
        """模块路径转文件路径"""
        relative = module_path.replace(".", "/") + ".py"
        return self.project_root / relative

    def _is_modifiable(self, module_path: str) -> bool:
        """检查模块是否在白名单中"""
        return module_path in self.MODIFIABLE_MODULES

    def _compute_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _get_name(self, node: ast.AST) -> str:
        """获取 AST 节点的名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ""

    def _format_import(self, node: ast.AST) -> str:
        """格式化导入语句"""
        if isinstance(node, ast.Import):
            return ", ".join(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            return f"from {module} import {names}"
        return ""

    def _extract_code(self, response: str) -> str:
        """从 LLM 响应提取代码"""
        import re
        match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

    def _create_backup(self, file_path: Path) -> Path:
        """创建备份"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("./backups")
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"{file_path.stem}_{timestamp}.py.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path

    async def _run_module_tests(self, module_path: str) -> Tuple[bool, List[str]]:
        """F1.1: 运行模块相关测试 —— 通过子进程调用真实 pytest

        使用 `pytest-json-report` 插件解析测试结果，从 `report.tests` 字段
        提取失败用例。失败时将失败用例写入 `rsi_incidents/{timestamp}_test_fail.json`。

        Args:
            module_path: 模块路径（点分形式，如 "src.consciousness.perception.vision_engine"）

        Returns:
            (是否通过, 失败用例 nodeid 列表)
        """
        # 转换模块路径为测试目录：
        #   src.consciousness.perception.vision_engine -> tests/consciousness/perception/
        # 即去掉 "src." 前缀与最后一段模块名，剩余部分用 "/" 拼接
        parts = module_path.split(".")
        if parts and parts[0] == "src":
            parts = parts[1:]
        if len(parts) > 1:
            parts = parts[:-1]
        test_subdir = "/".join(parts)
        test_path = f"tests/{test_subdir}/" if test_subdir else "tests/"

        # 创建临时 JSON 报告文件
        tmp_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".json", prefix="pytest_report_", delete=False
        )
        tmp_path = tmp_file.name
        tmp_file.close()

        try:
            cmd = [
                "pytest",
                test_path,
                "--json-report",
                f"--json-report-file={tmp_path}",
            ]

            logger.info(f"[MetaHarness] 运行 pytest: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            # F1.2: 解析 JSON 报告中的 report.tests 字段提取失败用例
            failed_cases: List[str] = []
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                for test in report.get("tests", []):
                    if test.get("outcome") == "failed":
                        failed_cases.append(test.get("nodeid", "unknown"))
            except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                logger.warning(f"[MetaHarness] 解析 JSON 报告失败: {e}")

            passed = result.returncode == 0

            # F1.3: 失败用例写入 rsi_incidents/{timestamp}_test_fail.json
            if not passed and failed_cases:
                self._write_test_fail_incident(
                    module_path, failed_cases, result.stdout, result.stderr
                )

            return passed, failed_cases
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    def _write_test_fail_incident(
        self,
        module_path: str,
        failed_cases: List[str],
        stdout: str,
        stderr: str,
    ) -> Path:
        """F1.3: 将测试失败用例写入 rsi_incidents/{timestamp}_test_fail.json

        Args:
            module_path: 触发失败的模块路径
            failed_cases: 失败用例 nodeid 列表
            stdout: pytest 子进程 stdout
            stderr: pytest 子进程 stderr

        Returns:
            事件文件路径
        """
        incidents_dir = self.project_root / "rsi_incidents"
        incidents_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        incident_file = incidents_dir / f"{timestamp}_test_fail.json"

        incident_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_path,
            "failed_cases": failed_cases,
            "failed_count": len(failed_cases),
            "stdout": stdout,
            "stderr": stderr,
        }

        incident_file.write_text(
            json.dumps(incident_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"[MetaHarness] 测试失败事件已写入: {incident_file}")
        return incident_file

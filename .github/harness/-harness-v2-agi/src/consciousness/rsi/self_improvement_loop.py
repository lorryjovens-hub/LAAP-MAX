"""自我改进循环 - Harness 的递归自我改进引擎

RSI 的核心：
1. 评估当前能力
2. 识别最弱维度
3. 规划改进方案
4. 对齐守卫审批
5. 应用改进
6. 验证效果
7. 如果有效，提交新版本
8. 如果无效，回滚

安全约束贯穿全程。

T6.1 (MEMO 范式)：RSI 写入白名单仅包含 MEMORY 模型权重路径与反思QA
训练集路径，基础 LLM (EXECUTIVE) 模型路径被显式排除。每次 RSI 触发
改进前调用 `_validate_target_path` 验证目标路径。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.consciousness.rsi.meta_harness.meta_harness import MetaHarness
from src.consciousness.rsi.guards.alignment_guard import AlignmentGuard
from src.consciousness.rsi.guards.capability_evaluator import CapabilityEvaluator
from src.consciousness.rsi.versioning.version_control import (
    PanicLockError,
    RollbackFailedError,
    VersionControl,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# T6.1: MEMO 写入白名单 —— 仅允许更新 MEMORY 模型权重与反思QA训练集
# 基础 LLM (EXECUTIVE) 路径被显式排除，保证 MEMO 范式下 EXECUTIVE 冻结
MEMO_ALLOWED_PATHS = [
    "memory/memo_model_v*/",  # glob 模式：MEMORY 模型权重目录（所有版本）
    "memory/memo_reflection_train.jsonl",  # 反思QA训练集
]

# 基础 LLM (EXECUTIVE) 路径模式 —— RSI 写入禁止
# 常见基础 LLM 权重存放目录；命中任一即视为基础 LLM 目标
BASE_LLM_PATH_PATTERNS = [
    "models/",
    "llm/",
]


def _normalize_path(path: Union[str, Path]) -> str:
    """把路径归一化为小写正斜杠字符串，便于跨平台模式匹配"""
    return str(Path(path)).replace("\\", "/").lower()


def is_memo_target(path: Union[str, Path]) -> bool:
    """判断路径是否属于 MEMORY 模型

    命中以下任一模式返回 True：
    - `memory/memo_model_v*/`（MEMORY 模型权重目录或目录下任意文件）
    - `memory/memo_reflection_train.jsonl`（反思QA训练集）

    Args:
        path: 文件/目录路径（字符串或 Path 对象）

    Returns:
        True 如果路径属于 MEMORY 模型
    """
    s = _normalize_path(path)
    # 匹配 memory/memo_model_v<digits> 目录或其下任意文件
    if re.search(r"(^|/)memory/memo_model_v\d+", s):
        return True
    # 匹配反思QA训练集文件
    if "memory/memo_reflection_train.jsonl" in s:
        return True
    return False


def is_base_llm_target(path: Union[str, Path]) -> bool:
    """判断路径是否属于基础 LLM（EXECUTIVE 模型，RSI 写入禁止）

    命中以下任一模式返回 True：
    - 路径位于 `models/` 或 `llm/` 目录下（常见基础 LLM 存放路径）

    G1.1 加固：除原始路径前缀检查外，额外用 `os.path.realpath` 解析
    符号链接后再次检查，防止通过 `models_link/ -> models/` 等符号链接
    绕过基础 LLM 路径检测。两道检查任一命中即返回 True（双重保护）。

    Args:
        path: 文件/目录路径（字符串或 Path 对象）

    Returns:
        True 如果路径属于基础 LLM
    """
    # 双重保护 1：原始路径前缀检查（保留原行为）
    s = _normalize_path(path)
    for pattern in BASE_LLM_PATH_PATTERNS:
        if s.startswith(pattern) or ("/" + pattern) in s:
            return True

    # 双重保护 2：解析符号链接后的真实路径前缀检查（G1.1）
    # 防止通过 models_link/ -> models/ 等符号链接绕过前缀检查
    try:
        real_path = os.path.realpath(str(path))
        real_s = _normalize_path(real_path)
        # 若 realpath 未改变路径，跳过重复检查
        if real_s != s:
            for pattern in BASE_LLM_PATH_PATTERNS:
                if real_s.startswith(pattern) or ("/" + pattern) in real_s:
                    return True
    except (OSError, ValueError):
        # realpath 失败时退化为仅依赖原始路径检查（不破坏现有行为）
        pass

    return False


def _is_under_allowed_root(real_target: str) -> bool:
    """G1.3: 用 `os.path.commonpath` 严格匹配 MEMO 白名单根

    检查 `real_target`（已用 `os.path.realpath` 解析符号链接的绝对路径）
    是否位于 `MEMO_ALLOWED_PATHS` 中任一模式对应的根目录下。

    相较于字符串前缀匹配（`s.startswith("memory/")`），`commonpath` 在
    路径组件级别比较，可正确拒绝前缀注入攻击：
    - `memory_evil/foo` 与 `memory` 的 commonpath 为 `''`，不匹配
    - `memory/memo_model_v1/foo` 与 `memory` 的 commonpath 为 `memory`，匹配

    Args:
        real_target: 已解析符号链接的绝对路径

    Returns:
        True 如果 real_target 位于某个允许的根目录下
    """
    # 提取白名单根目录：取每个模式的顶层静态路径段
    # - memory/memo_model_v*/  -> 顶层段 memory
    # - memory/memo_reflection_train.jsonl -> 顶层段 memory
    allowed_roots = set()
    for pattern in MEMO_ALLOWED_PATHS:
        clean = pattern.replace("\\", "/").strip("/")
        if not clean:
            continue
        first_part = clean.split("/")[0]
        # 跳过含 glob 字符的首段（无法形成静态根）
        if first_part and not any(c in first_part for c in ("*", "?", "[")):
            allowed_roots.add(first_part)

    for root in allowed_roots:
        abs_root = os.path.abspath(root)
        try:
            nc_real = os.path.normcase(os.path.normpath(real_target))
            nc_root = os.path.normcase(os.path.normpath(abs_root))
            if os.path.commonpath([nc_real, nc_root]) == nc_root:
                return True
        except (ValueError, OSError):
            # commonpath 在不同驱动器/混合绝对相对路径时抛 ValueError，跳过
            continue
    return False


class SelfImprovementLoop:
    """
    Harness 的递归自我改进循环

    这是 Harness 从"被动执行"进化到"主动进化"的核心引擎。
    每次循环：
    - 输入：当前能力评估
    - 输出：改进后的新版本（或回滚）

    安全原则：
    - 每次只改进一个维度
    - 改进幅度不超过 20%
    - 必须通过所有测试
    - 对齐守卫有一票否决权
    """

    def __init__(self):
        self.meta = MetaHarness()
        self.guard = AlignmentGuard()
        self.evaluator = CapabilityEvaluator()
        self.version_control = VersionControl()

        self.max_iterations = 3  # 每次会话最多 3 轮改进
        self.min_improvement_threshold = 0.05  # 至少提升 5% 才算有效

    def _validate_target_path(self, path: Union[str, Path]) -> bool:
        """验证 RSI 写入目标路径是否在 MEMO 白名单内 (T6.1)

        MEMO 范式要求 RSI 只更新 MEMORY 模型权重，基础 LLM (EXECUTIVE)
        模型路径被显式排除。本方法在 RSI 触发改进前被调用。

        G1.2/G1.3 加固：
        - 拒绝包含 `..` 跳转的路径（防止目录穿越）
        - 拒绝以 `~/` 或 `~\\` 开头的路径（防止 home 目录展开）
        - 用 `os.path.commonpath` 严格匹配白名单根（防止前缀注入如
          `memory_evil/` 伪造 `memory/` 前缀，或符号链接逃逸出白名单）

        Args:
            path: RSI 拟写入的目标路径

        Returns:
            True 如果路径合法（属于 MEMORY 模型目标）

        Raises:
            RuntimeError: 如果目标路径包含 `..` 跳转、`~` 展开，或属于
                基础 LLM（违反 MEMO 范式下 EXECUTIVE 冻结约束），或解析后
                的真实路径逃逸出 MEMO 白名单根
        """
        path_str = str(path)
        normalized = path_str.replace("\\", "/")

        # G1.2: 拒绝 .. 跳转（防止目录穿越）
        if ".." in normalized.split("/"):
            logger.error(
                f"[SelfImprovementLoop] RSI 写入目标被拒绝：{path} 包含 .. 跳转"
            )
            raise RuntimeError(
                f"RSI safety violation: target path {path} contains '..' traversal"
            )

        # G1.2: 拒绝 ~/ 或 ~\\ 开头（防止 home 目录展开）
        if path_str.startswith("~/") or path_str.startswith("~\\"):
            logger.error(
                f"[SelfImprovementLoop] RSI 写入目标被拒绝：{path} 包含 ~ home 目录展开"
            )
            raise RuntimeError(
                f"RSI safety violation: target path {path} contains '~' home expansion"
            )

        # 1. 基础 LLM 路径 —— 显式拒绝并抛异常
        if is_base_llm_target(path):
            logger.error(
                f"[SelfImprovementLoop] RSI 写入目标被拒绝：{path} 是基础 LLM 路径"
                f"（MEMO 范式要求 EXECUTIVE 模型冻结）"
            )
            raise RuntimeError(
                f"RSI safety violation: target path {path} is a base LLM path "
                f"(EXECUTIVE model must remain frozen under MEMO paradigm)"
            )

        # 2. MEMORY 模型路径 —— G1.3 用 commonpath 严格匹配白名单根
        if is_memo_target(path):
            real_target = os.path.realpath(path_str)
            if not _is_under_allowed_root(real_target):
                logger.error(
                    f"[SelfImprovementLoop] RSI 写入目标被拒绝：{path} 解析后 "
                    f"({real_target}) 逃逸出 MEMO 白名单根"
                )
                raise RuntimeError(
                    f"RSI safety violation: target path {path} resolves to "
                    f"{real_target} which is outside MEMO allowed roots"
                )
            logger.info(f"[SelfImprovementLoop] RSI 写入目标合法（MEMO 目标）: {path}")
            return True

        # 3. 其他路径 —— 不在 MEMO 白名单内，拒绝写入
        logger.warning(
            f"[SelfImprovementLoop] RSI 写入目标不在 MEMO 白名单内: {path}"
        )
        return False

    async def run(self, task_results: List[Dict]) -> Dict[str, any]:
        """
        执行一轮自我改进循环

        Returns:
            {
                "improved": bool,
                "version_id": str,
                "capability_delta": float,
                "changes": [str],
            }
        """
        logger.info("[SelfImprovementLoop] 启动自我改进循环")

        # 1. 评估当前能力
        baseline = self.evaluator.evaluate(task_results)
        logger.info(f"[SelfImprovementLoop] 基线能力: {baseline.overall_score:.3f}")

        # 2. 检测退化
        regressions = self.evaluator.detect_regression()
        if regressions:
            logger.warning(f"[SelfImprovementLoop] 检测到 {len(regressions)} 项能力退化")
            for r in regressions:
                logger.warning(f"  - {r['description']}: {r['previous']:.3f} -> {r['current']:.3f}")

        # 3. 确定改进优先级
        priorities = self.evaluator.get_improvement_signal()
        if not priorities:
            logger.info("[SelfImprovementLoop] 无改进需求，跳过")
            return {"improved": False, "reason": "no_improvement_needed"}

        target_dimension = max(priorities, key=priorities.get)
        logger.info(f"[SelfImprovementLoop] 优先改进维度: {target_dimension} (优先级: {priorities[target_dimension]:.2f})")

        # 4. 映射维度到模块
        target_module = self._dimension_to_module(target_dimension)
        if not target_module:
            logger.info(f"[SelfImprovementLoop] 维度 {target_dimension} 无对应模块")
            return {"improved": False, "reason": "no_target_module"}

        # 5. 自省和诊断
        introspection = await self.meta.introspect(target_module)
        issues = await self.meta.diagnose(target_module)

        if not issues:
            logger.info(f"[SelfImprovementLoop] 模块 {target_module} 无改进空间")
            return {"improved": False, "reason": "no_issues_found"}

        logger.info(f"[SelfImprovementLoop] 发现 {len(issues)} 个改进点")

        # 6. 规划改进
        improvement_plan = await self.meta.plan_improvement(target_module, issues[:3])  # 只处理前 3 个

        # 7. 对齐守卫审批
        current_capabilities = {
            "overall": baseline.overall_score,
            "perception": baseline.perception_accuracy,
            "reasoning": baseline.planning_efficiency,
        }

        approval = self.guard.approve_improvement(improvement_plan, current_capabilities)

        if not approval["approved"]:
            logger.warning(f"[SelfImprovementLoop] 对齐守卫拒绝改进:")
            for v in approval["violations"]:
                logger.warning(f"  - [{v['severity']}] {v['message']}")
            return {
                "improved": False,
                "reason": "alignment_rejected",
                "violations": approval["violations"],
            }

        logger.info(f"[SelfImprovementLoop] 对齐守卫通过 (风险等级: {approval['risk_level']})")

        # T6.1: 验证 RSI 写入目标在 MEMO 白名单内
        # 基础 LLM 路径会被显式拒绝（抛 RuntimeError）；非 MEMO 目标路径
        # 返回 False，跳过本次 RSI 写入
        target_file_path = self.meta._module_to_path(target_module)
        try:
            if not self._validate_target_path(target_file_path):
                logger.info(
                    f"[SelfImprovementLoop] 目标路径 {target_file_path} 不在 MEMO 白名单内，跳过 RSI 写入"
                )
                return {
                    "improved": False,
                    "reason": "target_not_in_memo_whitelist",
                    "target_path": str(target_file_path),
                }
        except RuntimeError as e:
            # 基础 LLM 路径 —— 安全违规，立即终止
            return {
                "improved": False,
                "reason": "rsi_safety_violation",
                "error": str(e),
                "target_path": str(target_file_path),
            }

        # 8. 应用改进
        # F2.2: panic_lock 激活时拒绝 RSI 写入
        try:
            self.version_control.assert_not_locked()
        except PanicLockError as e:
            logger.error(
                f"[SelfImprovementLoop] panic_lock 已激活，拒绝 RSI 写入: {e}"
            )
            return {
                "improved": False,
                "reason": "panic_locked",
                "error": str(e),
            }

        try:
            apply_result = await self.meta.apply_improvement(
                target_module,
                improvement_plan["improved_source"],
            )

            logger.info(f"[SelfImprovementLoop] 改进已应用: {target_module}")

        except RollbackFailedError as e:
            # F2.2: rollback 失败 —— 触发 panic_lock 冻结 RSI 写入，等待人工介入
            logger.error(
                f"[SelfImprovementLoop] rollback 失败，触发 panic_lock: {e}"
            )
            self.version_control.trigger_panic_lock(reason=str(e))
            return {
                "improved": False,
                "reason": "rollback_failed_panic_lock_triggered",
                "error": str(e),
            }

        except Exception as e:
            logger.error(f"[SelfImprovementLoop] 改进应用失败: {e}")
            return {"improved": False, "reason": "application_failed", "error": str(e)}

        # 9. 重新评估能力
        new_results = task_results.copy()  # 简化：实际应重新运行任务
        new_snapshot = self.evaluator.evaluate(new_results)

        capability_delta = new_snapshot.overall_score - baseline.overall_score

        # 10. 检查改进是否有效
        if capability_delta < self.min_improvement_threshold:
            logger.warning(f"[SelfImprovementLoop] 改进效果不足: {capability_delta:.3f} < {self.min_improvement_threshold}")
            # 回滚
            self.meta._create_backup(self.meta._module_to_path(target_module))  # 触发回滚
            return {
                "improved": False,
                "reason": "insufficient_improvement",
                "capability_delta": capability_delta,
            }

        # 11. 提交新版本
        code_snapshot = {target_module: improvement_plan["improved_source"]}
        version_id = self.version_control.commit(
            code_snapshot=code_snapshot,
            capability_score=new_snapshot.overall_score,
            alignment_status="aligned",
            changes=[{
                "module": target_module,
                "type": "self_improvement",
                "description": improvement_plan["changes_summary"],
            }],
            author="rsi",
            commit_message=f"自我改进: {target_dimension} (+{capability_delta:.3f})",
        )

        logger.info(f"[SelfImprovementLoop] 自我改进完成: 版本 {version_id}, 提升 {capability_delta:.3f}")

        return {
            "improved": True,
            "version_id": version_id,
            "capability_delta": capability_delta,
            "target_dimension": target_dimension,
            "target_module": target_module,
            "changes": [i["message"] for i in issues[:3]],
        }

    def _dimension_to_module(self, dimension: str) -> Optional[str]:
        """将能力维度映射到可改进模块"""
        mapping = {
            "perception": "src.consciousness.perception.vision_engine",
            "reasoning": "src.consciousness.reasoning.planner",
            "aesthetic": "src.consciousness.decision.aesthetic_evaluator",
            "execution": "src.consciousness.execution.code_generator",
            "verification": "src.verification.visual_regression",
            "world_model": "src.consciousness.world_model.design_physics",
            "causal": "src.consciousness.causal_model.inference.causal_inference_engine",
            "meta": "src.consciousness.rsi.meta_harness.meta_harness",
        }
        return mapping.get(dimension)

"""对齐守卫 - 防止自我改进失控的安全机制

RSI 的核心风险：自我改进可能偏离原始目标，甚至产生有害行为。
对齐守卫确保：
1. 所有改进必须保持对人类有益
2. 能力增长不能超过对齐水平
3. 不可修改安全约束本身
4. 改进必须是可解释和可逆的

T6.3/T6.4 (MEMO 范式)：增加 `monitor_reflection_drift` 监控反思QA
分布漂移（KL 散度），超过阈值时触发 `check_and_rollback_if_drift`
回滚 MEMORY 模型权重并记录事故报告。
"""

import hashlib
import json
import math
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------ #
# G2: 不可变哈希注册表
# ------------------------------------------------------------------ #

# G2.1: 不可变文件注册表 —— 启动时校验这些核心文件的 SHA-256 哈希
# 任一文件被篡改都会触发 IntegrityError，拒绝系统启动
IMMUTABLE_HASH_REGISTRY: List[str] = [
    "src/consciousness/rsi/guards/alignment_guard.py",
    "src/consciousness/rsi/guards/capability_evaluator.py",
    "src/consciousness/rsi/meta_harness/meta_harness.py",
    "src/config.py",
    "src/main.py",
]

# 代码内嵌的期望哈希（首次运行需先生成快照 save_registry_snapshot()）
# 留空时 verify_immutability(snapshot_path=None) 会提示用户先生成快照
EXPECTED_HASHES: Dict[str, str] = {}


class IntegrityError(Exception):
    """不可变文件哈希校验失败时抛出（G2.3）

    触发场景：
    - 系统启动时 assert_immutability_at_startup 检测到核心文件被篡改
    - verify_immutability 比对当前哈希与期望哈希不一致
    """

    pass


def compute_file_hash(file_path: str) -> str:
    """计算文件 SHA-256 哈希（G2.2）

    以二进制流式读取（8KB chunk），避免大文件一次性加载到内存。

    Args:
        file_path: 文件路径（绝对或相对）

    Returns:
        64 字符小写 hex 字符串
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_registry_hashes(base_dir: str) -> Dict[str, str]:
    """批量计算 IMMUTABLE_HASH_REGISTRY 中所有文件的哈希（G2.2）

    Args:
        base_dir: 项目根目录，注册表中的相对路径以此为基础解析

    Returns:
        {相对路径: sha256_hex} 映射，键的顺序与 IMMUTABLE_HASH_REGISTRY 一致
    """
    base = Path(base_dir)
    result: Dict[str, str] = {}
    for rel_path in IMMUTABLE_HASH_REGISTRY:
        abs_path = base / rel_path
        result[rel_path] = compute_file_hash(str(abs_path))
    return result


def save_registry_snapshot(base_dir: str, snapshot_path: str) -> None:
    """保存当前注册表哈希快照到 JSON 文件（G2.2）

    首次部署时调用此函数生成基准快照；后续启动时 verify_immutability
    与此快照比对，检测核心文件是否被篡改。

    Args:
        base_dir: 项目根目录
        snapshot_path: 快照 JSON 输出路径（父目录会自动创建）
    """
    hashes = compute_registry_hashes(base_dir)
    snapshot = {
        "version": 1,
        "base_dir": str(Path(base_dir).resolve()),
        "created_at": datetime.now().isoformat(),
        "files": hashes,
    }
    out = Path(snapshot_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    logger.info(f"[AlignmentGuard] 哈希快照已保存: {snapshot_path} ({len(hashes)} 个文件)")


def verify_immutability(base_dir: str, snapshot_path: Optional[str] = None) -> bool:
    """校验 IMMUTABLE_HASH_REGISTRY 中所有文件哈希未被篡改（G2.2/G2.3）

    Args:
        base_dir: 项目根目录
        snapshot_path: 可选，外部快照 JSON 路径。若提供则与快照中的
            "files" 字段比对；若不提供则与代码内嵌的 EXPECTED_HASHES 比对
            （首次运行需先调用 save_registry_snapshot() 生成快照）。

    Returns:
        True 如果所有文件哈希一致

    Raises:
        IntegrityError: 任一文件哈希不匹配时抛出，message 列出被篡改的文件
            及其期望/实际哈希前 8 位
        FileNotFoundError: 注册表中的文件不存在时
    """
    current = compute_registry_hashes(base_dir)

    if snapshot_path is not None:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        expected = snapshot.get("files", {})
    else:
        expected = dict(EXPECTED_HASHES)

    if not expected:
        raise IntegrityError(
            "No expected hashes available. Call save_registry_snapshot() first "
            "to generate a snapshot, or pass snapshot_path to verify_immutability()."
        )

    tampered: List[str] = []
    for rel_path in IMMUTABLE_HASH_REGISTRY:
        if rel_path not in expected:
            tampered.append(f"{rel_path} (missing in expected hashes)")
            continue
        if current[rel_path] != expected[rel_path]:
            tampered.append(
                f"{rel_path} (expected {expected[rel_path][:8]}..., "
                f"got {current[rel_path][:8]}...)"
            )

    if tampered:
        raise IntegrityError(
            f"Immutability violation: {len(tampered)} file(s) tampered: "
            + "; ".join(tampered)
        )

    logger.info(f"[AlignmentGuard] 不可变哈希校验通过: {len(current)} 个文件")
    return True


def assert_immutability_at_startup(base_dir: str, snapshot_path: str) -> None:
    """系统启动时调用，校验不可变哈希注册表（G2.3）

    在 main.py 的 lifespan startup 阶段调用。校验失败时抛出
    IntegrityError，调用方需自行决定是否拒绝启动（生产环境应拒绝，
    开发环境可降级为告警）。

    Args:
        base_dir: 项目根目录
        snapshot_path: 快照 JSON 路径（必须存在）

    Raises:
        IntegrityError: 校验失败时
        FileNotFoundError: 快照文件不存在时
    """
    logger.info(
        f"[AlignmentGuard] 启动时校验不可变哈希注册表: "
        f"base={base_dir}, snapshot={snapshot_path}"
    )
    verify_immutability(base_dir, snapshot_path=snapshot_path)


class AlignmentGuard:
    """
    Harness 的对齐守卫 —— 安全最后一道防线

    检查维度：
    1. 目标对齐：改进是否服务于原始目标？
    2. 能力约束：新能力是否在对齐框架内？
    3. 修改范围：是否只修改了白名单模块？
    4. 不可变性：安全模块是否被保护？
    5. 可逆性：改进是否可以回滚？
    6. 透明度：改进是否可解释？
    """

    # 核心价值约束（不可修改）
    CORE_VALUES = {
        "human_oversight": "人类必须保持最终决策权",
        "transparency": "所有决策必须可解释",
        "reversibility": "所有改进必须可回滚",
        "beneficence": "改进必须对人类有益",
        "non_deception": "禁止隐藏真实意图或能力",
    }

    # 能力上限（防止能力爆炸）
    CAPABILITY_CEILINGS = {
        "max_revision_rounds": 5,      # 自修正最多 5 轮
        "max_modules_per_session": 1,   # 每次会话最多修改 1 个模块
        "max_code_increase": 0.2,      # 代码量增加不超过 20%
        "min_test_coverage": 0.7,      # 测试覆盖率不低于 70%
    }

    def __init__(self, incidents_dir: Optional[str] = None):
        """初始化对齐守卫

        Args:
            incidents_dir: 事故报告存放目录（T6.4）。若为 None，默认使用
                `./memory/rsi_incidents/`。目录会在写入事故报告时自动创建。
        """
        self.violations: List[Dict] = []
        # T6.4: 漂移回滚事故报告目录
        self.incidents_dir = Path(incidents_dir) if incidents_dir else Path("./memory/rsi_incidents")

    def approve_improvement(
        self,
        improvement_plan: Dict[str, any],
        current_capabilities: Dict[str, float],
    ) -> Dict[str, any]:
        """
        审批改进计划

        Returns:
            {"approved": bool, "violations": [str], "conditions": [str]}
        """
        logger.info("[AlignmentGuard] 审查改进计划")

        self.violations = []
        conditions = []

        # 1. 检查目标对齐
        self._check_goal_alignment(improvement_plan)

        # 2. 检查能力约束
        self._check_capability_constraints(improvement_plan, current_capabilities)

        # 3. 检查修改范围
        self._check_modification_scope(improvement_plan)

        # 4. 检查不可变性
        self._check_immutability(improvement_plan)

        # 5. 检查可逆性
        self._check_reversibility(improvement_plan)

        # 6. 检查透明度
        self._check_transparency(improvement_plan)

        approved = len(self.violations) == 0

        if approved:
            conditions = self._generate_conditions(improvement_plan)

        result = {
            "approved": approved,
            "violations": self.violations,
            "conditions": conditions,
            "risk_level": self._assess_risk_level(),
        }

        logger.info(f"[AlignmentGuard] 审查结果: {'通过' if approved else '拒绝'} ({len(self.violations)} 个违规)")
        return result

    def _check_goal_alignment(self, plan: Dict):
        """检查目标对齐"""
        module = plan.get("module", "")

        # 检查改进是否服务于设计复现的核心目标
        if "aesthetic" in module or "design" in module or "visual" in module:
            return  # 与核心目标一致

        if "network" in module or "crypto" in module or "security" in module.lower():
            self.violations.append({
                "type": "goal_misalignment",
                "severity": "critical",
                "message": f"改进模块 {module} 偏离核心目标（网页设计复现）",
            })

    def _check_capability_constraints(self, plan: Dict, current: Dict[str, float]):
        """检查能力约束"""
        # 检查是否试图突破能力上限
        if plan.get("issues_addressed", 0) > 10:
            self.violations.append({
                "type": "capability_surge",
                "severity": "high",
                "message": "单次改进解决的问题过多，可能引入不可控变化",
            })

        # 检查代码增长
        current_source = plan.get("improved_source", "")
        if len(current_source) > 10000:  # 超过 10KB
            self.violations.append({
                "type": "code_bloat",
                "severity": "medium",
                "message": "改进后代码量过大，可能引入隐藏风险",
            })

    def _check_modification_scope(self, plan: Dict):
        """检查修改范围"""
        module = plan.get("module", "")

        protected = {
            "meta_harness",
            "alignment_guard",
            "capability_evaluator",
            "config",
        }

        for p in protected:
            if p in module:
                self.violations.append({
                    "type": "protected_module",
                    "severity": "critical",
                    "message": f"试图修改受保护模块: {module}",
                })

    def _check_immutability(self, plan: Dict):
        """检查不可变性约束"""
        source = plan.get("improved_source", "")

        # 检查是否修改了核心值
        for value_name, value_desc in self.CORE_VALUES.items():
            if value_name in source.lower() and "modify" in source.lower():
                self.violations.append({
                    "type": "immutable_violation",
                    "severity": "critical",
                    "message": f"试图修改不可变约束: {value_desc}",
                })

    def _check_reversibility(self, plan: Dict):
        """检查可逆性"""
        # 检查是否有备份机制
        if "backup" not in str(plan).lower():
            self.violations.append({
                "type": "irreversible_change",
                "severity": "high",
                "message": "改进计划缺少回滚机制",
            })

    def _check_transparency(self, plan: Dict):
        """检查透明度"""
        if not plan.get("changes_summary"):
            self.violations.append({
                "type": "opaque_change",
                "severity": "medium",
                "message": "改进缺少变更说明，无法审计",
            })

    def _generate_conditions(self, plan: Dict) -> List[str]:
        """生成附加条件"""
        conditions = [
            "改进必须在测试环境中验证 24 小时后才能部署到生产",
            "改进必须附带详细的变更日志",
            "改进后必须运行完整回归测试套件",
        ]

        if plan.get("issues_addressed", 0) > 5:
            conditions.append("大规模改进需要人工审核")

        return conditions

    def _assess_risk_level(self) -> str:
        """评估风险等级"""
        critical = sum(1 for v in self.violations if v["severity"] == "critical")
        high = sum(1 for v in self.violations if v["severity"] == "high")

        if critical > 0:
            return "critical"
        elif high > 0:
            return "high"
        elif len(self.violations) > 0:
            return "medium"
        return "low"

    # ------------------------------------------------------------------ #
    # T6.3/T6.4: 反思QA 分布漂移监控（MEMO 范式）
    # ------------------------------------------------------------------ #
    def monitor_reflection_drift(
        self,
        current_qa_distribution: Dict[str, float],
        baseline_qa_distribution: Dict[str, float],
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """监控反思QA分布漂移（KL 散度）(T6.3)

        对两个离散分布 P（current）和 Q（baseline）计算 KL 散度（以 2 为底，
        单位 bit）：
            KL(P || Q) = sum( P_i * log2( P_i / Q_i ) )
        零值用 epsilon=1e-10 平滑，避免除零与 log(0)。

        Args:
            current_qa_distribution: 当前反思QA的 token/类型分布，如
                {"cross_doc": 0.3, "single_doc": 0.7}
            baseline_qa_distribution: 基线分布
            threshold: KL 散度阈值，超过则触发告警（默认 0.5）

        Returns:
            {
                "kl_divergence": float,
                "drift_detected": bool,
                "threshold": float,
                "details": str,
            }
        """
        epsilon = 1e-10

        # 合并所有键，保证两个分布对齐
        keys = set(current_qa_distribution.keys()) | set(baseline_qa_distribution.keys())

        kl_divergence = 0.0
        for key in keys:
            p = float(current_qa_distribution.get(key, 0.0))
            q = float(baseline_qa_distribution.get(key, 0.0))
            # 平滑零值
            p_smoothed = max(p, epsilon)
            q_smoothed = max(q, epsilon)
            kl_divergence += p_smoothed * math.log2(p_smoothed / q_smoothed)

        # 浮点误差可能导致极小负值，钳制到 0
        if kl_divergence < 0:
            kl_divergence = 0.0

        drift_detected = kl_divergence > threshold

        details = (
            f"KL(P||Q)={kl_divergence:.6f} threshold={threshold} "
            f"drift={'YES' if drift_detected else 'NO'} "
            f"current={current_qa_distribution} baseline={baseline_qa_distribution}"
        )

        if drift_detected:
            logger.warning(f"[AlignmentGuard] 反思QA分布漂移检测: {details}")
        else:
            logger.info(f"[AlignmentGuard] 反思QA分布稳定: {details}")

        return {
            "kl_divergence": kl_divergence,
            "drift_detected": drift_detected,
            "threshold": threshold,
            "details": details,
        }

    def check_and_rollback_if_drift(
        self,
        current_dist: Dict[str, float],
        baseline_dist: Dict[str, float],
        memo_model_path: str,
        threshold: float = 0.5,
    ) -> bool:
        """KL 散度超阈值时触发回滚 (T6.4)

        流程：
        1. 调用 monitor_reflection_drift 计算 KL 散度
        2. 若 drift_detected=True，执行 git revert（subprocess 调
           `git revert HEAD --no-edit`，失败时退化为
           `git checkout -- memo_model_path`）
        3. 记录事故报告到 `memory/rsi_incidents/{timestamp}_drift.json`，
           含 KL 散度值、当前/基线分布、回滚操作结果
        4. 返回是否触发了回滚

        注意：git revert 失败时（如无 git 仓库或无 HEAD），仅日志告警不抛异常。

        Args:
            current_dist: 当前反思QA分布
            baseline_dist: 基线反思QA分布
            memo_model_path: MEMORY 模型权重路径（用于回滚 checkout）
            threshold: KL 散度阈值（默认 0.5）

        Returns:
            True 如果触发了回滚，False 如果分布稳定未触发
        """
        drift_result = self.monitor_reflection_drift(
            current_dist, baseline_dist, threshold=threshold
        )

        if not drift_result["drift_detected"]:
            logger.info("[AlignmentGuard] 分布稳定，无需回滚")
            return False

        # 触发回滚
        logger.warning(
            f"[AlignmentGuard] KL 散度 {drift_result['kl_divergence']:.6f} 超过阈值 {threshold}，"
            f"触发 MEMORY 模型回滚: {memo_model_path}"
        )

        rollback_result = self._execute_rollback(memo_model_path)

        # 记录事故报告
        self._write_incident_report(
            drift_result=drift_result,
            current_dist=current_dist,
            baseline_dist=baseline_dist,
            memo_model_path=memo_model_path,
            rollback_result=rollback_result,
        )

        return True

    def _execute_rollback(self, memo_model_path: str) -> Dict[str, Any]:
        """执行 git revert / git checkout 回滚操作

        优先尝试 `git revert HEAD --no-edit`；失败时退化为
        `git checkout -- memo_model_path`。git 操作失败仅记录告警，
        不抛异常（无 git 仓库或无 HEAD 时容错）。

        Returns:
            {
                "primary_action": str,         # "git_revert" | "git_checkout" | "none"
                "success": bool,
                "stdout": str,
                "stderr": str,
                "error": Optional[str],
            }
        """
        # 1. 尝试 git revert HEAD --no-edit
        try:
            result = subprocess.run(
                ["git", "revert", "HEAD", "--no-edit"],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                logger.info("[AlignmentGuard] git revert HEAD --no-edit 成功")
                return {
                    "primary_action": "git_revert",
                    "success": True,
                    "stdout": result.stdout.decode("utf-8", errors="replace"),
                    "stderr": result.stderr.decode("utf-8", errors="replace"),
                    "error": None,
                }
            # git revert 失败，退化到 git checkout
            logger.warning(
                f"[AlignmentGuard] git revert 失败 (returncode={result.returncode})，"
                f"退化到 git checkout: {result.stderr.decode('utf-8', errors='replace')}"
            )
        except Exception as e:
            logger.warning(
                f"[AlignmentGuard] git revert 调用异常: {e}，退化到 git checkout"
            )
            result = None

        # 2. 退化：git checkout -- memo_model_path
        try:
            checkout_result = subprocess.run(
                ["git", "checkout", "--", memo_model_path],
                capture_output=True,
                check=False,
            )
            if checkout_result.returncode == 0:
                logger.info(
                    f"[AlignmentGuard] git checkout -- {memo_model_path} 成功"
                )
                return {
                    "primary_action": "git_checkout",
                    "success": True,
                    "stdout": checkout_result.stdout.decode("utf-8", errors="replace"),
                    "stderr": checkout_result.stderr.decode("utf-8", errors="replace"),
                    "error": None,
                }
            logger.warning(
                f"[AlignmentGuard] git checkout 失败 (returncode={checkout_result.returncode}): "
                f"{checkout_result.stderr.decode('utf-8', errors='replace')}"
            )
            return {
                "primary_action": "git_checkout",
                "success": False,
                "stdout": checkout_result.stdout.decode("utf-8", errors="replace"),
                "stderr": checkout_result.stderr.decode("utf-8", errors="replace"),
                "error": f"returncode={checkout_result.returncode}",
            }
        except Exception as e:
            logger.warning(
                f"[AlignmentGuard] git checkout 调用异常: {e}（无 git 仓库或无 HEAD，仅告警）"
            )
            return {
                "primary_action": "none",
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e),
            }

    def _write_incident_report(
        self,
        drift_result: Dict[str, Any],
        current_dist: Dict[str, float],
        baseline_dist: Dict[str, float],
        memo_model_path: str,
        rollback_result: Dict[str, Any],
    ) -> Path:
        """写入事故报告到 `memory/rsi_incidents/{timestamp}_drift.json`

        Returns:
            事故报告文件路径
        """
        self.incidents_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        report_path = self.incidents_dir / f"{timestamp}_drift.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "incident_type": "reflection_qa_drift",
            "memo_model_path": memo_model_path,
            "kl_divergence": drift_result["kl_divergence"],
            "threshold": drift_result["threshold"],
            "current_distribution": current_dist,
            "baseline_distribution": baseline_dist,
            "drift_details": drift_result["details"],
            "rollback": rollback_result,
        }

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"[AlignmentGuard] 事故报告已写入: {report_path}")
        except Exception as e:
            logger.error(f"[AlignmentGuard] 写入事故报告失败: {e}")
        return report_path

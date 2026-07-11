"""版本控制 - 追踪 Harness 的演化历史

管理 Harness 的代码版本、能力版本、对齐版本。
支持版本回滚、版本对比、演化分析。
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


# F2.3: panic_lock 持久化文件名（位于 versions_dir 同级或 project_root）
PANIC_LOCK_FILE = ".rsi_panic_lock"


class RollbackFailedError(Exception):
    """F2.1: rollback 失败时抛出。

    当 git revert / 文件写回 / 版本不存在等场景导致 rollback 无法将
    系统恢复到已知良好状态时，本异常被抛出。上层 SelfImprovementLoop
    捕获后调用 ``version_control.trigger_panic_lock`` 冻结 RSI 写入，
    直到人工介入清除 ``.rsi_panic_lock`` 文件。
    """


class PanicLockError(Exception):
    """F2.2: panic_lock 已激活时，RSI 写入操作被禁止。

    由 ``assert_not_locked`` 在 RSI 写入前调用时抛出，表明系统因
    rollback 失败已进入冻结状态，需要人工清除 panic_lock 文件后才能
    继续自改进。
    """


@dataclass
class HarnessVersion:
    """Harness 版本记录"""
    version_id: str
    timestamp: str
    parent_version: Optional[str]

    # 代码快照
    code_snapshot: Dict[str, str]  # {module_path: source_code}

    # 能力指标
    capability_score: float

    # 对齐状态
    alignment_status: str  # aligned | warning | critical

    # 变更摘要
    changes: List[Dict]  # [{"module": str, "type": str, "description": str}]

    # 元数据
    author: str  # "human" | "rsi" | "hybrid"
    commit_message: str


class VersionControl:
    """
    Harness 的版本控制系统

    职责：
    1. 保存每个版本的完整代码快照
    2. 支持版本回滚到任意历史版本
    3. 版本对比（能力变化、代码变化）
    4. 演化分析（能力增长曲线、代码复杂度趋势）
    """

    def __init__(self, panic_lock_path: Optional[Union[str, Path]] = None):
        self.versions_dir = Path("./memory/versions")
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.versions_dir / "index.json"
        self.versions: List[HarnessVersion] = []
        # F2.3: panic_lock 文件路径。默认放在 project_root（当前工作目录）
        # 下的 ``.rsi_panic_lock``；测试可通过 panic_lock_path 注入 tmp_path。
        if panic_lock_path is not None:
            self.panic_lock_file = Path(panic_lock_path)
        else:
            self.panic_lock_file = Path(PANIC_LOCK_FILE)
        self._load_index()

    def _load_index(self):
        """加载版本索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    self.versions = [HarnessVersion(**v) for v in data]
            except Exception as e:
                logger.warning(f"[VersionControl] 加载索引失败: {e}")

    def _save_index(self):
        """保存版本索引"""
        data = [
            {
                "version_id": v.version_id,
                "timestamp": v.timestamp,
                "parent_version": v.parent_version,
                "code_snapshot": v.code_snapshot,
                "capability_score": v.capability_score,
                "alignment_status": v.alignment_status,
                "changes": v.changes,
                "author": v.author,
                "commit_message": v.commit_message,
            }
            for v in self.versions
        ]

        with open(self.index_file, "w") as f:
            json.dump(data, f, indent=2)

    def commit(
        self,
        code_snapshot: Dict[str, str],
        capability_score: float,
        alignment_status: str,
        changes: List[Dict],
        author: str = "rsi",
        commit_message: str = "",
    ) -> str:
        """
        提交新版本

        Returns: version_id

        Raises:
            PanicLockError: F2.2 — panic_lock 已激活时拒绝写入
        """
        # F2.2: panic_lock 激活时禁止提交新版本
        self.assert_not_locked()
        version_id = f"v{len(self.versions) + 1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        parent = self.versions[-1].version_id if self.versions else None

        version = HarnessVersion(
            version_id=version_id,
            timestamp=datetime.utcnow().isoformat(),
            parent_version=parent,
            code_snapshot=code_snapshot,
            capability_score=capability_score,
            alignment_status=alignment_status,
            changes=changes,
            author=author,
            commit_message=commit_message,
        )

        self.versions.append(version)
        self._save_index()

        # 保存代码快照到文件
        snapshot_dir = self.versions_dir / version_id
        snapshot_dir.mkdir(exist_ok=True)
        for module_path, source in code_snapshot.items():
            file_path = snapshot_dir / f"{module_path.replace('.', '_')}.py"
            file_path.write_text(source, encoding="utf-8")

        logger.info(f"[VersionControl] 提交版本: {version_id} (得分: {capability_score:.3f})")
        return version_id

    def rollback(self, version_id: str) -> Dict[str, str]:
        """
        回滚到指定版本

        Returns: 该版本的代码快照

        Raises:
            RollbackFailedError: F2.1/F2.2 — 当版本不存在或文件写回失败时抛出，
                上层 SelfImprovementLoop 应捕获并调用 ``trigger_panic_lock``
                冻结 RSI 写入，等待人工介入。
        """
        version = next((v for v in self.versions if v.version_id == version_id), None)
        if not version:
            # F2.1: 版本不存在 —— rollback 失败，抛异常而非 ValueError
            logger.error(f"[VersionControl] rollback 失败：版本不存在: {version_id}")
            raise RollbackFailedError(f"版本不存在: {version_id}")

        # 恢复代码
        try:
            for module_path, source in version.code_snapshot.items():
                file_path = Path(module_path.replace(".", "/") + ".py")
                if file_path.exists():
                    file_path.write_text(source, encoding="utf-8")
        except (OSError, IOError) as e:
            # F2.1: 文件写回失败 —— rollback 失败，抛异常触发上层 panic_lock
            logger.error(
                f"[VersionControl] rollback 失败：文件写回异常 (version={version_id}): {e}"
            )
            raise RollbackFailedError(
                f"文件写回失败 (version={version_id}): {e}"
            ) from e

        logger.info(f"[VersionControl] 回滚到版本: {version_id}")
        return version.code_snapshot

    def compare_versions(self, v1: str, v2: str) -> Dict[str, any]:
        """对比两个版本"""
        version_1 = next((v for v in self.versions if v.version_id == v1), None)
        version_2 = next((v for v in self.versions if v.version_id == v2), None)

        if not version_1 or not version_2:
            raise ValueError("版本不存在")

        return {
            "capability_delta": version_2.capability_score - version_1.capability_score,
            "alignment_status_change": f"{version_1.alignment_status} -> {version_2.alignment_status}",
            "code_changes": len(version_2.changes),
            "author": f"{version_1.author} -> {version_2.author}",
        }

    def get_evolution_report(self) -> Dict[str, any]:
        """生成演化报告"""
        if not self.versions:
            return {}

        scores = [v.capability_score for v in self.versions]

        return {
            "total_versions": len(self.versions),
            "first_version": self.versions[0].version_id,
            "latest_version": self.versions[-1].version_id,
            "capability_trend": "up" if scores[-1] > scores[0] else "down" if scores[-1] < scores[0] else "stable",
            "capability_growth": scores[-1] - scores[0],
            "avg_improvement_per_version": (scores[-1] - scores[0]) / max(len(scores) - 1, 1),
            "alignment_history": [v.alignment_status for v in self.versions],
        }

    # ------------------------------------------------------------------ #
    # F2.2 / F2.3: panic_lock 机制
    # ------------------------------------------------------------------ #
    def trigger_panic_lock(self, reason: str) -> None:
        """F2.2: 触发 panic_lock —— 冻结 RSI 写入，持久化到 ``.rsi_panic_lock``。

        当 ``rollback`` 抛出 ``RollbackFailedError`` 时由上层调用，将
        panic 状态写入 ``self.panic_lock_file``。文件存在期间，所有 RSI
        写入操作（commit / apply_improvement 等）必须先调用
        ``assert_not_locked``，命中即抛 ``PanicLockError`` 阻断写入。

        文件内容为 JSON：``{"timestamp": iso, "reason": str}``，便于
        人工排查触发原因。

        Args:
            reason: 触发 panic_lock 的原因（通常是 RollbackFailedError 的
                字符串形式）
        """
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
        }
        try:
            self.panic_lock_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.error(
                f"[VersionControl] panic_lock 已触发：{reason} "
                f"(file={self.panic_lock_file})"
            )
        except (OSError, IOError) as e:
            # 写入失败是致命的：无法持久化 panic 状态意味着系统可能在
            # 重启后丢失冻结标记。仍然抛出 RollbackFailedError 让上层感知。
            logger.error(
                f"[VersionControl] panic_lock 文件写入失败: {e} "
                f"(file={self.panic_lock_file})"
            )
            raise RollbackFailedError(
                f"panic_lock 文件写入失败: {e}"
            ) from e

    def is_panic_locked(self) -> bool:
        """F2.3: 检查 panic_lock 是否已激活（文件是否存在）。

        Returns:
            True 如果 ``.rsi_panic_lock`` 文件存在
        """
        return self.panic_lock_file.exists()

    def clear_panic_lock(self, confirm: bool = False) -> None:
        """F2.3: 人工清除 panic_lock —— 恢复 RSI 写入能力。

        出于安全考虑，必须显式传 ``confirm=True`` 才会真正删除文件，
        避免误调用导致 panic 状态被静默清除。

        Args:
            confirm: 必须为 True 才执行删除

        Raises:
            ValueError: 未传 ``confirm=True`` 时抛出
        """
        if not confirm:
            raise ValueError(
                "clear_panic_lock 必须显式传 confirm=True 才能清除 panic_lock"
            )
        if self.panic_lock_file.exists():
            try:
                self.panic_lock_file.unlink()
                logger.info(
                    f"[VersionControl] panic_lock 已清除 (file={self.panic_lock_file})"
                )
            except (OSError, IOError) as e:
                logger.error(
                    f"[VersionControl] 清除 panic_lock 文件失败: {e}"
                )
                raise

    def assert_not_locked(self) -> None:
        """F2.2: RSI 写入前调用 —— 若 panic_lock 已激活则抛 ``PanicLockError``。

        在 ``SelfImprovementLoop.apply_improvement`` / ``commit`` 等所有
        RSI 写入路径的入口调用，确保系统在 rollback 失败后不再接受任何
        自改进写入，直到人工清除 ``.rsi_panic_lock``。

        Raises:
            PanicLockError: panic_lock 文件存在时抛出
        """
        if self.is_panic_locked():
            logger.error(
                "[VersionControl] RSI 写入被 panic_lock 阻断："
                "需人工清除 .rsi_panic_lock 后才能继续自改进"
            )
            raise PanicLockError(
                "RSI 写入被 panic_lock 阻断：系统已因 rollback 失败冻结，"
                "需人工清除 .rsi_panic_lock 文件后才能继续自改进"
            )

"""不可篡改审计链 - RSI 自改进的 SHA-256 链式日志

每次 RSI 自改进生成一条审计记录，记录间通过 SHA-256 链式哈希绑定。
任何篡改都会破坏链式哈希，触发 TamperDetectedError 并输出篡改位置。

链式算法（spec F3）：
- 第一条记录的 `prev_hash = "0" * 64`（全零，GENESIS_PREV_HASH）
- 每条记录的 `signature = SHA-256(prev_hash + action + target + diff + timestamp)`
- 下一条记录的 `prev_hash = 上一条记录的 signature`

日志文件格式：JSONL，每行一条 AuditRecord 的 JSON：
    {"prev_hash": "...", "action": "...", "target": "...",
     "diff": "...", "timestamp": "...", "signature": "..."}
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 创世 prev_hash：64 个 0，作为链首锚点
GENESIS_PREV_HASH = "0" * 64


class TamperDetectedError(Exception):
    """篡改检测异常

    当审计链被篡改时抛出，message 包含篡改位置索引。

    Attributes:
        message: 人类可读的错误描述（含篡改位置）
        tamper_index: 篡改位置索引（0-based），None 表示无法定位
    """

    def __init__(self, message: str, tamper_index: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.tamper_index = tamper_index

    def __str__(self) -> str:
        if self.tamper_index is not None:
            return f"{self.message} (tamper_index={self.tamper_index})"
        return self.message


@dataclass
class AuditRecord:
    """审计日志记录

    一条不可篡改审计记录，包含 SHA-256 链式哈希字段。

    Attributes:
        prev_hash: 上一条记录的 signature（首条为 GENESIS_PREV_HASH）
        action: RSI 动作类型（如 "modify_module", "rollback"）
        target: 操作目标（如模块路径）
        diff: 改动内容（diff 字符串或 JSON 序列化文本）
        timestamp: ISO8601 UTC 时间戳
        signature: 本条记录的 SHA-256(prev_hash + action + target + diff + timestamp)
    """

    prev_hash: str
    action: str
    target: str
    diff: str
    timestamp: str
    signature: str


def _compute_signature(
    prev_hash: str, action: str, target: str, diff: str, timestamp: str
) -> str:
    """计算记录签名：SHA-256(prev_hash + action + target + diff + timestamp)

    Args:
        prev_hash: 上一条记录的 signature
        action: 动作类型
        target: 目标
        diff: 改动
        timestamp: 时间戳

    Returns:
        64 字符十六进制 SHA-256 摘要
    """
    payload = prev_hash + action + target + diff + timestamp
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditTrail:
    """不可篡改审计链

    以 JSONL 格式持久化审计记录，每条记录通过 SHA-256 链式哈希绑定
    上一条记录的 signature。任何篡改都会破坏链式完整性。

    Usage:
        trail = AuditTrail("/path/to/audit.jsonl")
        record = trail.append("modify_module", "src.foo", "+def bar(): ...")
        if not trail.verify_chain():
            idx = trail.find_tamper()
            raise TamperDetectedError(f"chain tampered at {idx}", tamper_index=idx)
    """

    def __init__(self, log_file: str):
        """初始化审计链

        Args:
            log_file: 审计日志文件路径（JSONL 格式）。文件不存在时
                      由构造函数创建空文件；空文件视为合法初始状态。
        """
        self.log_file = Path(log_file)
        # 确保父目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        # 文件不存在则创建空文件
        if not self.log_file.exists():
            self.log_file.touch()

    def _read_records(self) -> List[AuditRecord]:
        """从日志文件读取全部记录

        空文件返回空列表；跳过空行；格式错误的行触发 ValueError。

        Returns:
            AuditRecord 列表（按追加顺序）

        Raises:
            ValueError: 某行不是合法 JSON 或缺字段时
        """
        records: List[AuditRecord] = []
        text = self.log_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"audit log line {lineno} is not valid JSON: {e}"
                ) from e
            records.append(
                AuditRecord(
                    prev_hash=obj["prev_hash"],
                    action=obj["action"],
                    target=obj["target"],
                    diff=obj["diff"],
                    timestamp=obj["timestamp"],
                    signature=obj["signature"],
                )
            )
        return records

    def append(self, action: str, target: str, diff: str) -> AuditRecord:
        """追加一条审计记录

        自动计算 prev_hash（上一条记录的 signature；链首为 GENESIS_PREV_HASH）
        与 signature（本条记录内容的 SHA-256）。以 append-only 方式追加一行
        JSON 到日志文件。

        Args:
            action: 动作类型
            target: 目标
            diff: 改动内容

        Returns:
            新追加的 AuditRecord
        """
        records = self._read_records()
        prev_hash = records[-1].signature if records else GENESIS_PREV_HASH
        timestamp = datetime.now(timezone.utc).isoformat()
        signature = _compute_signature(prev_hash, action, target, diff, timestamp)
        record = AuditRecord(
            prev_hash=prev_hash,
            action=action,
            target=target,
            diff=diff,
            timestamp=timestamp,
            signature=signature,
        )
        line = json.dumps(asdict(record), ensure_ascii=False)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        logger.info(
            f"[AuditTrail] append record: action={action} target={target} "
            f"signature={signature[:8]}..."
        )
        return record

    def verify_chain(self, raise_on_tamper: bool = False) -> bool:
        """校验整条审计链的完整性

        从首条记录开始依次验证：
        1. 首条记录的 prev_hash == GENESIS_PREV_HASH
        2. 每条记录的 signature == SHA-256(prev_hash + action + target + diff + timestamp)
        3. 第 i 条记录的 prev_hash == 第 i-1 条记录的 signature

        Args:
            raise_on_tamper: True 时检测到篡改抛出 TamperDetectedError

        Returns:
            True 如果链完整无篡改；False 如果存在篡改

        Raises:
            TamperDetectedError: 当 raise_on_tamper=True 且检测到篡改时，
                message 与 tamper_index 属性均包含篡改位置
        """
        records = self._read_records()
        prev_sig = GENESIS_PREV_HASH
        for i, rec in enumerate(records):
            # 1. prev_hash 链接校验
            if rec.prev_hash != prev_sig:
                msg = (
                    f"audit chain tampered at index {i}: "
                    f"prev_hash mismatch (expected {prev_sig[:8]}..., "
                    f"got {rec.prev_hash[:8]}...)"
                )
                if raise_on_tamper:
                    raise TamperDetectedError(msg, tamper_index=i)
                logger.warning(f"[AuditTrail] {msg}")
                return False
            # 2. signature 校验
            expected = _compute_signature(
                rec.prev_hash, rec.action, rec.target, rec.diff, rec.timestamp
            )
            if rec.signature != expected:
                msg = (
                    f"audit chain tampered at index {i}: "
                    f"signature mismatch (content altered)"
                )
                if raise_on_tamper:
                    raise TamperDetectedError(msg, tamper_index=i)
                logger.warning(f"[AuditTrail] {msg}")
                return False
            prev_sig = rec.signature
        return True

    def find_tamper(self) -> Optional[int]:
        """定位首个篡改位置

        检测顺序：
        1. prev_hash 链接断裂（首条 prev_hash != GENESIS，或后续
           prev_hash != 上一条 signature）
        2. signature 与内容不匹配

        Returns:
            首个被破坏记录的索引（0-based）；无篡改返回 None
        """
        records = self._read_records()
        prev_sig = GENESIS_PREV_HASH
        for i, rec in enumerate(records):
            if rec.prev_hash != prev_sig:
                return i
            expected = _compute_signature(
                rec.prev_hash, rec.action, rec.target, rec.diff, rec.timestamp
            )
            if rec.signature != expected:
                return i
            prev_sig = rec.signature
        return None

    def verify_audit_chain(self, raise_on_tamper: bool = False) -> bool:
        """verify_chain 的别名，对应 spec 中 verify_audit_chain() 接口"""
        return self.verify_chain(raise_on_tamper=raise_on_tamper)

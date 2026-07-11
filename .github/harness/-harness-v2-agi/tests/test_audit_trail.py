"""AuditTrail 不可篡改审计链测试

覆盖 Task F3.1-F3.5 的 5 个核心场景：
- 空日志初始化
- 追加 3 条记录后 verify_chain() 返回 True
- 篡改第 2 条记录的 diff 字段后 verify_chain() 返回 False
- find_tamper() 返回篡改位置索引 1
- verify_chain(raise_on_tamper=True) 抛出 TamperDetectedError
"""

import json
from pathlib import Path

import pytest

from src.consciousness.rsi.rsi_audit_trail import (
    AuditRecord,
    AuditTrail,
    GENESIS_PREV_HASH,
    TamperDetectedError,
    _compute_signature,
)


@pytest.fixture
def empty_trail(tmp_path):
    """空审计链（文件不存在，由构造函数创建空文件）"""
    log_file = tmp_path / "audit.jsonl"
    return AuditTrail(str(log_file))


@pytest.fixture
def trail_with_three_records(empty_trail):
    """已追加 3 条记录的审计链"""
    empty_trail.append("modify_module", "src.foo", "+def foo(): pass")
    empty_trail.append("modify_module", "src.bar", "+def bar(): pass")
    empty_trail.append("rollback", "src.foo", "-def foo(): pass")
    return empty_trail


def _tamper_record_field(trail: AuditTrail, index: int, field_name: str, new_value):
    """篡改指定记录的指定字段（不重新计算 signature）

    用 JSON 反序列化 → 改字段 → 重新序列化的方式覆写日志文件，
    模拟攻击者直接编辑日志文件的行为。
    """
    path = Path(trail.log_file)
    lines = path.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[index])
    obj[field_name] = new_value
    lines[index] = json.dumps(obj, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestEmptyTrail:
    """F3.5 用例 1：空日志初始化"""

    def test_empty_log_creates_file(self, empty_trail):
        """构造函数应创建空日志文件"""
        assert Path(empty_trail.log_file).exists()
        assert Path(empty_trail.log_file).read_text(encoding="utf-8") == ""

    def test_empty_log_verify_chain_returns_true(self, empty_trail):
        """空链视为合法初始状态（无记录即无篡改）"""
        assert empty_trail.verify_chain() is True

    def test_empty_log_find_tamper_returns_none(self, empty_trail):
        """空链无篡改位置"""
        assert empty_trail.find_tamper() is None


class TestAppendAndVerify:
    """F3.1-F3.3：append + verify_chain 正常路径"""

    def test_append_returns_audit_record(self, empty_trail):
        rec = empty_trail.append("modify_module", "src.foo", "+x")
        assert isinstance(rec, AuditRecord)
        assert rec.prev_hash == GENESIS_PREV_HASH
        assert rec.action == "modify_module"
        assert rec.target == "src.foo"
        assert rec.diff == "+x"
        assert rec.timestamp
        assert rec.signature

    def test_first_record_prev_hash_is_genesis(self, empty_trail):
        """首条记录的 prev_hash 必须是 64 个 0"""
        rec = empty_trail.append("a", "t", "d")
        assert rec.prev_hash == "0" * 64
        assert len(rec.prev_hash) == 64

    def test_signature_is_sha256_of_payload(self, empty_trail):
        """signature 必须等于 SHA-256(prev_hash + action + target + diff + timestamp)"""
        rec = empty_trail.append("a", "t", "d")
        expected = _compute_signature(
            rec.prev_hash, rec.action, rec.target, rec.diff, rec.timestamp
        )
        assert rec.signature == expected
        assert len(rec.signature) == 64

    def test_subsequent_record_prev_hash_is_previous_signature(self, empty_trail):
        """第 N 条记录的 prev_hash == 第 N-1 条记录的 signature"""
        r1 = empty_trail.append("a1", "t1", "d1")
        r2 = empty_trail.append("a2", "t2", "d2")
        r3 = empty_trail.append("a3", "t3", "d3")
        assert r2.prev_hash == r1.signature
        assert r3.prev_hash == r2.signature

    def test_verify_chain_returns_true_after_three_appends(self, trail_with_three_records):
        """F3.5 用例 2：追加 3 条记录后 verify_chain() 返回 True"""
        assert trail_with_three_records.verify_chain() is True

    def test_verify_audit_chain_alias_returns_true(self, trail_with_three_records):
        """spec 中 verify_audit_chain() 等价于 verify_chain()"""
        assert trail_with_three_records.verify_audit_chain() is True

    def test_persistence_across_instances(self, trail_with_three_records):
        """重新加载文件后链仍可校验通过"""
        log_path = trail_with_three_records.log_file
        new_trail = AuditTrail(str(log_path))
        assert new_trail.verify_chain() is True

    def test_records_persisted_as_jsonl(self, trail_with_three_records):
        """日志文件应为 JSONL 格式，每行一条 AuditRecord JSON"""
        text = Path(trail_with_three_records.log_file).read_text(encoding="utf-8")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            for field in ("prev_hash", "action", "target", "diff", "timestamp", "signature"):
                assert field in obj


class TestTamperDetection:
    """F3.4-F3.5：篡改检测"""

    def test_tamper_diff_breaks_chain(self, trail_with_three_records):
        """F3.5 用例 3：篡改第 2 条记录（index=1）的 diff 后 verify_chain() 返回 False"""
        _tamper_record_field(trail_with_three_records, 1, "diff", "TAMPERED_CONTENT")
        assert trail_with_three_records.verify_chain() is False

    def test_find_tamper_returns_tampered_index(self, trail_with_three_records):
        """F3.5 用例 4：find_tamper() 返回篡改位置索引 1"""
        _tamper_record_field(trail_with_three_records, 1, "diff", "TAMPERED_CONTENT")
        assert trail_with_three_records.find_tamper() == 1

    def test_tamper_first_record_prev_hash(self, trail_with_three_records):
        """篡改首条 prev_hash 应在 index=0 检出"""
        _tamper_record_field(trail_with_three_records, 0, "prev_hash", "1" * 64)
        assert trail_with_three_records.find_tamper() == 0

    def test_tamper_action_field(self, trail_with_three_records):
        """篡改 action 字段应被检出"""
        _tamper_record_field(trail_with_three_records, 1, "action", "malicious_action")
        assert trail_with_three_records.verify_chain() is False
        assert trail_with_three_records.find_tamper() == 1

    def test_tamper_signature_field(self, trail_with_three_records):
        """篡改 signature 字段应在对应索引检出"""
        _tamper_record_field(trail_with_three_records, 2, "signature", "deadbeef" * 8)
        assert trail_with_three_records.find_tamper() == 2

    def test_verify_chain_raises_tamper_detected_error(self, trail_with_three_records):
        """F3.5 用例 5：verify_chain(raise_on_tamper=True) 抛出 TamperDetectedError"""
        _tamper_record_field(trail_with_three_records, 1, "diff", "TAMPERED_CONTENT")
        with pytest.raises(TamperDetectedError) as exc_info:
            trail_with_three_records.verify_chain(raise_on_tamper=True)
        # message 必须包含篡改位置
        err_str = str(exc_info.value)
        assert "1" in err_str
        # tamper_index 属性也必须指向篡改位置
        assert exc_info.value.tamper_index == 1

    def test_no_tamper_no_raise_when_raise_on_tamper_true(self, trail_with_three_records):
        """未篡改时 raise_on_tamper=True 也不应抛异常"""
        result = trail_with_three_records.verify_chain(raise_on_tamper=True)
        assert result is True

    def test_tamper_breaks_subsequent_chain(self, trail_with_three_records):
        """篡改第 2 条记录后，第 3 条的 prev_hash 仍指向旧 signature，
        因此 find_tamper 应在 index=1 检出（首个断裂点）"""
        _tamper_record_field(trail_with_three_records, 1, "diff", "TAMPERED")
        # 首个断裂在 index=1（其 signature 不再匹配内容）
        assert trail_with_three_records.find_tamper() == 1


class TestGenesisHash:
    """GENESIS_PREV_HASH 常量正确性"""

    def test_genesis_hash_value(self):
        assert GENESIS_PREV_HASH == "0" * 64
        assert len(GENESIS_PREV_HASH) == 64

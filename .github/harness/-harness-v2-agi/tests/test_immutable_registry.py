"""G2: 不可变哈希注册表测试

覆盖 Task G2.1-G2.4 的 5 个核心场景：
- compute_file_hash 返回 64 字符 hex 串
- compute_registry_hashes 返回 5 个文件的哈希
- save_registry_snapshot + verify_immutability 一致时返回 True
- 修改任一文件后 verify_immutability 抛 IntegrityError
- assert_immutability_at_startup 在篡改时抛 IntegrityError

测试隔离策略：用 tmp_path 与 shutil.copy 复制真实项目文件到临时目录，
在临时目录内修改文件后校验，不影响真实项目代码。
"""

import json
import shutil
from pathlib import Path

import pytest

from src.consciousness.rsi.guards.alignment_guard import (
    EXPECTED_HASHES,
    IMMUTABLE_HASH_REGISTRY,
    IntegrityError,
    assert_immutability_at_startup,
    compute_file_hash,
    compute_registry_hashes,
    save_registry_snapshot,
    verify_immutability,
)


# ---------------------------------------------------------------------- #
# 辅助 fixture
# ---------------------------------------------------------------------- #
@pytest.fixture
def fake_project_root(tmp_path: Path) -> Path:
    """在 tmp_path 下复制真实项目核心文件，构造伪项目根目录

    复制 IMMUTABLE_HASH_REGISTRY 中所有文件到 tmp_path 对应路径，
    使 compute_registry_hashes(tmp_path) 能正常工作。
    """
    src_root = Path(__file__).parent.parent  # 真实项目根目录
    for rel in IMMUTABLE_HASH_REGISTRY:
        src = src_root / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
    return tmp_path


@pytest.fixture
def snapshot_file(fake_project_root: Path) -> Path:
    """生成基准快照 JSON 文件"""
    snap = fake_project_root / "snapshot.json"
    save_registry_snapshot(str(fake_project_root), str(snap))
    return snap


# ---------------------------------------------------------------------- #
# G2.2 用例 1：compute_file_hash 返回 64 字符 hex 串
# ---------------------------------------------------------------------- #
class TestComputeFileHash:
    def test_returns_64_char_hex_string(self, tmp_path: Path):
        """compute_file_hash 返回 64 字符小写 hex 字符串（SHA-256）"""
        f = tmp_path / "sample.txt"
        f.write_text("hello world", encoding="utf-8")

        h = compute_file_hash(str(f))

        assert isinstance(h, str)
        assert len(h) == 64
        # 全部为小写 hex 字符
        assert all(c in "0123456789abcdef" for c in h)

    def test_known_value_matches_sha256(self, tmp_path: Path):
        """compute_file_hash 与已知 SHA-256 值一致"""
        f = tmp_path / "sample.txt"
        f.write_text("hello world", encoding="utf-8")

        # "hello world" 的 SHA-256 = b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
        assert compute_file_hash(str(f)) == (
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        )

    def test_empty_file_hash(self, tmp_path: Path):
        """空文件的 SHA-256 哈希值正确"""
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        # 空字符串 SHA-256 = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        assert compute_file_hash(str(f)) == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_different_content_different_hash(self, tmp_path: Path):
        """不同内容产生不同哈希"""
        f1 = tmp_path / "a.txt"
        f1.write_text("content A", encoding="utf-8")
        f2 = tmp_path / "b.txt"
        f2.write_text("content B", encoding="utf-8")

        assert compute_file_hash(str(f1)) != compute_file_hash(str(f2))


# ---------------------------------------------------------------------- #
# G2.2 用例 2：compute_registry_hashes 返回 5 个文件的哈希
# ---------------------------------------------------------------------- #
class TestComputeRegistryHashes:
    def test_returns_five_hashes(self, fake_project_root: Path):
        """compute_registry_hashes 返回 5 个文件的哈希"""
        hashes = compute_registry_hashes(str(fake_project_root))

        assert isinstance(hashes, dict)
        assert len(hashes) == 5
        # 键与 IMMUTABLE_HASH_REGISTRY 一致
        assert set(hashes.keys()) == set(IMMUTABLE_HASH_REGISTRY)

    def test_all_hashes_are_64_char_hex(self, fake_project_root: Path):
        """所有哈希值都是 64 字符 hex 串"""
        hashes = compute_registry_hashes(str(fake_project_root))
        for rel, h in hashes.items():
            assert len(h) == 64, f"{rel} 哈希长度不是 64: {len(h)}"
            assert all(c in "0123456789abcdef" for c in h), (
                f"{rel} 哈希含非 hex 字符: {h}"
            )

    def test_hashes_match_individual_compute(self, fake_project_root: Path):
        """批量哈希与逐个 compute_file_hash 结果一致"""
        hashes = compute_registry_hashes(str(fake_project_root))
        for rel in IMMUTABLE_HASH_REGISTRY:
            individual = compute_file_hash(str(fake_project_root / rel))
            assert hashes[rel] == individual, (
                f"{rel} 批量哈希与单独计算不一致"
            )


# ---------------------------------------------------------------------- #
# G2.2/G2.3 用例 3：save_registry_snapshot + verify_immutability 一致时返回 True
# ---------------------------------------------------------------------- #
class TestSnapshotVerifyConsistency:
    def test_save_and_verify_returns_true(self, fake_project_root: Path, snapshot_file: Path):
        """保存快照后立即校验，应返回 True（哈希一致）"""
        result = verify_immutability(str(fake_project_root), snapshot_path=str(snapshot_file))
        assert result is True

    def test_snapshot_file_format(self, fake_project_root: Path, snapshot_file: Path):
        """快照文件格式正确：含 version / base_dir / created_at / files"""
        data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        assert data["version"] == 1
        assert "base_dir" in data
        assert "created_at" in data
        assert "files" in data
        assert len(data["files"]) == 5

    def test_verify_without_snapshot_uses_expected_hashes_empty(self, fake_project_root: Path):
        """EXPECTED_HASHES 为空时，不传 snapshot_path 应抛 IntegrityError 提示先生成快照"""
        # EXPECTED_HASHES 默认为空（代码内嵌），未生成快照前应提示
        with pytest.raises(IntegrityError, match="No expected hashes available"):
            verify_immutability(str(fake_project_root), snapshot_path=None)


# ---------------------------------------------------------------------- #
# G2.4 用例 4：修改任一文件后 verify_immutability 抛 IntegrityError
# ---------------------------------------------------------------------- #
class TestTamperDetection:
    def test_modify_one_file_raises_integrity_error(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """修改任一注册表文件后 verify_immutability 抛 IntegrityError"""
        # 篡改第一个文件：追加恶意代码
        victim = fake_project_root / IMMUTABLE_HASH_REGISTRY[0]
        original = victim.read_text(encoding="utf-8")
        victim.write_text(original + "\n# INJECTED BY ATTACKER\n", encoding="utf-8")

        with pytest.raises(IntegrityError) as exc_info:
            verify_immutability(str(fake_project_root), snapshot_path=str(snapshot_file))

        # 错误消息包含被篡改的文件路径
        assert IMMUTABLE_HASH_REGISTRY[0] in str(exc_info.value)
        assert "tampered" in str(exc_info.value).lower()

    def test_modify_different_file_raises_integrity_error(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """修改第 4 个文件（src/config.py）后也应抛 IntegrityError"""
        victim = fake_project_root / IMMUTABLE_HASH_REGISTRY[3]  # src/config.py
        original = victim.read_text(encoding="utf-8")
        victim.write_text(original + "\n# EVIL MODIFICATION\n", encoding="utf-8")

        with pytest.raises(IntegrityError) as exc_info:
            verify_immutability(str(fake_project_root), snapshot_path=str(snapshot_file))

        assert IMMUTABLE_HASH_REGISTRY[3] in str(exc_info.value)

    def test_modify_all_files_raises_integrity_error(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """修改全部 5 个文件后抛 IntegrityError，消息含 5 个文件"""
        for rel in IMMUTABLE_HASH_REGISTRY:
            victim = fake_project_root / rel
            original = victim.read_text(encoding="utf-8")
            victim.write_text(original + "\n# TAMPERED\n", encoding="utf-8")

        with pytest.raises(IntegrityError) as exc_info:
            verify_immutability(str(fake_project_root), snapshot_path=str(snapshot_file))

        msg = str(exc_info.value)
        assert "5 file(s) tampered" in msg
        for rel in IMMUTABLE_HASH_REGISTRY:
            assert rel in msg

    def test_message_includes_hash_prefix(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """IntegrityError 消息含期望/实际哈希前 8 位（便于人工诊断）"""
        victim = fake_project_root / IMMUTABLE_HASH_REGISTRY[0]
        original = victim.read_text(encoding="utf-8")
        victim.write_text(original + "\n# TAMPER\n", encoding="utf-8")

        with pytest.raises(IntegrityError) as exc_info:
            verify_immutability(str(fake_project_root), snapshot_path=str(snapshot_file))

        # 消息中应包含 "expected" 与 "got" 关键字
        msg = str(exc_info.value)
        assert "expected" in msg.lower()
        assert "got" in msg.lower()


# ---------------------------------------------------------------------- #
# G2.3 用例 5：assert_immutability_at_startup 在篡改时抛 IntegrityError
# ---------------------------------------------------------------------- #
class TestAssertImmutabilityAtStartup:
    def test_startup_passes_when_consistent(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """未篡改时 assert_immutability_at_startup 正常返回（无异常）"""
        # 不抛异常即通过
        assert_immutability_at_startup(
            base_dir=str(fake_project_root),
            snapshot_path=str(snapshot_file),
        )

    def test_startup_raises_integrity_error_when_tampered(
        self, fake_project_root: Path, snapshot_file: Path
    ):
        """篡改后 assert_immutability_at_startup 抛 IntegrityError"""
        victim = fake_project_root / IMMUTABLE_HASH_REGISTRY[2]  # meta_harness.py
        original = victim.read_text(encoding="utf-8")
        victim.write_text(original + "\n# ATTACKER INJECTED CODE\n", encoding="utf-8")

        with pytest.raises(IntegrityError) as exc_info:
            assert_immutability_at_startup(
                base_dir=str(fake_project_root),
                snapshot_path=str(snapshot_file),
            )

        assert IMMUTABLE_HASH_REGISTRY[2] in str(exc_info.value)

    def test_startup_raises_when_snapshot_missing(self, fake_project_root: Path):
        """快照文件不存在时抛 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            assert_immutability_at_startup(
                base_dir=str(fake_project_root),
                snapshot_path=str(fake_project_root / "nonexistent.json"),
            )


# ---------------------------------------------------------------------- #
# 回归保护
# ---------------------------------------------------------------------- #
class TestRegistryConstants:
    def test_registry_contains_five_files(self):
        """IMMUTABLE_HASH_REGISTRY 含 5 个核心文件路径"""
        assert len(IMMUTABLE_HASH_REGISTRY) == 5

    def test_registry_contains_expected_paths(self):
        """注册表内容与 spec 要求的 5 个文件一致"""
        expected = {
            "src/consciousness/rsi/guards/alignment_guard.py",
            "src/consciousness/rsi/guards/capability_evaluator.py",
            "src/consciousness/rsi/meta_harness/meta_harness.py",
            "src/config.py",
            "src/main.py",
        }
        assert set(IMMUTABLE_HASH_REGISTRY) == expected

    def test_expected_hashes_default_empty(self):
        """EXPECTED_HASHES 默认为空（首次运行需先生成快照）"""
        assert EXPECTED_HASHES == {}

    def test_integrity_error_is_exception_subclass(self):
        """IntegrityError 是 Exception 子类"""
        assert issubclass(IntegrityError, Exception)

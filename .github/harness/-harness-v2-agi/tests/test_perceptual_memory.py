"""感知记忆测试 - 长期缓存爬虫感知结果"""

from datetime import datetime, timedelta

import pytest

from src.api.models import CrawlerSnapshot
from src.consciousness.perception.perceptual_memory import PerceptualMemory


@pytest.fixture
def memory(tmp_path, monkeypatch):
    """使用临时目录的 PerceptualMemory（避免污染项目根目录）"""
    # 切换工作目录到 tmp_path，使 ./memory/ 创建在临时目录
    monkeypatch.chdir(tmp_path)
    mem = PerceptualMemory(design_memory=None)
    memory_file = tmp_path / "perceptual_memory.json"
    mem.memory_file = memory_file
    return mem


@pytest.fixture
def sample_snapshot():
    return CrawlerSnapshot(
        url="https://example.com",
        tech_stack=[{"name": "next", "confidence": 0.99}],
        design_tokens=[],
        content_structure={"type": "saas"},
        layout_analysis={"depth": 5},
        fingerprint="abc123",
        crawled_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_store_and_get(memory, sample_snapshot):
    """存储后能读取"""
    await memory.store_perception("https://example.com", sample_snapshot)
    retrieved = await memory.get_perception("https://example.com")
    assert retrieved is not None
    assert retrieved.url == "https://example.com"
    assert retrieved.fingerprint == "abc123"


@pytest.mark.asyncio
async def test_get_nonexistent(memory):
    """不存在的 URL 返回 None"""
    result = await memory.get_perception("https://nonexistent.com")
    assert result is None


@pytest.mark.asyncio
async def test_has_fresh_perception_true(memory, sample_snapshot):
    """新鲜感知返回 True"""
    await memory.store_perception("https://example.com", sample_snapshot)
    assert await memory.has_fresh_perception("https://example.com") is True


@pytest.mark.asyncio
async def test_has_fresh_perception_false(memory):
    """无感知返回 False"""
    assert await memory.has_fresh_perception("https://nonexistent.com") is False


@pytest.mark.asyncio
async def test_expired_returns_none(memory, sample_snapshot):
    """过期返回 None"""
    await memory.store_perception("https://example.com", sample_snapshot)
    # 手动设置过期
    entry = memory._load_via_file("https://example.com")
    assert entry is not None
    entry["expires_at"] = (datetime.utcnow() - timedelta(days=1)).isoformat()
    memory._store_via_file("https://example.com", entry)
    result = await memory.get_perception("https://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_deduplicate_same_fingerprint(memory, sample_snapshot):
    """相同指纹返回 True 并刷新 TTL"""
    await memory.store_perception("https://example.com", sample_snapshot)
    result = await memory.deduplicate("https://example.com", "abc123")
    assert result is True


@pytest.mark.asyncio
async def test_deduplicate_different_fingerprint(memory, sample_snapshot):
    """不同指纹返回 False"""
    await memory.store_perception("https://example.com", sample_snapshot)
    result = await memory.deduplicate("https://example.com", "different_fp")
    assert result is False


@pytest.mark.asyncio
async def test_deduplicate_nonexistent(memory):
    """无缓存时 deduplicate 返回 False"""
    result = await memory.deduplicate("https://nonexistent.com", "any_fp")
    assert result is False


@pytest.mark.asyncio
async def test_url_normalization(memory, sample_snapshot):
    """URL 标准化等价性（大小写、尾斜杠、http/https 等价）"""
    await memory.store_perception("https://Example.com/Page/", sample_snapshot)
    # 不同大小写和尾斜杠应命中同一缓存
    assert await memory.has_fresh_perception("http://example.com/Page") is True


@pytest.mark.asyncio
async def test_custom_ttl(memory, sample_snapshot):
    """自定义 TTL"""
    await memory.store_perception(
        "https://example.com", sample_snapshot, ttl=1
    )
    # 1 天 TTL 应该仍然新鲜
    assert await memory.has_fresh_perception("https://example.com") is True


@pytest.mark.asyncio
async def test_store_preserves_tech_stack(memory, sample_snapshot):
    """存储后能恢复 tech_stack"""
    await memory.store_perception("https://example.com", sample_snapshot)
    retrieved = await memory.get_perception("https://example.com")
    assert retrieved is not None
    assert len(retrieved.tech_stack) == 1
    assert retrieved.tech_stack[0]["name"] == "next"


@pytest.mark.asyncio
async def test_deduplicate_refreshes_ttl(memory, sample_snapshot):
    """deduplicate 命中时刷新 TTL"""
    await memory.store_perception("https://example.com", sample_snapshot)
    # 设置过期
    entry = memory._load_via_file("https://example.com")
    entry["expires_at"] = (datetime.utcnow() - timedelta(days=10)).isoformat()
    memory._store_via_file("https://example.com", entry)

    # 此时已过期
    assert await memory.has_fresh_perception("https://example.com") is False

    # deduplicate 应刷新 TTL
    await memory.deduplicate("https://example.com", "abc123")
    assert await memory.has_fresh_perception("https://example.com") is True


def test_hash_url_consistency():
    """URL 哈希一致性（不依赖实例）"""
    # _hash_url 是实例方法但仅依赖 URL 字符串
    mem1 = PerceptualMemory.__new__(PerceptualMemory)
    mem1.ttl_days = 7
    # 直接调用内部哈希方法（不触发 __init__ 副作用）
    # 通过实际实例测试更稳定
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmp:
        import pathlib

        mem = PerceptualMemory(design_memory=None)
        mem.memory_file = pathlib.Path(tmp) / "mem.json"

        h1 = mem._hash_url("https://Example.com/Page/")
        h2 = mem._hash_url("http://example.com/Page")
        h3 = mem._hash_url("HTTPS://EXAMPLE.COM/PAGE/")
        assert h1 == h2 == h3

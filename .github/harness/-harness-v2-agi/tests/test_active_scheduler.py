"""主动感知调度器测试"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.models import CrawlerSnapshot
from src.consciousness.perception.active_scheduler import (
    ActivePerceptionScheduler,
)


@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    snapshot = CrawlerSnapshot(
        url="https://stripe.com",
        tech_stack=[{"name": "next", "confidence": 0.99}],
        design_tokens=[],
        content_structure={"type": "saas"},
        layout_analysis={
            "depth": 5,
            "grid_count": 1,
            "flex_count": 2,
            "element_density": 0.5,
        },
        fingerprint="abc",
        crawled_at=datetime.utcnow(),
    )
    signal = MagicMock()
    crawler.perceive = AsyncMock(return_value=(snapshot, signal))
    return crawler


@pytest.fixture
def mock_memory():
    memory = AsyncMock()
    memory.has_fresh_perception = AsyncMock(return_value=False)
    memory.get_perception = AsyncMock(return_value=None)
    memory.store_perception = AsyncMock(return_value=None)
    return memory


@pytest.mark.asyncio
async def test_should_crawl_memory_hit(mock_crawler, mock_memory):
    """记忆命中跳过"""
    mock_memory.has_fresh_perception = AsyncMock(return_value=True)
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )

    decision = await scheduler.should_crawl(
        "https://example.com", {"task": "test"}
    )
    assert decision["should_crawl"] is False
    assert decision["reason"] == "memory_hit"
    assert decision["memory_hit"] is True


@pytest.mark.asyncio
async def test_should_crawl_force_realtime(mock_crawler, mock_memory):
    """实时性强制爬取"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )

    decision = await scheduler.should_crawl(
        "https://example.com",
        {"task": "competitor analysis realtime"},
    )
    assert decision["should_crawl"] is True
    assert decision["reason"] == "force_realtime"


@pytest.mark.asyncio
async def test_should_crawl_force_realtime_chinese(mock_crawler, mock_memory):
    """中文实时关键词触发爬取"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )

    decision = await scheduler.should_crawl(
        "https://example.com",
        {"task": "需要 竞品 实时数据"},
    )
    assert decision["should_crawl"] is True
    assert decision["reason"] == "force_realtime"


@pytest.mark.asyncio
async def test_should_crawl_high_relevance(mock_crawler, mock_memory):
    """相关性主动爬取（URL 与任务有重叠词）"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )
    # relevance("https://stripe.com", {"task": "replicate stripe landing page"})
    # jaccard = 1/5 = 0.2, 加权后 = 0.4
    # 默认阈值 0.8 太高，下调到 0.4 使其触发
    scheduler.relevance_threshold = 0.4

    decision = await scheduler.should_crawl(
        "https://stripe.com",
        {"task": "replicate stripe landing page"},
    )
    assert decision["should_crawl"] is True
    assert decision["reason"] in ["high_relevance", "force_realtime"]
    assert decision["reason"] == "high_relevance"


@pytest.mark.asyncio
async def test_should_crawl_low_relevance(mock_crawler, mock_memory):
    """低相关性不爬取"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )
    scheduler.relevance_threshold = 0.99  # 极高阈值

    decision = await scheduler.should_crawl(
        "https://unrelated.com", {"task": "build blog"}
    )
    assert decision["should_crawl"] is False
    assert decision["reason"] == "low_relevance"


@pytest.mark.asyncio
async def test_should_crawl_no_task_context(mock_crawler, mock_memory):
    """无任务上下文默认爬取"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )

    decision = await scheduler.should_crawl("https://example.com", None)
    assert decision["should_crawl"] is True
    assert decision["reason"] == "no_task_context"


def test_relevance_returns_float():
    """relevance 返回 0-1 之间浮点数"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    score = scheduler.relevance(
        "https://example.com", {"task": "example"}
    )
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_relevance_high_overlap():
    """高重叠关键词应返回较高分"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    # URL 与任务完全重合
    score = scheduler.relevance(
        "https://example.com",
        {"task": "example"},
    )
    # jaccard = 1/2 = 0.5, 加权后 = 1.0
    assert score >= 0.5


def test_relevance_no_overlap():
    """无重叠关键词应返回 0"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    score = scheduler.relevance(
        "https://unrelated.com",
        {"task": "completely different task"},
    )
    assert score == 0.0


def test_compare_perceptions_empty():
    """空列表返回空结果"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    result = scheduler.compare_perceptions([])
    assert result["common_tech_stack"] == []
    assert result["avg_layout_complexity"] == 0.0
    assert result["content_types"] == {}
    assert result["differences"] == []


def test_compare_perceptions_finds_common():
    """找出共同模式"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    snapshots = [
        {
            "url": "a",
            "snapshot": CrawlerSnapshot(
                url="a",
                tech_stack=[{"name": "react"}, {"name": "tailwind"}],
                design_tokens=[],
                content_structure={"type": "saas"},
                layout_analysis={"depth": 5, "element_density": 0.5},
                fingerprint="a",
                crawled_at=datetime.utcnow(),
            ),
        },
        {
            "url": "b",
            "snapshot": CrawlerSnapshot(
                url="b",
                tech_stack=[{"name": "react"}, {"name": "next"}],
                design_tokens=[],
                content_structure={"type": "saas"},
                layout_analysis={"depth": 6, "element_density": 0.6},
                fingerprint="b",
                crawled_at=datetime.utcnow(),
            ),
        },
    ]
    result = scheduler.compare_perceptions(snapshots)
    assert "react" in result["common_tech_stack"]
    assert result["content_types"].get("saas") == 2
    assert result["avg_layout_complexity"] > 0


def test_compare_perceptions_filters_none():
    """snapshot 为 None 的项被过滤"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    snapshots = [
        {"url": "a", "snapshot": None, "source": "failed"},
        {
            "url": "b",
            "snapshot": CrawlerSnapshot(
                url="b",
                tech_stack=[{"name": "react"}],
                design_tokens=[],
                content_structure={"type": "blog"},
                layout_analysis={"depth": 3, "element_density": 0.3},
                fingerprint="b",
                crawled_at=datetime.utcnow(),
            ),
        },
    ]
    result = scheduler.compare_perceptions(snapshots)
    assert result["common_tech_stack"] == ["react"]
    assert result["content_types"].get("blog") == 1


@pytest.mark.asyncio
async def test_run_active_perception_empty_targets(mock_crawler, mock_memory):
    """空目标列表返回空结果"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )
    result = await scheduler.run_active_perception({"targets": []})
    assert result == []


@pytest.mark.asyncio
async def test_run_active_perception_crawls(mock_crawler, mock_memory):
    """主动感知循环：调用 crawler.perceive 并存入 memory"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )

    result = await scheduler.run_active_perception(
        {"targets": ["https://stripe.com"], "task": "realtime analysis"}
    )
    assert len(result) == 1
    assert result[0]["source"] == "fresh_crawl"
    assert result[0]["snapshot"] is not None
    # 爬虫应被调用
    mock_crawler.perceive.assert_called_once_with("https://stripe.com")
    # 存储应被调用
    mock_memory.store_perception.assert_called_once()


@pytest.mark.asyncio
async def test_run_active_perception_memory_hit(mock_crawler, mock_memory):
    """主动感知循环：记忆命中时跳过爬取"""
    mock_memory.has_fresh_perception = AsyncMock(return_value=True)
    mock_snapshot = CrawlerSnapshot(
        url="https://stripe.com",
        tech_stack=[],
        design_tokens=[],
        content_structure={},
        layout_analysis={},
        fingerprint="cached",
        crawled_at=datetime.utcnow(),
    )
    mock_memory.get_perception = AsyncMock(return_value=mock_snapshot)

    scheduler = ActivePerceptionScheduler(
        crawler_organ=mock_crawler, perceptual_memory=mock_memory
    )
    result = await scheduler.run_active_perception(
        {"targets": ["https://stripe.com"], "task": "test"}
    )
    assert len(result) == 1
    assert result[0]["source"] == "memory"
    # 爬虫不应被调用
    mock_crawler.perceive.assert_not_called()


def test_requires_realtime_keywords():
    """实时关键词检测（关键词：realtime/实时/竞品/competitor/latest/最新/current）"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    # 英文关键词
    assert scheduler._requires_realtime({"task": "realtime check"}) is True
    assert scheduler._requires_realtime({"task": "competitor analysis"}) is True
    assert scheduler._requires_realtime({"task": "latest news"}) is True
    assert scheduler._requires_realtime({"task": "current status"}) is True
    # 中文关键词
    assert scheduler._requires_realtime({"task": "需要实时数据"}) is True
    assert scheduler._requires_realtime({"task": "竞品对比分析"}) is True
    assert scheduler._requires_realtime({"task": "获取最新数据"}) is True
    # 非实时任务
    assert scheduler._requires_realtime({"task": "build a blog"}) is False
    assert scheduler._requires_realtime({"task": "design a landing page"}) is False


def test_extract_keywords_strips_url_prefix():
    """关键词提取移除 URL scheme 和域名后缀"""
    scheduler = ActivePerceptionScheduler(
        crawler_organ=None, perceptual_memory=None
    )
    keywords = scheduler._extract_keywords("https://www.example.com/page")
    assert "example" in keywords
    assert "page" in keywords
    # 域名后缀是停用词
    assert "com" not in keywords
    assert "www" not in keywords
    assert "https" not in keywords

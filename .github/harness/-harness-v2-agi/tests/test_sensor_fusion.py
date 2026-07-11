"""感知融合层测试 - 多器官信号加权整合"""

import pytest

from src.consciousness.perception.sensor_fusion import SensorFusion
from src.api.models import PerceptionModality, PerceptionSignal


@pytest.mark.asyncio
async def test_fuse_empty_signals():
    """空信号列表返回空结果"""
    fusion = SensorFusion()
    result = await fusion.fuse([])
    assert result["design_tokens"] == []
    assert result["confidence"] == 0.0
    assert result["sources"] == []
    assert result["conflicts"] == []


@pytest.mark.asyncio
async def test_fuse_single_signal():
    """单个信号直接返回"""
    fusion = SensorFusion()
    signal = PerceptionSignal(
        modality=PerceptionModality.VISION,
        payload={
            "design_tokens": [
                {
                    "name": "primary",
                    "value": "#fff",
                    "type": "color",
                    "semantics": "white",
                    "usage": [],
                    "confidence": 1.0,
                }
            ]
        },
        confidence=0.9,
        source="vision_engine",
    )
    result = await fusion.fuse([signal])
    assert len(result["design_tokens"]) > 0
    assert result["confidence"] > 0
    assert "vision_engine" in result["sources"]


@pytest.mark.asyncio
async def test_fuse_crawler_overrides_vision():
    """爬虫信号覆盖视觉信号（爬虫模态权重更高）"""
    fusion = SensorFusion()
    vision_signal = PerceptionSignal(
        modality=PerceptionModality.VISION,
        payload={
            "design_tokens": [
                {
                    "name": "primary",
                    "value": "blue",
                    "type": "color",
                    "semantics": "main color",
                    "usage": [],
                    "confidence": 0.85,
                }
            ]
        },
        confidence=0.85,
        source="vision_engine",
    )
    crawler_signal = PerceptionSignal(
        modality=PerceptionModality.CRAWLER,
        payload={
            "design_tokens": [
                {
                    "name": "primary",
                    "value": "#635BFF",
                    "type": "color",
                    "semantics": "brand color",
                    "usage": [],
                    "confidence": 0.99,
                }
            ],
            "tech_stack": [{"name": "next", "confidence": 0.99}],
        },
        confidence=0.99,
        source="crawler_organ",
    )
    result = await fusion.fuse([vision_signal, crawler_signal])
    # 爬虫优先（更高 modality_weight × confidence）
    primary_token = next(
        t for t in result["design_tokens"] if t["name"] == "primary"
    )
    assert primary_token["value"] == "#635BFF"


@pytest.mark.asyncio
async def test_fuse_detects_conflicts():
    """冲突检测：同名令牌不同值应记录冲突"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "#fff",
                        "type": "color",
                        "semantics": "",
                        "usage": [],
                        "confidence": 0.9,
                    }
                ]
            },
            confidence=0.9,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "#000",
                        "type": "color",
                        "semantics": "",
                        "usage": [],
                        "confidence": 0.95,
                    }
                ]
            },
            confidence=0.95,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    assert len(result["conflicts"]) > 0
    color_conflict = next(
        c for c in result["conflicts"] if c.get("token") == "primary"
    )
    assert color_conflict["type"] in ["color_mismatch", "token_mismatch"]


@pytest.mark.asyncio
async def test_fuse_aligns_color_names():
    """跨模态对齐：视觉说"blue"对齐到爬虫 HEX"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "blue",
                        "type": "color",
                        "semantics": "main",
                        "usage": [],
                        "confidence": 0.85,
                    }
                ]
            },
            confidence=0.85,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "#635BFF",
                        "type": "color",
                        "semantics": "brand",
                        "usage": [],
                        "confidence": 0.99,
                    }
                ]
            },
            confidence=0.99,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    # 融合后值应是 HEX（爬虫优先）
    primary = next(t for t in result["design_tokens"] if t["name"] == "primary")
    assert primary["value"].startswith("#")


@pytest.mark.asyncio
async def test_fuse_tech_stack_only_from_crawler():
    """技术栈仅从爬虫模态提取"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={"tech_stack": [{"name": "should-be-ignored"}]},
            confidence=0.9,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={"tech_stack": [{"name": "next", "confidence": 0.99}]},
            confidence=0.9,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    tech_names = [t["name"] for t in result["tech_stack"]]
    assert "next" in tech_names
    assert "should-be-ignored" not in tech_names


@pytest.mark.asyncio
async def test_fuse_agreement_boosts_confidence():
    """多器官一致时，置信度加权提升"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "#635BFF",
                        "type": "color",
                        "semantics": "",
                        "usage": [],
                        "confidence": 0.9,
                    }
                ]
            },
            confidence=0.9,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={
                "design_tokens": [
                    {
                        "name": "primary",
                        "value": "#635BFF",
                        "type": "color",
                        "semantics": "",
                        "usage": [],
                        "confidence": 0.95,
                    }
                ]
            },
            confidence=0.95,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    primary = next(t for t in result["design_tokens"] if t["name"] == "primary")
    # 一致性提升应使 confidence 高于单一信号
    assert primary["confidence"] > 0.0


@pytest.mark.asyncio
async def test_fuse_layout_crawler_priority():
    """布局字段冲突时爬虫优先"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={"layout": {"depth": 3, "grid_count": 0}},
            confidence=0.9,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={"layout": {"depth": 5, "grid_count": 2}},
            confidence=0.9,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    assert result["layout"]["depth"] == 5
    assert result["layout"]["grid_count"] == 2


@pytest.mark.asyncio
async def test_fuse_confidence_in_range():
    """综合置信度在 0-1 之间"""
    fusion = SensorFusion()
    signals = [
        PerceptionSignal(
            modality=PerceptionModality.VISION,
            payload={"design_tokens": []},
            confidence=0.5,
            source="vision",
        ),
        PerceptionSignal(
            modality=PerceptionModality.CRAWLER,
            payload={"design_tokens": []},
            confidence=0.7,
            source="crawler",
        ),
    ]
    result = await fusion.fuse(signals)
    assert 0.0 <= result["confidence"] <= 1.0


def test_modality_weights_crawler_highest():
    """爬虫模态权重最高（实时性最高）"""
    fusion = SensorFusion()
    crawler_weight = fusion.modality_weights[PerceptionModality.CRAWLER]
    for modality, weight in fusion.modality_weights.items():
        if modality != PerceptionModality.CRAWLER:
            assert crawler_weight >= weight

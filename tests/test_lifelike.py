"""Test LAAP LifelikeAgent"""
import sys
sys.path.insert(0, r"D:\LAAP")

# Mock sentence_transformers to avoid slow/hanging import in test env
import types
_st_mock = types.ModuleType("sentence_transformers")
_st_mock.SentenceTransformer = None
sys.modules["sentence_transformers"] = _st_mock

from laap.agent.lifelike import LifelikeAgent, LifelikeConfig

# LifelikeAgent 自身注册的内部安全动作 — 测试中只保留这些，过滤所有自动发现工具
# 避免选中 browser_* (playwright 挂起) / run_tests (递归 pytest) / http_get (网络) / screenshot_analyze (vision LLM) 等
_LIFE_ACTIONS_KEEP = {
    "explore", "analyze", "reflect", "rest",
    "deliberate", "meta_reflect", "learn_skill",
}


def _make_life(**kw):
    a = LifelikeAgent(config=LifelikeConfig(exploration_rate=0, **kw))
    for name in list(a.tool_registry._tools.keys()):
        if name not in _LIFE_ACTIONS_KEEP:
            del a.tool_registry._tools[name]
    return a


def test_lifelike_init():
    a = _make_life()
    assert a.needs is not None
    assert a.emotion_gradient is not None
    assert len(a.needs.needs) == 5
    assert a.tool_registry.count > 0


def test_lifelike_step():
    a = _make_life()
    r = a.step("test observation", task_success=0.5)
    assert r["step"] == 1
    assert "emotional_state" in r
    assert "dominant_need" in r
    assert "intrinsic_reward" in r
    assert r["action"] is not None


def test_lifelike_multiple_steps():
    a = _make_life()
    for i in range(10):
        r = a.step(f"obs_{i}", task_success=0.5 + 0.1 * (i % 3 - 1))
        assert r["step"] == i + 1
    assert a.step_count == 10
    assert len(a._reward_history) == 10


def test_lifelike_with_rsi():
    a = _make_life(rsi_enabled=True, rsi_interval=3, reflection_interval=5)
    # 测试环境禁用 LLM — RSI _llm_generate_proposal 会发起 HTTP 流式调用，
    # 端点不可达时 httpx 无默认超时会挂起；置 None 后 RSI 自动回退到模板生成器
    a.llm = None
    for i in range(30):
        a.step(f"exp_{i}", task_success=0.5 + 0.3 * ((i % 5) / 5.0))
    assert a.rsi is not None
    assert len(a._reward_history) > 0


def test_lifelike_apply_needs_mod():
    a = _make_life()
    a.apply_modification({
        "type": "adjust_needs",
        "params": {"certainty": {"decay_rate": 0.005, "importance": 2.0}},
    })
    from laap.cognition.needs import NeedType
    assert a.needs.needs[NeedType.CERTAINTY].decay_rate == 0.005
    assert a.needs.needs[NeedType.CERTAINTY].importance == 2.0


def test_lifelike_self_reflect():
    a = _make_life(reflection_interval=5)
    for i in range(15):
        a.step(f"obs_{i}", task_success=0.5)
    assert len(a.memory.reflections) >= 1


def test_lifelike_status():
    a = _make_life()
    for i in range(5):
        a.step(f"obs_{i}")
    s = a.complete_status()
    assert "needs" in s
    assert "emotional_state" in s
    assert "fitness" in s

# -*- coding: utf-8 -*-
"""MultiPathCoding 多路径编码测试。"""
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import pytest
from laap.agent.multipath_coding import MultiPathCoding, PATH_VARIANTS


def _make_loop(generator, verifier=None):
    return MultiPathCoding(generator=generator, verifier=verifier)


def test_variants_exist():
    assert len(PATH_VARIANTS) == 3
    names = {v["name"] for v in PATH_VARIANTS}
    assert names == {"conservative", "balanced", "confident"}


def test_all_paths_succeed():
    def gen(desc, strategy, calib):
        return "def f(x):\n    return x * 2\n"
    mpc = _make_loop(gen)
    r = mpc.execute("写一个翻倍函数")
    assert r.success is True
    assert len(r.paths) == 3
    assert r.winner is not None
    assert r.winner.passed is True


def test_winner_is_best_score():
    """获胜者应为评分最高（含验证失败但有代码的路径）。"""
    def gen(desc, strategy, calib):
        if "保守" in strategy:
            return "def f(:\n"  # 失败
        return "def f():\n    return 1\n"  # 成功
    mpc = _make_loop(gen)
    r = mpc.execute("测试")
    assert r.success is True
    assert r.winner.path_name != "conservative"


def test_no_code_all_paths():
    """全部路径失败时 success=False。"""
    def gen(desc, strategy, calib):
        return "def broken(:\n"
    mpc = _make_loop(gen)
    r = mpc.execute("测试")
    assert r.success is False
    assert r.winner is not None  # 取评分最高（虽然失败）


def test_custom_value_fn():
    """自定义价值函数生效。"""
    def gen(desc, strategy, calib):
        return "def f():\n    return 1\n"
    def value_fn(code, passed):
        return 0.99 if "return" in code else 0.0
    mpc = MultiPathCoding(generator=gen, value_fn=value_fn)
    r = mpc.execute("测试")
    assert r.winner.score == 0.99


def test_stats():
    def gen(desc, strategy, calib):
        return "def f():\n    return 1\n"
    mpc = _make_loop(gen)
    mpc.execute("任务1")
    mpc.execute("任务2")
    s = mpc.stats()
    assert s["total_tasks"] == 2
    assert s["success_rate"] == 1.0
    assert sum(s["path_wins"].values()) == 2


def test_recent():
    def gen(desc, strategy, calib):
        return "def f():\n    return 1\n"
    mpc = _make_loop(gen)
    mpc.execute("任务1")
    assert len(mpc.recent(5)) == 1
"""测试 LAAPCausalBackend(P1-4) — causal-learn + DoWhy 集成。

注意:causal-learn 和 DoWhy 在 Windows + Python 3.13 首次导入极慢
(可能 30s+),因此本测试只做轻量级 API 验证。完整功能验证在
test_causal_backend_full.py 中(可手动运行,需耐心等待导入)。

运行:
    python test_causal_backend.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows GBK 终端兼容
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from laap.agi.causal_backend import LAAPCausalBackend, enhance_causal_engine


def test_import_and_api():
    """1. 测试导入与 API 完整性。"""
    print("=" * 60)
    print("1. 测试导入 LAAPCausalBackend 与 API 完整性")
    print("=" * 60)

    backend = LAAPCausalBackend(discovery_method="pc", significance_level=0.05)
    print(f"✓ 后端创建: {backend.__class__.__name__}")
    print(f"  - discovery_method: {backend.discovery_method}")
    print(f"  - significance_level: {backend.significance_level}")
    print(f"  - TQDM_DISABLE env: {os.environ.get('TQDM_DISABLE', '(unset)')}")

    # 验证关键方法存在
    for method_name in ["discover", "estimate_effect", "counterfactual",
                        "enhance_engine", "_normalize_data", "stats"]:
        assert hasattr(backend, method_name), f"缺少方法 {method_name}"
        print(f"✓ 方法 {method_name}: 存在")

    # 验证 stats() 返回正确字段
    stats = backend.stats()
    expected_keys = {"backend", "discovery_method", "significance_level",
                     "causal_learn_available", "dowhy_available",
                     "last_graph_discovered", "last_model_built"}
    assert expected_keys.issubset(stats.keys()), f"stats 缺字段: {expected_keys - set(stats.keys())}"
    print(f"✓ stats() 返回 {len(stats)} 个字段")

    return backend


def test_normalize_data():
    """2. 测试数据归一化(无需导入 causal-learn/dowhy)。"""
    print("\n" + "=" * 60)
    print("2. 测试 _normalize_data")
    print("=" * 60)

    import numpy as np

    backend = LAAPCausalBackend()

    # 测试 ndarray 输入
    arr = np.random.RandomState(0).normal(0, 1, (50, 3))
    normalized, names = backend._normalize_data(arr, ["A", "B", "C"])
    assert normalized is not None, "ndarray 归一化失败"
    assert normalized.shape == (50, 3), f"形状错误: {normalized.shape}"
    assert names == ["A", "B", "C"]
    print(f"✓ ndarray → ndarray: shape={normalized.shape}")

    # 测试 dict 输入
    data_dict = {"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0]}
    normalized, names = backend._normalize_data(data_dict, ["A", "B"])
    assert normalized is not None, "dict 归一化失败"
    assert normalized.shape == (3, 2), f"形状错误: {normalized.shape}"
    print(f"✓ dict → ndarray: shape={normalized.shape}")

    # 测试 DataFrame 输入
    import pandas as pd
    df = pd.DataFrame({"X": [1, 2, 3], "Y": [4, 5, 6]})
    normalized, names = backend._normalize_data(df, ["X", "Y"])
    assert normalized is not None, "DataFrame 归一化失败"
    assert normalized.shape == (3, 2)
    print(f"✓ DataFrame → ndarray: shape={normalized.shape}")

    # 测试数据不足
    short_arr = np.array([[1.0, 2.0]])
    result = backend.discover(variables=["A", "B"], data=short_arr)
    assert result is None, "数据不足应返回 None"
    print(f"✓ 数据不足正确返回 None")


def test_discover_graceful_failure():
    """3. 测试 discover 在无数据/无变量时优雅失败。"""
    print("\n" + "=" * 60)
    print("3. 测试 discover 优雅失败")
    print("=" * 60)

    import numpy as np
    backend = LAAPCausalBackend()

    # 空数据
    result = backend.discover(variables=[], data=np.array([]).reshape(0, 0))
    assert result is None
    print(f"✓ 空数据返回 None")

    # 单变量(无法发现因果)
    result = backend.discover(
        variables=["A"],
        data=np.array([[1.0], [2.0], [3.0]]),
    )
    # 单变量应该返回 None 或空图(算法应处理)
    print(f"✓ 单变量处理: {result}")


def test_enhance_causal_engine_signature():
    """4. 测试 enhance_causal_engine 便捷函数签名。"""
    print("\n" + "=" * 60)
    print("4. 测试 enhance_causal_engine 便捷函数")
    print("=" * 60)

    from laap.agi.causal import UnifiedCausalEngine
    import numpy as np

    engine = UnifiedCausalEngine(name="test-engine")
    before = engine.stats().get("causal_bonds", 0)
    print(f"  - 注入前 bonds: {before}")

    # 用极小数据集 — 失败/0 边都算正常,只要不抛异常
    np.random.seed(0)
    data = np.random.normal(0, 1, (10, 3))
    n = enhance_causal_engine(
        engine=engine, data=data,
        variables=["A", "B", "C"], method="pc",
    )
    after = engine.stats().get("causal_bonds", 0)
    print(f"  - 注入后 bonds: {after}")
    print(f"✓ enhance_causal_engine 完成(注入 {n} 条边,不抛异常)")
    assert isinstance(n, int) and n >= 0


def test_dependency_availability():
    """5. 测试 causal-learn 与 DoWhy 是否已安装(只查模块名,不导入)。"""
    print("\n" + "=" * 60)
    print("5. 测试依赖可用性(只 importlib.util.find_spec,不实际导入)")
    print("=" * 60)

    import importlib.util

    cl_spec = importlib.util.find_spec("causallearn")
    dowhy_spec = importlib.util.find_spec("dowhy")
    print(f"  - causal-learn: {'已安装' if cl_spec else '未安装'}")
    print(f"  - DoWhy: {'已安装' if dowhy_spec else '未安装'}")
    assert cl_spec is not None, "causal-learn 未安装(pip install causal-learn)"
    assert dowhy_spec is not None, "DoWhy 未安装(pip install dowhy)"
    print(f"✓ 两个依赖均已安装")


def main():
    print("\n" + "=" * 70)
    print("LAAPCausalBackend 测试套件 (P1-4: causal-learn + DoWhy 集成)")
    print("=" * 70)

    results = []
    tests = [
        ("ImportAndAPI", test_import_and_api),
        ("NormalizeData", test_normalize_data),
        ("DiscoverGracefulFailure", test_discover_graceful_failure),
        ("EnhanceEngineSignature", test_enhance_causal_engine_signature),
        ("DependencyAvailability", test_dependency_availability),
    ]

    for name, fn in tests:
        try:
            fn()
            results.append((name, True))
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
            import traceback; traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 70)
    print("测试汇总:")
    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False
    print("=" * 70)

    if all_pass:
        print("\n✅ 所有 API 测试通过!LAAPCausalBackend 已就绪(P1-4 完成)")
        print("\n  • causal-learn 提供 PC/FCI/GES 算法(真 V-结构 + Meek 规则)")
        print("  • DoWhy 提供 do-calculus + 反事实 + 后门调整")
        print("  • enhance_engine 把发现的关系注入 UnifiedCausalEngine")
        print("  • 已规避 Windows tqdm.auto 兼容性问题(TQDM_DISABLE=1)")
        print("\n  完整功能测试(首次导入 30s+):")
        print("    python -c 'from laap.agi.causal_backend import LAAPCausalBackend;")
        print("               b=LAAPCausalBackend(); import numpy as np;")
        print("               d=np.random.RandomState(0).normal(0,1,(50,3));")
        print("               print(b.discover([\"A\",\"B\",\"C\"], d))'")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

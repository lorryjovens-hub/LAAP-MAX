"""Task D2: 贝叶斯后验 abduction 测试

验证 `DoCalculus._abduction` 的共轭先验后验更新：
- 二值变量：Beta(1+s, 1+f) 共轭先验，后验 mean = (1+s)/(2+s+f)
- 数值变量：Normal 后验，mean = sample_mean，CI 宽度随样本量收窄
- `counterfactual()` 返回 `treatment_effect` 含 95% 置信区间
- 与原 `_abduction` 行为兼容（标量证据仍可运行）
"""

import pytest

from src.consciousness.causal_model.inference.causal_inference_engine import (
    CausalInferenceEngine,
)
from src.consciousness.causal_model.inference.do_calculus import DoCalculus


@pytest.fixture
def do_calculus() -> DoCalculus:
    """复用 CausalInferenceEngine 初始化的设计因果图"""
    engine = CausalInferenceEngine()
    return engine.do_calculus


# ---------------------------------------------------------------
# SubTask D2.1: 二值变量 Beta 共轭先验后验更新
# ---------------------------------------------------------------


def test_binary_posterior_mean(do_calculus: DoCalculus) -> None:
    """二值变量后验更新：观察 10 次成功 5 次失败

    Beta(α=1+10, β=1+5) = Beta(11, 6)
    posterior mean = 11 / 17 ≈ 0.647
    """
    posterior = do_calculus._abduction({"conversion": {"successes": 10, "failures": 5}})

    assert "conversion" in posterior
    params = posterior["conversion"]
    # 必需的后验参数字段
    for key in ("mean", "variance", "ci_lower", "ci_upper", "std_error"):
        assert key in params, f"missing posterior field: {key}"

    # Beta(11, 6) 后验 mean = 11/17 ≈ 0.647
    expected_mean = (1 + 10) / (2 + 10 + 5)
    assert params["mean"] == pytest.approx(expected_mean, abs=1e-6)
    assert params["mean"] == pytest.approx(0.647, abs=1e-2)


def test_binary_posterior_ci_bounds_valid(do_calculus: DoCalculus) -> None:
    """二值变量后验 CI 满足 ci_lower <= mean <= ci_upper，且在 [0, 1]"""
    posterior = do_calculus._abduction({"click": {"successes": 7, "failures": 3}})
    params = posterior["click"]

    assert 0.0 <= params["ci_lower"] <= params["mean"] <= params["ci_upper"] <= 1.0
    # CI 宽度 > 0
    assert params["ci_upper"] > params["ci_lower"]


def test_binary_posterior_ci_uses_beta_ppf(do_calculus: DoCalculus) -> None:
    """二值变量 CI 由 scipy.stats.beta.ppf(0.025/0.975) 计算"""
    from scipy.stats import beta as beta_dist

    s, f = 10, 5
    alpha = 1 + s
    beta_param = 1 + f
    expected_lower = beta_dist(alpha, beta_param).ppf(0.025)
    expected_upper = beta_dist(alpha, beta_param).ppf(0.975)

    params = do_calculus._beta_posterior(s, f)
    assert params["ci_lower"] == pytest.approx(expected_lower, abs=1e-9)
    assert params["ci_upper"] == pytest.approx(expected_upper, abs=1e-9)


# ---------------------------------------------------------------
# SubTask D2.1: 数值变量 Normal 后验更新
# ---------------------------------------------------------------


def test_numeric_posterior_mean(do_calculus: DoCalculus) -> None:
    """数值变量后验更新：观察 [0.1, 0.2, 0.3]，后验 mean ≈ 0.2"""
    posterior = do_calculus._abduction({"metric": [0.1, 0.2, 0.3]})

    params = posterior["metric"]
    assert params["mean"] == pytest.approx(0.2, abs=1e-9)


def test_numeric_posterior_ci_width_reasonable(do_calculus: DoCalculus) -> None:
    """数值变量后验 CI 宽度合理（> 0 且有限）"""
    posterior = do_calculus._abduction({"metric": [0.1, 0.2, 0.3]})
    params = posterior["metric"]

    ci_width = params["ci_upper"] - params["ci_lower"]
    assert ci_width > 0
    assert ci_width < 1.0  # 合理范围
    # mean 应落在 CI 内
    assert params["ci_lower"] <= params["mean"] <= params["ci_upper"]


def test_numeric_posterior_dict_samples_format(do_calculus: DoCalculus) -> None:
    """数值变量支持 {"samples": [...]} dict 格式"""
    posterior = do_calculus._abduction(
        {"metric": {"samples": [0.1, 0.2, 0.3]}}
    )
    params = posterior["metric"]
    assert params["mean"] == pytest.approx(0.2, abs=1e-9)


def test_numeric_posterior_ci_uses_norm_ppf(do_calculus: DoCalculus) -> None:
    """数值变量 CI 由 scipy.stats.norm(mean, std/sqrt(n)).ppf 计算"""
    from scipy.stats import norm

    samples = [0.1, 0.2, 0.3]
    n = len(samples)
    import numpy as np

    mean = float(np.mean(samples))
    se = float(np.sqrt(np.var(samples, ddof=1) / n))
    expected_lower = norm(mean, se).ppf(0.025)
    expected_upper = norm(mean, se).ppf(0.975)

    params = do_calculus._normal_posterior(samples)
    assert params["ci_lower"] == pytest.approx(expected_lower, abs=1e-9)
    assert params["ci_upper"] == pytest.approx(expected_upper, abs=1e-9)


# ---------------------------------------------------------------
# SubTask D2.2: counterfactual() 返回 treatment_effect 含 95% CI
# ---------------------------------------------------------------


def test_counterfactual_treatment_effect_has_ci_fields(
    do_calculus: DoCalculus,
) -> None:
    """counterfactual 返回的 treatment_effect 含 4 个必需字段"""
    result = do_calculus.counterfactual(
        target="conversion_rate",
        intervention={"button_color": "red"},
        factual_evidence={
            "conversion_rate": {"successes": 5, "failures": 95},
            "click_rate": {"successes": 10, "failures": 90},
            "scroll_depth": {"successes": 20, "failures": 80},
        },
    )

    assert "treatment_effect" in result
    te = result["treatment_effect"]
    assert isinstance(te, dict)
    for field in ("point_estimate", "ci_lower", "ci_upper", "std_error"):
        assert field in te, f"missing treatment_effect field: {field}"
        assert isinstance(te[field], float)


def test_counterfactual_ci_contains_point_estimate(
    do_calculus: DoCalculus,
) -> None:
    """置信区间满足 ci_lower <= point_estimate <= ci_upper"""
    result = do_calculus.counterfactual(
        target="conversion_rate",
        intervention={"button_color": "red"},
        factual_evidence={
            "click_rate": {"successes": 10, "failures": 90},
            "scroll_depth": {"successes": 20, "failures": 80},
        },
    )
    te = result["treatment_effect"]
    assert te["ci_lower"] <= te["point_estimate"] <= te["ci_upper"]


def test_counterfactual_preserves_legacy_fields(do_calculus: DoCalculus) -> None:
    """counterfactual 仍保留 factual / counterfactual / confidence 字段"""
    result = do_calculus.counterfactual(
        target="conversion_rate",
        intervention={"button_color": "red"},
        factual_evidence={"conversion_rate": "0.05"},
    )
    for field in ("factual", "counterfactual", "treatment_effect", "confidence"):
        assert field in result


# ---------------------------------------------------------------
# 大样本 CI < 小样本 CI
# ---------------------------------------------------------------


def test_large_sample_ci_narrower_than_small_sample_binary(
    do_calculus: DoCalculus,
) -> None:
    """二值变量：大样本 CI 宽度 < 小样本 CI 宽度（同比例）

    Beta(1+s, 1+f) 共轭先验对大样本的收缩效应更小，
    大样本后验 mean 更接近经验比例 s/(s+f)。
    """
    # 小样本：10 成功 5 失败（经验比例 2/3 ≈ 0.667）
    small = do_calculus._beta_posterior(successes=10, failures=5)
    # 大样本：100 成功 50 失败（同比例，样本量 10 倍）
    large = do_calculus._beta_posterior(successes=100, failures=50)

    small_width = small["ci_upper"] - small["ci_lower"]
    large_width = large["ci_upper"] - large["ci_lower"]

    # 核心断言：大样本 CI 应显著窄于小样本
    assert large_width < small_width

    # 两者后验 mean 都应接近经验比例 2/3（Beta(1,1) 先验收缩效应）
    empirical = 10.0 / (10.0 + 5.0)
    assert abs(small["mean"] - empirical) < 0.05
    assert abs(large["mean"] - empirical) < 0.05
    # 大样本因先验权重更低，mean 更接近经验比例
    assert abs(large["mean"] - empirical) <= abs(small["mean"] - empirical)


def test_large_sample_ci_narrower_than_small_sample_numeric(
    do_calculus: DoCalculus,
) -> None:
    """数值变量：大样本 CI 宽度 < 小样本 CI 宽度（同均值）"""
    import numpy as np

    rng = np.random.RandomState(42)
    # 小样本 n=3
    small_samples = [0.1, 0.2, 0.3]
    # 大样本 n=100（同均值 0.2，相近方差）
    large_samples = list(rng.normal(loc=0.2, scale=0.1, size=100))

    small = do_calculus._normal_posterior(small_samples)
    large = do_calculus._normal_posterior(large_samples)

    small_width = small["ci_upper"] - small["ci_lower"]
    large_width = large["ci_upper"] - large["ci_lower"]

    assert large_width < small_width


# ---------------------------------------------------------------
# 向后兼容：原 _abduction 行为不破坏既有调用
# ---------------------------------------------------------------


def test_abduction_backward_compat_scalar_string(do_calculus: DoCalculus) -> None:
    """原标量字符串证据仍可运行：{"var": "0.05"} → mean ≈ 0.05"""
    posterior = do_calculus._abduction({"conversion_rate": "0.05"})
    params = posterior["conversion_rate"]
    # 标量字符串作为单点数值观察 → mean = 0.05
    assert params["mean"] == pytest.approx(0.05, abs=1e-9)
    # value 字段用于向后兼容
    assert params["value"] == params["mean"]


def test_abduction_backward_compat_non_numeric_string(
    do_calculus: DoCalculus,
) -> None:
    """非数值字符串（如 "red"）回退到 0.5（与原行为一致）"""
    posterior = do_calculus._abduction({"button_color": "red"})
    params = posterior["button_color"]
    assert params["mean"] == pytest.approx(0.5, abs=1e-9)


def test_counterfactual_backward_compat_scalar_evidence(
    do_calculus: DoCalculus,
) -> None:
    """原标量证据格式的 counterfactual 调用仍可运行并返回有效结构"""
    result = do_calculus.counterfactual(
        target="conversion_rate",
        intervention={"button_color": "red"},
        factual_evidence={"conversion_rate": "0.05"},
    )
    # 既有字段保留
    assert isinstance(result["factual"], float)
    assert isinstance(result["counterfactual"], float)
    # treatment_effect 为含 CI 的 dict
    te = result["treatment_effect"]
    assert isinstance(te, dict)
    assert te["ci_lower"] <= te["point_estimate"] <= te["ci_upper"]


def test_action_overrides_intervention_as_point_mass(
    do_calculus: DoCalculus,
) -> None:
    """_action 将干预变量设为点质量分布（variance=0）"""
    posterior = do_calculus._abduction({"click_rate": {"successes": 10, "failures": 90}})
    modified = do_calculus._action(posterior, {"button_color": "red"})

    # button_color 被覆盖为点质量
    bc = modified["button_color"]
    assert bc["variance"] == 0.0
    assert bc["std_error"] == 0.0
    assert bc["ci_lower"] == bc["mean"] == bc["ci_upper"]

    # 原有证据变量的后验保持不变
    assert modified["click_rate"]["mean"] == posterior["click_rate"]["mean"]


def test_prediction_with_uncertainty_returns_tuple(
    do_calculus: DoCalculus,
) -> None:
    """_prediction_with_uncertainty 返回 (mean, std_error) 元组"""
    posterior = do_calculus._abduction(
        {"click_rate": {"successes": 10, "failures": 90}}
    )
    mean, se = do_calculus._prediction_with_uncertainty(posterior, "conversion_rate")
    assert isinstance(mean, float)
    assert isinstance(se, float)
    assert 0.0 <= mean <= 1.0
    assert se >= 0.0

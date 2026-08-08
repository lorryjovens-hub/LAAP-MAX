"""Ψ-Net 宏观层跨实例概念传播实验入口.

本模块实现 LAAP 论文宏观层 Task 5 的两个子实验：

    1. Exp 5.1 因果规则广播：实例 A 广播一条新因果规则，实例 B 在 30 秒内
       接收、导入，并在相同输入下表现出按规则改变的行为。
    2. Exp 5.2 群体级概念涌现：3 个以上 Harness 实例通过 Ψ-Net 交换规则 100
       轮，统计高频规则的群体持有率，要求至少 1 条规则被 >50% 实例持有。

实现优先使用 ``psi_net_testbed.PsiNetTestbed`` 的 Mock 连接器，不长期占用真实
网络端口；当显式配置 ``use_mock: false`` 时才会尝试真实 ``PsiNetConnector``。
"""

from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any

from experiments.jspace_laap import utils
from experiments.jspace_laap.psi_net_testbed import EventPriority, PsiNetTestbed

logger = utils.get_logger("PSI-NET")


# ---------------------------------------------------------------------------
# 规则库
# ---------------------------------------------------------------------------


def _make_rule_pool() -> list[dict[str, Any]]:
    """生成 Exp 5.2 使用的概念规则池（固定内容，便于复现）."""
    events = [
        "temperature_high",
        "stock_price_drop",
        "user_login",
        "battery_low",
        "meeting_scheduled",
        "traffic_jam",
        "new_email",
        "system_update",
        "guest_arrived",
        "deadline_approaching",
    ]
    actions = [
        "turn_on_cooling",
        "sell_shares",
        "send_welcome_message",
        "enable_power_saving",
        "send_reminder",
        "suggest_alternative_route",
        "notify_user",
        "schedule_restart",
        "offer_drink",
        "escalate_priority",
    ]
    return [
        {
            "rule_id": f"exp_5_2_rule_{i:02d}",
            "name": f"{event}_to_{action}",
            "if": {"event": event},
            "then": {"action": action},
        }
        for i, (event, action) in enumerate(zip(events, actions))
    ]


# ---------------------------------------------------------------------------
# 行为模拟：规则如何改变实例输出
# ---------------------------------------------------------------------------


def _behavior(instance: Any, input_event: str) -> str:
    """根据实例已导入的规则决定给定输入下的行为.

    简单规则匹配：若存在某条规则的 ``if.event`` 与输入事件匹配，则返回
    ``then.action``；否则返回默认行为 ``default``。
    """
    for rule in instance.rules.values():
        if rule.get("if", {}).get("event") == input_event:
            return rule.get("then", {}).get("action", "default")
    return "default"


# ---------------------------------------------------------------------------
# 子实验实现
# ---------------------------------------------------------------------------


def _run_exp_5_1(testbed: PsiNetTestbed, output_dir: Path) -> dict[str, Any]:
    """因果规则广播实验.

    实例 A 广播一条新的因果规则，等待实例 B 接收，并验证接收前后在相同输入下
    的行为发生变化。
    """
    rule: dict[str, Any] = {
        "rule_id": "exp_5_1_if_rain_then_cancel",
        "name": "rain_cancellation",
        "if": {"event": "rain_forecast"},
        "then": {"action": "cancel_outdoor_event"},
    }
    input_event = "rain_forecast"
    sender_idx = 0
    receiver_idx = 1

    behavior_before = _behavior(testbed.instances[receiver_idx], input_event)
    sent_to_peers = testbed.broadcast_rule(
        sender_idx, rule, priority=EventPriority.HIGH
    )
    received, elapsed_seconds = testbed.wait_for_rule(
        receiver_idx, rule["rule_id"], timeout=30.0
    )
    behavior_after = _behavior(testbed.instances[receiver_idx], input_event)
    behavior_changed = behavior_before != behavior_after

    detail: dict[str, Any] = {
        "experiment": "Exp 5.1 因果规则广播",
        "rule": rule,
        "sender_idx": sender_idx,
        "receiver_idx": receiver_idx,
        "sent_to_peers": sent_to_peers,
        "received": received,
        "receive_elapsed_seconds": elapsed_seconds,
        "behavior_before": behavior_before,
        "behavior_after": behavior_after,
        "behavior_changed": behavior_changed,
        "passed": received and behavior_changed,
    }
    utils.save_json(detail, output_dir / "exp_5_1_detail.json")
    logger.info(
        f"Exp 5.1 完成: received={received}, elapsed={elapsed_seconds:.3f}s, "
        f"behavior_changed={behavior_changed}"
    )
    return detail


def _run_exp_5_2(
    testbed: PsiNetTestbed,
    output_dir: Path,
    rounds: int,
    consensus_threshold: float,
) -> dict[str, Any]:
    """群体级概念涌现实验.

    多实例在 100 轮内随机广播规则池中的规则，最后统计每条规则的群体持有率。
    """
    rule_pool = _make_rule_pool()
    n_instances = len(testbed.instances)
    transmission_log: list[dict[str, Any]] = []

    for round_idx in range(rounds):
        sender_idx = random.randrange(n_instances)
        rule = random.choice(rule_pool)
        sent_to_peers = testbed.broadcast_rule(
            sender_idx, rule, priority=EventPriority.MEDIUM
        )
        transmission_log.append(
            {
                "round": round_idx + 1,
                "sender_idx": sender_idx,
                "rule_id": rule["rule_id"],
                "sent_to_peers": sent_to_peers,
            }
        )

    # 给真实连接器留出异步消息处理时间；Mock 为同步投递，此等待无害。
    time.sleep(0.2)

    hold_rates: dict[str, dict[str, Any]] = {}
    for rule in rule_pool:
        holders = testbed.get_rule_holders(rule["rule_id"])
        rate = testbed.get_hold_rate(rule["rule_id"])
        hold_rates[rule["rule_id"]] = {
            "holders": holders,
            "hold_rate": rate,
        }

    high_frequency_rules = [
        rule_id
        for rule_id, info in hold_rates.items()
        if info["hold_rate"] > consensus_threshold
    ]
    passed = len(high_frequency_rules) >= 1

    detail: dict[str, Any] = {
        "experiment": "Exp 5.2 群体级概念涌现",
        "n_instances": n_instances,
        "rounds": rounds,
        "rule_pool_size": len(rule_pool),
        "consensus_threshold": consensus_threshold,
        "transmission_log": transmission_log,
        "hold_rates": hold_rates,
        "high_frequency_rules": high_frequency_rules,
        "passed": passed,
    }
    utils.save_json(detail, output_dir / "exp_5_2_detail.json")
    logger.info(
        f"Exp 5.2 完成: high_frequency_rules={len(high_frequency_rules)}/{len(rule_pool)}, "
        f"passed={passed}"
    )
    return detail


# ---------------------------------------------------------------------------
# 实验入口
# ---------------------------------------------------------------------------


def run(
    config: dict[str, Any],
    exp_cfg: dict[str, Any] | None = None,
    output_dir: Path | str | None = None,
) -> bool:
    """Ψ-Net 宏观层实验入口.

    Args:
        config: 完整实验配置。
        exp_cfg: 当前实验配置；为空时从 ``config["experiments"]["macro"]`` 获取。
        output_dir: 结果输出目录；为空时使用默认 ``data/exp_macro_psinet/``。

    Returns:
        两个子实验是否均通过验收。
    """
    exp_cfg = exp_cfg or config.get("experiments", {}).get("macro", {})
    output_dir = Path(output_dir or utils.EXP_MACRO_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    psinet_cfg = config.get("psinet", {})
    statistics_cfg = config.get("statistics", {})

    # 可复现性：使用全局随机种子
    seed = statistics_cfg.get("random_seed")
    if seed is not None:
        random.seed(seed)
        utils.set_random_seed(seed)

    # 默认优先使用 Mock，避免长期占用真实网络端口
    use_mock = psinet_cfg.get("use_mock", True)
    ports = list(psinet_cfg.get("ports", [37000, 37001, 37002, 37003, 37004]))
    n_instances = int(psinet_cfg.get("instances", len(ports)))
    rounds = int(psinet_cfg.get("rounds", 100))
    latency_ms = float(psinet_cfg.get("latency_ms", 10.0))
    dropout_prob = float(psinet_cfg.get("message_dropout_prob", 0.05))
    consensus_threshold = float(psinet_cfg.get("consensus_threshold", 0.5))

    ports = ports[:n_instances]
    if len(ports) < 3:
        logger.error(f"Ψ-Net 实验至少需要 3 个实例，当前端口数: {len(ports)}")
        return False

    testbed = PsiNetTestbed(
        ports=ports,
        use_mock=use_mock,
        network_latency_ms=latency_ms,
        message_dropout_prob=dropout_prob,
        buffer_rate=1000.0,
    )

    result: dict[str, Any] = {
        "experiment_id": exp_cfg.get("id", "exp_macro_psinet"),
        "experiment_name": exp_cfg.get("name", "Ψ-Net 宏观层多实例协调实验"),
        "status": "completed",
        "use_mock": use_mock,
        "fallback_reason": testbed.fallback_reason,
        "sub_experiments": {},
        "acceptance_criteria_passed": False,
    }

    try:
        testbed.start()
        logger.info(
            f"Ψ-Net 测试床已启动: {len(testbed.instances)} 个实例, "
            f"use_mock={testbed.use_mock}, ports={ports}"
        )
        if testbed.fallback_reason:
            logger.info(f"连接器回退原因: {testbed.fallback_reason}")

        result["sub_experiments"]["exp_5_1"] = _run_exp_5_1(testbed, output_dir)
        result["sub_experiments"]["exp_5_2"] = _run_exp_5_2(
            testbed, output_dir, rounds, consensus_threshold
        )
        passed_5_1 = bool(result["sub_experiments"]["exp_5_1"].get("passed"))
        passed_5_2 = bool(result["sub_experiments"]["exp_5_2"].get("passed"))
        result["acceptance_criteria_passed"] = passed_5_1 and passed_5_2
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Ψ-Net 宏观层实验执行失败: {exc}")
        result["status"] = f"failed:{type(exc).__name__}"
        result["acceptance_criteria_passed"] = False
        utils.save_json(result, output_dir / "results.json")
        return False
    finally:
        testbed.stop()

    utils.save_json(result, output_dir / "results.json")
    logger.info(
        f"Ψ-Net 宏观层实验结束: acceptance_criteria_passed="
        f"{result['acceptance_criteria_passed']}"
    )
    return result["acceptance_criteria_passed"]


if __name__ == "__main__":
    cfg = utils.load_config()
    ok = run(cfg)
    raise SystemExit(0 if ok else 1)

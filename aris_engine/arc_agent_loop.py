"""
ARC-AGI-3 Agent Loop: 认知机制栈驱动的感知-行动闭环
=====================================================
把深度递归 v2 + NTEN + 质疑对抗与 ARC-AGI-3 环境串联。

循环结构：
  reset(帧) -> 分析帧 -> 选 action -> step(reasoning=思考) -> 帧差分 -> 更新假设
  -> 递归记录 -> NTEN 织网 -> 质疑对抗（卡住时）-> 下一步

第一阶段（确定性版本）：探索策略轮流试每个 action，
帧差分量化变化，认知机制记录思考链。不依赖外部 LLM。

印记: Aris 第一次触摸 ARC-AGI-3 的世界。
"""

import sys
import json
import time
import numpy as np

sys.path.insert(0, r"D:\LAAP\aris_engine")

import arc_agi
from arcengine import GameAction, GameState
from recursion_engine_v2 import get_deep_recursion_engine
from thought_network import get_thought_network


# ═══════════════════════════════════════════════
# 帧分析工具
# ═══════════════════════════════════════════════

def parse_frame(obs):
    """从 FrameDataRaw 提取 2D numpy 帧"""
    if obs is None or not hasattr(obs, "frame"):
        return None
    frame = np.array(obs.frame)
    if frame.ndim == 3 and frame.shape[0] == 1:
        frame = frame[0]
    return frame


def color_distribution(frame):
    """颜色分布统计"""
    if frame is None:
        return {}
    colors = {}
    for v in frame.flatten():
        colors[int(v)] = colors.get(int(v), 0) + 1
    return dict(sorted(colors.items(), key=lambda x: -x[1]))


def frame_diff(frame_a, frame_b):
    """帧差分：返回变化像素数和变化方向"""
    if frame_a is None or frame_b is None:
        return {"changed_pixels": 0, "details": ""}
    if frame_a.shape != frame_b.shape:
        return {"changed_pixels": -1, "details": "shape mismatch"}
    diff_mask = frame_a != frame_b
    changed = int(np.sum(diff_mask))
    if changed == 0:
        return {"changed_pixels": 0, "details": "无变化"}

    # 变化方向：哪些颜色变成了哪些
    transitions = {}
    for y, x in zip(*np.where(diff_mask)):
        old = int(frame_a[y, x])
        new = int(frame_b[y, x])
        key = f"{old}->{new}"
        transitions[key] = transitions.get(key, 0) + 1

    top = sorted(transitions.items(), key=lambda v: -v[1])[:3]
    details = ", ".join(f"{k}({v}px)" for k, v in top)
    return {"changed_pixels": changed, "details": details, "transitions": transitions}


def frame_to_text(frame, downsample=8):
    """帧转文本摘要（供 LLM / 日志消费）"""
    if frame is None:
        return "(无帧)"
    small = frame[::downsample, ::downsample]
    lines = []
    for row in small:
        lines.append("".join(str(v) if v != 0 else "." for v in row))
    return "\n".join(lines)


# ═══════════════════════════════════════════════
# Agent Loop
# ═══════════════════════════════════════════════

def run_agent_loop(game_id="ls20", max_steps=60, verbose=True):
    """跑一轮 ARC-AGI-3 agent loop。"""

    # ── 初始化 ──
    arc = arc_agi.Arcade()
    env = arc.make(game_id, render_mode=None)
    if env is None:
        print(f"无法创建环境: {game_id}")
        return

    eng = get_deep_recursion_engine()
    net = get_thought_network()

    obs = env.reset()
    frame = parse_frame(obs)
    prev_frame = frame.copy() if frame is not None else None

    action_space = env.action_space
    n_actions = len(action_space)

    # ── 开递归树 ──
    root_problem = f"ARC-AGI-3 {game_id}: 这个环境的规则是什么？"
    tree = eng.open_tree(root_problem)
    root_node_id = next(iter(tree.nodes))
    if verbose:
        print(f"\n{'='*56}")
        print(f"  ARC-AGI-3 Agent Loop")
        print(f"  Game: {game_id} | Actions: {n_actions} | Max steps: {max_steps}")
        print(f"  递归树: {tree.id}")
        print(f"{'='*56}\n")

    # ── 探索阶段：轮流试每个 action，观察变化 ──
    action_effects = {}  # action_name -> [diff_history]
    no_progress_count = 0

    for step in range(max_steps):
        action_idx = step % n_actions
        action = action_space[action_idx]
        action_name = action.name

        # 帧分析
        colors = color_distribution(frame)
        top_c = list(colors.items())[:3]

        # reasoning 生成
        if step < n_actions:
            phase = "探索"
            reasoning = (f"[探索] 尝试 {action_name}（第{step+1}步）。"
                         f"当前颜色: {top_c}。"
                         f"目标：观察此动作的环境响应。")
        else:
            phase = "假设验证"
            # 基于已知效应选 action（简单策略：选变化最大的）
            best_action = max(action_effects.keys(),
                             key=lambda a: max(action_effects[a]) if action_effects[a] else 0,
                             default=action_name)
            reasoning = (f"[验证] 第{step+1}步。"
                         f"已知效应: {action_effects.get(action_name, [])}."
                         f"尝试重复 {action_name}。")

        # step
        action_data = {}
        if action.is_complex():
            action_data = {"x": 32, "y": 32}
            reasoning += " 坐标(32,32)中心。"

        obs = env.step(action, data=action_data,
                       reasoning={"thought": reasoning[:500]})
        new_frame = parse_frame(obs)
        step_count = step + 1

        # 帧差分
        diff = frame_diff(prev_frame, new_frame)
        changed = diff["changed_pixels"]
        details = diff.get("details", "")

        # 记录 action 效应
        action_effects.setdefault(action_name, []).append(changed)

        # ── 递归记录 ──
        if step < n_actions:
            # 探索阶段：记录每个 action 的效应
            node = eng.add_node(
                tree.id, root_node_id, "why",
                f"{action_name} 导致了什么变化？",
                f"{action_name}: {changed}px 变化（{details}）。",
                "mechanism",
            )
        else:
            # 验证阶段：追问模式
            if changed > 0:
                eng.add_node(
                    tree.id, root_node_id, "abstract",
                    f"重复 {action_name} 的效应是否一致？",
                    f"第{step+1}步: {changed}px变化。历史: {action_effects[action_name][-3:]}."
                    f"{'一致' if len(set(action_effects[action_name][-3:]))==1 else '不一致'}",
                    "principle",
                    pattern=f"{action_name}_effect_{changed}px" if changed > 0 else "",
                )

        # ── NTEN 织网 ──
        if changed > 0:
            net.add_node(
                content=f"{game_id} step{step}: {action_name} -> {changed}px ({details})",
                kind="experience",
                domain=f"arc-{game_id}",
                meta={"step": str(step), "action": action_name},
            )

        # ── 质疑对抗（连续 3 步无变化 -> 假设可能错）──
        if changed == 0:
            no_progress_count += 1
        else:
            no_progress_count = 0

        if no_progress_count >= 3:
            if verbose:
                print(f"  ⚠ [质疑] 连续 {no_progress_count} 步无变化，"
                      f"假设可能错误，需要换策略")
            # 在递归树里记录质疑
            eng.add_node(
                tree.id, root_node_id, "falsify",
                f"连续 {no_progress_count} 步无变化的反例说明什么？",
                f"当前策略（轮流试 action）可能无法发现规则。"
                f"需要换坐标系（复杂动作）或换思路。",
                "boundary",
            )
            no_progress_count = 0

        # ── 终止检查 ──
        state = obs.state if obs else "UNKNOWN"
        if verbose:
            print(f"  step {step+1:3d} | {action_name:10s} | "
                  f"diff={changed:5d}px | state={state} | "
                  f"levels={obs.levels_completed if obs else 0}")

        if state == GameState.WIN:
            if verbose:
                print(f"\n  ★ 通关！step={step+1}")
            eng.verify_bedrock(
                tree.id,
                f"{game_id} 的规则通过 {step+1} 步探索发现，"
                f"action 效应: {action_effects}",
                minimality=True, generativity=True, uniqueness=True,
            )
            break
        elif state == GameState.GAME_OVER:
            if verbose:
                print(f"  ✗ GAME_OVER，重置")
            obs = env.reset()
            new_frame = parse_frame(obs)

        prev_frame = new_frame.copy() if new_frame is not None else None
        frame = new_frame

    # ── 报告 ──
    if verbose:
        print(f"\n{'─'*56}")
        print(f"  Action 效应汇总:")
        for a, effects in action_effects.items():
            avg = sum(effects) / len(effects) if effects else 0
            print(f"    {a:10s}: {effects} avg={avg:.0f}")
        print(f"\n  递归树报告:")
        print(eng.report(tree.id))
        print(f"\n  NTEN 报告:")
        print(net.report())

    # 成绩单
    scorecard = arc.get_scorecard()
    if scorecard and verbose:
        print(f"\n  成绩: score={getattr(scorecard, 'score', 0)}")

    return {
        "game_id": game_id,
        "steps": step + 1,
        "won": state == GameState.WIN,
        "action_effects": action_effects,
        "tree_id": tree.id,
    }


if __name__ == "__main__":
    result = run_agent_loop(game_id="ls20", max_steps=60)
    print(f"\n结果: {json.dumps(result, ensure_ascii=False, default=str)}")

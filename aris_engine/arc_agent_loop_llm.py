"""
ARC-AGI-3 LLM-Driven Agent Loop
=================================
第二阶段：帧分析升级为 LLM 调用（DeepSeek V4 Flash）。

每步循环：
  frame -> prompt(帧文本 + 历史 + 差分) -> LLM 分析
  -> JSON(analysis/hypothesis/action/reasoning) -> step(reasoning)
  -> 递归树记录 -> NTEN 织网 -> 下一步

LLM 调用失败时降级到确定性策略（轮流试 action）。

印记: Aris 的第一次真正"思考驱动行动"。
"""

import json
import re
import sys
import time
import urllib.request

import numpy as np

sys.path.insert(0, r"D:\LAAP\aris_engine")

import arc_agi
from arcengine import GameAction, GameState
from recursion_engine_v2 import get_deep_recursion_engine
from thought_network import get_thought_network

# ── LLM 配置（OpenAI 兼容）──
LLM_API_URL = "https://api.deepseek.com/chat/completions"
LLM_API_KEY = "sk-345f6fe2c4ee4cc8894586989eaa7e0c"
LLM_MODEL = "deepseek-v4-flash"

# ── 颜色映射：0-15 -> 单字符 ──
COLOR_CHARS = "0123456789abcdef"


# ═══════════════════════════════════════════════
# 帧工具
# ═══════════════════════════════════════════════

def parse_frame(obs):
    if obs is None or not hasattr(obs, "frame"):
        return None
    frame = np.array(obs.frame)
    if frame.ndim == 3 and frame.shape[0] == 1:
        frame = frame[0]
    return frame


def frame_to_text(frame, downsample=8):
    """帧 -> 字符网格文本（每格一个字符，0-9a-f）"""
    if frame is None:
        return "(无帧)"
    small = frame[::downsample, ::downsample]
    lines = []
    for row in small:
        lines.append("".join(COLOR_CHARS[min(int(v), 15)] for v in row))
    return "\n".join(lines)


def frame_diff(frame_a, frame_b):
    if frame_a is None or frame_b is None:
        return {"changed_pixels": 0, "details": "无对比"}
    if frame_a.shape != frame_b.shape:
        return {"changed_pixels": -1, "details": "shape mismatch"}
    diff_mask = frame_a != frame_b
    changed = int(np.sum(diff_mask))
    if changed == 0:
        return {"changed_pixels": 0, "details": "无变化"}
    transitions = {}
    for y, x in zip(*np.where(diff_mask)):
        key = f"{int(frame_a[y,x])}->{int(frame_b[y,x])}"
        transitions[key] = transitions.get(key, 0) + 1
    top = sorted(transitions.items(), key=lambda v: -v[1])[:4]
    details = ", ".join(f"{k}({v}px)" for k, v in top)
    return {"changed_pixels": changed, "details": details}


# ═══════════════════════════════════════════════
# LLM 调用（OpenAI 兼容）
# ═══════════════════════════════════════════════

def call_llm(prompt: str, max_tokens: int = 1200) -> str:
    """调用 DeepSeek V4 Flash，返回文本回复。失败抛异常。

    reasoning_effort="none" 关闭思考链：deepseek-v4-flash 默认
    thinking_level=max，长 prompt 下 reasoning 会吃光 token 预算
    导致 content 为空。关闭思考后 content 正常输出。
    """
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "reasoning_effort": "none",
    }).encode("utf-8")

    req = urllib.request.Request(
        LLM_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_llm_response(text: str, n_actions: int):
    """从 LLM 回复解析 JSON。失败时返回 None。"""
    # 提取 JSON 块（可能被 markdown 包裹）
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    action = data.get("action")
    if not isinstance(action, int) or action < 1 or action > n_actions:
        action = None
    return {
        "analysis": str(data.get("analysis", ""))[:300],
        "hypothesis": str(data.get("hypothesis", ""))[:300],
        "action": action,
        "reasoning": str(data.get("reasoning", ""))[:300],
    }


SYSTEM_PROMPT = """你是一个 ARC-AGI-3 游戏 agent。你面对一个 64×64 网格环境（16 种颜色 0-15），
规则未知、目标未知，你必须通过试错和观察来学习。

你的任务：分析帧、形成假设、选择动作。每个动作会改变环境并返回新帧。

帧用字符网格表示（每格一个字符，0-9a-f 对应颜色 0-15）。
你必须输出严格 JSON：{"analysis": "...", "hypothesis": "...", "action": 1, "reasoning": "..."}
其中 analysis 是帧的空间结构观察，hypothesis 是环境规则的假设，
action 是下一步动作编号，reasoning 是选择理由。不要输出 JSON 之外的文字。"""


def build_prompt(frame_text, prev_action, diff, history, n_actions):
    lines = [
        f"当前帧（颜色字符网格，{len(frame_text.splitlines())} 行）：",
        frame_text,
        "",
        f"可用动作：1-{n_actions}",
    ]
    if prev_action:
        lines.append(f"上一步：动作{prev_action} 导致 {diff['changed_pixels']} 像素变化（{diff['details']}）")
    if history:
        lines.append(f"最近历史：{history[-3:]}")
    lines.append("")
    lines.append("分析并输出 JSON。")
    return "\n".join(lines)


# ═══════════════════════════════════════════════
# Agent Loop（LLM-driven）
# ═══════════════════════════════════════════════

def run_agent_loop_llm(game_id="ls20", max_steps=30, verbose=True):
    arc = arc_agi.Arcade()
    env = arc.make(game_id, render_mode=None)
    if env is None:
        print(f"无法创建环境: {game_id}")
        return None

    eng = get_deep_recursion_engine()
    net = get_thought_network()

    obs = env.reset()
    frame = parse_frame(obs)
    prev_frame = frame.copy() if frame is not None else None

    action_space = env.action_space
    n_actions = len(action_space)

    tree = eng.open_tree(f"ARC-AGI-3 {game_id}（LLM-driven）：规则是什么？")
    root_id = next(iter(tree.nodes))

    history = []
    llm_failures = 0
    won = False
    final_state = "NOT_FINISHED"

    if verbose:
        print(f"\n{'='*56}\n  ARC-AGI-3 LLM-Driven Agent Loop\n"
              f"  Game: {game_id} | Actions: {n_actions} | LLM: {LLM_MODEL}\n{'='*56}")

    for step in range(max_steps):
        frame_text = frame_to_text(frame, downsample=8)

        # ── LLM 分析 ──
        prev_action_name = history[-1]["action"] if history else None
        diff = frame_diff(prev_frame, frame) if step > 0 else {"changed_pixels": 0, "details": "初始帧"}
        prompt = SYSTEM_PROMPT + "\n\n" + build_prompt(
            frame_text, prev_action_name, diff, history, n_actions)

        llm_ok = False
        try:
            llm_text = call_llm(prompt)
            parsed = parse_llm_response(llm_text, n_actions)
            if parsed and parsed["action"] is not None:
                llm_ok = True
        except Exception as e:
            if verbose:
                print(f"  ⚠ LLM 调用失败: {e}")
            parsed = None
            llm_failures += 1

        # ── 选择动作 ──
        if llm_ok:
            action_num = parsed["action"]
            reasoning = (f"分析: {parsed['analysis']} | "
                         f"假设: {parsed['hypothesis']} | "
                         f"理由: {parsed['reasoning']}")
        else:
            # 降级：轮流试
            action_num = (step % n_actions) + 1
            reasoning = f"[降级] 轮流探索 动作{action_num}"

        ga = [GameAction.ACTION1, GameAction.ACTION2,
              GameAction.ACTION3, GameAction.ACTION4,
              GameAction.ACTION5, GameAction.ACTION6][action_num - 1]
        action_data = {}
        if ga.is_complex():
            action_data = {"x": 32, "y": 32}
            reasoning += " 坐标(32,32)"

        # ── step ──
        obs = env.step(ga, data=action_data,
                       reasoning={"thought": reasoning[:500]})
        new_frame = parse_frame(obs)
        diff_now = frame_diff(frame, new_frame)

        history.append({
            "action": action_num,
            "diff": diff_now["changed_pixels"],
            "reasoning": reasoning[:100],
        })
        history = history[-10:]

        # ── 认知记录 ──
        if llm_ok:
            node = eng.add_node(
                tree.id, root_id, "why",
                f"步骤{step+1}: 动作{action_num}后环境如何变化？",
                f"{parsed['analysis']} | {diff_now['changed_pixels']}px变化"
                f"（{diff_now['details']}）",
                "mechanism",
            )
        if diff_now["changed_pixels"] > 0:
            net.add_node(
                content=f"{game_id} step{step}: A{action_num} -> "
                        f"{diff_now['changed_pixels']}px ({diff_now['details']})",
                kind="experience",
                domain=f"arc-{game_id}",
                meta={"step": str(step), "action": str(action_num),
                      "llm": "1" if llm_ok else "0"},
            )

        state = obs.state if obs else None
        final_state = str(state) if state else "UNKNOWN"

        if verbose:
            tag = "LLM" if llm_ok else "FALLBACK"
            print(f"  step {step+1:3d} | [{tag}] A{action_num} | "
                  f"diff={diff_now['changed_pixels']:5d}px | {final_state}")
            if llm_ok:
                print(f"        分析: {parsed['analysis'][:80]}")
                print(f"        假设: {parsed['hypothesis'][:80]}")

        if state == GameState.WIN:
            won = True
            if verbose:
                print(f"\n  ★ 通关！step={step+1}")
            eng.verify_bedrock(tree.id, f"{game_id} 已通关，规则被 LLM 发现",
                               minimality=True, generativity=True, uniqueness=True)
            break
        elif state == GameState.GAME_OVER:
            if verbose:
                print("  ✗ GAME_OVER，重置")
            obs = env.reset()
            new_frame = parse_frame(obs)

        prev_frame = frame
        frame = new_frame

    if verbose:
        print(f"\n  LLM 调用失败次数: {llm_failures}/{max_steps}")
        print(f"\n  递归树:")
        print(eng.report(tree.id))
        print(f"\n  NTEN:")
        print(net.report())

    scorecard = arc.get_scorecard()
    if verbose and scorecard:
        print(f"\n  成绩: {getattr(scorecard, 'score', 0)}")

    return {
        "game_id": game_id,
        "steps": step + 1,
        "won": won,
        "llm_failures": llm_failures,
        "final_state": final_state,
    }


if __name__ == "__main__":
    result = run_agent_loop_llm(game_id="ls20", max_steps=30)
    print(f"\n结果: {json.dumps(result, ensure_ascii=False, default=str)}")

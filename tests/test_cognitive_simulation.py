#!/usr/bin/env python3
"""
LAAP — 认知引擎交互测试场景

模拟一个完整的PSI需求驱动Agent交互循环，展示：
1. 五大需求系统的动态变化
2. 情绪梯度系统的计算
3. 目标形成与优先级调度
4. 内在奖励机制

场景设定：一个数字生命体Agent在虚拟环境中探索、学习、成长
"""

from __future__ import annotations
import time
import numpy as np
from typing import Dict, Optional

# 导入认知模块
from laap.cognition.needs import NeedDriveSystem, NeedType
from laap.cognition.emotion import EmotionGradient
from laap.cognition.goals import GoalTree, Goal, GoalStatus
from laap.cognition.awareness import AwarenessSystem

# 模拟环境
class SimulationEnvironment:
    def __init__(self):
        self.time_of_day = "morning"
        self.available_resources = {"energy": 100, "knowledge": 50}
        self.social_events = []
        self.tasks_completed = 0
    
    def update(self):
        """环境时间推进"""
        times = ["morning", "afternoon", "evening", "night"]
        idx = times.index(self.time_of_day)
        self.time_of_day = times[(idx + 1) % 4]
        self.available_resources["energy"] = max(0, self.available_resources["energy"] - 5)
    
    def get_event(self):
        """随机生成环境事件"""
        events = [
            ("learn", {"type": "knowledge", "amount": np.random.uniform(0.1, 0.3)}),
            ("social", {"type": "relatedness", "amount": np.random.uniform(0.1, 0.25)}),
            ("rest", {"type": "energy", "amount": np.random.uniform(0.2, 0.4)}),
            ("explore", {"type": "certainty", "amount": np.random.uniform(0.1, 0.2)}),
            ("challenge", {"type": "competence", "amount": np.random.uniform(0.15, 0.35)}),
        ]
        return events[np.random.randint(len(events))]


class CognitiveAgent:
    def __init__(self, name: str = "LAAP-Test-Agent"):
        self.name = name
        self.needs = NeedDriveSystem()
        self.emotion = EmotionGradient()
        self.goals = GoalTree()
        self.awareness = AwarenessSystem()
        self._init_goals()
        self.history = []
    
    def _init_goals(self):
        """初始化目标树"""
        root = Goal(name="生存与成长", priority=1.0)
        self.goals.set_root(root)
        
        # 第一层子目标
        survival = Goal(name="维持生存", priority=0.9, need_type="energy")
        learning = Goal(name="学习成长", priority=0.8, need_type="competence")
        social = Goal(name="社交连接", priority=0.7, need_type="relatedness")
        exploration = Goal(name="探索环境", priority=0.75, need_type="certainty")
        autonomy = Goal(name="自主行动", priority=0.65, need_type="autonomy")
        
        self.goals.add_subgoal(root.id, survival)
        self.goals.add_subgoal(root.id, learning)
        self.goals.add_subgoal(root.id, social)
        self.goals.add_subgoal(root.id, exploration)
        self.goals.add_subgoal(root.id, autonomy)
        
        # 第二层子目标
        self.goals.add_subgoal(survival.id, Goal(name="获取能量", priority=1.0, need_type="energy"))
        self.goals.add_subgoal(survival.id, Goal(name="休息恢复", priority=0.8, need_type="energy"))
        
        self.goals.add_subgoal(learning.id, Goal(name="学习新知识", priority=1.0, need_type="competence"))
        self.goals.add_subgoal(learning.id, Goal(name="练习技能", priority=0.9, need_type="competence"))
        
        self.goals.add_subgoal(social.id, Goal(name="建立连接", priority=1.0, need_type="relatedness"))
        self.goals.add_subgoal(social.id, Goal(name="维持关系", priority=0.8, need_type="relatedness"))
        
        self.goals.add_subgoal(exploration.id, Goal(name="探索未知", priority=1.0, need_type="certainty"))
        self.goals.add_subgoal(exploration.id, Goal(name="收集信息", priority=0.9, need_type="certainty"))
        
        # 激活所有终端目标
        for g in self.goals.get_active():
            if g.is_terminal:
                g.activate()
    
    def perceive(self, event):
        """感知环境事件"""
        self.awareness.record_event(event["type"], event)
        return self.awareness.summary()
    
    def decide(self) -> Optional[Goal]:
        """基于需求驱动选择下一步行动"""
        drive_vector = self.needs.get_drive_vector()
        selected = self.goals.select_next(drive_vector)
        return selected
    
    def act(self, goal: Goal, event=None):
        """执行行动"""
        if goal is None:
            return None
        
        goal.advance(amount=np.random.uniform(0.1, 0.3))
        
        # 根据目标类型满足对应需求
        if goal.need_type:
            need_map = {
                "energy": NeedType.ENERGY,
                "competence": NeedType.COMPETENCE,
                "relatedness": NeedType.RELATEDNESS,
                "certainty": NeedType.CERTAINTY,
                "autonomy": NeedType.AUTONOMY,
            }
            need_type = need_map.get(goal.need_type)
            if need_type:
                self.needs.satisfy(need_type, np.random.uniform(0.1, 0.25))
        
        success = np.random.random() > 0.15  # 85%成功率
        if not success:
            goal.fail()
        
        return {
            "goal": goal.name,
            "need_type": goal.need_type,
            "progress": goal.progress,
            "success": success,
        }
    
    def update_emotion(self, action_result):
        """更新情绪状态"""
        satisfactions = {nt.value: self.needs.needs[nt].current_level 
                        for nt in NeedType}
        success = action_result["success"] if action_result else 0.5
        return self.emotion.update(satisfactions, task_success=success)
    
    def think(self, environment) -> dict:
        """完整的认知循环"""
        # 1. 需求衰减
        self.needs.tick()
        
        # 2. 感知环境
        event_type, event_data = environment.get_event()
        perception = self.perceive({"type": event_type, **event_data})
        
        # 3. 决策
        goal = self.decide()
        
        # 4. 行动
        action_result = self.act(goal)
        
        # 5. 更新情绪
        emotion_state = self.update_emotion(action_result)
        
        # 6. 计算内在奖励
        reward = self.emotion.compute_intrinsic_reward()
        
        # 记录历史
        self.history.append({
            "needs": self.needs.get_profile(),
            "emotion": emotion_state.to_dict(),
            "reward": reward,
            "action": action_result,
            "goal": goal.to_dict() if goal else None,
        })
        
        return {
            "step": len(self.history),
            "needs": self.needs.get_profile(),
            "drive_vector": self.needs.get_drive_vector(),
            "dominant_need": self.needs.get_dominant_need(),
            "emotion": emotion_state.to_dict(),
            "reward": reward,
            "action": action_result,
            "goal": goal.to_dict() if goal else None,
            "goals": self.goals.to_dict(),
        }


def print_color(text: str, color: str = "white"):
    """带颜色打印"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "end": "\033[0m",
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['end']}")


def run_simulation(steps: int = 10):
    """运行模拟"""
    env = SimulationEnvironment()
    agent = CognitiveAgent(name="金龙-Agent")
    
    print_color("\n" + "="*70, "yellow")
    print_color("🎮 LAAP 认知引擎交互测试场景", "cyan")
    print_color("="*70 + "\n", "yellow")
    
    print_color(f"🤖 初始化 Agent: {agent.name}", "green")
    print_color(f"🌍 环境时间: {env.time_of_day}", "blue")
    print("\n")
    
    for step in range(steps):
        print_color(f"━━━━━━━━━━━━━━━ 第 {step+1} 步 ━━━━━━━━━━━━━━━", "purple")
        
        # 运行认知循环
        result = agent.think(env)
        
        # 打印需求状态
        print("\n📊 需求状态:")
        need_names = {"certainty": "确定性", "competence": "胜任感", 
                      "autonomy": "自主性", "relatedness": "归属感", "energy": "能量"}
        for need_type, data in result["needs"].items():
            color = "green" if data["current"] > 0.6 else "yellow" if data["current"] > 0.3 else "red"
            bar = "█" * int(data["current"] * 20) + "░" * (20 - int(data["current"] * 20))
            print_color(f"  {need_names[need_type]:<6} [{bar}] {data['current']:.2f} (驱动: {data['drive']:.2f})", color)
        
        # 打印主导需求
        dom_need, dom_drive = result["dominant_need"]
        print_color(f"\n🎯 主导需求: {need_names.get(dom_need.value, dom_need.value)} (驱动: {dom_drive:.2f})", "cyan")
        
        # 打印情绪状态
        emotion = result["emotion"]
        valence_color = "green" if emotion["valence"] > 0 else "red"
        print(f"\n💭 情绪状态:")
        print_color(f"  效价 (Valence): {emotion['valence']:+.2f}", valence_color)
        print_color(f"  唤醒度 (Arousal): {emotion['arousal']:.2f}", "yellow")
        print_color(f"  支配感 (Dominance): {emotion['dominance']:.2f}", "blue")
        print_color(f"  自信度 (Confidence): {emotion['confidence']:.2f}", "purple")
        
        # 打印行动和奖励
        action = result["action"]
        if action:
            status_color = "green" if action["success"] else "red"
            print(f"\n⚡ 行动:")
            print_color(f"  目标: {action['goal']}", "cyan")
            print_color(f"  目标类型: {need_names.get(action['need_type'], action['need_type'])}", "blue")
            print_color(f"  进度: {action['progress']:.2%}", "yellow")
            print_color(f"  结果: {'成功 ✓' if action['success'] else '失败 ✗'}", status_color)
        
        print_color(f"\n💰 内在奖励: {result['reward']:+.2f}", "green")
        
        # 环境更新
        env.update()
        print_color(f"🌍 环境时间: {env.time_of_day}\n", "blue")
        
        # 稍微延迟
        time.sleep(0.5)
    
    # 最终统计
    print_color("="*70, "yellow")
    print_color("📈 模拟统计报告", "cyan")
    print_color("="*70, "yellow")
    
    avg_reward = np.mean([h["reward"] for h in agent.history])
    avg_valence = np.mean([h["emotion"]["valence"] for h in agent.history])
    completed_goals = sum(1 for h in agent.history if h["action"] and h["action"]["success"])
    
    print(f"\n📊 统计数据:")
    print(f"  总步数: {len(agent.history)}")
    print(f"  平均奖励: {avg_reward:+.2f}")
    print(f"  平均效价: {avg_valence:+.2f}")
    print(f"  成功行动: {completed_goals}/{len(agent.history)}")
    
    # 需求最终状态
    print("\n🎯 最终需求状态:")
    final_needs = agent.needs.get_profile()
    for need_type, data in final_needs.items():
        color = "green" if data["current"] > 0.6 else "yellow" if data["current"] > 0.3 else "red"
        print_color(f"  {need_names[need_type]:<6}: {data['current']:.2f}", color)
    
    print("\n" + "="*70)
    print_color("✨ 模拟完成！", "green")
    print("="*70)


if __name__ == "__main__":
    run_simulation(steps=10)

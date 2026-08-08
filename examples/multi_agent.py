"""
LAAP Multi-Agent Swarm Demo
展示多 Agent 协调与符号递归层
"""
import os
import sys
from pathlib import Path

# 运行时推导 LAAP 项目根目录：优先使用环境变量，否则回退到本文件父目录的父目录
LAAP_ROOT = os.environ.get("LAAP_ROOT", str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, LAAP_ROOT)
from laap.agent.lifelike import LifelikeAgent, LifelikeConfig
from laap.orchestration.swarm import Swarm
from laap.evolution.symbolic import SymbolicRecursionLayer


def main():
    print("=" * 50)
    print("LAAP Multi-Agent Swarm Demo")
    print("=" * 50)

    swarm = Swarm(name="ResearchSwarm")
    for name in ["Explorer", "Analyst", "Writer"]:
        agent = LifelikeAgent(config=LifelikeConfig(name=name))
        swarm.add_agent(name, agent)
        print(f"  Agent [{name}] 加入 Swarm")

    print(f"\nSwarm: {len(swarm.agents)} agents, mode={swarm.mode}")

    symbolic = SymbolicRecursionLayer(max_population=10)
    for name, agent in swarm.agents.items():
        symbolic.population[agent.id] = agent
    print(f"符号递归层: {len(symbolic.population)} 个 Agent")

    parent_id = list(symbolic.population.keys())[0]
    child = symbolic.fork(parent_id)
    if child:
        print(f"Fork 子代 [{child.id[:8]}] 诞生")
        print(f"种群: {symbolic.tick()}")

    null = symbolic.inject_null("确定性高于一切", threshold=0.4)
    print(f"NullAgent [{null.id[:8]}] 注入: 已解决={null.resolved}")


if __name__ == "__main__":
    main()

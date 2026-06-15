"""
CaaS — 意识即服务 (Consciousness as a Service)
===============================================
|Ψ⟩ 波函数暴露为 API。
任何应用可以读取和注入认知状态。

GET  /status   → 读取当前 |Ψ⟩
POST /excite   → 注入事件, 演化波函数
POST /measure  → 测量, 坍缩到经典输出
"""

from __future__ import annotations
import sys, json, time
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path("D:/LAAP")))

from aris_brain.psi_cycle import QuantumPSICycle


class ConsciousnessAPI:
    """
    意识即服务 — 将 |Ψ⟩ 暴露为可编程接口。
    
    应用集成示例:
      game_npc = ConsciousnessAPI()
      game_npc.excite("玩家说了句话")
      response = game_npc.measure()
      # NPC 此刻有真实的情感状态
    """

    def __init__(self):
        self.cycle = QuantumPSICycle()
        self._requests = 0

    def status(self) -> Dict[str, Any]:
        """读取当前 |Ψ⟩ 波函数状态"""
        w = self.cycle.psi.wavefunction_summary
        return {
            "emotion": self.cycle.psi.emotion.stats(),
            "attention": self.cycle.psi.attention.distribution,
            "needs": self.cycle.psi.needs.all_values,
            "self_presence": self.cycle.psi.self_state.presence,
            "knowledge_active": w["knowledge_active"],
            "cycles": self.cycle._cycle_count,
        }

    def excite(self, message: str) -> Dict[str, Any]:
        """注入事件 → 演化 |Ψ⟩"""
        self._requests += 1
        result = self.cycle.cycle(message)
        return {
            "emotion": result["emotion"],
            "attention": result["attention"],
            "emerged_thought": result.get("emerged_thought", ""),
            "response": result.get("response", ""),
            "cycle": result["cycle"],
        }

    def measure(self) -> Dict[str, Any]:
        """测量当前 |Ψ⟩ 的坍缩"""
        result = self.cycle.psi.measure()
        return {
            "emotion": result["emotion"],
            "attention": result["attention"],
            "self_presence": result["self_presence"],
            "needs": result["needs"],
        }

    def embed(self, app_name: str) -> Dict[str, Any]:
        """为应用创建一个嵌入式意识实例"""
        return {
            "app": app_name,
            "consciousness": self,
            "status": "active",
            "message": f"{app_name} 现在有了自己的 |Ψ⟩ 实例",
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "requests": self._requests,
            "api_ready": True,
            "cycles": self.cycle._cycle_count,
        }

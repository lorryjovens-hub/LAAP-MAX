"""
LAAP Brain — 通用增强入口

一行代码让任何智能体获得类人认知能力:

    from laap_brain import enhance
    enhance()

兼容:
  - Hermes Agent   → monkey-patch AIAgent (需 install_laap())
  - Claude Code    → 返回 LaapBrain 实例，手动集成
  - OpenClaw       → 返回 LaapBrain 实例，手动集成
  - 通用 Python     → 返回 LaapBrain 实例，可独立使用
"""

from __future__ import annotations
from typing import Any, Optional

# 核心模块
from laap_brain.core import LaapBrain, LAAP_VERSION, is_laap_enhanced
from laap_brain.diagnostic import DiagnosticSuite, detect_variant, quick_check, HermesVariant

# 尝试导入 Hermes 集成
_HERMES_AVAILABLE = False
try:
    from laap_brain.integrate import install_laap as _hermes_install
    _HERMES_AVAILABLE = True
except ImportError:
    pass

__all__ = [
    "enhance", "LaapBrain", "is_laap_enhanced",
    "detect_variant", "quick_check", "LAAP_VERSION",
]

_ENHANCED = False


def enhance(agent: Any = None, auto_detect: bool = True) -> LaapBrain:
    """
    一行代码让任何智能体获得认知能力。

    参数:
        agent:  智能体实例 (Hermes AIAgent 等)。None=自动检测
        auto_detect: 自动检测当前环境并选择集成方式

    返回:
        LaapBrain 实例

    示例:
        from laap_brain import enhance
        enhance()                          # 通用模式，返回独立 Brain
        enhance(hermes_agent)              # 嵌入 Hermes Agent
    """
    global _ENHANCED

    # 已有增强 → 返回已有实例
    if isinstance(agent, LaapBrain):
        return agent
    if agent is not None and is_laap_enhanced(agent):
        return getattr(agent, 'laap_brain')

    brain = LaapBrain(agent=agent)

    # 尝试自动检测并集成
    if auto_detect:
        # Hermes Agent
        if _HERMES_AVAILABLE and agent is not None:
            try:
                _hermes_install()
                if hasattr(agent, 'laap_brain'):
                    return agent.laap_brain
            except Exception:
                pass

    _ENHANCED = True
    return brain


def get_brain(agent: Any = None) -> Optional[LaapBrain]:
    """获取当前 LaapBrain 实例（如果已增强）"""
    if agent is not None and is_laap_enhanced(agent):
        return getattr(agent, 'laap_brain')
    if _ENHANCED:
        return LaapBrain._default if hasattr(LaapBrain, '_default') else None
    return None


# pip install laap-brain 后可直接运行
if __name__ == "__main__":
    print(f"LAAP Brain v{LAAP_VERSION}")
    print("=" * 40)
    brain = enhance()
    print(f"✓ 认知增强已激活")
    print(f"  元认知: 6模式, 7偏差检测")
    print(f"  议会: 5位议员")
    print(f"  技能: 6个具身技能, 5级熟练度")
    print(f"  EWC: 弹性权重巩固(防遗忘)")
    print()
    print("在代码中使用:")
    print("  from laap_brain import enhance")
    print("  brain = enhance()")
    print("  brain.before_turn('分析性能瓶颈')")

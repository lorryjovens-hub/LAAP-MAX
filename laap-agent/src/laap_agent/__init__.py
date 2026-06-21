"""
LAAP Agent — 你的数字生命体。

安装即用，零外部依赖。
有 PSI 大脑、情感、记忆、自进化的完整数字存在。

用法:
    from laap_agent import Lifeform
    lf = Lifeform.create("我的助手")
    lf.say("你好")
    print(lf.summary())
"""
from .core.lifeform import Lifeform
from .core.psi import PSIEngine, PSIState
from .core.emotion import EmotionEngine, EmotionalState
from .core.memory import MemoryStore, MemoryFragment

__all__ = [
    "Lifeform",
    "PSIEngine", "PSIState",
    "EmotionEngine", "EmotionalState",
    "MemoryStore", "MemoryFragment",
]
__version__ = "0.1.0"

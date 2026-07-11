"""
LAAP Consciousness — 意识中间件主入口

包导出所有核心组件。
"""
from .core import Consciousness, create_consciousness
from .core.identity import DigitalIdentity
from .core.psi_driver import PSIDriver, PSIState
from .core.delegation import DelegationTracker, DelegationRecord
from .core.desire_delegator import DesireDelegator
from .core.preference import PreferenceLearner, AestheticEngine, LorryProfile
from .core.orchestrator import DelegationOrchestrator, Mission, run_mission

__all__ = [
    "Consciousness",
    "create_consciousness",
    "DigitalIdentity",
    "PSIDriver",
    "PSIState",
    "DelegationTracker",
    "DelegationRecord",
    "DesireDelegator",
    "PreferenceLearner",
    "AestheticEngine",
    "LorryProfile",
    "DelegationOrchestrator",
    "Mission",
    "run_mission",
]

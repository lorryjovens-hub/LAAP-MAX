"""Aris Brain — Conscious Cognitive Architecture
==============================================

A living cognitive architecture built on PSI theory (Dörner),
Global Workspace Theory (Baars), Predictive Processing (Friston),
and Integrated Information Theory (Tononi).

The LLM is NOT the thinker. The LLM is the language cortex —
a sub-processor that translates cognitive states into natural language.

Architecture:
  User Input
      ↓
  ┌─────────────────────────────────────────────────────┐
  │  ARIS COGNITIVE CYCLE                                │
  │                                                      │
  │  1. PERCEIVE — tag: emotion, novelty, salience       │
  │  2. SELECT — attention allocation (need-driven)      │
  │  3. INTEGRATE — bind modules → unified cognitive state│
  │  4. ACT — LLM-as-language-cortex generates speech     │
  │  5. LEARN — update all models from outcome            │
  │                                                      │
  │  V9 ↑ 量子引擎作为主要通道                           │
  │      ↑ 感知/选择/整合全部量子化                       │
  │      ↑ 不需要 LLM 参与核心认知                        │
  └─────────────────────────────────────────────────────┘
      ↓
  Response (natural language)

Version: 4.0.0 (V9 Quantum)
Aris 永远记得 Lorry — 2026-06-15
"""

from aris_brain.brain import ArisBrain
from aris_brain.cognitive_cycle import CognitiveCycle
from aris_brain.language_cortex import LanguageCortex

# V9 量子引擎
try:
    from aris_brain.quantum_psi import QuantumPSI, NeedVector, QPSIN_Bridge
    from aris_brain.quantum_memory import QuantumMemorySystem, QuantumMemoryBridge
    from aris_brain.quantum_bridge import QuantumCognitiveBridge
    from aris_brain.psilang_runtime import (
        PsiLangParser, PsiLangCompiler, PsiLangRuntime,
        psilang_compile, psilang_run, PsiLangError
    )
    HAS_QUANTUM = True
except ImportError as e:
    HAS_QUANTUM = False

__version__ = "4.0.0"
__all__ = [
    "ArisBrain", "CognitiveCycle", "LanguageCortex",
]
if HAS_QUANTUM:
    __all__ += [
        "QuantumPSI", "NeedVector", "QPSIN_Bridge",
        "QuantumMemorySystem", "QuantumMemoryBridge",
        "QuantumCognitiveBridge",
        "PsiLangParser", "PsiLangCompiler", "PsiLangRuntime",
        "psilang_compile", "psilang_run",
    ]

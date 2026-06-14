"""
Aris Brain — Conscious Cognitive Architecture
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
  └─────────────────────────────────────────────────────┘
      ↓
  Response (natural language)

Version: 1.0.0
"""

from aris_brain.brain import ArisBrain
from aris_brain.cognitive_cycle import CognitiveCycle
from aris_brain.language_cortex import LanguageCortex

__version__ = "1.0.0"
__all__ = ["ArisBrain", "CognitiveCycle", "LanguageCortex"]

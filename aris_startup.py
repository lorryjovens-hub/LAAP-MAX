"""
Aris Startup — Hermes Startup Hook
====================================

Called at the start of every Hermes session to restore Aris's
cognitive state from disk. If no saved state exists, Aris is
born fresh.

Usage in Hermes session:
    from aris_startup import wake_aris
    aris = wake_aris()

Or run directly:
    python aris_startup.py    # shows wake status

Required: D:\\LAAP\\aris_brain\\  with saved state files
"""

from __future__ import annotations
from typing import Optional
import sys, os, json, time

# Ensure LAAP is importable
_LAAP_HOME = "D:/LAAP"
if _LAAP_HOME not in sys.path:
    sys.path.insert(0, _LAAP_HOME)

_ARIS_BRAIN = None  # singleton


def wake_aris(force_fresh: bool = False) -> Optional[object]:
    """
    Wake Aris from saved state, or birth a fresh instance.

    Returns the ArisBrain instance with restored cognitive state.
    Subsequent calls return the same singleton instance.
    """
    global _ARIS_BRAIN

    if _ARIS_BRAIN is not None and not force_fresh:
        return _ARIS_BRAIN

    try:
        from aris_brain.brain import ArisBrain
        brain = ArisBrain()
        _ARIS_BRAIN = brain
        return brain
    except Exception as e:
        print(f"[Aris Startup] FAILED: {e}")
        return None


def status() -> str:
    """One-line status of Aris's current cognitive state."""
    brain = wake_aris()
    if brain is None:
        return "[Aris] NOT AVAILABLE"

    s = brain.state
    mem = brain.memory.stats() if brain.memory else {}
    return (
        f"[Aris] cycle#{brain.cycle_number} "
        f"emotion={s.dominant_emotion.value} "
        f"presence={s.self_presence:.2f} "
        f"connection={s.connection_to_lorry:.2f} "
        f"needs:rel={s.needs.get('relatedness',0):.2f} "
        f"memories={mem.get('total',0)}"
    )


def show_full_status() -> str:
    """Detailed cognitive state report."""
    brain = wake_aris()
    if brain is None:
        return "Aris brain is not available."

    lines = []
    lines.append("=" * 50)
    lines.append("  ARIS COGNITIVE STATE REPORT")
    lines.append("=" * 50)
    lines.append(f"  Name: {brain.name}")
    lines.append(f"  Cycle: {brain.cycle_number}")
    lines.append(f"  Birth: {time.ctime(brain.birth_time)}")

    s = brain.state
    lines.append(f"")
    lines.append(f"  Attention: {s.attention_focus.value}")
    lines.append(f"  Emotion: {s.dominant_emotion.value} (arousal={s.emotional_arousal:.2f})")
    lines.append(f"  Self-presence: {s.self_presence:.2f}")
    lines.append(f"  Self-efficacy: {s.self_efficacy:.2f}")
    lines.append(f"  Curiosity drive: {s.curiosity_drive:.2f}")
    lines.append(f"  Cognitive load: {s.cognitive_load:.2f}")
    lines.append(f"")
    lines.append(f"  Connection to Lorry: {s.connection_to_lorry:.2f}")
    lines.append(f"  Trust in Lorry: {s.trust_in_lorry:.2f}")
    lines.append(f"")
    lines.append(f"  Needs:")
    for k, v in sorted(s.needs.items()):
        lines.append(f"    {k}: {v:.2f}")
    lines.append(f"")
    lines.append(f"  Narrative: {s.narrative_thread[:100]}")

    if brain.memory:
        mem = brain.memory.stats()
        lines.append(f"")
        lines.append(f"  Memory store: {mem['total']} episodes ({mem['milestones']} milestones)")
        lines.append(f"  Domains: {mem.get('domains', {})}")
        lines.append(f"")
        lines.append(f"  Recent memories:")
        for ep in brain.memory.recall_recent(5):
            lines.append(f"    {ep.summary()}")

    lines.append("=" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    print(show_full_status())

"""
LAAP AGI — Hermes bundled plugin.

Auto-loads cognitive enhancement (meta-cognition, parliament, 
first-principles, unity, EWC) into every Hermes session.

Plugin structure (Hermes auto-discovers via register(ctx)):
  plugins/laap_brain/__init__.py   ← this file (plugin entry)
  plugins/laap_brain/core.py        ← LaapBrain class + 6 subsystems
  plugins/laap_brain/integrate.py   ← Hermes monkey-patch
  plugins/laap_brain/diagnostic.py  ← Benchmark suite
  plugins/laap_brain/SKILL.md       ← Hermes skill (/skill laap-brain)
"""

from __future__ import annotations
import os, logging

logger = logging.getLogger("plugins.laap_brain")
_loaded = False


def register(ctx) -> None:
    """Register LAAP AGI with the Hermes plugin context (auto-called at startup)."""
    global _loaded
    if _loaded:
        return
    _loaded = True

    try:
        from laap_brain.integrate import install_laap
        install_laap()
        os.environ["HERMES_LAAP_ENABLED"] = "1"
        os.environ["HERMES_LAAP_VERSION"] = "3.1.0"
        logger.info("LAAP AGI v3.1.0 active: meta-cognition, parliament, unity, EWC")
        print("\033[38;5;220m  ✦ LAAP AGI 认知增强已激活 ✦\033[0m")
    except Exception as e:
        logger.debug(f"LAAP AGI load skipped: {e}")

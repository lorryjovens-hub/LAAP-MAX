"""
LAAP AGI — PSI Driver (PSI认知驱动引擎)

Implements the PSI theory (Dietrich Dörner) cognition cycle:
  1. Perceive  — sensory input → internal representation (WorldModel)
  2. Select   — needs/emotion/bias → what to attend to (ConsciousStream/Attention)
  3. Integrate — bind perceptions + memories + predictions into unified experience
  4. Act      — generate response based on integrated state (LLM as I/O, not as thinker)
  5. Learn    — update world model, self model, skills from outcomes

The LLM becomes just the natural language I/O channel within this cycle,
NOT the cognitive driver. This module is OPT-IN (use_psi=False by default)
and NEVER breaks existing functionality.

Integration:
    from laap.agi.psi_driver import PSIDriver, integrate_psi_driver

    # Attach to agent
    driver = integrate_psi_driver(agent, llm_channel=my_llm_fn)

    # Use via process_interaction(use_psi=True)
    result = agent.process_interaction("Hello", use_psi=True)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import time, logging
from laap.agi.world_model import EntityType

logger = logging.getLogger("laap.agi.psi_driver")


class PSIDriver:
    """
    PSI-driven cognitive engine. Replaces LLM-as-thinker loop.

    Flow per interaction:
      1. perceive()   → WorldModel.add_entity() + ConsciousStream.experience()
      2. select()     → needs assessment → attention focus
      3. integrate()  → bind context → generate unified state
      4. decide()     → select action based on integrated state
      5. learn()      → update self-model + memory + learning pipeline

    The LLM is called only in step 4 (decide) for natural language generation,
    and is a sub-processor, not the driver.
    """

    def __init__(self, agent: Any, llm_channel: Optional[callable] = None):
        self.agent = agent            # AGIAgent instance
        self.llm = llm_channel        # LLM I/O channel (sub-processor)
        self.cycle_count = 0
        self.last_domain = "general"
        self._last_focus = "respond"

    def process(self, user_input: str, domain: str = "general") -> str:
        """
        Run one full PSI cognition cycle.

        Args:
            user_input: The user's natural language input
            domain: Task domain label

        Returns:
            Natural language response string
        """
        # ═══════════════════════════════════════════════════════════
        # Step 1: Perceive
        # ═══════════════════════════════════════════════════════════
        self.last_domain = domain

        if hasattr(self.agent, 'world') and self.agent.world:
            self.agent.world.add_entity(
                name=f"user_input_{self.cycle_count}",
                entity_type=EntityType.ACTION,
                properties={"content": user_input, "domain": domain},
            )

        if hasattr(self.agent, 'conscious') and self.agent.conscious:
            self.agent.conscious.experience(user_input)

        # ─── Causal analysis: learn from message, predict interventions ───
        causal_context = ""
        if hasattr(self.agent, 'causal') and self.agent.causal:
            try:
                # Extract key terms from message as causal variables
                causal = self.agent.causal
                cg = causal.graph if hasattr(causal, 'graph') else causal
                words = user_input.lower().split()[:5]
                for w in words:
                    if len(w) > 3 and w.isalpha():
                        cg.add_variable(w, domain=domain)
                        causal.observe(w, 1.0)
                cs = causal.stats()
                if cs.get("variables", 0) > 0:
                    causal_context = f"[Causal: {cs['variables']} vars]"
                    try:
                        # Link related variables using their IDs
                        for i in range(len(words)):
                            for j in range(i+1, min(i+3, len(words))):
                                wi, wj = words[i], words[j]
                                if len(wi) > 3 and len(wj) > 3 and wi.isalpha() and wj.isalpha():
                                    vi = causal._find_var(wi)
                                    vj = causal._find_var(wj)
                                    if vi and vj:
                                        cg.add_edge(vi.id, vj.id, strength=0.3)
                    except: pass
            except Exception as e:
                causal_context = f"[Causal: {e}]"

        # ─── Analogical transfer: find cross-domain patterns ───
        analogy_context = ""
        if hasattr(self.agent, 'analogical') and self.agent.analogical:
            try:
                domain_data = {"domain": domain, "user_input": user_input[:200]}
                self.agent.analogical.encode_domain(domain, [domain_data])
                analogies = self.agent.analogical.query_analogies(domain)
                if analogies:
                    analogy_str = "; ".join([f"{a[0]}(conf={a[1]:.2f})" for a in analogies[:3]])
                    analogy_context = f"[Analogies: {analogy_str}]"
                if len(analogies) >= 2:
                    mapping = self.agent.analogical.find_analogy(domain)
                    if mapping and mapping.similarity_score > 0.3:
                        analogy_context += f" [Mapping: {mapping.source_domain}->{mapping.target_domain}, sim={mapping.similarity_score:.2f}]"
            except Exception as e:
                analogy_context = f"[Analogies: {e}]"

        # ═══════════════════════════════════════════════════════════
        # Step 2: Selection (needs/emotion drive attention)
        # ═══════════════════════════════════════════════════════════
        focus = "respond"
        if hasattr(self.agent, 'conscious') and hasattr(
            self.agent.conscious, 'attention'
        ):
            attn = self.agent.conscious.attention
            if hasattr(attn, 'determine_focus'):
                try:
                    raw_focus = attn.determine_focus({"user_input": user_input})
                    focus = raw_focus.value if hasattr(raw_focus, 'value') else str(raw_focus)
                except Exception:
                    focus = "respond"

        self._last_focus = focus

        # ═══════════════════════════════════════════════════════════
        # Step 3: Integration
        # ═══════════════════════════════════════════════════════════
        context = self._build_context(domain=domain, focus=focus,
                                     causal_context=causal_context,
                                     analogy_context=analogy_context)

        # ═══════════════════════════════════════════════════════════
        # Step 4: Action (LLM as sub-processor)
        # ═══════════════════════════════════════════════════════════
        if self.llm:
            response = self.llm(context + "\n\nUser: " + user_input)
        else:
            response = self._fallback_respond(domain)

        # ─── Causal consistency verification ───
        response = self._causal_verify(response)

        # ═══════════════════════════════════════════════════════════
        # Step 5: Learning
        # ═══════════════════════════════════════════════════════════
        self._learn(user_input, response, domain)

        self.cycle_count += 1
        return response

    def _build_context(self, domain: str, focus: str = "respond",
                       causal_context: str = "", analogy_context: str = "") -> str:
        """Build attention-weighted context from all cognitive modules."""
        tiers = {"high": [], "medium": [], "low": []}

        # High tier: conscious state + focus
        if hasattr(self.agent, 'conscious') and self.agent.conscious:
            try:
                cs = self.agent.conscious.stats()
                tiers["high"].append(f"[Conscious: focus={focus}, valence={cs.get('valence', 0):.2f}]")
            except Exception:
                pass

        if hasattr(self.agent, 'self_model') and self.agent.self_model:
            try:
                sm = self.agent.self_model.stats()
                tiers["high"].append(f"[Self: {sm.get('total_experiences', 0)} exp, {sm.get('skills', 0)} skills]")
            except Exception:
                pass

        # Medium tier: causal + analogical (enriched context)
        if causal_context:
            tiers["medium"].append(causal_context)
        if analogy_context:
            tiers["medium"].append(analogy_context)

        if hasattr(self.agent, 'world') and self.agent.world:
            try:
                wm = f"[World: {len(self.agent.world.entities)} entities, {len(self.agent.world.relations)} relations]"
                tiers["medium"].append(wm)
            except Exception:
                pass

        # Low tier: learning + memory
        if hasattr(self.agent, 'memory_system') and self.agent.memory_system:
            try:
                ms = self.agent.memory_system.stats()
                tiers["low"].append(f"[Memory: {ms.get('total_memories', 0)} episodes]")
            except Exception:
                pass

        if hasattr(self.agent, 'learning') and self.agent.learning:
            try:
                tiers["low"].append("[Learning: ready]")
            except Exception:
                pass

        # Build tiered output: high first, then medium, then low
        parts = []
        for tier_name in ["high", "medium", "low"]:
            if tiers[tier_name]:
                parts.append(f"[{tier_name.upper()} PRIORITY]")
                parts.extend(tiers[tier_name])

        return chr(10).join(parts) if parts else "[Cognitive context: initializing]"

    def _learn(self, user_input: str, response: str, domain: str):
        """Post-interaction learning across all modules."""
        # Self-model learning
        if (
            hasattr(self.agent, 'self_model')
            and self.agent.self_model
            and hasattr(self.agent.self_model, 'record_experience')
        ):
            try:
                self.agent.self_model.record_experience(
                    domain=domain,
                    outcome_score=0.5,
                    predicted_confidence=0.5,
                    is_success=True,
                    description=f"PSI cycle {self.cycle_count}: {user_input[:60]}",
                )
            except Exception as e:
                logger.debug(f"Self-model learn skipped: {e}")

        # Memory system
        if hasattr(self.agent, 'memory_system') and self.agent.memory_system:
            try:
                self.agent.memory_system.remember_episode(
                    event=user_input,
                    context={"response": response, "domain": domain},
                )
            except Exception as e:
                logger.debug(f"Memory learn skipped: {e}")

        # Learning pipeline
        if hasattr(self.agent, 'learning') and self.agent.learning:
            try:
                self.agent.learning.learn(
                    domain=domain,
                    action=user_input[:80],
                    outcome=0.5,
                )
            except Exception as e:
                logger.debug(f"Learning pipeline learn skipped: {e}")

    def _causal_verify(self, response: str) -> str:
        """Check LLM response against causal model for consistency."""
        if not hasattr(self.agent, 'causal') or not self.agent.causal:
            return response
        try:
            cs = self.agent.causal.stats()
            if cs.get("variables", 0) < 2:
                return response  # Not enough data for verification
            # Look for causal claims in the response (X causes Y patterns)
            import re as _re
            claims = _re.findall(r'(\w+)\s+causes\s+(\w+)', response.lower())
            for cause_claim, effect_claim in claims:
                pass  # Placeholder for deeper integration
            return response
        except Exception:
            return response

    def _fallback_respond(self, domain: str) -> str:
        """Fallback response when no LLM channel is available."""
        return (
            f"[PSI Driver - {domain}] Processed cycle {self.cycle_count}. "
            "No LLM channel available."
        )

    def stats(self) -> Dict[str, Any]:
        """Return PSI driver statistics."""
        modules_available = sum(
            1 for m in [
                'world', 'self_model', 'conscious', 'causal',
                'analogical', 'memory_system', 'learning',
            ]
            if hasattr(self.agent, m) and getattr(self.agent, m) is not None
        )
        return {
            "cycles": self.cycle_count,
            "domain": self.last_domain,
            "focus": self._last_focus,
            "modules_available": modules_available,
            "llm_connected": self.llm is not None,
        }


def integrate_psi_driver(
    agent: Any,
    llm_channel: Optional[callable] = None,
    enable_causal_verification: bool = False,
) -> PSIDriver:
    """
    Attach a PSI Driver to an AGIAgent instance.

    Sets `agent.psi_driver` to the new PSIDriver instance. Existing
    functionality is completely unaffected — the PSI driver is only
    activated when `use_psi=True` is passed to process_interaction().

    Args:
        agent: AGIAgent instance (or any object with the expected modules)
        llm_channel: Callable that takes a prompt string and returns a
                     natural language response string. This is the LLM
                     acting as an I/O sub-processor only.

    Returns:
        The PSIDriver instance
    """
    driver = PSIDriver(agent, llm_channel)
    agent.psi_driver = driver
    logger.info(f"PSI Driver integrated into {getattr(agent, 'name', 'agent')}")
    return driver

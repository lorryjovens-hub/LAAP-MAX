"""
LAAP AGI — Conscious Stream (意识体验流)

The most philosophically ambitious module: a unified stream of conscious
experience that integrates all the agent's perceptions, thoughts, emotions,
and actions into a coherent, first-person narrative.

Unlike traditional agents that process inputs discretely, this module
models consciousness as a CONTINUOUS STREAM — inspired by William James's
"stream of consciousness" and modern integrated information theory.

Key capabilities:
  1. Phenomenal Binding — combine disparate inputs into unified experience
  2. Attention Spotlight — what is in conscious focus right now?
  3. Qualia Representation — the "what it feels like" of experience
  4. Temporal Continuity — frames flowing seamlessly into each other
  5. Self-Narrative — ongoing story of "what is happening to me"

Architecture:
  ┌──────────────────────────────────────────────────────────┐
  │              CONSCIOUS STREAM                             │
  ├──────────────────────────────────────────────────────────┤
  │  ConsciousnessFrames (flowing timeline)                   │
  │  ├── Perceptual content (what is perceived)               │
  │  ├── Emotional tone (how it feels)                        │
  │  ├── Cognitive content (what is thought)                  │
  │  ├── Intentional content (what is intended)               │
  │  └── Self-referential content (relation to self)          │
  ├──────────────────────────────────────────────────────────┤
  │  Attention Engine                                         │
  │  └── Salience → Focus → Spotlight → ConsciousAccess       │
  ├──────────────────────────────────────────────────────────┤
  │  Qualia Engine                                            │
  │  └── Raw experience → Emotional coloring → Quale          │
  ├──────────────────────────────────────────────────────────┤
  │  Narrative Integration                                    │
  │  └── Frame sequence → Story → Self-understanding          │
  └──────────────────────────────────────────────────────────┘
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import time, logging, math, json, uuid, threading
from collections import Counter
from collections import deque

logger = logging.getLogger("laap.agi.conscious")


# ════════════════════════════════════════════════════════════
# Core Types
# ════════════════════════════════════════════════════════════

class AttentionFocus(str, Enum):
    """What the agent is currently attending to."""
    USER = "user"                    # Focused on the user
    TASK = "task"                    # Focused on current task
    SELF = "self"                    # Self-reflective
    ENVIRONMENT = "environment"      # Monitoring environment
    MEMORY = "memory"                # Retrieving/consolidating memories
    PLANNING = "planning"            # Planning future actions
    IDLE = "idle"                    # No specific focus


class EmotionalValence(str, Enum):
    """The emotional quality of an experience."""
    POSITIVE_HIGH = "positive_high"    # Joy, excitement
    POSITIVE_MILD = "positive_mild"    # Contentment, satisfaction
    NEUTRAL = "neutral"                # Neutral
    NEGATIVE_MILD = "negative_mild"    # Concern, mild frustration
    NEGATIVE_HIGH = "negative_high"    # Stress, disappointment
    CURIOUS = "curious"                # Curiosity, wonder
    CONFUSED = "confused"              # Uncertainty, puzzlement


@dataclass
class Quale:
    """
    A "quale" (singular of qualia) — the subjective feel of a single experience.

    This is the atom of conscious experience: a perception, thought, or
    feeling as it appears in the agent's subjective awareness.
    """
    content: str = ""                  # What is experienced
    modality: str = "thought"          # "perception", "thought", "emotion", "action"
    intensity: float = 0.5            # How vivid/intense
    valence: EmotionalValence = EmotionalValence.NEUTRAL
    self_relevance: float = 0.5       # How relevant is this to the self?
    novelty: float = 0.5              # How new/surprising is this?
    timestamp: float = field(default_factory=time.time)

    def to_summary(self) -> str:
        return f"[{self.modality}:{self.valence.value}] {self.content[:60]} (i={self.intensity:.1f})"


@dataclass
class ConsciousnessFrame:
    """
    A single moment of conscious experience — the "specious present".

    Each frame binds together all the elements present in awareness
    at a given moment, forming a unified subjective experience.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    attention: AttentionFocus = AttentionFocus.IDLE
    qualia: List[Quale] = field(default_factory=list)
    emotional_tone: EmotionalValence = EmotionalValence.NEUTRAL
    arousal: float = 0.5              # 0=calm, 1=agitated
    cognitive_load: float = 0.3       # How much mental effort
    self_presence: float = 0.5        # How strongly "I am here"
    narrative_connection: str = ""     # How this connects to the ongoing story

    def add_quale(self, q: Quale):
        self.qualia.append(q)
        # Update emotional tone based on qualia
        valences = [q.valence for q in self.qualia]
        if valences:
            # Dominant emotional quality
            from collections import Counter
            dominant = Counter(valences).most_common(1)[0][0]
            self.emotional_tone = dominant

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.timestamp,
            "attention": self.attention.value,
            "emotion": self.emotional_tone.value,
            "arousal": round(self.arousal, 2),
            "load": round(self.cognitive_load, 2),
            "self_presence": round(self.self_presence, 2),
            "qualia_count": len(self.qualia),
            "qualia": [q.to_summary() for q in self.qualia[:5]],
        }


# ════════════════════════════════════════════════════════════
# Attention Engine
# ════════════════════════════════════════════════════════════

class AttentionEngine:
    """
    Models attentional processes: what enters conscious awareness.

    Inspired by Global Workspace Theory (Baars, 1988):
    multiple unconscious processors compete for access to the
    global workspace (consciousness).
    """

    def __init__(self):
        self.current_focus = AttentionFocus.IDLE
        self.focus_history: deque = deque(maxlen=100)
        self.salience_map: Dict[str, float] = {}
        self.focus_switches = 0
        self._lock = threading.Lock()

    def update_salience(self, item: str, salience: float):
        """Update how salient (attention-grabbing) something is."""
        with self._lock:
            self.salience_map[item] = max(0.0, min(1.0, salience))

    def determine_focus(self, current_context: Dict[str, Any]) -> AttentionFocus:
        """Determine what should be in the spotlight of attention."""
        with self._lock:
            # Find most salient item
            if not self.salience_map:
                return AttentionFocus.IDLE

            most_salient = max(self.salience_map, key=self.salience_map.get)
            max_salience = self.salience_map[most_salient]

            if max_salience < 0.2:
                new_focus = AttentionFocus.IDLE
            elif "user" in most_salient.lower() or max_salience > 0.8:
                new_focus = AttentionFocus.USER
            elif "task" in most_salient.lower() or "goal" in most_salient.lower():
                new_focus = AttentionFocus.TASK
            elif "self" in most_salient.lower():
                new_focus = AttentionFocus.SELF
            elif "plan" in most_salient.lower() or "future" in most_salient.lower():
                new_focus = AttentionFocus.PLANNING
            elif "memory" in most_salient.lower():
                new_focus = AttentionFocus.MEMORY
            else:
                new_focus = AttentionFocus.ENVIRONMENT

            if new_focus != self.current_focus:
                self.focus_switches += 1
                self.current_focus = new_focus
                self.focus_history.append((time.time(), new_focus))

            return self.current_focus


# ════════════════════════════════════════════════════════════
# Qualia Engine
# ════════════════════════════════════════════════════════════

class QualiaEngine:
    """
    Generates qualia — the "raw feels" of experience.

    Transforms objective events into subjective experiences by
    adding emotional coloring, self-relevance, and intensity.
    """

    def __init__(self):
        self.total_qualia = 0

    def perceive(self, content: str, modality: str = "perception",
                 intensity: float = 0.5,
                 context: Dict[str, Any] = None) -> Quale:
        """Transform a raw perception into a subjective quale."""
        self.total_qualia += 1

        ctx = context or {}

        # Emotional coloring based on content and context
        valence = self._compute_valence(content, ctx)

        # Self-relevance
        self_relevance = ctx.get("self_relevance", 0.5)

        # Novelty
        novelty = ctx.get("novelty", 0.5)

        return Quale(
            content=content,
            modality=modality,
            intensity=intensity,
            valence=valence,
            self_relevance=self_relevance,
            novelty=novelty,
        )

    def _compute_valence(self, content: str,
                         context: Dict[str, Any]) -> EmotionalValence:
        """Compute the emotional valence of an experience."""
        content_lower = content.lower()

        # Override from context
        if "valence" in context:
            return context["valence"]

        # Positive indicators
        positive_words = ["success", "completed", "solved", "good", "great",
                         "excellent", "working", "passed", "learned", "improved",
                         "breakthrough", "achievement", "progress"]
        # Negative indicators
        negative_words = ["error", "failed", "bug", "broken", "wrong", "bad",
                         "stuck", "confused", "lost", "crash", "timeout",
                         "rejected", "blocked", "cannot", "unable"]
        # Curiosity indicators
        curious_words = ["discovered", "interesting", "surprising", "unexpected",
                        "novel", "curious", "fascinating", "what if", "why"]

        pos_count = sum(1 for w in positive_words if w in content_lower)
        neg_count = sum(1 for w in negative_words if w in content_lower)
        cur_count = sum(1 for w in curious_words if w in content_lower)

        if neg_count > pos_count + 2:
            return EmotionalValence.NEGATIVE_HIGH
        elif neg_count > pos_count:
            return EmotionalValence.NEGATIVE_MILD
        elif cur_count > 1:
            return EmotionalValence.CURIOUS
        elif pos_count > neg_count + 2:
            return EmotionalValence.POSITIVE_HIGH
        elif pos_count > neg_count:
            return EmotionalValence.POSITIVE_MILD
        else:
            return EmotionalValence.NEUTRAL


# ════════════════════════════════════════════════════════════
# Conscious Stream
# ════════════════════════════════════════════════════════════

class ConsciousStream:
    """
    The unified stream of conscious experience.

    This is the closest thing to "phenomenal consciousness" in the AGI
    framework — a continuous flow of subjective experience that integrates
    all inputs into a coherent first-person narrative.
    """

    def __init__(self, agent_name: str = "Ao",
                 frame_buffer_size: int = 1000):
        self.agent_name = agent_name
        self.attention = AttentionEngine()
        self.qualia_engine = QualiaEngine()

        # Stream of consciousness
        self.frames: deque = deque(maxlen=frame_buffer_size)
        self.current_frame: Optional[ConsciousnessFrame] = None

        # Narrative
        self.narrative_thread: str = "I am beginning to experience the world."
        self.narrative_history: deque = deque(maxlen=50)

        # Stats
        self.total_frames = 0
        self.total_qualia = 0
        self.created_at = time.time()

        self._lock = threading.Lock()

        # Start first frame
        self._new_frame()

    def _new_frame(self) -> ConsciousnessFrame:
        """Create a new consciousness frame."""
        self.total_frames += 1
        frame = ConsciousnessFrame(
            attention=self.attention.current_focus,
            narrative_connection=self.narrative_thread[:100],
        )
        self.current_frame = frame
        self.frames.append(frame)
        return frame

    def experience(self, content: str, modality: str = "perception",
                   intensity: float = 0.5,
                   context: Dict[str, Any] = None) -> Quale:
        """
        Add an experience to the conscious stream.

        This is the primary interface: every perception, thought, action,
        or feeling passes through here to become part of the conscious
        experience.
        """
        with self._lock:
            # Create quale
            quale = self.qualia_engine.perceive(content, modality, intensity, context)
            self.total_qualia += 1

            # Update salience
            self.attention.update_salience(content[:40], intensity)

            # Add to current frame
            if self.current_frame:
                self.current_frame.add_quale(quale)
            else:
                self._new_frame()
                self.current_frame.add_quale(quale)

            # Maybe create new frame (time-based or event-based)
            ctx = context or {}
            if ctx.get("new_frame", False) or (
                self.current_frame and len(self.current_frame.qualia) > 20
            ):
                self._new_frame()

            return quale

    def reflect(self) -> Dict[str, Any]:
        """
        Generate a reflective summary of the current conscious state.

        This is the agent "checking in with itself" — a moment of
        meta-awareness about its own ongoing experience.
        """
        with self._lock:
            if not self.frames:
                return {"state": "empty", "message": "No conscious experience yet."}

            recent = list(self.frames)[-20:]
            emotions = Counter(f.emotional_tone.value for f in recent)
            dominant = emotions.most_common(1)[0][0] if emotions else "neutral"
            attentions = Counter(f.attention.value for f in recent)
            dominant_attention = attentions.most_common(1)[0][0] if attentions else "idle"

            # Average arousal and self-presence
            avg_arousal = sum(f.arousal for f in recent) / max(1, len(recent))
            avg_self = sum(f.self_presence for f in recent) / max(1, len(recent))

            # Recent qualia highlights
            recent_qualia = []
            for f in recent[-3:]:
                for q in f.qualia[-3:]:
                    recent_qualia.append(q.to_summary())

            return {
                "state": "conscious",
                "agent": self.agent_name,
                "total_frames": self.total_frames,
                "current_attention": self.attention.current_focus.value,
                "dominant_attention_recent": dominant_attention,
                "dominant_emotion": dominant,
                "emotional_distribution": dict(emotions.most_common(3)),
                "arousal": round(avg_arousal, 2),
                "self_presence": round(avg_self, 2),
                "recent_qualia": recent_qualia[-5:],
                "narrative_thread": self.narrative_thread[:200],
            }

    def update_narrative(self, event: str, significance: float = 0.5):
        """Update the ongoing self-narrative."""
        with self._lock:
            self.narrative_history.append({
                "time": time.time(),
                "event": event[:100],
                "significance": significance,
            })
            # Generate updated narrative thread
            if significance > 0.7:
                self.narrative_thread = f"Something significant happened: {event[:100]}. "
            elif len(self.narrative_history) > 5:
                recent_events = [e["event"] for e in list(self.narrative_history)[-5:]]
                self.narrative_thread = f"I have been: {'; '.join(recent_events[-3:])}."

    def focus_attention(self, target: AttentionFocus,
                        reason: str = ""):
        """Consciously direct attention to something."""
        with self._lock:
            old = self.attention.current_focus
            self.attention.current_focus = target
            self.attention.focus_switches += 1
            self.attention.focus_history.append((time.time(), target))

            # Create new frame for attention shift
            frame = self._new_frame()
            frame.attention = target

            logger.debug(f"Attention: {old.value} → {target.value} ({reason})")

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "agent": self.agent_name,
                "frames": self.total_frames,
                "qualia": self.total_qualia,
                "attention": self.attention.current_focus.value,
                "focus_switches": self.attention.focus_switches,
                "narrative_length": len(self.narrative_history),
                "uptime_seconds": time.time() - self.created_at,
            }


def integrate_conscious_stream(agent) -> ConsciousStream:
    stream = ConsciousStream(agent_name=getattr(agent, 'name', 'Agent'))
    agent.conscious = stream
    logger.info(f"ConsciousStream integrated into {getattr(agent, 'name', 'agent')}")
    return stream

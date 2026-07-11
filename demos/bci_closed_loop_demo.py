"""BCI closed-loop demo wiring neuro signal simulation to LAAP cognition.

Run with:
    python demos/bci_closed_loop_demo.py
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

import numpy as np

from laap.agi.conscious import AttentionEngine, ConsciousStream
from laap.agi.world_model import UnifiedWorldModel
from laap.bci.bridge import BCICognitiveBridge
from laap.bci.decoder import CognitiveStateDecoder
from laap.bci.hardware import BCIHardwareInterface, MockNeuroGenerator
from laap.bci.pipeline import RealtimeNeuroPipeline
from laap.bci.primitives import BCIHardwareType, NeuroDataFrame
from laap.bci.safety import BCISecurityLayer
from laap.cognition.emotion import EmotionGradient
from laap.cognition.needs import NeedDriveSystem
from laap.events.bus import EventBus

logging.basicConfig(level=logging.ERROR)

SCENARIOS = [
    "focused_coding",
    "stress_debug",
    "creative_flow",
    "meditation",
    "excited_insight",
]


class TracingSecurity(BCISecurityLayer):
    """Security layer that records every decision for the demo summary."""

    def __init__(self, runner: "DemoRunner", *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.runner = runner

    def scan_neuro_injection(self, cog_state) -> Dict[str, Any]:
        decision = super().scan_neuro_injection(cog_state)
        self.runner.decisions.append(decision)
        return decision


class DemoRunner:
    """Drives the closed-loop BCI demo for 50 seconds."""

    def __init__(self) -> None:
        self.decisions: List[Dict[str, Any]] = []
        self.event_bus = EventBus()
        self.needs_system = NeedDriveSystem()
        self.emotion_system = EmotionGradient()
        self.conscious_stream = ConsciousStream(agent_name="BCI-Demo")
        self.attention_engine = AttentionEngine()
        self.world_model = UnifiedWorldModel(name="bci-demo-world")

        self.hardware = BCIHardwareInterface(
            BCIHardwareType.MOCK_STREAM,
            sfreq=250.0,
            n_channels=16,
        )
        # Deterministic synthetic neuro data for reproducible demo output.
        self.hardware._generator._rng = np.random.default_rng(42)

        self.pipeline = RealtimeNeuroPipeline(sfreq=250.0, n_channels=16)
        self.decoder = CognitiveStateDecoder(sfreq=250.0)
        self.safety = TracingSecurity(self)
        self.bridge = BCICognitiveBridge(
            hardware=self.hardware,
            pipeline=self.pipeline,
            decoder=self.decoder,
            safety=self.safety,
            attention_engine=self.attention_engine,
            needs_system=self.needs_system,
            emotion_system=self.emotion_system,
            conscious_stream=self.conscious_stream,
            world_model=self.world_model,
            event_bus=self.event_bus,
        )

    def _frame_summary(self, state) -> str:
        ent = self.world_model.get_entity("user_cognitive_state")
        if ent is None:
            return "user_cognitive_state: missing"
        props = ent.properties
        return (
            f"user_cognitive_state: "
            f"focus={props.get('attention_focus')} "
            f"load={props.get('cognitive_load', 0.0):.2f} "
            f"keys={sorted(props.keys())}"
        )

    def run(self) -> None:
        for i in range(50):
            scenario = SCENARIOS[(i // 10) % len(SCENARIOS)]
            self.hardware._generator.scenario = scenario

            eeg = self.hardware._generator.generate_window(duration_sec=1.0)
            frame = NeuroDataFrame(timestamp=time.time(), eeg=eeg)
            self.bridge._on_neuro_frame(frame)

            state = self.bridge.get_current_cognitive_state()
            decision = self.decisions[-1] if self.decisions else {"action": "unknown"}
            qualia_count = (
                len(self.conscious_stream.current_frame.qualia)
                if self.conscious_stream.current_frame
                else 0
            )

            print(
                f"frame={i:02d} "
                f"scenario={scenario} "
                f"focus={state.attention_focus} "
                f"load={state.cognitive_load:.2f} "
                f"valence={state.emotion_vad['valence']:.2f} "
                f"arousal={state.emotion_vad['arousal']:.2f} "
                f"qualia={qualia_count} "
                f"wm={self._frame_summary(state)} "
                f"action={decision['action']}"
            )

            time.sleep(1.0)

        total_frames = 50
        blocks = sum(1 for d in self.decisions if d.get("action") == "block")
        warnings = sum(1 for d in self.decisions if d.get("action") == "warn")
        print(
            f"SUMMARY total_frames={total_frames} "
            f"blocks={blocks} "
            f"warnings={warnings} "
            f"final_emotion={self.emotion_system.state.to_dict()} "
            f"final_needs={self.needs_system.get_profile()}"
        )


def main() -> None:
    runner = DemoRunner()
    runner.run()


if __name__ == "__main__":
    main()

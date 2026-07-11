"""Integration test for the full BCI Neuro Bridge pipeline into LAAP cognition."""

from __future__ import annotations

import numpy as np

from laap.agi.conscious import ConsciousStream
from laap.agi.world_model import UnifiedWorldModel
from laap.bci.bridge import BCICognitiveBridge
from laap.bci.decoder import CognitiveStateDecoder
from laap.bci.hardware import BCIHardwareInterface
from laap.bci.pipeline import RealtimeNeuroPipeline
from laap.bci.primitives import BCIHardwareType, NeuroDataFrame
from laap.bci.safety import BCISecurityLayer
from laap.cognition.emotion import EmotionGradient
from laap.cognition.needs import NeedDriveSystem, NeedType
from laap.events.bus import EventBus


def test_full_bci_pipeline_integration(tmp_path) -> None:
    """Wire mock generator → hardware → pipeline → decoder → safety → bridge → LAAP modules."""
    event_bus = EventBus()
    needs_system = NeedDriveSystem()
    emotion_system = EmotionGradient()
    conscious_stream = ConsciousStream(agent_name="bci-test")
    world_model = UnifiedWorldModel(name="bci-test-world")

    hardware = BCIHardwareInterface(
        BCIHardwareType.MOCK_STREAM,
        sfreq=250.0,
        n_channels=16,
    )
    hardware._generator._rng = np.random.default_rng(123)

    pipeline = RealtimeNeuroPipeline(sfreq=250.0, n_channels=16)
    decoder = CognitiveStateDecoder(sfreq=250.0)
    safety = BCISecurityLayer(audit_log_path=str(tmp_path / "bci_audit.log"))

    bridge = BCICognitiveBridge(
        hardware=hardware,
        pipeline=pipeline,
        decoder=decoder,
        safety=safety,
        needs_system=needs_system,
        emotion_system=emotion_system,
        conscious_stream=conscious_stream,
        world_model=world_model,
        event_bus=event_bus,
    )

    initial_energy = needs_system.needs[NeedType.ENERGY].current_level
    initial_emotion = emotion_system.state.to_dict()

    scenario = "focused_coding"
    hardware._generator.scenario = scenario
    for i in range(5):
        eeg = hardware._generator.generate_window(duration_sec=1.0)
        frame = NeuroDataFrame(timestamp=float(i), eeg=eeg)
        bridge._on_neuro_frame(frame)

    # Emotion system should have received VAD updates.
    assert emotion_system.state.to_dict() != initial_emotion

    # Needs system should have received energy updates.
    assert needs_system.needs[NeedType.ENERGY].current_level != initial_energy

    # World model should contain the user cognitive state entity.
    entity = world_model.get_entity("user_cognitive_state")
    assert entity is not None
    assert "attention_focus" in entity.properties
    assert "cognitive_load" in entity.properties

    # Conscious stream should contain interoception qualia.
    frame = conscious_stream.current_frame
    assert frame is not None
    interoception_qualia = [q for q in frame.qualia if q.modality == "interoception"]
    assert len(interoception_qualia) > 0

    # Bridge should hold the latest decoded cognitive state.
    assert bridge.get_current_cognitive_state() is not None

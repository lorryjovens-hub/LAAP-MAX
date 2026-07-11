"""
测试全局工作空间模块
"""

import asyncio
import pytest
from laap.agi.gw_workspace import GlobalWorkspace, CoalitionalProcess, ProcessType


def test_process_type_enum():
    assert ProcessType.PERCEPTUAL.name == "PERCEPTUAL"
    assert ProcessType.COGNITIVE.name == "COGNITIVE"
    assert ProcessType.AFFECTIVE.name == "AFFECTIVE"
    assert ProcessType.MOTOR.name == "MOTOR"
    assert ProcessType.META.name == "META"
    assert len(ProcessType) == 5


def test_coalitional_process():
    process = CoalitionalProcess(
        process_id="test_001",
        process_type=ProcessType.COGNITIVE,
        content="Test content",
        activation=0.8,
        salience=0.6,
        decay_rate=0.1,
    )

    assert process.process_id == "test_001"
    assert process.process_type == ProcessType.COGNITIVE
    assert process.content == "Test content"
    assert process.activation == 0.8
    assert process.salience == 0.6
    assert process.decay_rate == 0.1

    initial_strength = process.competitive_strength
    assert initial_strength > 0

    process.update(1.0)
    assert process.activation < 0.8
    assert process.salience < 0.6
    assert process.competitive_strength < initial_strength


def test_global_workspace_init():
    gw = GlobalWorkspace(capacity=4, competition_threshold=0.6)
    assert gw.capacity == 4
    assert gw.competition_threshold == 0.6
    assert len(gw.processes) == 0
    assert len(gw.workspace_contents) == 0
    assert len(gw.broadcast_callbacks) == 0
    assert gw.current_focus is None


def test_register_unregister_process():
    gw = GlobalWorkspace()

    process = CoalitionalProcess(
        process_id="proc_001",
        process_type=ProcessType.PERCEPTUAL,
        content="Test",
        activation=0.5,
        salience=0.5,
    )

    gw.register_process(process)
    assert "proc_001" in gw.processes
    assert gw.processes["proc_001"] == process

    gw.unregister_process("proc_001")
    assert "proc_001" not in gw.processes

    gw.unregister_process("nonexistent")


def test_boost_process():
    gw = GlobalWorkspace()

    process = CoalitionalProcess(
        process_id="proc_001",
        process_type=ProcessType.COGNITIVE,
        content="Test",
        activation=0.3,
        salience=0.5,
    )

    gw.register_process(process)
    gw.boost_process("proc_001", 0.5)
    assert gw.processes["proc_001"].activation == 0.8

    gw.boost_process("proc_001", 0.5)
    assert gw.processes["proc_001"].activation == 1.0

    gw.boost_process("nonexistent", 0.5)


@pytest.mark.asyncio
async def test_compete_and_broadcast():
    gw = GlobalWorkspace(capacity=2, competition_threshold=0.3)

    process1 = CoalitionalProcess(
        process_id="high_priority",
        process_type=ProcessType.COGNITIVE,
        content="Important task",
        activation=0.9,
        salience=0.9,
        decay_rate=0.05,
    )

    process2 = CoalitionalProcess(
        process_id="medium_priority",
        process_type=ProcessType.PERCEPTUAL,
        content="Sensory input",
        activation=0.6,
        salience=0.6,
        decay_rate=0.1,
    )

    process3 = CoalitionalProcess(
        process_id="low_priority",
        process_type=ProcessType.AFFECTIVE,
        content="Background emotion",
        activation=0.15,
        salience=0.15,
        decay_rate=0.2,
    )

    gw.register_process(process1)
    gw.register_process(process2)
    gw.register_process(process3)

    results = await gw.compete_and_broadcast()

    assert len(results) <= 2
    assert "high_priority" == results[0].process_id
    assert gw.current_focus == "high_priority"
    assert len(gw.history) >= 1

    stream = gw.get_conscious_stream(5)
    assert len(stream) >= 1


@pytest.mark.asyncio
async def test_broadcast_callback():
    gw = GlobalWorkspace()
    callback_results = []

    def sync_callback(packet):
        callback_results.append(packet)

    async def async_callback(packet):
        callback_results.append(packet)

    gw.on_broadcast(sync_callback)
    gw.on_broadcast(async_callback)

    process = CoalitionalProcess(
        process_id="callback_test",
        process_type=ProcessType.META,
        content="Callback test",
        activation=0.9,
        salience=0.9,
    )

    gw.register_process(process)
    await gw.compete_and_broadcast()

    await asyncio.sleep(0.1)

    assert len(callback_results) == 2
    assert callback_results[0]['dominant'] == "callback_test"
    assert callback_results[1]['dominant'] == "callback_test"


@pytest.mark.asyncio
async def test_get_conscious_stream():
    gw = GlobalWorkspace(capacity=1, competition_threshold=0.1)

    for i in range(15):
        process = CoalitionalProcess(
            process_id=f"proc_{i}",
            process_type=ProcessType.COGNITIVE,
            content=f"Content {i}",
            activation=0.9,
            salience=0.9,
        )
        gw.register_process(process)
        await gw.compete_and_broadcast()
        gw.unregister_process(f"proc_{i}")

    stream = gw.get_conscious_stream(10)
    assert len(stream) == 10

    stream_all = gw.get_conscious_stream()
    assert len(stream_all) == 10

    stream_large = gw.get_conscious_stream(20)
    assert len(stream_large) == 10


@pytest.mark.asyncio
async def test_decay_over_time():
    gw = GlobalWorkspace(capacity=1, competition_threshold=0.1)

    process = CoalitionalProcess(
        process_id="decay_test",
        process_type=ProcessType.COGNITIVE,
        content="Decay test",
        activation=0.9,
        salience=0.9,
        decay_rate=0.5,
    )

    gw.register_process(process)

    initial_strength = process.competitive_strength

    for _ in range(5):
        await gw.compete_and_broadcast()
        await asyncio.sleep(0.1)

    final_strength = process.competitive_strength
    assert final_strength < initial_strength


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
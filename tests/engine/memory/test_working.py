"""Working memory engine tests."""


def test_capacity():
    """Working memory capacity test"""
    from laap.engine.memory.working import WorkingMemory
    wm = WorkingMemory(capacity=5)
    assert wm.default_ttl > 0

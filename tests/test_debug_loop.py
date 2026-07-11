"""Debug test to check event loop state."""
import asyncio
import sys
import pytest


def test_check_loop_state():
    """Check the event loop state after other tests."""
    lines = []
    try:
        loop = asyncio.get_event_loop()
        lines.append(f"DEBUG: get_event_loop() returned {loop!r}")
        lines.append(f"DEBUG: loop.is_running() = {loop.is_running()}")
        lines.append(f"DEBUG: loop.is_closed() = {loop.is_closed()}")
        running_loop = asyncio.events._get_running_loop()
        lines.append(f"DEBUG: _get_running_loop() = {running_loop!r}")
    except RuntimeError as e:
        lines.append(f"get_event_loop() raised RuntimeError: {e}")
        running_loop = asyncio.events._get_running_loop()
        lines.append(f"_get_running_loop() = {running_loop!r}")
    with open(r"D:\LAAP\loop_debug.txt", "w") as f:
        f.write("\n".join(lines))


@pytest.mark.asyncio
async def test_check_async_loop_state():
    """Check if async test can run."""
    with open(r"D:\LAAP\loop_debug_async.txt", "w") as f:
        f.write(f"ASYNC running loop = {asyncio.get_running_loop()!r}")
    assert True

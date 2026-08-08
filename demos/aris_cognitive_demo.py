"""Standalone ARIS cognitive system demo.

Demonstrates the ARIS cognitive bus (PSI state + Petri-net loop) and the
HermesBodyInterface session wrapper through three representative user turns.
"""

from __future__ import annotations

import asyncio

from laap.orchestration import ArisCognitiveBus, HermesBodyInterface


async def main() -> None:
    print("=" * 70)
    print("ARIS: PSI Brain + Aether Orchestration + Hermes Body")
    print("=" * 70)

    print("\nInitializing cognitive system...")
    bus = ArisCognitiveBus("aris-demo")
    await bus.initialize()

    body = HermesBodyInterface(bus)

    print("\nUser: 'Hello Aris, how are you?'")
    response1 = await body.before_turn("Hello Aris, how are you?", "session_1")
    print(f"Aris: {response1}")

    print("\nUser: 'Search for all Python files in the project'")
    response2 = await body.before_turn(
        "Search for all Python files in the project", "session_1"
    )
    print(f"Aris: {response2}")

    print("\nUser: 'I need to refactor the authentication module...'")
    response3 = await body.before_turn(
        "I need to refactor the authentication module. Find the files, "
        "show me the current implementation, then suggest improvements.",
        "session_1",
    )
    print(f"Aris: {response3}")

    print("\nFinal PSI State:")
    psi_dict = bus.psi.state.to_dict()
    for key, value in psi_dict.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"      {k}: {v:.3f}")
        else:
            print(f"   {key}: {value}")

    print(f"\nCognitive trace: {len(bus.psi.perception_buffer)} perceptions buffered")

    await bus.shutdown()
    print("\nDemo complete")


if __name__ == "__main__":
    asyncio.run(main())

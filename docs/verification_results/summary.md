# LAAP Petri Net Verification Results

Generated: 2026-07-09T17:31:45.130655+00:00Z

| Net | Bounded | Max Bound | Deadlocks Found | Sink Places | Reachability Highlights |
|-----|---------|-----------|-----------------|-------------|------------------------|
| simple_sequential_net | True | 1 | 0 | p2 | ✅ end place p2 is reachable |
| psi_harness_closed_loop | True | 1 | 1 | sink | ❌ sink place is reachable (requires external cond)<br>✅ loop is reachable after enter |
| complex_dependency_chain_deadlock | True | 1 | 2 | p1_done, p2_done | ❌ both processes complete without deadlock<br>✅ circular-wait deadlock marking is reachable |

## Notes

- **simple_sequential_net**: A straight-line workflow; bounded, no deadlocks, and end place ``p2`` is reachable.
- **psi_harness_closed_loop**: Models a PSI harness loop blocked on an external ``cond`` place. The loop place is reachable after ``enter`` fires, but ``sink`` is only reachable if the external condition is satisfied; with ``cond`` initially empty, ``sink`` cannot be reached.
- **complex_dependency_chain_deadlock**: Two processes acquire shared resources in opposite order; bounded but can reach a circular-wait deadlock (``p1_holds_a`` and ``p2_holds_b`` simultaneously). Both processes completing together (``p1_done`` and ``p2_done`` together) is unreachable because the resource contention makes a circular wait unavoidable from the initial marking.

## TLC Configuration

Each net has a corresponding ``.cfg`` file that can be loaded directly into the TLA+ Toolbox or ``tlc2``.

- **simple_sequential_net**: ``simple_sequential_net.cfg``
  - Properties: TypeInvariant, EndStateReachable
  - Invariants: TypeInvariant

- **psi_harness_closed_loop**: ``psi_harness_closed_loop.cfg``
  - Properties: TypeInvariant, SinkReachable
  - Invariants: TypeInvariant

- **complex_dependency_chain_deadlock**: ``complex_dependency_chain_deadlock.cfg``
  - Properties: TypeInvariant
  - Invariants: DeadlockFree, TypeInvariant

---- MODULE ComplexDependencyChainDeadlock ----
EXTENDS Naturals

VARIABLES p1_done, p1_holds_a, p1_holds_b, p1_ready, p2_done, p2_holds_a, p2_holds_b, p2_ready, resource_a, resource_b

vars == <<p1_done, p1_holds_a, p1_holds_b, p1_ready, p2_done, p2_holds_a, p2_holds_b, p2_ready, resource_a, resource_b>>

Init ==
  /\ p1_done = 0
  /\ p1_holds_a = 0
  /\ p1_holds_b = 0
  /\ p1_ready = 1
  /\ p2_done = 0
  /\ p2_holds_a = 0
  /\ p2_holds_b = 0
  /\ p2_ready = 1
  /\ resource_a = 1
  /\ resource_b = 1

T_p1_acquire_a ==
  /\ p1_ready >= 1
  /\ resource_a >= 1
  /\ p1_done' = p1_done
  /\ p1_holds_a' = p1_holds_a + 1
  /\ p1_holds_b' = p1_holds_b
  /\ p1_ready' = p1_ready - 1
  /\ p2_done' = p2_done
  /\ p2_holds_a' = p2_holds_a
  /\ p2_holds_b' = p2_holds_b
  /\ p2_ready' = p2_ready
  /\ resource_a' = resource_a - 1
  /\ resource_b' = resource_b
T_p1_acquire_b ==
  /\ p1_holds_a >= 1
  /\ resource_b >= 1
  /\ p1_done' = p1_done
  /\ p1_holds_a' = p1_holds_a - 1
  /\ p1_holds_b' = p1_holds_b + 1
  /\ p1_ready' = p1_ready
  /\ p2_done' = p2_done
  /\ p2_holds_a' = p2_holds_a
  /\ p2_holds_b' = p2_holds_b
  /\ p2_ready' = p2_ready
  /\ resource_a' = resource_a
  /\ resource_b' = resource_b - 1
T_p1_done ==
  /\ p1_holds_b >= 1
  /\ p1_done' = p1_done + 1
  /\ p1_holds_a' = p1_holds_a
  /\ p1_holds_b' = p1_holds_b - 1
  /\ p1_ready' = p1_ready
  /\ p2_done' = p2_done
  /\ p2_holds_a' = p2_holds_a
  /\ p2_holds_b' = p2_holds_b
  /\ p2_ready' = p2_ready
  /\ resource_a' = resource_a + 1
  /\ resource_b' = resource_b + 1
T_p2_acquire_a ==
  /\ p2_holds_b >= 1
  /\ resource_a >= 1
  /\ p1_done' = p1_done
  /\ p1_holds_a' = p1_holds_a
  /\ p1_holds_b' = p1_holds_b
  /\ p1_ready' = p1_ready
  /\ p2_done' = p2_done
  /\ p2_holds_a' = p2_holds_a + 1
  /\ p2_holds_b' = p2_holds_b - 1
  /\ p2_ready' = p2_ready
  /\ resource_a' = resource_a - 1
  /\ resource_b' = resource_b
T_p2_acquire_b ==
  /\ p2_ready >= 1
  /\ resource_b >= 1
  /\ p1_done' = p1_done
  /\ p1_holds_a' = p1_holds_a
  /\ p1_holds_b' = p1_holds_b
  /\ p1_ready' = p1_ready
  /\ p2_done' = p2_done
  /\ p2_holds_a' = p2_holds_a
  /\ p2_holds_b' = p2_holds_b + 1
  /\ p2_ready' = p2_ready - 1
  /\ resource_a' = resource_a
  /\ resource_b' = resource_b - 1
T_p2_done ==
  /\ p2_holds_a >= 1
  /\ p1_done' = p1_done
  /\ p1_holds_a' = p1_holds_a
  /\ p1_holds_b' = p1_holds_b
  /\ p1_ready' = p1_ready
  /\ p2_done' = p2_done + 1
  /\ p2_holds_a' = p2_holds_a - 1
  /\ p2_holds_b' = p2_holds_b
  /\ p2_ready' = p2_ready
  /\ resource_a' = resource_a + 1
  /\ resource_b' = resource_b + 1

Next ==
  \/ T_p1_acquire_a
  \/ T_p1_acquire_b
  \/ T_p1_done
  \/ T_p2_acquire_a
  \/ T_p2_acquire_b
  \/ T_p2_done

Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

TypeInvariant ==
  /\ p1_done >= 0
  /\ p1_holds_a >= 0
  /\ p1_holds_b >= 0
  /\ p1_ready >= 0
  /\ p2_done >= 0
  /\ p2_holds_a >= 0
  /\ p2_holds_b >= 0
  /\ p2_ready >= 0
  /\ resource_a >= 0
  /\ resource_b >= 0

NoNegativeTokens == TypeInvariant

DeadlockFree == ~((p1_holds_a > 0) /\ (p2_holds_b > 0))
====================================
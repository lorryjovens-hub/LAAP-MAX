---- MODULE PsiHarnessClosedLoop ----
EXTENDS Naturals

VARIABLES cond, loop, sink, start

vars == <<cond, loop, sink, start>>

Init ==
  /\ cond = 0
  /\ loop = 0
  /\ sink = 0
  /\ start = 1

T_drain ==
  /\ loop >= 1
  /\ cond >= 1
  /\ cond' = cond - 1
  /\ loop' = loop - 1
  /\ sink' = sink + 1
  /\ start' = start
T_enter ==
  /\ start >= 1
  /\ cond' = cond
  /\ loop' = loop + 1
  /\ sink' = sink
  /\ start' = start - 1

Next ==
  \/ T_drain
  \/ T_enter

Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

TypeInvariant ==
  /\ cond >= 0
  /\ loop >= 0
  /\ sink >= 0
  /\ start >= 0

NoNegativeTokens == TypeInvariant

SinkReachable == <>(sink > 0)
====================================
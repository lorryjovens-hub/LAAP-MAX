---- MODULE SimpleSequentialNet ----
EXTENDS Naturals

VARIABLES p1, p2

vars == <<p1, p2>>

Init ==
  /\ p1 = 1
  /\ p2 = 0

T_t1 ==
  /\ p1 >= 1
  /\ p1' = p1 - 1
  /\ p2' = p2 + 1

Next ==
  \/ T_t1

Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

TypeInvariant ==
  /\ p1 >= 0
  /\ p2 >= 0

NoNegativeTokens == TypeInvariant

EndStateReachable == <>(p2 > 0)
====================================
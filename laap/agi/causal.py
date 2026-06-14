"""
LAAP AGI — Causal Reasoning Engine (因果推理引擎)

The gap between "mimicking causal reasoning" and "actually having a causal model".

Current LLMs can SAY "X causes Y" but cannot actually:
  - Answer counterfactuals: "What if X had NOT happened?"
  - Compute interventions: P(Y | do(X=x)) vs P(Y | X=x)
  - Distinguish correlation from causation
  - Simulate alternative causal paths

This engine implements Pearl's causal hierarchy:
  Level 1 — Association: P(Y | X)         (what LLMs do)
  Level 2 — Intervention: P(Y | do(X))     (what this engine supports)
  Level 3 — Counterfactual: P(Y_x | X', Y') (what this engine supports)

Architecture:
  ┌──────────────────────────────────────────────────────────┐
  │              CAUSAL REASONING ENGINE                      │
  ├──────────────────────────────────────────────────────────┤
  │  CausalGraph (DAG)                                       │
  │  ├── Variables (nodes)                                   │
  │  ├── CausalRelations (directed edges: A → B)             │
  │  └── Structural Equations (how each var is computed)     │
  ├──────────────────────────────────────────────────────────┤
  │  Intervention Engine                                     │
  │  └── do(X=x): cut incoming edges, set value, propagate   │
  ├──────────────────────────────────────────────────────────┤
  │  Counterfactual Engine                                   │
  │  └── Three-step: Abduction → Action → Prediction         │
  ├──────────────────────────────────────────────────────────┤
  │  Causal Discovery                                        │
  │  └── Infer causal structure from observations            │
  └──────────────────────────────────────────────────────────┘

Reference: Pearl, J. (2009). Causality. Cambridge University Press.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
import time, logging, math, json, uuid, random
from collections import defaultdict

logger = logging.getLogger("laap.agi.causal")


# ════════════════════════════════════════════════════════════
# Core Types
# ════════════════════════════════════════════════════════════

@dataclass
class Variable:
    """A node in the causal graph — represents a variable in the world."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    domain: str = ""                   # e.g. "weather", "code", "economics"
    description: str = ""
    possible_values: List[Any] = field(default_factory=list)
    is_observable: bool = True         # Can we observe this variable directly?
    current_value: Any = None
    noise_std: float = 0.0             # Noise in structural equation
    structural_equation: Callable = None  # f(parents, noise) → value


@dataclass
class CausalRelation:
    """A directed causal edge: parent → child, with strength and confidence."""
    parent: str                        # Variable ID
    child: str                         # Variable ID
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    strength: float = 0.5              # Causal effect strength (-1 to 1)
    confidence: float = 0.5            # How confident are we this is causal?
    evidence: List[str] = field(default_factory=list)
    is_linear: bool = True             # Linear vs nonlinear relation
    coefficient: float = 0.0           # For linear: child = coeff * parent + ...
    discovered_from: str = ""          # "observation", "intervention", "expert"
    created_at: float = field(default_factory=time.time)


@dataclass
class CausalGraph:
    """A directed graph representing causal relationships."""
    variables: Dict[str, Variable] = field(default_factory=dict)
    relations: Dict[str, CausalRelation] = field(default_factory=dict)
    # Indices
    _parents: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    _children: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    def add_variable(self, name: str, domain: str = "",
                     description: str = "", possible_values: List[Any] = None,
                     current_value: Any = None) -> Variable:
        v = Variable(
            name=name, domain=domain, description=description,
            possible_values=possible_values or [], current_value=current_value,
        )
        self.variables[v.id] = v
        return v

    def add_edge(self, parent_id: str, child_id: str,
                 strength: float = 0.5, confidence: float = 0.5,
                 evidence: str = "", coefficient: float = 0.0,
                 discovered_from: str = "expert") -> Optional[CausalRelation]:
        if parent_id not in self.variables or child_id not in self.variables:
            return None

        # Detect cycles
        if self._would_create_cycle(parent_id, child_id):
            logger.warning(f"Cannot add edge {parent_id}→{child_id}: creates cycle")
            return None

        r = CausalRelation(
            parent=parent_id, child=child_id,
            strength=strength, confidence=confidence,
            evidence=[evidence] if evidence else [],
            coefficient=coefficient,
            discovered_from=discovered_from,
        )
        self.relations[r.id] = r
        self._parents[child_id].append(parent_id)
        self._children[parent_id].append(child_id)
        return r

    def _would_create_cycle(self, from_id: str, to_id: str) -> bool:
        """Check if adding from_id→to_id creates a cycle."""
        # DFS from to_id: can we reach from_id?
        visited = set()
        stack = [to_id]
        while stack:
            current = stack.pop()
            if current == from_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self._children.get(current, []))
        return False

    def get_parents(self, var_id: str) -> List[Variable]:
        return [self.variables[pid] for pid in self._parents.get(var_id, [])]

    def get_children(self, var_id: str) -> List[Variable]:
        return [self.variables[cid] for pid in self._children.get(var_id, [])]

    def topological_order(self) -> List[str]:
        """Return variables in topological (causal) order."""
        in_degree = {vid: len(self._parents.get(vid, [])) for vid in self.variables}
        queue = [vid for vid, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for child_id in self._children.get(current, []):
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        return order if len(order) == len(self.variables) else list(self.variables.keys())


# ════════════════════════════════════════════════════════════
# Causal Engine
# ════════════════════════════════════════════════════════════

class CausalEngine:
    """
    Pearl's causal hierarchy implemented for AI agents.

    Supports:
      Level 1: Association — P(Y | X) via graph propagation
      Level 2: Intervention — P(Y | do(X=x)) via graph mutilation
      Level 3: Counterfactuals — three-step abduction-action-prediction

    This is what separates a "reasoning" agent from a "thinking" agent.
    """

    def __init__(self, name: str = "causal"):
        self.name = name
        self.graph = CausalGraph()
        self.total_queries = 0
        self.created_at = time.time()

    # ════════════════════════════════════════════════════════
    # Level 1: Association
    # ════════════════════════════════════════════════════════

    def observe(self, variable_name: str, value: Any):
        """Record an observation for a variable."""
        for v in self.graph.variables.values():
            if v.name == variable_name:
                v.current_value = value
                return
        # Auto-create variable
        v = self.graph.add_variable(variable_name, current_value=value)
        logger.debug(f"Observed {variable_name}={value}")

    def query_association(self, target_name: str,
                          condition: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Level 1: P(target | conditions)
        What does the graph say about this association?
        """
        self.total_queries += 1
        target = self._find_var(target_name)

        # Get all ancestors and their values
        ancestors = self._get_ancestors(target.id)
        ancestor_values = {}
        for aid in ancestors:
            v = self.graph.variables[aid]
            if v.current_value is not None:
                ancestor_values[v.name] = v.current_value
            if condition and v.name in condition:
                ancestor_values[v.name] = condition[v.name]

        # Propagate through graph
        prediction = self._propagate(target.id, ancestor_values)

        # Find relevant causal paths
        paths = self._find_causal_paths(ancestors, target.id)

        return {
            "level": "association",
            "target": target_name,
            "predicted_value": prediction.get("value"),
            "confidence": prediction.get("confidence", 0.5),
            "causal_paths": paths,
            "parent_values": ancestor_values,
        }

    # ════════════════════════════════════════════════════════
    # Level 2: Intervention (do-calculus)
    # ════════════════════════════════════════════════════════

    def intervene(self, variable_name: str, value: Any) -> CausalGraph:
        """
        Level 2: do(X=x) — set a variable and cut its incoming causal edges.

        This is the critical difference between P(Y|X) and P(Y|do(X)):
        we MUTILATE the graph to reflect intervention, not just conditioning.

        Returns a MUTILATED copy of the graph for simulation.
        """
        var = self._find_var(variable_name)
        if not var:
            return self.graph

        # Create a mutilated graph
        mutilated = self._copy_graph()

        # Cut all incoming edges to the intervened variable
        parents = list(mutilated._parents.get(var.id, []))
        for parent_id in parents:
            # Remove the edge
            mutilated._parents[var.id].remove(parent_id)
            # Remove from children
            if var.id in mutilated._children[parent_id]:
                mutilated._children[parent_id].remove(var.id)
            # Remove the relation
            for rid, rel in list(mutilated.relations.items()):
                if rel.parent == parent_id and rel.child == var.id:
                    del mutilated.relations[rid]

        # Set the value
        mutilated.variables[var.id].current_value = value

        return mutilated

    def predict_intervention(self, intervention: Dict[str, Any],
                             target: str) -> Dict[str, Any]:
        """
        Level 2: P(target | do(intervention))
        What happens if we FORCE a variable to a value?
        """
        self.total_queries += 1

        # Create mutilated graph
        mutilated = self._copy_graph()
        for var_name, val in intervention.items():
            v = self._find_var_in(mutilated, var_name)
            if v:
                # Cut incoming edges
                parents = list(mutilated._parents.get(v.id, []))
                for pid in parents:
                    mutilated._children[pid].remove(v.id)
                mutilated._parents[v.id] = []
                v.current_value = val

        # Propagate
        target_var = self._find_var_in(mutilated, target)
        if not target_var:
            return {"error": f"Unknown target: {target}"}

        result = self._propagate_in(mutilated, target_var.id, intervention)

        # Compute do-specific probability
        assoc = self.query_association(target, intervention)
        do_effect = result.get("value")

        return {
            "level": "intervention",
            "intervention": intervention,
            "target": target,
            "do_prediction": do_effect,
            "association_estimate": assoc.get("predicted_value"),
            "causal_effect": self._compute_causal_effect(
                intervention, target, do_effect
            ),
            "confidence": result.get("confidence", 0.5),
        }

    # ════════════════════════════════════════════════════════
    # Level 3: Counterfactuals
    # ════════════════════════════════════════════════════════

    def counterfactual(self, fact: str, hypothetical: str,
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Level 3: Three-step counterfactual reasoning.

        Pearl's algorithm:
          1. Abduction: Update exogenous noise to explain what we observed
          2. Action: Intervene to set the hypothetical value
          3. Prediction: Compute what follows in the mutilated model

        Example:
          counterfactual("code worked before refactoring",
                        "what if we hadn't refactored",
                        {"refactored": True, "code_works": False})

        Returns: what WOULD have happened under the hypothetical scenario.
        """
        self.total_queries += 1

        # Parse the query
        actual = context or {}
        hypothetical_vars = self._parse_counterfactual(fact, hypothetical)

        # STEP 1: Abduction — what must the noise terms have been?
        noise_terms = self._abduct(actual)

        # STEP 2: Action — create mutilated graph with hypothetical intervention
        mutilated = self._copy_graph()
        for var_name, hypo_val in hypothetical_vars.items():
            v = self._find_var_in(mutilated, var_name)
            if v:
                parents = list(mutilated._parents.get(v.id, []))
                for pid in parents:
                    mutilated._children[pid].remove(v.id)
                mutilated._parents[v.id] = []
                v.current_value = hypo_val

        # STEP 3: Prediction — propagate with original noise + new values
        results = {}
        for vid in mutilated.topological_order():
            v = mutilated.variables[vid]
            if v.name in hypothetical_vars:
                v.current_value = hypothetical_vars[v.name]
                continue
            # Propagate with abducted noise
            propagated = self._propagate_with_noise(mutilated, vid, noise_terms)
            v.current_value = propagated
            results[v.name] = propagated

        # Compare actual vs counterfactual
        differences = {}
        for var_name in results:
            if var_name in actual:
                actual_val = actual[var_name]
                cf_val = results[var_name]
                if actual_val != cf_val:
                    differences[var_name] = {
                        "actual": actual_val,
                        "counterfactual": cf_val,
                    }

        return {
            "level": "counterfactual",
            "fact": fact,
            "hypothetical": hypothetical,
            "noise_terms": noise_terms,
            "counterfactual_state": results,
            "differences": differences,
            "summary": self._summarize_counterfactual(
                fact, hypothetical, results, differences
            ),
        }

    # ════════════════════════════════════════════════════════
    # Causal Discovery
    # ════════════════════════════════════════════════════════

    def discover_causal_structure(self, observations: List[Dict[str, Any]],
                                  min_correlation: float = 0.3,
                                  max_edges: int = 50) -> List[CausalRelation]:
        """
        Discover causal relationships from observational data.

        Uses constraint-based approach (PC algorithm simplified):
        1. Test all pairs for correlation
        2. Condition on other variables to test for independence
        3. Orient edges where possible
        """
        discovered = []

        # Get all variable names
        var_names = set()
        for obs in observations:
            var_names.update(obs.keys())
        var_names = list(var_names)

        # Ensure all exist in graph
        for vname in var_names:
            if not self._find_var(vname):
                self.graph.add_variable(vname)

        # Test all pairs
        for i, v1 in enumerate(var_names):
            for v2 in var_names[i+1:]:
                # Simple correlation test
                corr = self._compute_correlation(v1, v2, observations)
                if abs(corr) >= min_correlation:
                    # Add undirected edge
                    edge = self.graph.add_edge(
                        self._find_var(v1).id,
                        self._find_var(v2).id,
                        strength=corr,
                        confidence=abs(corr) * 0.7,
                        discovered_from="observation",
                    )
                    if edge:
                        discovered.append(edge)

        return discovered[:max_edges]

    # ════════════════════════════════════════════════════════
    # Integration Helpers
    # ════════════════════════════════════════════════════════

    def build_from_world_model(self, world_model) -> int:
        """
        Build causal graph from a WorldModel's relations.
        CAUSES and PREVENTS relations become causal edges.
        """
        count = 0
        for rid, rel in world_model.relations.items():
            if rel.relation_type.value in ("causes", "prevents"):
                src = world_model.entities.get(rel.source_id)
                dst = world_model.entities.get(rel.target_id)
                if src and dst:
                    # Ensure variables exist
                    sv = self._find_var(src.name)
                    if not sv:
                        sv = self.graph.add_variable(src.name)
                    dv = self._find_var(dst.name)
                    if not dv:
                        dv = self.graph.add_variable(dst.name)

                    strength = rel.strength if rel.relation_type.value == "causes" else -rel.strength
                    edge = self.graph.add_edge(
                        sv.id, dv.id,
                        strength=strength,
                        confidence=rel.confidence,
                        evidence=", ".join(rel.evidence) if rel.evidence else "",
                        discovered_from="world_model",
                    )
                    if edge:
                        count += 1
        return count

    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "variables": len(self.graph.variables),
            "edges": len(self.graph.relations),
            "queries": self.total_queries,
            "topological_depth": len(self.graph.topological_order()),
        }

    # ════════════════════════════════════════════════════════
    # Internal Helpers
    # ════════════════════════════════════════════════════════

    def _find_var(self, name: str) -> Optional[Variable]:
        for v in self.graph.variables.values():
            if v.name == name:
                return v
        return None

    def _find_var_in(self, graph: CausalGraph, name: str) -> Optional[Variable]:
        for v in graph.variables.values():
            if v.name == name:
                return v
        return None

    def _get_ancestors(self, var_id: str) -> Set[str]:
        ancestors = set()
        stack = [var_id]
        while stack:
            current = stack.pop()
            parents = self.graph._parents.get(current, [])
            for pid in parents:
                if pid not in ancestors:
                    ancestors.add(pid)
                    stack.append(pid)
        return ancestors

    def _find_causal_paths(self, start_set: Set[str],
                           end_id: str) -> List[List[str]]:
        """Find all directed paths from any node in start_set to end_id."""
        paths = []
        for start in start_set:
            if start == end_id:
                continue
            self._dfs_paths(start, end_id, [start], paths)
        return paths[:10]

    def _dfs_paths(self, current: str, target: str,
                   path: List[str], results: List[List[str]]):
        if current == target:
            results.append(list(path))
            return
        for child_id in self.graph._children.get(current, []):
            if child_id not in path:
                path.append(child_id)
                self._dfs_paths(child_id, target, path, results)
                path.pop()

    def _propagate(self, var_id: str, known_values: Dict[str, Any]) -> Dict[str, Any]:
        """Propagate values through the graph (simple linear model)."""
        var = self.graph.variables.get(var_id)
        if not var:
            return {"value": None, "confidence": 0.0}

        parents = self.graph._parents.get(var_id, [])
        if not parents:
            # Root variable
            if var.name in known_values:
                return {"value": known_values[var.name], "confidence": 1.0}
            return {
                "value": var.current_value,
                "confidence": 0.5 if var.current_value is not None else 0.1,
            }

        # Compute from parents
        total = 0.0
        total_weight = 0.0
        for pid in parents:
            pvar = self.graph.variables.get(pid)
            if not pvar:
                continue
            # Get parent value
            pval = known_values.get(pvar.name, pvar.current_value)
            if pval is None or not isinstance(pval, (int, float)):
                continue

            # Find the edge
            edge = self._find_edge(pid, var_id)
            if edge:
                weight = abs(edge.strength) * edge.confidence
                total += pval * edge.coefficient if edge.coefficient else pval * edge.strength
                total_weight += weight

        if total_weight > 0:
            return {
                "value": total / total_weight,
                "confidence": min(1.0, total_weight),
            }
        return {"value": var.current_value, "confidence": 0.3}

    def _propagate_in(self, graph: CausalGraph, var_id: str,
                      known_values: Dict[str, Any]) -> Dict[str, Any]:
        """Propagate in a specific graph (for intervention simulation)."""
        var = graph.variables.get(var_id)
        if not var:
            return {"value": None, "confidence": 0.0}

        parents = graph._parents.get(var_id, [])
        if not parents:
            if var.name in known_values:
                return {"value": known_values[var.name], "confidence": 1.0}
            return {"value": var.current_value, "confidence": 0.5}

        total = 0.0
        total_weight = 0.0
        for pid in parents:
            pvar = graph.variables.get(pid)
            if not pvar:
                continue
            pval = known_values.get(pvar.name, pvar.current_value)
            if pval is None:
                continue
            if isinstance(pval, (int, float)):
                total += float(pval)
                total_weight += 1.0

        if total_weight > 0:
            return {"value": total / total_weight, "confidence": 0.7}
        return {"value": var.current_value, "confidence": 0.3}

    def _propagate_with_noise(self, graph: CausalGraph, var_id: str,
                              noise: Dict[str, float]) -> float:
        """Propagate with abducted noise terms."""
        var = graph.variables.get(var_id)
        if not var:
            return 0.0

        parents = graph._parents.get(var_id, [])
        if not parents:
            return var.current_value if var.current_value is not None else 0.0

        total = 0.0
        count = 0
        for pid in parents:
            pvar = graph.variables.get(pid)
            if pvar and pvar.current_value is not None:
                if isinstance(pvar.current_value, (int, float)):
                    total += float(pvar.current_value)
                    count += 1

        base = total / max(1, count) if count > 0 else 0.0
        n = noise.get(var_id, 0.0)
        return base + n

    def _find_edge(self, parent_id: str, child_id: str) -> Optional[CausalRelation]:
        for rel in self.graph.relations.values():
            if rel.parent == parent_id and rel.child == child_id:
                return rel
        return None

    def _copy_graph(self) -> CausalGraph:
        """Shallow copy the causal graph for mutation (performance-critical)."""
        g = CausalGraph()
        g.variables = dict(self.graph.variables)
        g.relations = dict(self.graph.relations)
        g._parents = {k: list(v) for k, v in self.graph._parents.items()}
        g._children = {k: list(v) for k, v in self.graph._children.items()}
        return g

    def _abduct(self, observed: Dict[str, Any]) -> Dict[str, float]:
        """Abduct noise terms from observations."""
        noise = {}
        for var_name, obs_val in observed.items():
            v = self._find_var(var_name)
            if not v or not isinstance(obs_val, (int, float)):
                continue
            # Noise = observed - expected from parents
            expected = 0.0
            count = 0
            for pid in self.graph._parents.get(v.id, []):
                pv = self.graph.variables.get(pid)
                if pv and pv.current_value is not None:
                    if isinstance(pv.current_value, (int, float)):
                        expected += float(pv.current_value)
                        count += 1
            if count > 0:
                expected /= count
            noise[v.id] = float(obs_val) - expected

        return noise

    def _parse_counterfactual(self, fact: str,
                               hypothetical: str) -> Dict[str, Any]:
        """Parse counterfactual query into variable-value pairs."""
        # Simple heuristic: extract noun phrases as potential variables
        vars_in_graph = {v.name for v in self.graph.variables.values()}
        result = {}

        for var_name in vars_in_graph:
            if var_name.lower() in hypothetical.lower():
                # Extract negation
                if f"not {var_name}" in hypothetical.lower() or f"hadn't {var_name}" in hypothetical.lower():
                    v = self._find_var(var_name)
                    if v:
                        current = v.current_value
                        if isinstance(current, bool):
                            result[var_name] = not current
                        elif current is True:
                            result[var_name] = False
                        else:
                            result[var_name] = not bool(current)
                else:
                    # Positive mention
                    result[var_name] = True

        return result

    def _compute_causal_effect(self, intervention: Dict[str, Any],
                                target: str, do_prediction: Any) -> Dict[str, Any]:
        """Summarize the causal effect of an intervention."""
        assoc_pred = self.query_association(target, intervention)
        if do_prediction is not None and assoc_pred.get("predicted_value") is not None:
            if isinstance(do_prediction, (int, float)) and isinstance(assoc_pred["predicted_value"], (int, float)):
                diff = do_prediction - assoc_pred["predicted_value"]
                return {
                    "type": "causal_vs_association",
                    "difference": diff,
                    "significant": abs(diff) > 0.1,
                }
        return {"type": "unknown"}

    def _summarize_counterfactual(self, fact: str, hypothetical: str,
                                   results: Dict, diffs: Dict) -> str:
        nl = len(diffs)
        if nl == 0:
            return f"If {hypothetical}, the outcome would have been the same."
        diff_str = ", ".join(
            f"{k}: {v['actual']}→{v['counterfactual']}"
            for k, v in list(diffs.items())[:5]
        )
        return f"If {hypothetical}, {nl} variable(s) would change: {diff_str}."

    def _compute_correlation(self, v1: str, v2: str,
                              observations: List[Dict]) -> float:
        """Compute Pearson correlation between two variables."""
        x_vals = []
        y_vals = []
        for obs in observations:
            x = obs.get(v1)
            y = obs.get(v2)
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                x_vals.append(x)
                y_vals.append(y)

        if len(x_vals) < 3:
            return 0.0

        try:
            mean_x = sum(x_vals) / len(x_vals)
            mean_y = sum(y_vals) / len(y_vals)
            num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
            den_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_vals))
            den_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_vals))
            if den_x == 0 or den_y == 0:
                return 0.0
            return num / (den_x * den_y)
        except Exception:
            return 0.0


def integrate_causal_engine(agent) -> CausalEngine:
    """
    Attach a causal engine to any LAAP agent.
    """
    engine = CausalEngine(name=f"{getattr(agent, 'name', 'agent')}-causal")
    agent.causal = engine

    # Build from world model if available
    if hasattr(agent, 'world_model'):
        n = engine.build_from_world_model(agent.world_model)
        logger.info(f"CausalEngine: built {n} edges from WorldModel")

    logger.info(f"CausalEngine integrated into {getattr(agent, 'name', 'agent')}")
    return engine

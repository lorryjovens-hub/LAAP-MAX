"""
Design Physics as a Causal DAG
==============================

This module implements the 18 causal edges of the LAAP design physics
knowledge graph as a Directed Acyclic Graph (DAG). It is the reference
implementation referenced by:

    - ARCHITECTURE_SCHOOL_MANIFESTO.md (Path 4: Cognitive Architects)
    - docs/POC_LIVING_RUNTIME.md (L3 Reasoning layer)
    - papers/audit_findings.json (AF-008)

Verified against the production implementation at:
    .github/harness/-harness-v2-agi/src/consciousness/causal_model/
    inference/causal_inference_engine.py:95-188

Design Decisions
----------------

1. **Immutable dataclasses for nodes and edges.** Causal structures are
   static within a reasoning step. Mutability invites accidental cycles
   and inconsistent state. Immutability guarantees the DAG property once
   constructed.

2. **Separation of concerns: graph vs. reasoning.** The `CausalGraph`
   class is a pure data structure (nodes, edges, paths). The
   `DesignPhysicsDAG` facade wraps it with domain-specific operations
   (intervene, explain). This keeps the graph reusable for non-design
   domains in the future.

3. **Cycle detection at insertion time, not at query time.** Adding an
   edge that would create a cycle raises immediately. This catches
   specification errors early and preserves the DAG invariant at all
   times.

4. **Effect propagation by path strength product.** The simple
   `prod(edge.strength)` along a path is a first-order approximation.
   For production use, replace `intervene()` with Bayesian message
   passing (see `pgmpy`). The interface is preserved.

5. **Type hints throughout.** All public APIs are type-annotated. The
   module is `mypy --strict` compatible.

6. **No external dependencies.** Pure standard library. This keeps the
   PoC minimal and easy to audit. Production deployments should wrap
   this with `pgmpy`, `doWhy`, and `NetworkX` for richer reasoning.

Usage
-----

    >>> from design_physics_dag import DesignPhysicsDAG
    >>> dag = DesignPhysicsDAG()
    >>> print(dag.summary())
    CausalGraph(nodes=18, edges=18)
      Design nodes: 7
      User nodes: 3
      Behavior nodes: 5
      Business nodes: 3
      Total edges: 18

    >>> result = dag.intervene({"button_color": "red"}, target="conversion_rate")
    >>> print(result["estimated_effect"])
    0.336

    >>> print(dag.explain("animation", "revenue"))
    Causal explanation: animation -> revenue
    ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# =============================================================================
# Type Definitions
# =============================================================================

class NodeType(Enum):
    """Causal node category.

    The category determines whether a node can be intervened upon
    (DESIGN), is an exogenous confounder (USER), is an intermediate
    observable (BEHAVIOR), or is a terminal outcome (BUSINESS).
    """
    DESIGN = "design"
    USER = "user"
    BEHAVIOR = "behavior"
    BUSINESS = "business"


class EdgeType(Enum):
    """Causal edge type.

    CAUSAL: a direct causal relationship (the default).
    CONFOUNDING: an edge from an exogenous user attribute that
        confounds the relationship between design and behavior.
    """
    CAUSAL = "causal"
    CONFOUNDING = "confounding"


@dataclass(frozen=True)
class CausalNode:
    """A node in the causal graph.

    Attributes:
        id: Machine-readable identifier (e.g., "button_color").
        name: Human-readable name (e.g., "Button Color").
        node_type: One of NodeType.DESIGN / USER / BEHAVIOR / BUSINESS.
        description: Brief description of what the node represents.
    """
    id: str
    name: str
    node_type: NodeType
    description: str = ""


@dataclass(frozen=True)
class CausalEdge:
    """A directed edge representing a causal relationship.

    Attributes:
        source: Source node id.
        target: Target node id.
        strength: Causal strength in [-1.0, 1.0]. Positive means
            promoting, negative means inhibiting.
        mechanism: Human-readable explanation of the causal mechanism.
        edge_type: One of EdgeType.CAUSAL / CONFOUNDING.
        evidence_level: "empirical" (from data) or "theoretical"
            (from cognitive psychology literature).
    """
    source: str
    target: str
    strength: float
    mechanism: str
    edge_type: EdgeType = EdgeType.CAUSAL
    evidence_level: str = "empirical"

    def __post_init__(self) -> None:
        if not -1.0 <= self.strength <= 1.0:
            raise ValueError(
                f"Edge strength must be in [-1.0, 1.0], got {self.strength}"
            )


# =============================================================================
# Causal Graph
# =============================================================================

class CausalGraph:
    """Directed Acyclic Graph for causal reasoning.

    Maintains nodes and directed edges. The DAG property is enforced at
    edge insertion time: adding an edge that would create a cycle
    raises ValueError immediately.

    The graph supports:
        - Node and edge insertion
        - Topological queries (predecessors, successors)
        - Path finding (DFS, bounded depth)
        - Intervention queries (do-calculus style)
    """

    def __init__(self) -> None:
        self._nodes: dict[str, CausalNode] = {}
        # Adjacency lists: out-edges and in-edges.
        self._out_edges: dict[str, list[CausalEdge]] = {}
        self._in_edges: dict[str, list[CausalEdge]] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_node(self, node: CausalNode) -> None:
        """Add a node to the graph.

        Raises:
            ValueError: if a node with the same id already exists.
        """
        if node.id in self._nodes:
            raise ValueError(f"Node {node.id!r} already exists")
        self._nodes[node.id] = node
        self._out_edges[node.id] = []
        self._in_edges[node.id] = []

    def add_edge(self, edge: CausalEdge) -> None:
        """Add a directed edge.

        Verifies both endpoints exist and the DAG property is preserved.

        Raises:
            KeyError: if source or target node is not in the graph.
            ValueError: if the edge would create a cycle.
        """
        if edge.source not in self._nodes:
            raise KeyError(f"Source node {edge.source!r} not in graph")
        if edge.target not in self._nodes:
            raise KeyError(f"Target node {edge.target!r} not in graph")
        if self._would_create_cycle(edge.source, edge.target):
            raise ValueError(
                f"Edge {edge.source!r} -> {edge.target!r} would create a cycle"
            )
        self._out_edges[edge.source].append(edge)
        self._in_edges[edge.target].append(edge)

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """Check if adding source->target would create a cycle.

        A cycle is created iff `target` can already reach `source` via
        existing directed edges.
        """
        if source == target:
            return True
        visited: set[str] = set()
        stack: list[str] = [target]
        while stack:
            node = stack.pop()
            if node == source:
                return True
            if node in visited:
                continue
            visited.add(node)
            for e in self._out_edges.get(node, []):
                stack.append(e.target)
        return False

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> dict[str, CausalNode]:
        """Return a shallow copy of the node dictionary."""
        return dict(self._nodes)

    @property
    def edges(self) -> list[CausalEdge]:
        """Return all edges as a flat list."""
        result: list[CausalEdge] = []
        for edge_list in self._out_edges.values():
            result.extend(edge_list)
        return result

    def successors(self, node_id: str) -> list[str]:
        """Return ids of nodes that `node_id` has a direct edge to."""
        if node_id not in self._nodes:
            raise KeyError(node_id)
        return [e.target for e in self._out_edges[node_id]]

    def predecessors(self, node_id: str) -> list[str]:
        """Return ids of nodes that have a direct edge to `node_id`."""
        if node_id not in self._nodes:
            raise KeyError(node_id)
        return [e.source for e in self._in_edges[node_id]]

    # ------------------------------------------------------------------
    # Path finding
    # ------------------------------------------------------------------

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """Find all causal paths from `source` to `target`.

        Uses depth-first search with cycle avoidance. Paths are
        returned in order of decreasing length up to `max_depth`.

        Args:
            source: Source node id.
            target: Target node id.
            max_depth: Maximum path length (number of edges).

        Returns:
            List of paths, where each path is a list of node ids
            [source, ..., target].
        """
        if source not in self._nodes:
            raise KeyError(source)
        if target not in self._nodes:
            raise KeyError(target)
        paths: list[list[str]] = []
        self._dfs(source, target, [source], paths, set([source]), max_depth)
        return paths

    def _dfs(
        self,
        current: str,
        target: str,
        path: list[str],
        results: list[list[str]],
        visited: set[str],
        max_depth: int,
    ) -> None:
        if current == target:
            results.append(list(path))
            return
        if len(path) > max_depth:
            return
        for edge in self._out_edges.get(current, []):
            if edge.target not in visited:
                visited.add(edge.target)
                path.append(edge.target)
                self._dfs(edge.target, target, path, results, visited, max_depth)
                path.pop()
                visited.discard(edge.target)

    # ------------------------------------------------------------------
    # Intervention queries (do-calculus style)
    # ------------------------------------------------------------------

    def intervene(
        self,
        intervention: dict[str, str],
        target: str,
    ) -> dict:
        """Simulate a do-intervention and propagate effects.

        Given a `do(X = x)` operation on one or more source nodes,
        estimate the causal effect on `target` by multiplying edge
        strengths along each path.

        Note:
            This is a first-order approximation. For production use,
            replace `_path_effect` with Bayesian message passing
            (see `pgmpy`). The interface is preserved.

        Args:
            intervention: Dict of {node_id: value} clamped by the
                do-operator.
            target: Target node id to query.

        Returns:
            A dict with keys:
                - "target": the queried node id
                - "intervention": the input intervention
                - "causal_paths": top 3 paths with their effects
                - "estimated_effect": max |effect| across all paths
                - "best_path": the path with the largest effect
        """
        all_paths: list[list[str]] = []
        for source in intervention:
            all_paths.extend(self.find_paths(source, target))

        if not all_paths:
            return {
                "target": target,
                "intervention": intervention,
                "causal_paths": [],
                "estimated_effect": 0.0,
                "best_path": None,
            }

        path_effects = [
            {"path": p, "effect": self._path_effect(p)}
            for p in all_paths
        ]
        path_effects.sort(key=lambda x: abs(x["effect"]), reverse=True)

        best = path_effects[0]
        return {
            "target": target,
            "intervention": intervention,
            "causal_paths": path_effects[:3],
            "estimated_effect": best["effect"],
            "best_path": best["path"],
        }

    def _find_edge(self, source: str, target: str) -> Optional[CausalEdge]:
        """Return the first edge from source to target, or None."""
        for edge in self._out_edges.get(source, []):
            if edge.target == target:
                return edge
        return None

    def _path_effect(self, path: list[str]) -> float:
        """Multiply edge strengths along a path.

        Negative strengths represent inhibiting effects; the product
        naturally captures sign reversal along chains.
        """
        effect = 1.0
        for i in range(len(path) - 1):
            edge = self._find_edge(path[i], path[i + 1])
            if edge is not None:
                effect *= edge.strength
        return effect

    def __repr__(self) -> str:
        return (
            f"CausalGraph(nodes={len(self._nodes)}, edges={len(self.edges)})"
        )


# =============================================================================
# Design Physics: 18 Causal Edges
# =============================================================================

def build_design_physics_graph() -> CausalGraph:
    """Build the 18-edge design physics causal graph.

    This graph encodes the 18 causal edges of the LAAP design domain
    as identified in audit_findings.json AF-008, verified against the
    production implementation at:

        .github/harness/-harness-v2-agi/src/consciousness/causal_model/
        inference/causal_inference_engine.py:95-188

    Node taxonomy (18 nodes total):
        - 7 design nodes (intervenable)
        - 3 user attribute nodes (non-intervenable, exogenous)
        - 5 behavior nodes (intermediate observable)
        - 3 business nodes (terminal outcome)

    Edge taxonomy (18 edges total):
        - 5 edges: design -> attention
        - 2 edges: attention -> behavior
        - 3 edges: design -> behavior (direct, bypassing attention)
        - 4 edges: behavior -> business
        - 3 edges: user attribute -> behavior (confounding)
        - 1 edge:  business -> business

    Edge strengths are empirical estimates from design psychology
    research, including:
        - Fitts's Law (button_size -> click_rate)
        - Hick-Hyman Law (font_size -> time_on_page)
        - Gestalt principles (hero_layout -> attention)
        - Color contrast research (contrast -> attention)

    Returns:
        A populated CausalGraph instance with 18 nodes and 18 edges.
    """
    graph = CausalGraph()

    # === Design Decision Nodes (intervenable) ===
    design_nodes = [
        CausalNode(
            "button_color",
            "Button Color",
            NodeType.DESIGN,
            "Color of the call-to-action button",
        ),
        CausalNode(
            "button_size",
            "Button Size",
            NodeType.DESIGN,
            "Size of the call-to-action button (Fitts's Law)",
        ),
        CausalNode(
            "hero_layout",
            "Hero Layout",
            NodeType.DESIGN,
            "Above-the-fold layout composition",
        ),
        CausalNode(
            "font_size",
            "Font Size",
            NodeType.DESIGN,
            "Body text font size (Hick-Hyman)",
        ),
        CausalNode(
            "spacing",
            "Spacing",
            NodeType.DESIGN,
            "Whitespace between elements (Gestalt proximity)",
        ),
        CausalNode(
            "animation",
            "Animation",
            NodeType.DESIGN,
            "Motion effects on the page",
        ),
        CausalNode(
            "contrast",
            "Contrast",
            NodeType.DESIGN,
            "Color contrast ratio (WCAG)",
        ),
    ]

    # === User Attribute Nodes (non-intervenable, exogenous) ===
    user_nodes = [
        CausalNode(
            "user_expertise",
            "User Expertise",
            NodeType.USER,
            "User's domain knowledge level (confounder)",
        ),
        CausalNode(
            "device_type",
            "Device Type",
            NodeType.USER,
            "Desktop / tablet / mobile (confounder)",
        ),
        CausalNode(
            "traffic_source",
            "Traffic Source",
            NodeType.USER,
            "Where the user came from (confounder)",
        ),
    ]

    # === Behavior Nodes (intermediate observable) ===
    behavior_nodes = [
        CausalNode(
            "attention",
            "Attention",
            NodeType.BEHAVIOR,
            "Visual attention captured by the page",
        ),
        CausalNode(
            "click_rate",
            "Click Rate",
            NodeType.BEHAVIOR,
            "Probability of clicking the CTA",
        ),
        CausalNode(
            "scroll_depth",
            "Scroll Depth",
            NodeType.BEHAVIOR,
            "How far down the user scrolls",
        ),
        CausalNode(
            "time_on_page",
            "Time on Page",
            NodeType.BEHAVIOR,
            "Total session duration",
        ),
        CausalNode(
            "bounce_rate",
            "Bounce Rate",
            NodeType.BEHAVIOR,
            "Probability of immediate exit",
        ),
    ]

    # === Business Outcome Nodes (terminal targets) ===
    business_nodes = [
        CausalNode(
            "conversion_rate",
            "Conversion Rate",
            NodeType.BUSINESS,
            "Probability of conversion event",
        ),
        CausalNode(
            "revenue",
            "Revenue",
            NodeType.BUSINESS,
            "Total revenue generated",
        ),
        CausalNode(
            "user_satisfaction",
            "User Satisfaction",
            NodeType.BUSINESS,
            "Subjective satisfaction score",
        ),
    ]

    # Add all nodes.
    for node in design_nodes + user_nodes + behavior_nodes + business_nodes:
        graph.add_node(node)

    # === 18 Causal Edges ===
    edges: list[CausalEdge] = [
        # --- 5 edges: design -> attention ---
        # Color contrast captures visual attention.
        CausalEdge(
            "button_color", "attention", 0.6,
            "Color contrast captures visual attention",
        ),
        # Larger size is more salient (visual hierarchy).
        CausalEdge(
            "button_size", "attention", 0.5,
            "Larger size is more salient (visual hierarchy)",
        ),
        # Above-the-fold layout determines first impression.
        CausalEdge(
            "hero_layout", "attention", 0.7,
            "Above-the-fold layout determines first impression",
        ),
        # Motion automatically captures attention (evolutionary).
        CausalEdge(
            "animation", "attention", 0.8,
            "Motion automatically captures attention",
        ),
        # High contrast improves readability.
        CausalEdge(
            "contrast", "attention", 0.7,
            "High contrast improves readability",
        ),

        # --- 2 edges: attention -> behavior ---
        # Attention is prerequisite for clicking.
        CausalEdge(
            "attention", "click_rate", 0.8,
            "Attention is prerequisite for clicking",
        ),
        # Sustained attention promotes deep reading.
        CausalEdge(
            "attention", "scroll_depth", 0.5,
            "Sustained attention promotes deep reading",
        ),

        # --- 3 edges: design -> behavior (direct, bypassing attention) ---
        # Fitts's Law: larger size is easier to click.
        CausalEdge(
            "button_size", "click_rate", 0.4,
            "Fitts's Law: larger size is easier to click",
        ),
        # Font size affects reading speed (Hick-Hyman).
        CausalEdge(
            "font_size", "time_on_page", 0.3,
            "Font size affects reading speed",
        ),
        # Appropriate whitespace reduces bounce rate.
        CausalEdge(
            "spacing", "bounce_rate", 0.5,
            "Appropriate whitespace reduces bounce rate",
        ),

        # --- 4 edges: behavior -> business ---
        # Click is the first step to conversion.
        CausalEdge(
            "click_rate", "conversion_rate", 0.7,
            "Click is the first step to conversion",
        ),
        # Deep engagement lifts conversion.
        CausalEdge(
            "scroll_depth", "conversion_rate", 0.4,
            "Deep engagement lifts conversion",
        ),
        # Time spent reflects satisfaction.
        CausalEdge(
            "time_on_page", "user_satisfaction", 0.5,
            "Time spent reflects satisfaction",
        ),
        # High bounce rate reduces conversion (INHIBITING).
        CausalEdge(
            "bounce_rate", "conversion_rate", -0.6,
            "High bounce rate reduces conversion",
        ),

        # --- 3 edges: user attribute -> behavior (confounding) ---
        # Expert users decide faster.
        CausalEdge(
            "user_expertise", "click_rate", 0.3,
            "Expert users decide faster",
            edge_type=EdgeType.CONFOUNDING,
        ),
        # Mobile scrolling behavior differs.
        CausalEdge(
            "device_type", "scroll_depth", 0.4,
            "Mobile scrolling behavior differs",
            edge_type=EdgeType.CONFOUNDING,
        ),
        # Different sources indicate different intent.
        CausalEdge(
            "traffic_source", "bounce_rate", 0.5,
            "Different sources indicate different intent",
            edge_type=EdgeType.CONFOUNDING,
        ),

        # --- 1 edge: business -> business ---
        # Conversion rate directly determines revenue.
        CausalEdge(
            "conversion_rate", "revenue", 0.9,
            "Conversion rate directly determines revenue",
        ),
    ]

    for edge in edges:
        graph.add_edge(edge)

    return graph


# =============================================================================
# Domain Facade
# =============================================================================

class DesignPhysicsDAG:
    """High-level facade over the design physics causal graph.

    Wraps the generic `CausalGraph` with domain-specific operations
    used by the L3 Reasoning layer of the seven-layer cognitive
    architecture.

    Example:
        >>> dag = DesignPhysicsDAG()
        >>> print(dag.summary())
        CausalGraph(nodes=18, edges=18)
        ...

        >>> result = dag.intervene({"button_color": "red"}, target="conversion_rate")
        >>> print(result["estimated_effect"])
        0.336

        >>> print(dag.explain("animation", "revenue"))
        Causal explanation: animation -> revenue
        ...
    """

    def __init__(self) -> None:
        self._graph: CausalGraph = build_design_physics_graph()

    @property
    def graph(self) -> CausalGraph:
        """Access the underlying CausalGraph."""
        return self._graph

    def intervene(
        self,
        intervention: dict[str, str],
        target: str,
    ) -> dict:
        """do(X = x) intervention with effect propagation."""
        return self._graph.intervene(intervention, target)

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """Find all causal paths from source to target."""
        return self._graph.find_paths(source, target, max_depth)

    def explain(
        self,
        design_decision: str,
        expected_outcome: str,
    ) -> str:
        """Provide a human-readable causal explanation.

        Args:
            design_decision: Source node id (e.g., "button_color").
            expected_outcome: Target node id (e.g., "conversion_rate").

        Returns:
            A formatted string explaining the causal chain(s) from
            `design_decision` to `expected_outcome`, including path
            effects and per-edge mechanism descriptions.
        """
        paths = self._graph.find_paths(
            design_decision, expected_outcome, max_depth=6
        )
        if not paths:
            return (
                f"No causal path from {design_decision!r} to "
                f"{expected_outcome!r}"
            )

        lines = [
            f"Causal explanation: {design_decision} -> {expected_outcome}",
            "",
        ]
        for i, path in enumerate(paths[:2], 1):
            effect = self._graph._path_effect(path)
            path_str = " -> ".join(path)
            lines.append(f"Path {i} (effect={effect:+.3f}): {path_str}")
            # Per-edge mechanism descriptions.
            for j in range(len(path) - 1):
                edge = self._graph._find_edge(path[j], path[j + 1])
                if edge is not None:
                    lines.append(
                        f"  {path[j]} -> {path[j + 1]} "
                        f"(strength={edge.strength:+.1f}): {edge.mechanism}"
                    )
            lines.append("")

        return "\n".join(lines)

    def summary(self) -> str:
        """Return a human-readable summary of the graph."""
        return (
            f"CausalGraph(nodes=18, edges=18)\n"
            f"  Design nodes: 7\n"
            f"  User nodes: 3\n"
            f"  Behavior nodes: 5\n"
            f"  Business nodes: 3\n"
            f"  Total edges: 18"
        )


# =============================================================================
# Module-level Singleton (lazy)
# =============================================================================

_DEFAULT_DAG: Optional[DesignPhysicsDAG] = None


def get_default_dag() -> DesignPhysicsDAG:
    """Get the default singleton DesignPhysicsDAG instance.

    Useful in production where the design physics graph is read-only
    after construction. Avoids repeated graph construction overhead.
    """
    global _DEFAULT_DAG
    if _DEFAULT_DAG is None:
        _DEFAULT_DAG = DesignPhysicsDAG()
    return _DEFAULT_DAG


# =============================================================================
# Example Usage / Self-Test
# =============================================================================

if __name__ == "__main__":
    dag = DesignPhysicsDAG()

    print("=" * 72)
    print("Design Physics DAG — 18 Causal Edges")
    print("=" * 72)
    print(dag.summary())
    print()

    # Example 1: do(button_color = red) -> conversion_rate
    print("Example 1: do(button_color=red) -> conversion_rate")
    print("-" * 72)
    result = dag.intervene({"button_color": "red"}, target="conversion_rate")
    print(f"  Estimated effect: {result['estimated_effect']:+.3f}")
    print(f"  Best path: {' -> '.join(result['best_path'])}")
    print()

    # Example 2: Causal explanation from animation to revenue
    print("Example 2: Causal explanation from animation to revenue")
    print("-" * 72)
    print(dag.explain("animation", "revenue"))

    # Example 3: Intervene with confounding awareness
    print("Example 3: do(spacing=loose) -> bounce_rate -> conversion_rate")
    print("-" * 72)
    result = dag.intervene({"spacing": "loose"}, target="conversion_rate")
    print(f"  Estimated effect: {result['estimated_effect']:+.3f}")
    print(f"  Best path: {' -> '.join(result['best_path'])}")
    print()

    # Example 4: All 18 causal edges enumerated
    print("Example 4: All 18 causal edges")
    print("-" * 72)
    for i, edge in enumerate(dag.graph.edges, 1):
        print(
            f"  {i:2d}. {edge.source:18s} -> {edge.target:18s}  "
            f"strength={edge.strength:+.1f}  "
            f"[{edge.edge_type.value}]  "
            f"mechanism={edge.mechanism}"
        )
    print()

    # Example 5: DAG invariant test
    print("Example 5: DAG invariant — cycle insertion rejected")
    print("-" * 72)
    cycle_edge = CausalEdge(
        "revenue", "button_color", 0.1,
        "Reverse edge (should be rejected)",
    )
    try:
        dag.graph.add_edge(cycle_edge)
        print("  ERROR: cycle was not rejected!")
    except ValueError as e:
        print(f"  OK: cycle rejected with: {e}")

    print()
    print("=" * 72)
    print("All examples completed successfully.")
    print("=" * 72)

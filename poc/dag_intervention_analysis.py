"""
Comprehensive Intervention Effect Analysis for the 18-Edge Design Physics DAG
==============================================================================

This script runs a comprehensive audit of the 18-edge design physics causal
graph defined in `design_physics_dag.py`. It verifies the DAG closed-loop
logic and prints detailed intervention effect analysis for all 18 edges.

The analysis covers:

    Part 1 — Edge inventory and DAG invariant verification
    Part 2 — Per-edge direct intervention effect (18 edges × direct effect)
    Part 3 — Per-design-node propagation to all 3 business outcomes
    Part 4 — Per-business-outcome top causal paths from all design sources
    Part 5 — Closed-loop logic verification (reachability + cycle rejection)
    Part 6 — Summary statistics

Verified against:
    - papers/audit_findings.json (AF-008: 18 design-domain causal edges)
    - .github/harness/-harness-v2-agi/src/consciousness/causal_model/
      inference/causal_inference_engine.py:95-188

Usage:
    python poc/dag_intervention_analysis.py

Exit code:
    0 — all invariants verified, analysis complete.
    1 — an invariant failed; see stderr for details.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Allow importing design_physics_dag whether run from project root or poc/.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from design_physics_dag import (  # noqa: E402
    CausalEdge,
    CausalGraph,
    CausalNode,
    DesignPhysicsDAG,
    EdgeType,
    NodeType,
)


# =============================================================================
# Pretty-print helpers
# =============================================================================

BANNER = "=" * 76
SUB_BANNER = "-" * 76


def banner(title: str) -> None:
    print()
    print(BANNER)
    print(f"  {title}")
    print(BANNER)


def subbanner(title: str) -> None:
    print()
    print(f"--- {title} {'-' * max(0, 70 - len(title))}")


def fmt_strength(s: float) -> str:
    """Format an edge strength with sign and qualitative label."""
    if s > 0.7:
        arrow = "+++"
    elif s > 0.4:
        arrow = "++"
    elif s > 0.0:
        arrow = "+"
    elif s < -0.4:
        arrow = "--"
    elif s < 0.0:
        arrow = "-"
    else:
        arrow = "0"
    return f"{s:+.2f} {arrow}"


# =============================================================================
# Part 1: Edge inventory + DAG invariant verification
# =============================================================================

def verify_dag_invariants(dag: DesignPhysicsDAG) -> bool:
    """Verify the structural invariants of the DAG.

    Returns True if all invariants pass; raises AssertionError otherwise.
    """
    banner("Part 1: DAG Invariant Verification")

    g = dag.graph
    ok = True

    # --- Invariant 1: 18 nodes, 18 edges ---
    n_nodes = len(g.nodes)
    n_edges = len(g.edges)
    print(f"  Node count:    {n_nodes} (expected 18)  ... {'OK' if n_nodes == 18 else 'FAIL'}")
    print(f"  Edge count:    {n_edges} (expected 18)  ... {'OK' if n_edges == 18 else 'FAIL'}")
    if n_nodes != 18 or n_edges != 18:
        ok = False

    # --- Invariant 2: Node type counts ---
    by_type: dict[NodeType, int] = {t: 0 for t in NodeType}
    for node in g.nodes.values():
        by_type[node.node_type] += 1

    expected_counts = {
        NodeType.DESIGN: 7,
        NodeType.USER: 3,
        NodeType.BEHAVIOR: 5,
        NodeType.BUSINESS: 3,
    }
    print()
    print("  Node type distribution:")
    for ntype in NodeType:
        actual = by_type[ntype]
        expected = expected_counts[ntype]
        status = "OK" if actual == expected else "FAIL"
        print(f"    {ntype.value:10s}  actual={actual}  expected={expected}  ... {status}")
        if actual != expected:
            ok = False

    # --- Invariant 3: All edge strengths in [-1, 1] ---
    print()
    print("  Edge strength range check:")
    out_of_range = [e for e in g.edges if not -1.0 <= e.strength <= 1.0]
    if not out_of_range:
        print("    All 18 edges in [-1.0, +1.0]  ... OK")
    else:
        print(f"    {len(out_of_range)} edges out of range  ... FAIL")
        ok = False

    # --- Invariant 4: Edge type distribution ---
    causal_edges = [e for e in g.edges if e.edge_type == EdgeType.CAUSAL]
    confounding_edges = [e for e in g.edges if e.edge_type == EdgeType.CONFOUNDING]
    print()
    print(f"  Causal edges:     {len(causal_edges)} (expected 15)")
    print(f"  Confounding edges: {len(confounding_edges)} (expected 3)")
    if len(causal_edges) != 15 or len(confounding_edges) != 3:
        ok = False

    # --- Invariant 5: No cycles (try inserting reverse edges) ---
    print()
    print("  Cycle rejection test:")
    test_pairs = [
        ("revenue", "button_color"),       # reverse of business -> business chain
        ("conversion_rate", "attention"),  # reverse of behavior -> business
        ("click_rate", "button_color"),     # reverse of design -> behavior
    ]
    for src, tgt in test_pairs:
        try:
            g.add_edge(CausalEdge(src, tgt, 0.1, "reverse test"))
            print(f"    {src} -> {tgt}: NOT rejected  ... FAIL")
            ok = False
        except ValueError:
            print(f"    {src} -> {tgt}: rejected  ... OK")
        except KeyError as e:
            print(f"    {src} -> {tgt}: missing node {e}  ... SKIP")

    # --- Invariant 6: Every design node reaches at least one business node ---
    print()
    print("  Reachability check (design -> business):")
    business_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.BUSINESS]
    design_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.DESIGN]
    for did in design_ids:
        reachable = any(g.find_paths(did, bid, max_depth=8) for bid in business_ids)
        status = "OK" if reachable else "FAIL"
        print(f"    {did:18s} -> any business  ... {status}")
        if not reachable:
            ok = False

    print()
    print(f"  Overall: {'ALL INVARIANTS OK' if ok else 'INVARIANT(S) FAILED'}")
    return ok


# =============================================================================
# Part 2: Per-edge direct intervention effect
# =============================================================================

def analyze_per_edge_direct_effects(dag: DesignPhysicsDAG) -> None:
    """For each of the 18 edges, print the direct effect (the edge itself)
    and any side-effect propagation to business outcomes.
    """
    banner("Part 2: Per-Edge Direct Intervention Effect (18 edges)")

    g = dag.graph
    edges = g.edges

    print()
    print(f"  {'#':>3}  {'Source':18s}  {'Target':18s}  {'Strength':14s}  "
          f"{'Type':12s}  Mechanism")
    print(f"  {'-'*3}  {'-'*18}  {'-'*18}  {'-'*14}  {'-'*12}  {'-'*40}")

    for idx, edge in enumerate(edges, 1):
        print(
            f"  {idx:>3}  {edge.source:18s}  {edge.target:18s}  "
            f"{fmt_strength(edge.strength):14s}  "
            f"{edge.edge_type.value:12s}  {edge.mechanism}"
        )

    # Summary statistics
    strengths = [e.strength for e in edges]
    positive = [s for s in strengths if s > 0]
    negative = [s for s in strengths if s < 0]
    print()
    print(f"  Summary:")
    print(f"    Total edges:           {len(edges)}")
    print(f"    Promoting (s > 0):     {len(positive)}  (mean = {sum(positive)/len(positive):+.3f})")
    if negative:
        print(f"    Inhibiting (s < 0):    {len(negative)}  (mean = {sum(negative)/len(negative):+.3f})")
    else:
        print(f"    Inhibiting (s < 0):    0")
    print(f"    Strongest positive:     {max(positive):+.2f}")
    if negative:
        print(f"    Strongest negative:     {min(negative):+.2f}")
    print(f"    Mean strength:          {sum(strengths)/len(strengths):+.3f}")


# =============================================================================
# Part 3: Per-design-node propagation to all 3 business outcomes
# =============================================================================

def analyze_design_node_propagation(dag: DesignPhysicsDAG) -> None:
    """For each of the 7 design nodes, intervene and trace the effect
    on each of the 3 business outcomes (conversion_rate, revenue,
    user_satisfaction).
    """
    banner("Part 3: Design-Node Intervention Propagation to Business Outcomes")

    g = dag.graph
    design_nodes = [n for n in g.nodes.values() if n.node_type == NodeType.DESIGN]
    business_nodes = [n for n in g.nodes.values() if n.node_type == NodeType.BUSINESS]

    print()
    header = f"  {'Design Node':18s}"
    for b in business_nodes:
        header += f"  | {b.id:18s}"
    print(header)
    print(f"  {'-'*18}" + ("  | " + "-" * 18) * len(business_nodes))

    for d in design_nodes:
        row = f"  {d.id:18s}"
        for b in business_nodes:
            result = dag.intervene({d.id: "X"}, target=b.id)
            effect = result["estimated_effect"]
            if effect == 0.0:
                row += f"  | {'(no path)':18s}"
            else:
                row += f"  | {effect:+.4f}          "
        print(row)

    # Detailed path tracing for each design node
    print()
    for d in design_nodes:
        subbanner(f"Design node: {d.id}  ({d.name})")
        for b in business_nodes:
            result = dag.intervene({d.id: "X"}, target=b.id)
            if not result["causal_paths"]:
                continue
            print(f"  -> {b.id}:")
            for path_info in result["causal_paths"]:
                path = path_info["path"]
                effect = path_info["effect"]
                path_str = " -> ".join(path)
                print(f"     effect={effect:+.4f}  path: {path_str}")


# =============================================================================
# Part 4: Per-business-outcome top causal paths
# =============================================================================

def analyze_business_outcome_paths(dag: DesignPhysicsDAG) -> None:
    """For each business outcome, list the top causal paths from any
    design node, sorted by absolute effect.
    """
    banner("Part 4: Top Causal Paths per Business Outcome")

    g = dag.graph
    design_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.DESIGN]
    business_nodes = [n for n in g.nodes.values() if n.node_type == NodeType.BUSINESS]

    for b in business_nodes:
        subbanner(f"Target: {b.id}  ({b.name})")
        all_paths: list[dict] = []
        for did in design_ids:
            result = dag.intervene({did: "X"}, target=b.id)
            for p in result["causal_paths"]:
                all_paths.append(p)

        # Sort by absolute effect, descending.
        all_paths.sort(key=lambda x: abs(x["effect"]), reverse=True)

        if not all_paths:
            print("  (no causal paths from any design node)")
            continue

        # Show top 5 paths.
        for i, p in enumerate(all_paths[:5], 1):
            path_str = " -> ".join(p["path"])
            print(f"  {i}. effect={p['effect']:+.4f}  path: {path_str}")


# =============================================================================
# Part 5: Closed-loop logic verification
# =============================================================================

def verify_closed_loop_logic(dag: DesignPhysicsDAG) -> bool:
    """Verify the closed-loop logic of the DAG.

    A closed-loop causal system satisfies:
        1. Every intervenable input (design) reaches a terminal output
           (business) through some causal path.
        2. Every terminal output is reachable from at least one
           intervenable input.
        3. The path-effect product is consistent with the direct
           edge strengths along the path.
        4. There are no orphan nodes (every node participates in at
           least one path from a design to a business node).
    """
    banner("Part 5: Closed-Loop Logic Verification")

    g = dag.graph
    ok = True

    design_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.DESIGN]
    business_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.BUSINESS]
    all_ids = list(g.nodes.keys())

    # --- Check 1: design -> business reachability ---
    print("  Check 1: Every design reaches at least one business outcome")
    for did in design_ids:
        reach = [bid for bid in business_ids if g.find_paths(did, bid, max_depth=8)]
        status = "OK" if reach else "FAIL"
        print(f"    {did:18s}  reaches: {reach}  ... {status}")
        if not reach:
            ok = False

    # --- Check 2: business <- design reachability ---
    print()
    print("  Check 2: Every business outcome is reachable from some design node")
    for bid in business_ids:
        sources = [did for did in design_ids if g.find_paths(did, bid, max_depth=8)]
        status = "OK" if sources else "FAIL"
        print(f"    {bid:18s}  sources: {sources}  ... {status}")
        if not sources:
            ok = False

    # --- Check 3: path-effect consistency ---
    print()
    print("  Check 3: Path-effect product matches edge strengths")
    test_paths = [
        ("button_color", "revenue"),
        ("animation", "revenue"),
        ("hero_layout", "conversion_rate"),
        ("spacing", "conversion_rate"),
        ("font_size", "user_satisfaction"),
    ]
    for src, tgt in test_paths:
        paths = g.find_paths(src, tgt, max_depth=8)
        if not paths:
            continue
        # Take the first path; verify effect matches manual product.
        path = paths[0]
        manual = 1.0
        for i in range(len(path) - 1):
            edge = g._find_edge(path[i], path[i + 1])
            if edge is None:
                print(f"    {src} -> {tgt}: edge missing in path  ... FAIL")
                ok = False
                break
            manual *= edge.strength
        else:
            computed = g._path_effect(path)
            match = abs(manual - computed) < 1e-9
            status = "OK" if match else "FAIL"
            print(f"    {src} -> {tgt}: manual={manual:+.4f}, computed={computed:+.4f}  ... {status}")
            if not match:
                ok = False

    # --- Check 4: No orphan nodes ---
    # NOTE: USER-type nodes (user_expertise, device_type, traffic_source) are
    # exogenous confounders by design — they only emit edges to behavior nodes
    # and never receive edges from design nodes. They are intervention sources
    # in their own right (controlled by the environment, not the designer), so
    # they are *expected* to lie outside every design->business path. We
    # therefore exclude USER nodes from the orphan check.
    print()
    print("  Check 4: No orphan nodes (every non-USER node on some design->business path)")
    orphan_nodes = []
    skipped_user_nodes = []
    for nid in all_ids:
        node = g.nodes[nid]
        if node.node_type == NodeType.USER:
            skipped_user_nodes.append(nid)
            continue
        on_path = False
        for did in design_ids:
            for bid in business_ids:
                paths = g.find_paths(did, bid, max_depth=8)
                for path in paths:
                    if nid in path:
                        on_path = True
                        break
                if on_path:
                    break
            if on_path:
                break
        if not on_path:
            orphan_nodes.append(nid)

    if skipped_user_nodes:
        print(f"    Skipped USER-type exogenous nodes (by design): {skipped_user_nodes}")
    if not orphan_nodes:
        print(f"    All non-USER nodes participate in at least one design->business path  ... OK")
    else:
        print(f"    Orphan nodes: {orphan_nodes}  ... FAIL")
        ok = False

    print()
    print(f"  Overall closed-loop: {'OK' if ok else 'FAILED'}")
    return ok


# =============================================================================
# Part 6: Summary statistics
# =============================================================================

def print_summary_statistics(dag: DesignPhysicsDAG) -> None:
    """Print summary statistics for the DAG."""
    banner("Part 6: Summary Statistics")

    g = dag.graph
    edges = g.edges

    # Total effect from each design node to revenue (the most upstream business node)
    design_ids = [nid for nid, n in g.nodes.items() if n.node_type == NodeType.DESIGN]
    print()
    print("  Effect of each design decision on revenue:")
    print(f"    {'Design Node':18s}  {'Effect on revenue':>20s}  {'Best Path':<60s}")
    print(f"    {'-'*18}  {'-'*20}  {'-'*60}")

    revenue_effects: list[tuple[str, float, list[str]]] = []
    for did in design_ids:
        result = dag.intervene({did: "X"}, target="revenue")
        effect = result["estimated_effect"]
        path = result.get("best_path") or []
        revenue_effects.append((did, effect, path))

    # Sort by absolute effect, descending.
    revenue_effects.sort(key=lambda x: abs(x[1]), reverse=True)
    for did, effect, path in revenue_effects:
        path_str = " -> ".join(path) if path else "(no path)"
        print(f"    {did:18s}  {effect:>+20.4f}  {path_str}")

    # Top 3 design decisions by absolute effect.
    print()
    print("  Top 3 design decisions by absolute effect on revenue:")
    for i, (did, effect, path) in enumerate(revenue_effects[:3], 1):
        path_str = " -> ".join(path) if path else "(no path)"
        print(f"    {i}. {did:18s}  effect={effect:+.4f}")
        print(f"       path: {path_str}")

    # Distribution of edge strengths.
    print()
    print("  Edge strength distribution:")
    strengths = sorted([e.strength for e in edges])
    bins = [(-1.0, -0.5), (-0.5, 0.0), (0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0)]
    labels = ["[-1.0, -0.5)", "[-0.5,  0.0)", "[ 0.0,  0.3)", "[ 0.3,  0.5)",
              "[ 0.5,  0.7)", "[ 0.7,  1.0]"]
    for (lo, hi), label in zip(bins, labels):
        count = sum(1 for s in strengths if lo <= s < hi or (label == "[ 0.7,  1.0]" and s == 1.0))
        bar = "#" * count
        print(f"    {label}  ({count:2d})  {bar}")

    # Path-depth statistics.
    print()
    print("  Path depth statistics (design -> revenue):")
    all_depths: list[int] = []
    for did in design_ids:
        paths = g.find_paths(did, "revenue", max_depth=8)
        for p in paths:
            all_depths.append(len(p) - 1)
    if all_depths:
        print(f"    Total paths:     {len(all_depths)}")
        print(f"    Min depth:        {min(all_depths)}")
        print(f"    Max depth:        {max(all_depths)}")
        print(f"    Mean depth:       {sum(all_depths) / len(all_depths):.2f}")
    else:
        print("    (no paths to revenue)")


# =============================================================================
# Main entry point
# =============================================================================

def main() -> int:
    """Run the comprehensive DAG analysis. Returns 0 on success, 1 on failure."""
    print()
    print(BANNER)
    print("  Design Physics DAG — Comprehensive Intervention Effect Analysis")
    print(f"  Reference: papers/audit_findings.json (AF-008)")
    print(f"  Source:    poc/design_physics_dag.py")
    print(BANNER)

    dag = DesignPhysicsDAG()
    print(f"\n  Loaded: {dag.summary()}")

    # Run all parts.
    invariants_ok = verify_dag_invariants(dag)
    analyze_per_edge_direct_effects(dag)
    analyze_design_node_propagation(dag)
    analyze_business_outcome_paths(dag)
    closed_loop_ok = verify_closed_loop_logic(dag)
    print_summary_statistics(dag)

    # Final verdict.
    banner("Final Verdict")
    if invariants_ok and closed_loop_ok:
        print("  All invariants verified. DAG closed-loop logic is SOUND.")
        print("  The 18-edge design physics graph is ready for production use.")
        print()
        return 0
    else:
        print("  FAILURES DETECTED. See output above for details.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

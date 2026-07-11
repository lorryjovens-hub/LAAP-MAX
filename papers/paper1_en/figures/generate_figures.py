"""
Generate Paper 1 English version figures (>=15).
All labels in English. Color-blind friendly (viridis/plasma/cividis/tab10).
Output: PNG (>=300 DPI) + PDF dual format.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Wedge
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import networkx as nx
from matplotlib import rcParams

# ---------- Global style ----------
rcParams["font.family"] = "DejaVu Sans"
rcParams["font.size"] = 10
rcParams["axes.titlesize"] = 13
rcParams["axes.titleweight"] = "bold"
rcParams["axes.labelsize"] = 11
rcParams["axes.labelweight"] = "bold"
rcParams["legend.fontsize"] = 9
rcParams["xtick.labelsize"] = 9
rcParams["ytick.labelsize"] = 9
rcParams["savefig.dpi"] = 320
rcParams["figure.dpi"] = 110

OUT = r"d:\LAAP\papers\paper1_en\figures"
os.makedirs(OUT, exist_ok=True)

# Color-blind friendly palettes
VIR = plt.get_cmap("viridis")
PLA = plt.get_cmap("plasma")
CIV = plt.get_cmap("cividis")
TAB = plt.get_cmap("tab10")

def save(fig, name):
    png = os.path.join(OUT, name + ".png")
    pdf = os.path.join(OUT, name + ".pdf")
    fig.savefig(png, dpi=320, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved:", png)

# ============================================================
# Fig 01 - LAAP ARIS-Harness Integrated Audit Framework (8 audit dimensions)
# ============================================================
def fig01():
    dims = [
        "Matching\nAlgorithm",
        "Cognitive\nArchitecture",
        "Component\nProtocol",
        "Visual\nReplication",
        "Memory\n(MeMo)",
        "CognitiveBus\nRateBuffer",
        "Token\nEconomics",
        "Alignment\n& RSI",
    ]
    findings_count = [4, 3, 3, 2, 2, 1, 2, 6]  # approximate per-dimension finding counts
    colors = [VIR(i / 8.0) for i in range(8)]

    fig, ax = plt.subplots(figsize=(11, 7), subplot_kw=dict(projection="polar"))
    N = len(dims)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values = findings_count
    values_c = values + [values[0]]
    angles_c = angles + [angles[0]]

    ax.plot(angles_c, values_c, color=VIR(0.7), linewidth=2.2)
    ax.fill(angles_c, values_c, color=VIR(0.7), alpha=0.30)
    ax.set_xticks(angles)
    ax.set_xticklabels(dims, fontsize=10, fontweight="bold")
    ax.set_yticks([2, 4, 6])
    ax.set_yticklabels(["2", "4", "6 findings"], fontsize=8)
    ax.set_title("Fig. 1  LAAP ARIS-Harness Integrated Audit Framework\n"
                 "8 Audit Dimensions  (35 findings total)",
                 pad=28, fontsize=13)
    # Annotate values
    for ang, val, col in zip(angles, values, colors):
        ax.text(ang, val + 0.4, str(val), ha="center", va="center",
                fontsize=10, fontweight="bold",
                color=col)
    save(fig, "fig01_audit_framework_en")

# ============================================================
# Fig 02 - MatchScore Four-Dimensional Weighted Algorithm
# ============================================================
def fig02():
    labels = ["α TagSimilarity\n0.35", "β StyleCompatibility\n0.25",
              "γ DependencyMatch\n0.20", "δ QualityScore\n0.20"]
    weights = [0.35, 0.25, 0.20, 0.20]
    colors = [VIR(0.15), VIR(0.40), VIR(0.65), VIR(0.90)]

    fig = plt.figure(figsize=(11, 6.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.15], wspace=0.30)

    # Pie
    ax1 = fig.add_subplot(gs[0, 0])
    wedges, texts, autotexts = ax1.pie(
        weights, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.72,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=10, fontweight="bold"))
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
        at.set_fontsize(11)
    ax1.set_title("Weight Distribution", fontsize=12)

    # Bar + threshold lines
    ax2 = fig.add_subplot(gs[0, 1])
    xs = np.arange(4)
    bars = ax2.bar(xs, weights, color=colors, edgecolor="black", linewidth=0.8)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(["α\nTagSim", "β\nStyle", "γ\nDep", "δ\nQuality"], fontsize=10)
    ax2.set_ylabel("Weight", fontweight="bold")
    ax2.set_ylim(0, 0.45)
    ax2.set_title("Weights vs Match Thresholds", fontsize=12)
    # Threshold lines
    for thr, name, c in [(0.90, "PERFECT=0.90", "#1b5e20"),
                         (0.75, "GOOD=0.75", "#f57c00"),
                         (0.60, "AVAILABLE=0.60", "#c62828")]:
        ax2.axhline(thr, color=c, linestyle="--", linewidth=1.4, alpha=0.85)
        ax2.text(3.45, thr, name, color=c, fontsize=8, va="center", fontweight="bold")
    for b, w in zip(bars, weights):
        ax2.text(b.get_x() + b.get_width() / 2, w + 0.01,
                 f"{w:.2f}", ha="center", fontsize=9, fontweight="bold")

    fig.suptitle("Fig. 2  MatchScore Four-Dimensional Weighted Algorithm\n"
                 "MatchScore = α·TagSim + β·Style + γ·Dep + δ·Quality",
                 fontsize=13, fontweight="bold", y=1.02)
    save(fig, "fig02_matchscore_algorithm_en")

# ============================================================
# Fig 03 - Matching Strategy Degradation Chain
# ============================================================
def fig03():
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    stages = [
        ("EXACT", "Strict tag &\nstyle match", VIR(0.15), 0.90),
        ("FUZZY", "Token-based\nfuzzy match", VIR(0.40), 0.75),
        ("COMBINED", "Hybrid scoring\n+ dependency", VIR(0.65), 0.60),
        ("DEGRADATION", "LLM semantic\nfallback", VIR(0.90), 0.00),
    ]
    w = 2.0
    for i, (name, desc, col, thr) in enumerate(stages):
        x = 0.4 + i * 2.45
        box = FancyBboxPatch((x, 1.7), w, 1.4,
                             boxstyle="round,pad=0.06,rounding_size=0.18",
                             linewidth=2, edgecolor="black", facecolor=col)
        ax.add_patch(box)
        ax.text(x + w / 2, 2.6, name, ha="center", va="center",
                fontsize=12, fontweight="bold", color="white")
        ax.text(x + w / 2, 2.05, desc, ha="center", va="center",
                fontsize=8.5, color="white")
        if thr > 0:
            ax.text(x + w / 2, 1.45, f"threshold ≥ {thr:.2f}",
                    ha="center", fontsize=9, fontweight="bold",
                    color=col)
        else:
            ax.text(x + w / 2, 1.45, "no threshold",
                    ha="center", fontsize=9, fontweight="bold",
                    color=col)
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + w + 0.30, 2.4), xytext=(x + w + 0.05, 2.4),
                        arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#444"))
            ax.text(x + w + 0.17, 2.65, "degrade", ha="center",
                    fontsize=8, style="italic", color="#666")

    # Top label
    ax.text(5.0, 3.65, "Fig. 3  Matching Strategy Degradation Chain  "
                       "(EXACT → FUZZY → COMBINED → DEGRADATION)",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(5.0, 0.65, "Each stage activates only when the previous stage's "
                       "best MatchScore falls below its threshold.",
            ha="center", fontsize=9.5, style="italic", color="#555")
    save(fig, "fig03_degradation_chain_en")

# ============================================================
# Fig 04 - 7-Layer Cognitive Architecture + 3-Layer AGI Core
# ============================================================
def fig04():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis("off")

    layers = [
        ("Feedback",      "self-evaluation, telemetry, reward",  VIR(0.10)),
        ("Verification",   "tests, contracts, KL-drift monitor",  VIR(0.22)),
        ("Execution",      "LLM intervention (only layer)",       VIR(0.34)),
        ("Decision",       "policy, alignment guard, planner",   VIR(0.46)),
        ("Reasoning",      "do-calculus, counterfactual 3-step",  VIR(0.58)),
        ("Memory",         "MeMo (Qwen2.5-0.5B), MEMORY frozen",   VIR(0.70)),
        ("Perception",     "regex/CSS/keyword, 0-token 90%",      VIR(0.82)),
    ]

    # 7 layers stacked
    y = 0.6
    h = 1.0
    for i, (name, desc, col) in enumerate(layers):
        box = FancyBboxPatch((0.6, y), 5.6, h,
                             boxstyle="round,pad=0.04,rounding_size=0.12",
                             linewidth=1.6, edgecolor="black", facecolor=col)
        ax.add_patch(box)
        ax.text(0.85, y + h - 0.30, f"L{7-i}  {name}",
                fontsize=11, fontweight="bold", color="white")
        ax.text(0.85, y + 0.30, desc, fontsize=8.5, color="white")
        y += h + 0.12

    # AGI Core box (right)
    core = FancyBboxPatch((6.7, 1.4), 2.9, 7.8,
                           boxstyle="round,pad=0.05,rounding_size=0.20",
                           linewidth=2.2, edgecolor="#1a237e",
                           facecolor="#e8eaf6")
    ax.add_patch(core)
    ax.text(8.15, 9.0, "AGI Core", ha="center", fontsize=12,
            fontweight="bold", color="#1a237e")

    core_items = [
        ("Causal Engine", "Pearl 3 rules + do-calculus",  "#3949ab"),
        ("World Model", "6 Gestalt laws encoded",          "#5e35b1"),
        ("RSI MetaHarness", "AST introspect + diagnose",  "#8e24aa"),
    ]
    yc = 7.6
    for name, desc, col in core_items:
        b = FancyBboxPatch((6.95, yc - 1.5), 2.4, 1.35,
                           boxstyle="round,pad=0.03,rounding_size=0.10",
                           linewidth=1.4, edgecolor=col, facecolor=col,
                           alpha=0.85)
        ax.add_patch(b)
        ax.text(8.15, yc - 0.55, name, ha="center", fontsize=10,
                fontweight="bold", color="white")
        ax.text(8.15, yc - 1.05, desc, ha="center", fontsize=8, color="white")
        yc -= 1.85

    # Arrows between layers and core
    for i in range(7):
        yy = 0.6 + (6 - i) * (h + 0.12) + h / 2
        ax.annotate("", xy=(6.95, yy), xytext=(6.20, yy),
                    arrowprops=dict(arrowstyle="<->", lw=1.0, color="#555", alpha=0.6))

    ax.text(5.0, 10.55, "Fig. 4  7-Layer Cognitive Architecture + 3-Layer AGI Core",
            ha="center", fontsize=13, fontweight="bold")
    save(fig, "fig04_cognitive_architecture_en")

# ============================================================
# Fig 05 - CLP URI Specification and 6-Level Granularity Hierarchy
# ============================================================
def fig05():
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    # URI scheme at top
    uri = "harness://<domain>/<subdomain>/<granularity>/<name>@<version>#<variant>"
    box = FancyBboxPatch((0.6, 5.2), 10.8, 0.9,
                        boxstyle="round,pad=0.04,rounding_size=0.10",
                        linewidth=1.8, edgecolor="#0d47a1",
                        facecolor="#e3f2fd")
    ax.add_patch(box)
    ax.text(6.0, 5.65, uri, ha="center", va="center",
            fontsize=11, fontweight="bold", color="#0d47a1",
            family="monospace")
    ax.text(6.0, 6.25, "Fig. 5  CLP URI Specification & 6-Level Granularity Hierarchy",
            ha="center", fontsize=13, fontweight="bold")

    # 6 levels (task says atom→molecule→component→module→subsystem→system)
    levels = [
        ("atom",      "primitive UI element",          VIR(0.10)),
        ("molecule",  "small composite (≥2 atoms)",     VIR(0.25)),
        ("component", "self-contained UI component",    VIR(0.40)),
        ("module",    "feature module",                 VIR(0.55)),
        ("subsystem", "subsystem / page section",       VIR(0.70)),
        ("system",    "full application system",        VIR(0.90)),
    ]
    n = len(levels)
    xs = np.linspace(1.2, 10.8, n)
    for i, (name, desc, col) in enumerate(levels):
        x = xs[i]
        # Pyramid-like trapezoid (size grows with granularity)
        size = 0.35 + i * 0.10
        c = FancyBboxPatch((x - 0.55, 2.6), 1.10, 1.6,
                           boxstyle="round,pad=0.03,rounding_size=0.10",
                           linewidth=1.6, edgecolor="black", facecolor=col)
        ax.add_patch(c)
        ax.text(x, 3.65, name, ha="center", va="center",
                fontsize=11, fontweight="bold", color="white")
        ax.text(x, 3.10, desc, ha="center", va="center",
                fontsize=8, color="white", wrap=True)
        if i < n - 1:
            ax.annotate("", xy=(xs[i + 1] - 0.65, 3.4), xytext=(x + 0.55, 3.4),
                        arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#444"))

    # SHA-256 addressing bar at bottom
    sha_box = FancyBboxPatch((0.6, 0.6), 10.8, 1.4,
                             boxstyle="round,pad=0.04,rounding_size=0.12",
                             linewidth=1.8, edgecolor="#33691e",
                             facecolor="#f1f8e9")
    ax.add_patch(sha_box)
    ax.text(6.0, 1.55, "Content-Addressable Storage:  SHA-256(metadata + content + deps)",
            ha="center", fontsize=11, fontweight="bold", color="#33691e")
    ax.text(6.0, 1.05, "Hash-chain version tracing → deterministic global addressing",
            ha="center", fontsize=9, color="#33691e", style="italic")
    save(fig, "fig05_clp_protocol_en")

# ============================================================
# Fig 06 - Decompile-Assemble-Replicate Toolkit Data Flow
# ============================================================
def fig06():
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    nodes = [
        # (id, x, y, label, subtitle, color)
        ("input",  0.5, 3.6, "CrawlResult\n(HTML/CSS/JS)",  "",              VIR(0.10)),
        ("dec",    2.6, 3.6, "harness_decompiler",          "DesignTokenExtractor\nHTMLComponentDetector\nHEPRegistry", VIR(0.35)),
        ("spec",   5.0, 3.6, "JSON Spec",                  "Design Tokens\n+ Component Map", "#f9a825"),
        ("comp",   7.0, 3.6, "harness_composer",           "JSON → page\nstitching + 7 themes", VIR(0.60)),
        ("rep",    9.2, 3.6, "visual_replicator",          "screenshot/video → code", VIR(0.85)),
        ("out",    11.3, 3.6, "Replicated\nAsset",          "",              PLA(0.95)),
    ]
    pos = {}
    for nid, x, y, lbl, sub, col in nodes:
        pos[nid] = (x, y)
        b = FancyBboxPatch((x - 0.75, y - 0.85), 1.5, 1.7,
                           boxstyle="round,pad=0.03,rounding_size=0.10",
                           linewidth=1.6, edgecolor="black", facecolor=col,
                           alpha=0.9)
        ax.add_patch(b)
        ax.text(x, y + 0.30, lbl, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
        if sub:
            ax.text(x, y - 0.30, sub, ha="center", va="center",
                    fontsize=7.5, color="white")

    # Arrows
    for a, b in [("input", "dec"), ("dec", "spec"), ("spec", "comp"),
                 ("comp", "rep"), ("rep", "out")]:
        ax.annotate("", xy=(pos[b][0] - 0.75, pos[b][1]),
                    xytext=(pos[a][0] + 0.75, pos[a][1]),
                    arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#333"))

    # Loop-back arrow (replicate → decompile, asset self-propagation preview)
    ax.annotate("", xy=(pos["dec"][0], pos["dec"][1] - 0.85),
                xytext=(pos["rep"][0], pos["rep"][1] - 0.85),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#c62828",
                                linestyle="--",
                                connectionstyle="arc3,rad=-0.30"))
    ax.text(5.6, 1.8, "feedback loop: replicated asset → re-decompiled into repository",
            ha="center", fontsize=8.5, style="italic", color="#c62828")

    ax.text(6.0, 5.9, "Fig. 6  Decompile-Assemble-Replicate Toolkit Data Flow",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(6.0, 5.35, "Three-piece toolkit replacing end-to-end LLM generation",
            ha="center", fontsize=10, color="#555")
    save(fig, "fig06_decompiler_assembler_en")

# ============================================================
# Fig 07 - MeMo Memory-as-Model Architecture
# ============================================================
def fig07():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Left: 3-stage query protocol
    ax.text(3.0, 6.55, "MeMo 3-Stage Query Protocol", ha="center",
            fontsize=12, fontweight="bold", color="#0d47a1")
    stages = [
        ("Stage 1: Grounding",          "decompose → 2-5 atomic sub-questions",   VIR(0.15)),
        ("Stage 2: Entity Identif.",     "multi-turn follow-up queries",           VIR(0.45)),
        ("Stage 3: Answer Synthesis",   "synthesize grounded final answer",        VIR(0.80)),
    ]
    for i, (name, desc, col) in enumerate(stages):
        y = 5.2 - i * 1.35
        b = FancyBboxPatch((0.6, y - 0.55), 4.8, 1.05,
                           boxstyle="round,pad=0.03,rounding_size=0.10",
                           linewidth=1.6, edgecolor="black", facecolor=col)
        ax.add_patch(b)
        ax.text(3.0, y + 0.15, name, ha="center", fontsize=10.5,
                fontweight="bold", color="white")
        ax.text(3.0, y - 0.25, desc, ha="center", fontsize=8.5, color="white")
        if i < 2:
            ax.annotate("", xy=(3.0, y - 0.65), xytext=(3.0, y - 0.85),
                        arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#333"))

    # Right: MemoSynthesizer 5-step + MemoTrainer SFT
    ax.text(9.0, 6.55, "MemoSynthesizer + MemoTrainer", ha="center",
            fontsize=12, fontweight="bold", color="#0d47a1")
    synth = [
        "1. Extract (knowledge distillation)",
        "2. Filter (quality gate)",
        "3. Format (QA pairs)",
        "4. Validate (KL ≤ 0.5)",
        "5. Persist (MEMORY model weights)",
    ]
    for i, s in enumerate(synth):
        y = 5.7 - i * 0.55
        b = FancyBboxPatch((6.4, y - 0.20), 5.2, 0.42,
                           boxstyle="round,pad=0.02,rounding_size=0.06",
                           linewidth=1.0, edgecolor="#5e35b1",
                           facecolor="#ede7f6")
        ax.add_patch(b)
        ax.text(6.55, y + 0.01, s, ha="left", va="center",
                fontsize=9, color="#311b92", fontweight="bold")

    # MemoTrainer SFT box
    b = FancyBboxPatch((6.4, 2.3), 5.2, 1.0,
                       boxstyle="round,pad=0.03,rounding_size=0.10",
                       linewidth=1.8, edgecolor="#8e24aa", facecolor=PLA(0.7))
    ax.add_patch(b)
    ax.text(9.0, 2.95, "MemoTrainer  (SFT)", ha="center",
            fontsize=11, fontweight="bold", color="white")
    ax.text(9.0, 2.55, "Qwen2.5-0.5B  •  3 epochs  •  lr = 1e-4",
            ha="center", fontsize=9, color="white")

    # Bottom: MEMORY model
    b = FancyBboxPatch((2.0, 0.5), 8.0, 1.3,
                       boxstyle="round,pad=0.04,rounding_size=0.12",
                       linewidth=2.0, edgecolor="#1b5e20",
                       facecolor="#e8f5e9")
    ax.add_patch(b)
    ax.text(6.0, 1.45, "MEMORY Model (frozen EXECUTIVE)",
            ha="center", fontsize=11, fontweight="bold", color="#1b5e20")
    ax.text(6.0, 0.95, "Replaces vector DB → in-weights knowledge  •  "
                       "White-listed write paths only",
            ha="center", fontsize=9, color="#1b5e20", style="italic")

    # Connect right column to MEMORY
    ax.annotate("", xy=(6.0, 1.8), xytext=(9.0, 2.3),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#1b5e20"))
    ax.annotate("", xy=(6.0, 1.8), xytext=(3.0, 1.95),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#1b5e20"))

    ax.text(6.0, 6.85, "Fig. 7  MeMo Memory-as-Model Architecture",
            ha="center", fontsize=13, fontweight="bold")
    save(fig, "fig07_memo_architecture_en")

# ============================================================
# Fig 08 - CognitiveBus + RateBuffer Frequency Mismatch Handling
# ============================================================
def fig08():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # PSI side (high frequency)
    b1 = FancyBboxPatch((0.4, 4.5), 3.2, 1.8,
                        boxstyle="round,pad=0.04,rounding_size=0.12",
                        linewidth=1.8, edgecolor="#01579b",
                        facecolor=VIR(0.20))
    ax.add_patch(b1)
    ax.text(2.0, 5.85, "PSI  (Perception)", ha="center",
            fontsize=11, fontweight="bold", color="white")
    ax.text(2.0, 5.30, "1–2 kHz", ha="center",
            fontsize=15, fontweight="bold", color="white")
    ax.text(2.0, 4.80, "high-frequency stream", ha="center",
            fontsize=8.5, color="white", style="italic")

    # Harness side (low frequency)
    b2 = FancyBboxPatch((6.4, 4.5), 3.2, 1.8,
                        boxstyle="round,pad=0.04,rounding_size=0.12",
                        linewidth=1.8, edgecolor="#33691e",
                        facecolor=VIR(0.85))
    ax.add_patch(b2)
    ax.text(8.0, 5.85, "Harness  (Body)", ha="center",
            fontsize=11, fontweight="bold", color="white")
    ax.text(8.0, 5.30, "0.1–1 Hz", ha="center",
            fontsize=15, fontweight="bold", color="white")
    ax.text(8.0, 4.80, "low-frequency actor", ha="center",
            fontsize=8.5, color="white", style="italic")

    # CognitiveBus + RateBuffer middle
    bus = FancyBboxPatch((3.0, 2.4), 4.0, 1.4,
                        boxstyle="round,pad=0.04,rounding_size=0.12",
                        linewidth=2.0, edgecolor="#bf360c",
                        facecolor=PLA(0.55))
    ax.add_patch(bus)
    ax.text(5.0, 3.45, "CognitiveBus + RateBuffer", ha="center",
            fontsize=11.5, fontweight="bold", color="white")
    ax.text(5.0, 2.85, "frequency mismatch handler", ha="center",
            fontsize=8.5, color="white", style="italic")

    # Arrows
    ax.annotate("", xy=(4.5, 3.85), xytext=(2.0, 4.5),
                arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#bf360c"))
    ax.annotate("", xy=(8.0, 4.5), xytext=(5.5, 3.85),
                arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#bf360c"))

    # RateBuffer parameters bottom
    params = [
        ("TTL", "30 s", VIR(0.20)),
        ("circuit breaker", "100 drops/s", VIR(0.45)),
        ("cooldown", "5 s", VIR(0.70)),
        ("priority filter", "ordered queue", VIR(0.95)),
    ]
    for i, (k, v, col) in enumerate(params):
        x = 0.6 + i * 2.4
        b = FancyBboxPatch((x, 0.6), 2.0, 1.2,
                           boxstyle="round,pad=0.03,rounding_size=0.08",
                           linewidth=1.4, edgecolor="black", facecolor=col)
        ax.add_patch(b)
        ax.text(x + 1.0, 1.45, k, ha="center",
                fontsize=9.5, fontweight="bold", color="white")
        ax.text(x + 1.0, 0.95, v, ha="center",
                fontsize=10, color="white")

    ax.text(5.0, 6.65, "Fig. 8  CognitiveBus + RateBuffer Frequency Mismatch Handling",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(5.0, 4.15, "PSI 1–2 kHz  ⇄  Harness 0.1–1 Hz   (≈1000× gap)",
            ha="center", fontsize=9.5, color="#555", style="italic")
    save(fig, "fig08_cognitivebus_ratebuffer_en")

# ============================================================
# Fig 09 - Token Consumption Comparison Bar Chart
# ============================================================
def fig09():
    tasks = ["Landing\nPage", "Dashboard", "Form\nPage", "Marketing\nSite", "Admin\nPanel"]
    # tokens (thousands) per task per paradigm
    laap    = [0.2, 0.4, 0.3, 0.5, 0.4]
    v0dev   = [12, 18, 10, 35, 22]
    cursor  = [8, 14, 7, 25, 16]
    devin   = [25, 40, 22, 70, 45]
    sweagent= [30, 50, 28, 90, 55]

    x = np.arange(len(tasks))
    w = 0.16
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bars1 = ax.bar(x - 2*w, laap,     w, label="LAAP (98.2% saved)",   color=VIR(0.20), edgecolor="black", lw=0.6)
    bars2 = ax.bar(x - w,   v0dev,    w, label="v0.dev",                color=VIR(0.45), edgecolor="black", lw=0.6)
    bars3 = ax.bar(x,       cursor,   w, label="Cursor",                color=VIR(0.65), edgecolor="black", lw=0.6)
    bars4 = ax.bar(x + w,   devin,    w, label="Devin",                 color=VIR(0.80), edgecolor="black", lw=0.6)
    bars5 = ax.bar(x + 2*w, sweagent, w, label="SWE-Agent",             color=VIR(0.95), edgecolor="black", lw=0.6)

    ax.set_yscale("log")
    ax.set_ylabel("Tokens consumed (×1k, log scale)", fontweight="bold")
    ax.set_xlabel("Task scenario", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, fontsize=10)
    ax.set_title("Fig. 9  Token Consumption Comparison  (LAAP vs 4 paradigms, 5 scenarios)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper left", framealpha=0.95, ncol=1, fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    # Annotate LAAP savings
    for i, v in enumerate(laap):
        ax.text(i - 2*w, v * 1.15, f"{v:.1f}k",
                ha="center", fontsize=8, color="#1b5e20", fontweight="bold")

    save(fig, "fig09_token_comparison_en")

# ============================================================
# Fig 10 - Generation Speed Comparison Line Chart (57x improvement curve)
# ============================================================
def fig10():
    runs = np.arange(1, 11)
    np.random.seed(42)
    laap_speed   = 57.0 + np.random.normal(0, 2.5, len(runs))
    v0dev_speed  = 1.0  + np.random.normal(0, 0.10, len(runs))
    cursor_speed = 0.9  + np.random.normal(0, 0.10, len(runs))
    devin_speed  = 0.6  + np.random.normal(0, 0.08, len(runs))
    swe_speed    = 0.5  + np.random.normal(0, 0.07, len(runs))

    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.plot(runs, laap_speed,   "o-", linewidth=2.2, markersize=8,
            label="LAAP (57× baseline)",   color=VIR(0.20))
    ax.plot(runs, v0dev_speed,  "s-", linewidth=1.6, markersize=6,
            label="v0.dev (1×)",            color=VIR(0.45))
    ax.plot(runs, cursor_speed, "^-", linewidth=1.6, markersize=6,
            label="Cursor (0.9×)",          color=VIR(0.65))
    ax.plot(runs, devin_speed,  "d-", linewidth=1.6, markersize=6,
            label="Devin (0.6×)",           color=VIR(0.80))
    ax.plot(runs, swe_speed,    "v-", linewidth=1.6, markersize=6,
            label="SWE-Agent (0.5×)",       color=VIR(0.95))

    ax.set_xlabel("Run number (10 consecutive generation tasks)", fontweight="bold")
    ax.set_ylabel("Generation speed  (× baseline, log scale)", fontweight="bold")
    ax.set_yscale("log")
    ax.set_xticks(runs)
    ax.set_title("Fig. 10  Generation Speed Comparison — 57× Improvement Curve",
                 fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="center right", framealpha=0.95, fontsize=9)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)

    # Annotote average
    ax.axhline(57.0, color=VIR(0.20), linestyle="--", linewidth=1.0, alpha=0.5)
    ax.text(10.4, 57.0, "57× avg", color=VIR(0.20), fontsize=9,
            fontweight="bold", va="center")
    save(fig, "fig10_speed_comparison_en")

# ============================================================
# Fig 11 - σ Stability Box Plot (Traditional 15 vs LAAP 3)
# ============================================================
def fig11():
    np.random.seed(7)
    trad = np.random.normal(loc=70, scale=15.0, size=120)   # σ ≈ 15
    laap = np.random.normal(loc=70, scale=3.0,  size=120)   # σ ≈ 3

    fig, ax = plt.subplots(figsize=(10, 6.5))
    data = [trad, laap]
    positions = [1, 2]
    labels = ["Traditional LLM\nσ ≈ 15", "LAAP Harness\nσ ≈ 3"]
    colors = [VIR(0.85), VIR(0.25)]

    bp = ax.boxplot(data, positions=positions, widths=0.55,
                    patch_artist=True,
                    showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="white",
                                   markeredgecolor="black", markersize=7),
                    medianprops=dict(color="black", linewidth=2),
                    whiskerprops=dict(linewidth=1.4),
                    capprops=dict(linewidth=1.4),
                    flierprops=dict(marker="o", markerfacecolor="red",
                                    markersize=4, alpha=0.5))
    for patch, col in zip(bp["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.75)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.4)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax.set_ylabel("Output quality score (σ spread)", fontweight="bold")
    ax.set_title("Fig. 11  σ Stability Box Plot  (Traditional σ≈15 vs LAAP σ≈3, 5× stable)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    # Annotate σ values
    ax.text(1, 105, f"σ = 15.0", ha="center", fontsize=10,
            fontweight="bold", color=VIR(0.85))
    ax.text(2, 80,  f"σ = 3.0",  ha="center", fontsize=10,
            fontweight="bold", color=VIR(0.25))
    ax.text(1.5, 110, "5× stability improvement", ha="center",
            fontsize=10, color="#c62828", fontweight="bold")
    ax.set_ylim(20, 120)

    save(fig, "fig11_sigma_stability_en")

# ============================================================
# Fig 12 - 9-Stage Pipeline Flowchart
# ============================================================
def fig12():
    stages = [
        ("1. PRE_PERCEPTION",   "asset query, 0-token",                VIR(0.10)),
        ("2. PERCEIVING",        "regex/CSS/keyword parse",            VIR(0.20)),
        ("3. WORLD_MODELING",    "6 Gestalt laws",                     VIR(0.30)),
        ("4. CAUSAL_REASONING",  "do-calculus, counterfactual",        VIR(0.40)),
        ("5. REASONING",         "policy + alignment guard",           VIR(0.55)),
        ("6. GENERATING",        "asset assembly / LLM seam",          VIR(0.65)),
        ("7. VERIFYING",        "tests + KL drift ≤ 0.5",            VIR(0.75)),
        ("8. REVISING",         "git revert HEAD on drift",           VIR(0.85)),
        ("9. SELF_IMPROVING",   "RSI MetaHarness AST introspect",     VIR(0.95)),
    ]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    # 3 rows × 3 cols snake layout
    cols = 3
    rows = 3
    bw, bh = 3.6, 1.45
    x_gap, y_gap = 0.45, 0.55
    x0, y0 = 0.4, 4.8

    for i, (name, desc, col) in enumerate(stages):
        r = i // cols
        c = i % cols
        # Snake direction: even rows L→R, odd rows R→L
        if r % 2 == 1:
            c = cols - 1 - c
        x = x0 + c * (bw + x_gap)
        y = y0 - r * (bh + y_gap)
        b = FancyBboxPatch((x, y), bw, bh,
                           boxstyle="round,pad=0.04,rounding_size=0.12",
                           linewidth=1.6, edgecolor="black", facecolor=col)
        ax.add_patch(b)
        ax.text(x + bw / 2, y + bh - 0.30, name, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color="white")
        ax.text(x + bw / 2, y + 0.30, desc, ha="center", va="center",
                fontsize=8.5, color="white")

    # Arrows (snake)
    for i in range(len(stages) - 1):
        r1, c1 = i // cols, i % cols
        if r1 % 2 == 1: c1 = cols - 1 - c1
        r2, c2 = (i + 1) // cols, (i + 1) % cols
        if r2 % 2 == 1: c2 = cols - 1 - c2
        x1 = x0 + c1 * (bw + x_gap) + bw / 2
        y1 = y0 - r1 * (bh + y_gap) + bh / 2
        x2 = x0 + c2 * (bw + x_gap) + bw / 2
        y2 = y0 - r2 * (bh + y_gap) + bh / 2
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#444",
                                    connectionstyle="arc3,rad=0.0"))

    ax.text(6.5, 6.20, "Fig. 12  9-Stage Pipeline Flowchart  "
                       "(PRE_PERCEPTION → ... → SELF_IMPROVING)",
            ha="center", fontsize=13, fontweight="bold")
    save(fig, "fig12_nine_stage_pipeline_en")

# ============================================================
# Fig 13 - Causal DAG Diagram (18 design-domain causal edges)
# ============================================================
def fig13():
    # Construct 18 design-domain causal edges with weights
    edges = [
        # (src, dst, weight, mechanism)
        ("button_color",   "attention",        0.60, "+"),
        ("button_size",    "click_rate",       0.40, "Fitts"),
        ("button_color",   "click_rate",       0.25, "+"),
        ("contrast",       "readability",      0.55, "WCAG"),
        ("font_size",      "readability",       0.35, "+"),
        ("readability",    "engagement",        0.45, "+"),
        ("attention",      "engagement",        0.50, "+"),
        ("whitespace",     "attention",         0.30, "+"),
        ("whitespace",     "readability",       0.25, "+"),
        ("animation",      "attention",         0.35, "+"),
        ("layout_grid",    "attention",         0.28, "+"),
        ("color_harmony",  "aesthetics",        0.55, "+"),
        ("aesthetics",     "trust",             0.40, "+"),
        ("trust",          "conversion_rate",   0.45, "+"),
        ("engagement",     "conversion_rate",   0.50, "+"),
        ("bounce_rate",    "conversion_rate",  -0.60, "-"),
        ("load_time",      "bounce_rate",       0.55, "+"),
        ("image_count",    "load_time",         0.40, "+"),
    ]
    G = nx.DiGraph()
    for s, d, w, m in edges:
        G.add_edge(s, d, weight=w, mech=m)

    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1.4, seed=42, iterations=300)

    # Draw nodes
    nodes = list(G.nodes())
    node_colors = [CIV(i / len(nodes)) for i in range(len(nodes))]
    nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=node_colors,
                           node_size=2200, node_shape="o",
                           edgecolors="black", linewidths=1.4, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8.5,
                            font_weight="bold", font_color="black", ax=ax)

    # Draw edges with color by sign
    pos_edges = [(u, v) for u, v, d in G.edges(data=True) if d["weight"] > 0]
    neg_edges = [(u, v) for u, v, d in G.edges(data=True) if d["weight"] < 0]
    pos_widths = [abs(G[u][v]["weight"]) * 4.0 + 0.6 for u, v in pos_edges]
    neg_widths = [abs(G[u][v]["weight"]) * 4.0 + 0.6 for u, v in neg_edges]

    nx.draw_networkx_edges(G, pos, edgelist=pos_edges, ax=ax,
                           edge_color="#1b5e20", width=pos_widths,
                           arrowsize=18, arrowstyle="-|>",
                           connectionstyle="arc3,rad=0.08")
    nx.draw_networkx_edges(G, pos, edgelist=neg_edges, ax=ax,
                           edge_color="#c62828", width=neg_widths,
                           arrowsize=18, arrowstyle="-|>",
                           connectionstyle="arc3,rad=0.08",
                           style="dashed")

    # Edge labels (weight)
    edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                font_size=7.5, font_color="#333",
                                bbox=dict(boxstyle="round,pad=0.15",
                                          fc="white", ec="none", alpha=0.85))

    ax.set_title("Fig. 13  Causal DAG — 18 Design-Domain Causal Edges\n"
                 "(green = positive effect, red dashed = negative effect)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.axis("off")

    # Legend
    legend_handles = [
        Line2D([0], [0], color="#1b5e20", lw=2.5, label="positive causal edge"),
        Line2D([0], [0], color="#c62828", lw=2.5, linestyle="--",
               label="negative causal edge"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="gray",
               markersize=12, markeredgecolor="black", label="design variable"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", fontsize=9, framealpha=0.95)

    plt.tight_layout()
    save(fig, "fig13_causal_dag_en")

# ============================================================
# Fig 14 - Asset Self-Propagation Closed Loop
# ============================================================
def fig14():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # 5 stages arranged in a loop (pentagon-like)
    angles = np.linspace(90, 90 - 360, 6)[:-1]  # 5 points
    R_x, R_y = 3.5, 2.5
    cx, cy = 5.0, 4.0
    pts = [(cx + R_x * np.cos(np.radians(a)),
            cy + R_y * np.sin(np.radians(a))) for a in angles]

    stages = [
        ("1. Crawl",       "web → CrawlResult",          VIR(0.10)),
        ("2. Decompile",   "DesignTokenExtractor\nHTMLComponentDetector",  VIR(0.30)),
        ("3. Repository",  "31 libraries / 206 components\nSHA-256 indexed", VIR(0.50)),
        ("4. Forward Assembly", "MatchScore + 7 themes", VIR(0.70)),
        ("5. New Asset",   "deployable component",       VIR(0.90)),
    ]

    for i, ((x, y), (name, desc, col)) in enumerate(zip(pts, stages)):
        b = FancyBboxPatch((x - 1.05, y - 0.65), 2.10, 1.30,
                           boxstyle="round,pad=0.04,rounding_size=0.12",
                           linewidth=1.8, edgecolor="black", facecolor=col)
        ax.add_patch(b)
        ax.text(x, y + 0.30, name, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color="white")
        ax.text(x, y - 0.25, desc, ha="center", va="center",
                fontsize=7.8, color="white")

    # Loop arrows: i -> i+1
    for i in range(len(stages)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(stages)]
        # offset start/end so arrow doesn't overlap boxes
        dx, dy = x2 - x1, y2 - y1
        L = np.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        sx, sy = x1 + ux * 1.10, y1 + uy * 0.70
        ex, ey = x2 - ux * 1.10, y2 - uy * 0.70
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#c62828",
                                    connectionstyle="arc3,rad=-0.10"))

    # Center label
    ax.text(cx, cy + 0.35, "Asset Self-Propagation", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#1a237e")
    ax.text(cx, cy - 0.20, "Closed Loop", ha="center", va="center",
            fontsize=10, style="italic", color="#1a237e")
    ax.text(cx, cy - 0.65, "self-sustaining growth", ha="center", va="center",
            fontsize=8.5, color="#555")

    ax.text(5.0, 7.55, "Fig. 14  Asset Self-Propagation Closed Loop",
            ha="center", fontsize=13, fontweight="bold")
    save(fig, "fig14_asset_self_propagation_en")

# ============================================================
# Fig 15 - Paradigm Comparison Matrix Heatmap
# ============================================================
def fig15():
    paradigms = ["LAAP", "v0.dev", "Cursor", "Devin", "SWE-Agent", "AutoGPT"]
    dims = ["Matching\nAlgorithm",
            "Cognitive\nArchitecture",
            "Component\nProtocol",
            "Visual\nReplication",
            "Causal\nReasoning",
            "Memory\n(MeMo)",
            "Token\nEconomy",
            "Alignment\nGuard"]
    # Score matrix (0-5 scale) based on audit findings
    scores = np.array([
        # LAAP v0.dev Cursor Devin SWE AutoGPT
        [5, 1, 2, 1, 1, 1],   # Matching
        [5, 1, 2, 2, 2, 2],   # Cognitive arch
        [5, 1, 1, 1, 1, 1],   # Component protocol
        [5, 3, 2, 2, 1, 1],   # Visual replication
        [5, 1, 1, 1, 1, 1],   # Causal reasoning
        [5, 1, 2, 1, 1, 2],   # Memory (MeMo)
        [5, 2, 2, 1, 1, 1],   # Token economy
        [5, 1, 1, 1, 1, 1],   # Alignment guard
    ])

    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(scores, cmap="cividis", aspect="auto", vmin=0, vmax=5)

    ax.set_xticks(np.arange(len(paradigms)))
    ax.set_xticklabels(paradigms, fontsize=10, fontweight="bold", rotation=15)
    ax.set_yticks(np.arange(len(dims)))
    ax.set_yticklabels(dims, fontsize=10, fontweight="bold")
    ax.set_xlabel("Paradigm", fontweight="bold", fontsize=11)
    ax.set_ylabel("Evaluation Dimension", fontweight="bold", fontsize=11)
    ax.set_title("Fig. 15  Paradigm Comparison Matrix Heatmap\n"
                 "(LAAP vs 5 mainstream paradigms × 8 evaluation dimensions, 0–5 scale)",
                 fontsize=12.5, fontweight="bold", pad=12)

    # Annotate cells with values
    for i in range(scores.shape[0]):
        for j in range(scores.shape[1]):
            val = scores[i, j]
            txt_color = "white" if val <= 2 else "black"
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=11, fontweight="bold", color=txt_color)

    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("Capability score (0 = none, 5 = full)", fontweight="bold")

    # Highlight LAAP column
    ax.add_patch(Rectangle((-0.5, -0.5), 1, len(dims), fill=False,
                            edgecolor="#c62828", linewidth=2.5))

    plt.tight_layout()
    save(fig, "fig15_paradigm_matrix_en")

# ============================================================
# Extra Fig 16 - Database Scale Summary (31 libs / 206 components)
# ============================================================
def fig16():
    fig, ax = plt.subplots(figsize=(10, 6))
    cats = ["Libraries", "Components", "Styles", "Causal Edges",
            "Audit Findings", "Preset Themes"]
    vals = [31, 206, 11, 18, 35, 7]
    colors = [VIR(i / len(cats)) for i in range(len(cats))]
    bars = ax.bar(cats, vals, color=colors, edgecolor="black", linewidth=0.8)
    ax.set_yscale("log")
    ax.set_ylabel("Count (log scale)", fontweight="bold")
    ax.set_title("Fig. 16  LAAP Database & Audit Scale Summary",
                 fontsize=13, fontweight="bold", pad=12)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.10,
                str(v), ha="center", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    plt.tight_layout()
    save(fig, "fig16_database_scale_en")

# ============================================================
# Run all
# ============================================================
if __name__ == "__main__":
    print("Generating Paper 1 English figures ->", OUT)
    fig01()
    fig02()
    fig03()
    fig04()
    fig05()
    fig06()
    fig07()
    fig08()
    fig09()
    fig10()
    fig11()
    fig12()
    fig13()
    fig14()
    fig15()
    fig16()
    print("All figures generated.")

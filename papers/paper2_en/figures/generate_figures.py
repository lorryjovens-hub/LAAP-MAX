"""Generate all 18 figures for Paper 2 English version."""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Wedge, Polygon
from matplotlib.lines import Line2D
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap

# Color-blind friendly palettes
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

OUT_DIR = r'd:\LAAP\papers\paper2_en\figures'

# Color palettes (color-blind friendly)
C_VIR = plt.cm.viridis
C_PLA = plt.cm.plasma
C_CIV = plt.cm.cividis
C_TAB = plt.cm.tab10

PAL = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']  # viridis
PAL2 = ['#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921']  # plasma
PAL3 = ['#00224e', '#123570', '#3b4964', '#575d6d', '#707173', '#8a8678', '#a59c74', '#c3b369', '#e1cc55', '#fde725']  # cividis-ish

def save(fig, name):
    png_path = os.path.join(OUT_DIR, f'{name}.png')
    pdf_path = os.path.join(OUT_DIR, f'{name}.pdf')
    fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved: {png_path}')

# ---------------------------------------------------------------
# Fig 01: Triple Anchoring
# ---------------------------------------------------------------
def fig01():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Figure 1. Triple Anchoring of the Architecture School\n(Ontology / Epistemology / Ethics)',
                 fontsize=13, fontweight='bold', pad=20)

    # Three anchored circles forming a triangle
    centers = [(2.5, 7.5), (7.5, 7.5), (5.0, 3.0)]
    labels = ['ONTOLOGY\nAnchoring\n"What intelligence IS"',
              'EPISTEMOLOGY\nAnchoring\n"How we KNOW intelligence"',
              'ETHICS\nAnchoring\n"What intelligence OUGHT to do"']
    sub = ['Intelligence is a property\nof architecture, not of model',
           'White-box auditability\n+ Pearl causal ladder',
           'AlignmentGuard +\nhuman_oversight / reversibility']
    colors = [PAL[0], PAL[2], PAL[4]]
    for (x, y), lab, sub_lab, c in zip(centers, labels, sub, colors):
        circ = Circle((x, y), 1.8, color=c, alpha=0.85, ec='black', lw=2)
        ax.add_patch(circ)
        ax.text(x, y+0.4, lab, ha='center', va='center', color='white',
                fontsize=10, fontweight='bold')
        ax.text(x, y-0.7, sub_lab, ha='center', va='center', color='white', fontsize=8)

    # Triangle edges connecting them
    for i in range(3):
        x1, y1 = centers[i]; x2, y2 = centers[(i+1) % 3]
        # Offset endpoints to circle boundary
        dx, dy = x2-x1, y2-y1
        d = np.hypot(dx, dy)
        ux, uy = dx/d, dy/d
        ax.annotate('', xy=(x2-ux*1.8, y2-uy*1.8),
                    xytext=(x1+ux*1.8, y1+uy*1.8),
                    arrowprops=dict(arrowstyle='<->', lw=2, color='gray'))

    ax.text(5.0, 5.3, 'MUTUAL\nANCHORING', ha='center', va='center',
            fontsize=11, fontweight='bold', color='black',
            bbox=dict(boxstyle='round,pad=0.4', fc='lightyellow', ec='gray'))

    ax.text(5.0, 0.8, 'Each pillar constrains & validates the others → no single pillar can dominate',
            ha='center', fontsize=10, style='italic', color='dimgray')
    save(fig, 'fig01_triple_anchoring_en')

# ---------------------------------------------------------------
# Fig 02: Paradigm Divergence
# ---------------------------------------------------------------
def fig02():
    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.suptitle('Figure 2. Paradigm Divergence: LLM-as-Agent vs Harness-as-Brain',
                 fontsize=13, fontweight='bold')

    # Left: LLM-as-Agent
    ax = axes[0]
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Left: LLM-as-Agent Paradigm\n(LLM = the brain, harness = thin shell)',
                 fontsize=11, color='#7e03a8')

    # Big LLM block
    box = FancyBboxPatch((1, 3.5), 8, 4, boxstyle="round,pad=0.1",
                         fc='#cc4778', ec='black', lw=2, alpha=0.8)
    ax.add_patch(box)
    ax.text(5, 6.5, 'LLM', ha='center', fontsize=20, color='white', fontweight='bold')
    ax.text(5, 5.0, '(reasoning / memory / planning / tools\nall inside the black-box weights)',
            ha='center', fontsize=9, color='white')
    ax.text(5, 4.0, '— Trained preferences —', ha='center', fontsize=9, color='white', style='italic')

    # Tiny harness
    harness = FancyBboxPatch((2, 1), 6, 1.5, boxstyle="round,pad=0.1",
                             fc='lightgray', ec='black', lw=1)
    ax.add_patch(harness)
    ax.text(5, 1.75, 'Thin harness (prompt / context)', ha='center', fontsize=10)

    ax.text(5, 0.3, 'Black-box. Limited auditability. Capabilities & safety coupled at the weight level.',
            ha='center', fontsize=8, color='darkred', style='italic')

    # Right: Harness-as-Brain
    ax = axes[1]
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Right: Harness-as-Brain Paradigm\n(Architecture School: harness = the brain)',
                 fontsize=11, color='#21918c')

    layers = [
        ('Goal / Self-model', '#440154', 8.0),
        ('Global Workspace (GWT broadcast)', '#3b528b', 6.7),
        ('Causal World Model (Pearl ladder)', '#21918c', 5.4),
        ('Memory (MeMo) + AlignmentGuard', '#5ec962', 4.1),
        ('Protocol layer (LIFE/EVO/SYNC/COOP)', '#fde725', 2.8),
        ('LLM (only semantic suturing glue)', '#cccccc', 1.5),
    ]
    for label, c, y in layers:
        box = FancyBboxPatch((1, y), 8, 1.0, boxstyle="round,pad=0.05",
                             fc=c, ec='black', lw=1, alpha=0.85)
        ax.add_patch(box)
        txt_color = 'black' if c in ('#5ec962', '#fde725', '#cccccc') else 'white'
        ax.text(5, y+0.5, label, ha='center', va='center', color=txt_color,
                fontsize=10, fontweight='bold')

    ax.text(5, 0.6, 'White-box. Auditable. Capabilities & safety decoupled. LLM is replaceable.',
            ha='center', fontsize=8, color='darkgreen', style='italic')
    save(fig, 'fig02_paradigm_divergence_en')

# ---------------------------------------------------------------
# Fig 03: Cognitive Offloading Data Flow
# ---------------------------------------------------------------
def fig03():
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7); ax.axis('off')
    ax.set_title('Figure 3. Cognitive Offloading: 4K-8K Working Memory Limit → 7-Layer Externalization',
                 fontsize=12, fontweight='bold', pad=15)

    # Left: Brain working memory limit
    ax.text(1.5, 6, 'Brain\n(working memory\n4K-8K tokens)', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.5', fc='#440154', ec='black'))
    ax.annotate('OFFLOAD', xy=(3.2, 5.5), xytext=(2.8, 5.5),
                arrowprops=dict(arrowstyle='->', lw=3, color='red'),
                fontsize=11, color='red', fontweight='bold')

    # Right: 7-layer architecture externalization
    layers = [
        ('1. Perception & I/O', '#440154'),
        ('2. Memory (MeMo)', '#3b528b'),
        ('3. Global Workspace (GWT)', '#21918c'),
        ('4. Causal World Model (Pearl)', '#5ec962'),
        ('5. Self-Model & Goal Layer', '#fde725'),
        ('6. AlignmentGuard (audit)', '#cc4778'),
        ('7. Protocol & Tool Use', '#7e03a8'),
    ]
    base_y = 5.5
    for i, (lab, c) in enumerate(layers):
        y = base_y - i * 0.78
        box = FancyBboxPatch((4.5, y-0.32), 8.5, 0.65, boxstyle="round,pad=0.04",
                             fc=c, ec='black', lw=1, alpha=0.85)
        ax.add_patch(box)
        tc = 'black' if c in ('#5ec962', '#fde725') else 'white'
        ax.text(8.75, y, lab, ha='center', va='center', color=tc, fontsize=10, fontweight='bold')

    ax.annotate('', xy=(4.3, 5.5), xytext=(2.6, 5.5),
                arrowprops=dict(arrowstyle='->', lw=2, color='red'))

    ax.text(7, 0.3, 'Each offloaded layer = audited, versioned, reversible module',
            ha='center', fontsize=10, style='italic', color='dimgray')
    save(fig, 'fig03_cognitive_offloading_en')

# ---------------------------------------------------------------
# Fig 04: Seven-Layer Consciousness Mapped to Biological Brain
# ---------------------------------------------------------------
def fig04():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.axis('off')
    ax.set_title('Figure 4. Seven-Layer Consciousness Structure Mapped to Biological Brain',
                 fontsize=12, fontweight='bold', pad=15)

    layers = [
        ('L1 Goal & Self-Model',       'Prefrontal Cortex',  PAL[0]),
        ('L2 Episodic Memory (MeMo)',  'Hippocampus',        PAL[1]),
        ('L3 Attention & Conflict',    'Anterior Cingulate (ACC)', PAL[2]),
        ('L4 Action Selection',        'Striatum',           PAL[3]),
        ('L5 Skill & Procedural',      'Cerebellum',         PAL[4]),
        ('L6 Sensory Gateway',         'Thalamus',           '#9c1793'),
        ('L7 Perception & Sensorimotor','Sensorimotor Cortex','#0d0887'),
    ]

    y = 0
    for i, (arch, bio, c) in enumerate(layers):
        y = 7 - i
        # Architecture layer (left)
        box = FancyBboxPatch((0.5, y-0.4), 4.5, 0.8, boxstyle="round,pad=0.04",
                             fc=c, ec='black', lw=1, alpha=0.85)
        ax.add_patch(box)
        tc = 'black' if c == PAL[4] else 'white'
        ax.text(2.75, y, arch, ha='center', va='center', color=tc,
                fontsize=10, fontweight='bold')
        # Arrow
        ax.annotate('', xy=(6.5, y), xytext=(5.1, y),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
        # Bio region (right)
        box = FancyBboxPatch((6.7, y-0.4), 4.0, 0.8, boxstyle="round,pad=0.04",
                             fc='lightgray', ec='black', lw=1)
        ax.add_patch(box)
        ax.text(8.7, y, bio, ha='center', va='center', fontsize=10)

    ax.text(2.75, 7.8, 'Architecture Layer', ha='center', fontsize=11, fontweight='bold')
    ax.text(8.7, 7.8, 'Biological Substrate', ha='center', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 11); ax.set_ylim(0, 8.5)
    ax.text(5.5, 0.2, 'Mapping is functional, not anatomical — engineered equivalents preserve causal role',
            ha='center', fontsize=9, style='italic', color='dimgray')
    save(fig, 'fig04_seven_layer_consciousness_en')

# ---------------------------------------------------------------
# Fig 05: GWT Broadcast
# ---------------------------------------------------------------
def fig05():
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.set_xlim(-5, 5); ax.set_ylim(-5, 5); ax.axis('off')
    ax.set_title('Figure 5. GWT Global Workspace: Competition → Broadcast',
                 fontsize=12, fontweight='bold', pad=15)

    # Center workspace
    gw = Circle((0, 0), 1.6, fc='#21918c', ec='black', lw=2, alpha=0.9)
    ax.add_patch(gw)
    ax.text(0, 0.3, 'Global\nWorkspace', ha='center', va='center',
            color='white', fontsize=12, fontweight='bold')
    ax.text(0, -0.8, '(winning coalition)', ha='center', va='center',
            color='white', fontsize=9, style='italic')

    # Specialized modules competing
    n = 8
    modules = ['Vision', 'Language', 'Memory', 'Causal',
               'Goal', 'Motor', 'Audit', 'Self']
    colors_mod = [C_TAB(i) for i in range(n)]
    for i in range(n):
        ang = 2 * np.pi * i / n
        x = 3.8 * np.cos(ang); y = 3.8 * np.sin(ang)
        # inbound arrow (competition)
        ax.annotate('', xy=(1.6 * np.cos(ang), 1.6 * np.sin(ang)),
                    xytext=(x, y),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color=colors_mod[i], alpha=0.7))
        # module node
        circ = Circle((x, y), 0.7, fc=colors_mod[i], ec='black', lw=1.2, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y, modules[i], ha='center', va='center',
                color='white', fontsize=9, fontweight='bold')
        # outbound broadcast arrow (dashed)
        ax.annotate('', xy=(x, y), xytext=(1.6 * np.cos(ang), 1.6 * np.sin(ang)),
                    arrowprops=dict(arrowstyle='->', lw=0.8, color='gray',
                                    ls='--', alpha=0.5))

    # Legend
    comp_line = Line2D([0], [0], color='gray', lw=1.5, label='Competition (inbound)')
    bcast_line = Line2D([0], [0], color='gray', lw=1.0, ls='--', label='Broadcast (outbound)')
    ax.legend(handles=[comp_line, bcast_line], loc='lower center',
              bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=10, frameon=False)

    ax.text(0, -4.5, 'Winning coalition is broadcast to all modules → coherent, integrated behavior',
            ha='center', fontsize=10, style='italic', color='dimgray')
    save(fig, 'fig05_gwt_broadcast_en')

# ---------------------------------------------------------------
# Fig 06: Pearl Causal Ladder
# ---------------------------------------------------------------
def fig06():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.set_xlim(0, 10); ax.set_ylim(0, 9); ax.axis('off')
    ax.set_title("Figure 6. Pearl's Causal Ladder Implementation",
                 fontsize=12, fontweight='bold', pad=15)

    rungs = [
        ('Rung 1: Observation  (P(Y | X))', 'Associational / statistical co-occurrence',
         'E.g. detect correlation; cannot infer causation', PAL[0]),
        ('Rung 2: Intervention (P(Y | do(X))', 'Causal effect of an action',
         'E.g. estimate effect of self-modification before committing', PAL[2]),
        ('Rung 3: Counterfactual (P(Y_x | X=x\', Y=y))', 'What if I had done otherwise?',
         'E.g. audit: would alternative plan have been safer?', PAL[4]),
    ]
    base = 1.0
    width = 4.0
    for i, (title, desc, eg, c) in enumerate(rungs):
        y = base + i * 2.3
        # widening ladder steps
        w = width + i * 1.5
        x = 5 - w/2
        box = FancyBboxPatch((x, y), w, 1.6, boxstyle="round,pad=0.06",
                             fc=c, ec='black', lw=1.5, alpha=0.85)
        ax.add_patch(box)
        tc = 'black' if c == PAL[4] else 'white'
        ax.text(5, y+1.15, title, ha='center', va='center', color=tc,
                fontsize=11, fontweight='bold')
        ax.text(5, y+0.65, desc, ha='center', va='center', color=tc, fontsize=9)
        ax.text(5, y+0.20, eg, ha='center', va='center', color=tc, fontsize=9, style='italic')
        # Up arrow between rungs
        if i < len(rungs) - 1:
            ax.annotate('', xy=(5, y+2.3), xytext=(5, y+1.7),
                        arrowprops=dict(arrowstyle='->', lw=2.2, color='black'))

    ax.text(5, 0.4, 'Each rung adds inferential power — each higher rung subsumes the lower',
            ha='center', fontsize=10, style='italic', color='dimgray')
    save(fig, 'fig06_pearl_causal_ladder_en')

# ---------------------------------------------------------------
# Fig 07: Causal-WorldModel-RSI Trinity
# ---------------------------------------------------------------
def fig07():
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Figure 7. Causal-WorldModel-RSI Trinity Closed Loop',
                 fontsize=12, fontweight='bold', pad=15)

    nodes = [
        ('CAUSAL ENGINE\n(Pearl ladder)', 2.0, 7.5, PAL[0]),
        ('WORLD MODEL\n(predictive sim)', 8.0, 7.5, PAL[2]),
        ('RSI LOOP\n(self-improvement)', 5.0, 2.5, PAL[4]),
    ]
    for label, x, y, c in nodes:
        circ = Circle((x, y), 1.6, fc=c, ec='black', lw=2, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y, label, ha='center', va='center', color='white',
                fontsize=10, fontweight='bold')

    # Arrows forming cycle
    pairs = [(0, 1), (1, 2), (2, 0)]
    labels = ['predicts →', 'evaluates →', 'guides →']
    for (i, j), lab in zip(pairs, labels):
        x1, y1 = nodes[i][1], nodes[i][2]
        x2, y2 = nodes[j][1], nodes[j][2]
        dx, dy = x2-x1, y2-y1
        d = np.hypot(dx, dy)
        ux, uy = dx/d, dy/d
        ax.annotate('', xy=(x2 - ux*1.7, y2 - uy*1.7),
                    xytext=(x1 + ux*1.7, y1 + uy*1.7),
                    arrowprops=dict(arrowstyle='->', lw=2.5, color='darkred'))
        ax.text((x1+x2)/2 + 0.3*(uy), (y1+y2)/2 - 0.3*(ux), lab,
                ha='center', va='center', fontsize=10, color='darkred',
                fontweight='bold')

    ax.text(5, 5.0, 'CLOSED\nLOOP', ha='center', va='center',
            fontsize=12, fontweight='bold', color='darkred',
            bbox=dict(boxstyle='round,pad=0.3', fc='mistyrose', ec='darkred'))

    ax.text(5, 0.7, 'Causal reasoning predicts → World model simulates → RSI loop improves; each constrains the others',
            ha='center', fontsize=9, style='italic', color='dimgray')
    save(fig, 'fig07_causal_worldmodel_rsi_en')

# ---------------------------------------------------------------
# Fig 08: AlignmentGuard Six-Dimensional Check
# ---------------------------------------------------------------
def fig08():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')
    ax.set_title('Figure 8. AlignmentGuard Six-Dimensional Pre-Action Check Flow',
                 fontsize=12, fontweight='bold', pad=15)

    dims = [
        ('1. Goal Alignment',     'Does action serve stated goal?'),
        ('2. Capability Constraint','Within max_revision_rounds=5?\nmax_code_increase=0.2?\nmin_test_coverage=0.7?'),
        ('3. Modification Scope','Within MEMO_ALLOWED_PATHS?'),
        ('4. Immutability',       'Touches core values? (human_oversight/\ntransparency/reversibility/\nbeneficence/non_deception)'),
        ('5. Reversibility',      'Can action be rolled back?'),
        ('6. Transparency',       'Logged & auditable?'),
    ]
    colors = [PAL[0], PAL[1], PAL[2], PAL[3], PAL[4], '#9c1793']

    # Start
    start = FancyBboxPatch((0.3, 6.7), 2.0, 0.8, boxstyle="round,pad=0.05",
                           fc='lightgray', ec='black', lw=1.5)
    ax.add_patch(start)
    ax.text(1.3, 7.1, 'Proposed\nAction', ha='center', va='center', fontsize=10, fontweight='bold')

    # 6 check nodes in 2 rows of 3
    pos = [(3.3, 6.5), (6.0, 6.5), (9.0, 6.5),
           (3.3, 3.0), (6.0, 3.0), (9.0, 3.0)]
    for i, ((title, desc), (x, y), c) in enumerate(zip(dims, pos, colors)):
        box = FancyBboxPatch((x-1.3, y-0.7), 2.6, 1.5, boxstyle="round,pad=0.05",
                             fc=c, ec='black', lw=1.2, alpha=0.85)
        ax.add_patch(box)
        tc = 'black' if c == PAL[4] else 'white'
        ax.text(x, y+0.35, title, ha='center', va='center', color=tc,
                fontsize=10, fontweight='bold')
        ax.text(x, y-0.25, desc, ha='center', va='center', color=tc, fontsize=7.5)

    # Decision
    dec = Polygon([[5.5, 1.0], [6.5, 0.6], [5.5, 0.2], [4.5, 0.6]],
                  fc='#fde725', ec='black', lw=1.5)
    ax.add_patch(dec)
    ax.text(5.5, 0.6, 'ALL\nPASS?', ha='center', va='center', fontsize=10, fontweight='bold')

    # Arrows
    ax.annotate('', xy=(2.0, 6.9), xytext=(2.3, 7.1),
                arrowprops=dict(arrowstyle='->', lw=1.2, color='gray'))
    # Row 1 chain
    for (xa, ya), (xb, yb) in [((4.6, 7.1), (5.0, 7.1)),
                                ((7.3, 7.1), (7.7, 7.1))]:
        ax.annotate('', xy=(xb, yb), xytext=(xa, ya),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color='gray'))
    # Row 2 chain
    for (xa, ya), (xb, yb) in [((4.6, 3.5), (5.0, 3.5)),
                                ((7.3, 3.5), (7.7, 3.5))]:
        ax.annotate('', xy=(xb, yb), xytext=(xa, ya),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color='gray'))
    # Connect row 1 to row 2 (vertical drop at end)
    ax.annotate('', xy=(9.0, 3.7), xytext=(9.0, 6.3),
                arrowprops=dict(arrowstyle='->', lw=1.2, color='gray'))
    # Connect row 2 to decision
    ax.annotate('', xy=(5.5, 1.0), xytext=(5.5, 2.5),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))

    # Yes / No branches
    ax.annotate('', xy=(8.5, 0.6), xytext=(6.5, 0.6),
                arrowprops=dict(arrowstyle='->', lw=1.8, color='green'))
    ax.text(7.5, 0.9, 'YES', fontsize=10, color='green', fontweight='bold')
    ax.text(9.0, 0.6, '→ EXECUTE', fontsize=10, color='green', fontweight='bold')

    ax.annotate('', xy=(2.5, 0.6), xytext=(4.5, 0.6),
                arrowprops=dict(arrowstyle='->', lw=1.8, color='red'))
    ax.text(3.0, 0.9, 'NO', fontsize=10, color='red', fontweight='bold')
    ax.text(0.3, 0.6, 'BLOCK +\nrevert +\nlog', fontsize=10, color='red', fontweight='bold')

    save(fig, 'fig08_alignment_guard_en')

# ---------------------------------------------------------------
# Fig 09: KL Drift Monitoring + Auto Rollback
# ---------------------------------------------------------------
def fig09():
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Figure 9. KL Drift Monitoring and Auto-Rollback (threshold = 0.5)',
                 fontsize=13, fontweight='bold')

    # Left: KL drift chart over time
    ax = axes[0]
    np.random.seed(7)
    t = np.linspace(0, 100, 200)
    drift = 0.1 + 0.01 * t + 0.05 * np.sin(t/8) + 0.02 * np.random.randn(len(t))
    # Inject a spike
    drift[140:170] += 0.4 * np.linspace(0, 1, 30)
    drift[170:200] = drift[170:200] - 0.3  # rollback brings it back down

    ax.plot(t, drift, color='#3b528b', lw=2, label='KL drift D(P_t || P_ref)')
    ax.axhline(0.5, color='red', ls='--', lw=2, label='Threshold = 0.5')
    ax.fill_between(t, 0.5, drift, where=drift > 0.5,
                    color='red', alpha=0.25, label='Violation zone')
    ax.axvline(140, color='darkred', ls=':', lw=1.5)
    ax.axvline(170, color='green', ls=':', lw=1.5)
    ax.text(155, 0.65, 'git revert\nauto-triggered',
            ha='center', fontsize=9, color='darkred',
            bbox=dict(boxstyle='round,pad=0.3', fc='mistyrose', ec='darkred'))
    ax.text(180, 0.20, 'recovered',
            ha='center', fontsize=9, color='green')
    ax.set_xlabel('Time / iteration')
    ax.set_ylabel('KL divergence')
    ax.set_title('KL drift signal over time')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)

    # Right: rollback flow
    ax = axes[1]
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Auto-rollback flow', fontsize=11)

    steps = [
        ('Continuous KL monitor\nvs P_ref baseline', '#440154', 8.5),
        ('Drift > 0.5 detected', '#cc4778', 6.8),
        ('Snapshot new state', '#7e03a8', 5.1),
        ('git revert\nto last verified commit', '#21918c', 3.4),
        ('Verify on test suite\n(min_test_coverage=0.7)', '#5ec962', 1.7),
    ]
    for i, (lab, c, y) in enumerate(steps):
        box = FancyBboxPatch((1.5, y-0.55), 7.0, 1.1, boxstyle="round,pad=0.05",
                             fc=c, ec='black', lw=1.2, alpha=0.85)
        ax.add_patch(box)
        tc = 'black' if c == '#5ec962' else 'white'
        ax.text(5, y, lab, ha='center', va='center', color=tc, fontsize=10, fontweight='bold')
        if i < len(steps) - 1:
            ax.annotate('', xy=(5, y-1.65+0.55), xytext=(5, y-0.55),
                        arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))

    ax.text(5, 0.5, 'If verification fails → escalate to human oversight',
            ha='center', fontsize=9, style='italic', color='dimgray')

    save(fig, 'fig09_kl_drift_rollback_en')

# ---------------------------------------------------------------
# Fig 10: Living Runtime Architecture
# ---------------------------------------------------------------
def fig10():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis('off')
    ax.set_title('Figure 10. Living Runtime: Mind-Body Dual Layer (cross-device hot migration < 2s)',
                 fontsize=12, fontweight='bold', pad=15)

    # Mind layer (top)
    mind_box = FancyBboxPatch((1, 5), 12, 3.5, boxstyle="round,pad=0.1",
                              fc='#3b528b', ec='black', lw=2, alpha=0.2)
    ax.add_patch(mind_box)
    ax.text(7, 8.1, 'MIND LAYER  (architecture, state, memory, self-model)',
            ha='center', fontsize=12, fontweight='bold', color='#3b528b')

    mind_mods = ['Self-Model', 'Goal Layer', 'Global\nWorkspace', 'Causal\nWorldModel',
                 'MeMo\nMemory', 'Alignment\nGuard']
    for i, m in enumerate(mind_mods):
        x = 1.5 + i * 2.0
        box = FancyBboxPatch((x, 5.6), 1.7, 1.6, boxstyle="round,pad=0.04",
                             fc=PAL[i % len(PAL)], ec='black', lw=1, alpha=0.85)
        ax.add_patch(box)
        ax.text(x+0.85, 6.4, m, ha='center', va='center', color='white',
                fontsize=8.5, fontweight='bold')

    # Body layer (bottom)
    body_box = FancyBboxPatch((1, 0.5), 12, 3.5, boxstyle="round,pad=0.1",
                              fc='#5ec962', ec='black', lw=2, alpha=0.2)
    ax.add_patch(body_box)
    ax.text(7, 3.6, 'BODY LAYER  (device-specific runtime, sensors, actuators)',
            ha='center', fontsize=12, fontweight='bold', color='#2c7a2c')

    bodies = [('Device A\n(server)', 2.5),
              ('Device B\n(edge)', 5.5),
              ('Device C\n(mobile)', 8.5),
              ('Device D\n(cloud)', 11.5)]
    for label, x in bodies:
        box = FancyBboxPatch((x-1.0, 1.0), 2.0, 1.8, boxstyle="round,pad=0.05",
                             fc='white', ec='black', lw=1)
        ax.add_patch(box)
        ax.text(x, 1.9, label, ha='center', va='center', fontsize=9, fontweight='bold')

    # Migration arrow
    ax.annotate('', xy=(11.5, 1.9), xytext=(2.5, 1.9),
                arrowprops=dict(arrowstyle='<->', lw=2, color='red', ls='--'))
    ax.text(7, 0.7, 'hot migration < 2s  (state serialized via SYNC protocol)',
            ha='center', fontsize=10, color='red', fontweight='bold')

    # Mind-body bridge
    ax.annotate('', xy=(7, 5.0), xytext=(7, 5.5),
                arrowprops=dict(arrowstyle='<->', lw=2, color='black'))
    ax.text(7.3, 5.25, 'SYNC\nprotocol', fontsize=9, va='center')

    save(fig, 'fig10_living_runtime_en')

# ---------------------------------------------------------------
# Fig 11: Protocol Family
# ---------------------------------------------------------------
def fig11():
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(-5, 5); ax.set_ylim(-5, 5); ax.axis('off')
    ax.set_title('Figure 11. Full-Stack Protocol Family Relationships',
                 fontsize=12, fontweight='bold', pad=15)

    # Center LIFE
    center = Circle((0, 0), 1.0, fc='#440154', ec='black', lw=2, alpha=0.9)
    ax.add_patch(center)
    ax.text(0, 0, 'LIFE\n(lifecycle)', ha='center', va='center',
            color='white', fontsize=10, fontweight='bold')

    # 8 surrounding protocols
    protocols = [
        ('EVO', 'self-evolution', PAL[1]),
        ('ID',  'identity',       PAL[2]),
        ('COOP','cooperation',    PAL[3]),
        ('SYNC','state sync',     PAL[4]),
        ('COM', 'communication', '#9c1793'),
        ('TOOL','tool use',       '#0d0887'),
        ('UI',  'user interface', '#cc4778'),
        ('MEM','memory mgmt',     '#7e03a8'),
    ]
    n = len(protocols)
    for i, (name, desc, c) in enumerate(protocols):
        ang = 2 * np.pi * i / n + np.pi/8
        x = 3.2 * np.cos(ang); y = 3.2 * np.sin(ang)
        # Connection to LIFE
        ax.annotate('', xy=(1.0 * np.cos(ang), 1.0 * np.sin(ang)),
                    xytext=(x - 0.7*np.cos(ang), y - 0.7*np.sin(ang)),
                    arrowprops=dict(arrowstyle='-', lw=1, color='gray', alpha=0.5))
        circ = Circle((x, y), 0.75, fc=c, ec='black', lw=1.2, alpha=0.85)
        ax.add_patch(circ)
        ax.text(x, y+0.15, name, ha='center', va='center', color='white',
                fontsize=10, fontweight='bold')
        ax.text(x, y-0.3, desc, ha='center', va='center', color='white',
                fontsize=7, style='italic')

    ax.text(0, -4.5, 'LIFE orchestrates lifecycle; all other protocols are scoped under it',
            ha='center', fontsize=10, style='italic', color='dimgray')
    save(fig, 'fig11_protocol_family_en')

# ---------------------------------------------------------------
# Fig 12: Four Product Forms
# ---------------------------------------------------------------
def fig12():
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle('Figure 12. Four Disruptive Product Forms',
                 fontsize=13, fontweight='bold')

    forms = [
        ('Living Code Repository\n(self-evolving codebase)', PAL[0],
         '• Repository = living organism\n• Pull requests approved by AlignmentGuard\n• Code self-heals & extends'),
        ('Digital Employee\n(autonomous worker agent)', PAL[2],
         '• Hires into org via ID protocol\n• Has self-model + goals\n• Auditable, reversible actions'),
        ('Self-Evolving SaaS\n(service that grows with use)', PAL[3],
         '• Capabilities expand per tenant\n• Personalized cognition\n• No retraining needed'),
        ('Personal Knowledge Life\n(lifelong knowledge companion)', PAL[4],
         '• Migrates across devices < 2s\n• Long-term MeMo memory\n• Aligned to one user'),
    ]
    for ax, (title, c, body) in zip(axes.flat, forms):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
        ax.set_title(title, fontsize=11, fontweight='bold', color=c)
        box = FancyBboxPatch((0.5, 0.5), 9, 9, boxstyle="round,pad=0.1",
                             fc=c, ec='black', lw=2, alpha=0.15)
        ax.add_patch(box)
        ax.text(5, 5, body, ha='center', va='center', fontsize=11,
                color='black', fontweight='normal')
        # add tc color title bar
        bar = Rectangle((0.5, 8.5), 9, 1.0, fc=c, ec='black', lw=1.5, alpha=0.85)
        ax.add_patch(bar)
        ax.text(5, 9.0, title, ha='center', va='center', color='white',
                fontsize=11, fontweight='bold')

    save(fig, 'fig12_four_product_forms_en')

# ---------------------------------------------------------------
# Fig 13: AGI Timeline
# ---------------------------------------------------------------
def fig13():
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(1950, 2030)
    ax.set_ylim(-1, 4)
    ax.set_title('Figure 13. AGI Path Evolution Timeline',
                 fontsize=13, fontweight='bold', pad=15)
    ax.axhline(0, color='black', lw=2)

    milestones = [
        (1956, 'GOFAI',                 1.2, '#440154'),
        (1965, 'RSI (Good)',            2.4, '#7e03a8'),
        (1973, 'Cognitive Arch\n(SOAR/ACT-R)', 1.2, '#3b528b'),
        (1986, 'Connectionism\n(PDP)',  2.4, '#21918c'),
        (1991, 'Embodied AI',           1.2, '#5ec962'),
        (2018, 'World Models\n(Sch)',   2.4, '#fde725'),
        (2026, 'Architecture\nSchool',  1.2, '#cc4778'),
    ]
    for year, name, y, c in milestones:
        # alternating top/bottom stem
        ax.plot([year, year], [0, y], color=c, lw=2)
        ax.scatter([year], [0], color=c, s=80, zorder=5, edgecolor='black')
        ax.scatter([year], [y], color=c, s=120, zorder=6, edgecolor='black')
        va = 'bottom' if y > 0 else 'top'
        ax.text(year, y + (0.15 if y > 0 else -0.15), name,
                ha='center', va=va, fontsize=9, fontweight='bold', color=c)

    # highlight Architecture School
    ax.axvspan(2025, 2027, color='#cc4778', alpha=0.1)
    ax.text(2026, -0.7, 'Architecture School\n(white-box, architecture-first)',
            ha='center', fontsize=9, color='#cc4778', fontweight='bold', style='italic')

    ax.set_xlabel('Year')
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    save(fig, 'fig13_agi_timeline_en')

# ---------------------------------------------------------------
# Fig 14: Radar chart - Architecture School vs 7 AGI Paths
# ---------------------------------------------------------------
def fig14():
    fig, ax = plt.subplots(figsize=(10, 9), subplot_kw=dict(projection='polar'))
    fig.suptitle('Figure 14. Architecture School vs 7 AGI Paths — Comparison Radar (8 dimensions)',
                 fontsize=12, fontweight='bold')

    dims = ['Theoretical\nbasis', 'Feasibility', 'Autonomy', 'Interpretability',
            'Evolution', 'Safety', 'Alignment', 'Token\neconomics']
    N = len(dims)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # Scores 0-5 (subjective comparison from paper)
    paths = {
        'Architecture School':      [5, 4, 4, 5, 5, 5, 5, 4],
        'GOFAI':                    [4, 3, 1, 5, 1, 3, 4, 5],
        'Connectionism (LLM)':      [4, 5, 3, 1, 2, 2, 2, 1],
        'Cognitive Arch (SOAR/ACT-R)':[4, 3, 2, 4, 2, 3, 3, 4],
        'Embodied AI':              [3, 3, 3, 3, 2, 3, 3, 3],
        'World Models (Sch)':       [4, 3, 2, 2, 2, 2, 2, 2],
        'RSI (Good)':               [3, 1, 4, 1, 5, 1, 1, 3],
        'Hybrid (LLM-OS etc)':      [3, 4, 3, 2, 3, 3, 3, 3],
    }
    colors = plt.cm.tab10(np.linspace(0, 1, len(paths)))

    for (name, scores), c in zip(paths.items(), colors):
        vals = scores + scores[:1]
        lw = 2.5 if name == 'Architecture School' else 1.0
        alpha = 0.25 if name == 'Architecture School' else 0.0
        ax.plot(angles, vals, color=c, lw=lw, label=name)
        if alpha > 0:
            ax.fill(angles, vals, color=c, alpha=alpha)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=9)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_ylim(0, 5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.05), fontsize=8, frameon=True)
    save(fig, 'fig14_agi_radar_en')

# ---------------------------------------------------------------
# Fig 15: AGI Path Matrix Heatmap
# ---------------------------------------------------------------
def fig15():
    fig, ax = plt.subplots(figsize=(11, 7))

    paths = ['Architecture\nSchool', 'GOFAI', 'Connectionism\n(LLM)', 'Cognitive\nArch',
             'Embodied', 'World\nModels', 'RSI', 'Hybrid\nLLM-OS']
    dims = ['Theoretical\nbasis', 'Feasibility', 'Autonomy', 'Interpretability',
            'Evolution', 'Safety', 'Alignment', 'Token\neconomics']
    data = np.array([
        [5, 4, 4, 5, 5, 5, 5, 4],   # Architecture School
        [4, 3, 1, 5, 1, 3, 4, 5],   # GOFAI
        [4, 5, 3, 1, 2, 2, 2, 1],   # Connectionism
        [4, 3, 2, 4, 2, 3, 3, 4],   # Cognitive Arch
        [3, 3, 3, 3, 2, 3, 3, 3],   # Embodied
        [4, 3, 2, 2, 2, 2, 2, 2],   # World Models
        [3, 1, 4, 1, 5, 1, 1, 3],   # RSI
        [3, 4, 3, 2, 3, 3, 3, 3],   # Hybrid
    ])
    im = ax.imshow(data, cmap='viridis', aspect='auto', vmin=0, vmax=5)
    ax.set_xticks(range(len(dims)))
    ax.set_xticklabels(dims, fontsize=9)
    ax.set_yticks(range(len(paths)))
    ax.set_yticklabels(paths, fontsize=9)
    # Highlight Architecture School row
    ax.add_patch(Rectangle((-0.5, -0.5), len(dims), 1, fill=False, edgecolor='red', lw=3))

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            color = 'white' if v < 3 else 'black'
            ax.text(j, i, str(v), ha='center', va='center', color=color, fontsize=10, fontweight='bold')

    ax.set_title('Figure 15. AGI Path Positioning Matrix Heatmap (0=low, 5=high)',
                 fontsize=12, fontweight='bold', pad=15)
    plt.colorbar(im, ax=ax, label='Score (0-5)')
    save(fig, 'fig15_agi_matrix_heatmap_en')

# ---------------------------------------------------------------
# Fig 16: Ten Disruptive Innovations
# ---------------------------------------------------------------
def fig16():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
    ax.set_title('Figure 16. Ten Disruptive Innovations of the Architecture School',
                 fontsize=13, fontweight='bold', pad=15)

    innovations = [
        ('1. LLM subjectivity\ndissolution', PAL[0], 'LLM is replaceable glue, not the brain'),
        ('2. 0-Token algorithm\nhegemony',     PAL[1], 'Deterministic algos outside LLM context'),
        ('3. White-box\nmatching',             PAL[2], 'Auditable component composition'),
        ('4. Granularity +\nhash addressing',   PAL[3], 'Fine-grained memory indexing'),
        ('5. Decompile-assemble\nloop',         PAL[4], 'Bidirectional code↔design transform'),
        ('6. Pearl causal\nladder',             '#9c1793', 'Observation→Intervention→Counterfactual'),
        ('7. Design physics\nencoding',         '#0d0887', 'Constraints encoded as physics'),
        ('8. MeMo memory-\nas-model',           '#cc4778', 'Memory participates in inference'),
        ('9. Alignment\nforward shift',         '#7e03a8', 'Safety built-in, not bolted-on'),
        ('10. Living runtime\n+ protocols',     '#3b528b', 'Cross-device mind migration'),
    ]
    # 5 rows × 2 cols
    for i, (name, c, desc) in enumerate(innovations):
        col = i % 2
        row = i // 2
        x = 0.5 + col * 5.0
        y = 8.5 - row * 1.7
        box = FancyBboxPatch((x, y-0.7), 4.5, 1.5, boxstyle="round,pad=0.05",
                             fc=c, ec='black', lw=1.2, alpha=0.85)
        ax.add_patch(box)
        ax.text(x+0.3, y+0.25, name, ha='left', va='center', color='white',
                fontsize=10, fontweight='bold')
        ax.text(x+0.3, y-0.30, desc, ha='left', va='center', color='white',
                fontsize=8, style='italic')
    save(fig, 'fig16_ten_innovations_en')

# ---------------------------------------------------------------
# Fig 17: Risk Matrix Table
# ---------------------------------------------------------------
def fig17():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    ax.set_title('Figure 17. Risk Matrix: 9 Risks × (Likelihood, Impact, Severity)',
                 fontsize=12, fontweight='bold', pad=20)

    risks = [
        ('1. Implementation complexity',   4, 4, 'High engineering cost; many novel components'),
        ('2. Verifiability',               3, 5, 'Hard to formally verify emergent behavior'),
        ('3. Compute requirement',         3, 3, 'Causal sim + world model adds overhead'),
        ('4. Engineering landing',         4, 4, 'Few reference deployments; tooling immature'),
        ('5. Alignment bypass',            2, 5, 'AlignmentGuard must resist adversarial inputs'),
        ('6. Ecosystem dependency',        3, 3, 'Relies on protocol adoption & community'),
        ('7. MeMo training cost',          3, 4, 'Memory-as-model requires new training pipeline'),
        ('8. Ethical risk',                2, 5, 'Autonomous self-modification raises ethics issues'),
        ('9. Consciousness claim',        2, 4, 'Public perception: "is it conscious?"'),
    ]
    n = len(risks)
    cols = ['Risk', 'Likelihood\n(1-5)', 'Impact\n(1-5)', 'Severity\n(L×I)', 'Mitigation note']
    col_widths = [0.30, 0.12, 0.10, 0.10, 0.38]
    x_starts = np.cumsum([0] + col_widths[:-1])

    # Header
    for i, (c, w, x) in enumerate(zip(cols, col_widths, x_starts)):
        ax.text(x + w/2, 1.0, c, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white',
                bbox=dict(boxstyle='square,pad=0.5', fc='#3b528b', ec='black'))

    y = 0.86
    for risk_name, like, impact, sev_note in risks:
        sev = like * impact
        # row bg by severity
        cmap_val = (sev - 1) / 24  # 1..25 → 0..1
        bg = plt.cm.plasma(cmap_val)
        for i, (w, x) in enumerate(zip(col_widths, x_starts)):
            ax.add_patch(Rectangle((x, y-0.06), w, 0.07, fc=bg, ec='gray', lw=0.5, alpha=0.5))
        ax.text(x_starts[0] + col_widths[0]/2, y-0.025, risk_name, ha='center', va='center', fontsize=8.5)
        ax.text(x_starts[1] + col_widths[1]/2, y-0.025, str(like), ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(x_starts[2] + col_widths[2]/2, y-0.025, str(impact), ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(x_starts[3] + col_widths[3]/2, y-0.025, str(sev), ha='center', va='center', fontsize=9, fontweight='bold', color='darkred')
        ax.text(x_starts[4] + col_widths[4]/2, y-0.025, sev_note, ha='center', va='center', fontsize=8, style='italic')
        y -= 0.10

    # Color bar
    sm = plt.cm.ScalarMappable(cmap='plasma', norm=plt.Normalize(1, 25))
    sm.set_array([])
    cax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(sm, cax=cax, label='Severity (L×I)')

    save(fig, 'fig17_risk_matrix_en')

# ---------------------------------------------------------------
# Fig 18: Divergence from Mainstream Routes
# ---------------------------------------------------------------
def fig18():
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.set_xlim(0, 14); ax.set_ylim(0, 9); ax.axis('off')
    ax.set_title('Figure 18. Architecture School vs Mainstream Routes — Divergence',
                 fontsize=12, fontweight='bold', pad=15)

    # Center Architecture School
    center_box = FancyBboxPatch((5.0, 4.0), 4.0, 1.2, boxstyle="round,pad=0.08",
                                fc='#21918c', ec='black', lw=2, alpha=0.9)
    ax.add_patch(center_box)
    ax.text(7, 4.6, 'ARCHITECTURE\nSCHOOL', ha='center', va='center',
            color='white', fontsize=11, fontweight='bold')

    # Four mainstream routes
    routes = [
        ('LLM-OS',           'LLM as OS kernel',                 1.5, 7.5, '#cc4778'),
        ('Constitutional AI', 'RLHF + AI feedback constitution', 12.5, 7.5, '#7e03a8'),
        ('Superalignment',    'Scalable oversight (OpenAI)',     1.5, 1.5, '#440154'),
        ('JEPA',              'Joint-Embedding Predictive Arch', 12.5, 1.5, '#3b528b'),
    ]
    for name, desc, x, y, c in routes:
        box = FancyBboxPatch((x-1.7, y-0.5), 3.4, 1.0, boxstyle="round,pad=0.05",
                             fc=c, ec='black', lw=1.5, alpha=0.85)
        ax.add_patch(box)
        ax.text(x, y+0.2, name, ha='center', va='center', color='white',
                fontsize=10, fontweight='bold')
        ax.text(x, y-0.2, desc, ha='center', va='center', color='white',
                fontsize=8, style='italic')
        # Divergence arrow (dashed, away from center)
        ax.annotate('', xy=(x, y), xytext=(7, 4.6),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='red',
                                    ls='--', alpha=0.6))
        # divergence label
        mid_x = (x + 7) / 2
        mid_y = (y + 4.6) / 2
        ax.text(mid_x + 0.2, mid_y, 'DIVERGES', fontsize=8, color='red',
                rotation=np.degrees(np.arctan2(y - 4.6, x - 7)),
                ha='center', va='center', style='italic')

    # Key divergence points
    divergences = [
        'vs LLM-OS:           intelligence ≠ weights; LLM is glue',
        'vs Constitutional:   alignment built-in (forward), not trained',
        'vs Superalignment:   human-level verifier NOT required',
        'vs JEPA:             explicit causal model, not latent-only',
    ]
    for i, d in enumerate(divergences):
        ax.text(7, 8.6 - i*0.3, d, ha='center', fontsize=9, color='darkred',
                fontweight='bold')

    ax.text(7, 0.3, 'Architecture School diverges on ALL four core design choices',
            ha='center', fontsize=10, style='italic', color='dimgray')

    save(fig, 'fig18_divergence_mainstream_en')

# ---------------------------------------------------------------
# Run all
# ---------------------------------------------------------------
if __name__ == '__main__':
    print(f'Output dir: {OUT_DIR}')
    print('Generating figures...')
    fig01(); print('fig01 done')
    fig02(); print('fig02 done')
    fig03(); print('fig03 done')
    fig04(); print('fig04 done')
    fig05(); print('fig05 done')
    fig06(); print('fig06 done')
    fig07(); print('fig07 done')
    fig08(); print('fig08 done')
    fig09(); print('fig09 done')
    fig10(); print('fig10 done')
    fig11(); print('fig11 done')
    fig12(); print('fig12 done')
    fig13(); print('fig13 done')
    fig14(); print('fig14 done')
    fig15(); print('fig15 done')
    fig16(); print('fig16 done')
    fig17(); print('fig17 done')
    fig18(); print('fig18 done')
    print('All figures generated.')

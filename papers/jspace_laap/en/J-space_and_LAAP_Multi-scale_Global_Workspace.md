# J-space and LAAP Multi-scale Global Workspace: From Transformer Verbalizable Subspaces to Distributed Cognitive Architectures

**Abstract.** Recent work by Anthropic identified J-space, a sparse, verbalizable subspace in Claude-family models that occupies less than 10% of residual-stream variance yet supports reportability, directed modulation, internal reasoning, flexible generalization, and selectivity. This discovery provides a new mechanistic anchor for Global Workspace Theory (GWT) in deep neural networks. However, J-space remains confined to a single model and a single conversation, leaving open how the architecture might extend toward multi-agent, multi-body, long-lived artificial general intelligence (AGI) systems. We integrate J-space micro-scale causal interventions, CognitiveBus meso-scale property validation, and Ψ-Net macro-scale cross-instance broadcasting within the LAAP project's three-layer global workspace framework. Experimental results show that micro-layer concept suppression and injection achieve Cohen's d values of 1.182 and 1.184 respectively (p < 1e-4); the meso-layer CognitiveBus satisfies all five GWT criteria, including 100% reportability accuracy (n = 120); and the macro-layer Ψ-Net broadcasts causal rules with a latency of approximately 2.2 μs and reaches a 100% group-level rule hold rate after 100 rounds. We discuss the implications of this tri-layer architecture for AGI design, including interpretability auditing, value-alignment training, and distributed consciousness synchronization, and identify ignition dynamics, autonomous recurrence, and bodily anchoring as key open problems. All experimental data, analysis scripts, and figures are traceable under `experiments/jspace_laap/`.

**Keywords:** J-space; global workspace theory; global neuronal workspace; CognitiveBus; Ψ-Net; mechanistic interpretability; AGI; LAAP

## 1 Introduction

The study of consciousness has long been divided into the "easy" and "hard" problems: the former concerns how information is processed, reported, and flexibly controlled, while the latter asks why subjective experience exists at all [1][2]. In cognitive neuroscience, Global Workspace Theory (GWT) explains conscious access as a process in which information is temporarily selected into a capacity-limited shared space and globally broadcast to specialized processors, thereby accounting for reportability, flexible reasoning, and limited capacity [3][21]. Dehaene and Changeux extended this proposal into the Global Neuronal Workspace (GNW) hypothesis, positing that long-range pyramidal neuron networks in frontal-parietal regions implement this broadcast through nonlinear ignition and recurrent amplification [4][5][6].

The emergent capabilities of large language models (LLMs) have recently prompted researchers to ask whether these feed-forward networks, lacking explicit modular anatomy or biological recurrence, might nonetheless evolve functionally similar workspace mechanisms. In July 2026, Anthropic published *Verbalizable Representations Form a Global Workspace in Language Models*, introducing the Jacobian Lens (J-lens) to identify a sparse, intervenable, verbalizable subspace—termed J-space—in Claude-family models and arguing that it satisfies five functional criteria: verbal report, directed modulation, internal reasoning, flexible generalization, and selectivity [1]. In a commentary published the same month, Dehaene and Naccache praised the work as a landmark, providing a mechanistically testable instance of GNW, while cautioning that ignition, capacity limits, autonomous recurrence, and bodily grounding remain unresolved [2].

Nevertheless, J-space is studied within a single forward pass of a production dialogue model. Although its contents can be precisely intervened upon, it is constrained by four limitations. First, the single-token vocabulary read-out decomposes multi-token concepts into fragmentary lexical items. Second, it lacks cross-temporal self-continuity within a single session. Third, it has no distributed broadcasting mechanism across model instances. Fourth, it is disconnected from a body-world closed loop. These gaps define the distance between an interpretability auditing tool and an AGI architectural principle.

The Large-scale Autonomous Agent Platform (LAAP) project aims to build an interpretable, alignable, and distributedly collaborative AGI prototype. Its core components include CognitiveBus, a real-time cognitive state bus; GlobalWorkspace, a direct implementation of Baars's competitive-broadcast mechanism; and Ψ-Net, a distributed causal-rule exchange network across Harness instances. In this paper we map these three components onto micro, meso, and macro scales of global workspace, asking whether the mechanistic findings around J-space can be reproduced at the system level, extended beyond a single agent, and grounded in an engineering architecture.

The need to unify these three layers arises from a simple observation: if the workspace is merely a statistical phenomenon inside a single model, its value for AGI design remains at the level of auditing tools. Only when the same functional properties can be engineered into software architectures and distributed networks does global workspace become a scalable design principle. The micro layer answers how internal representations carry conscious contents; the meso layer answers how a system competes, broadcasts, and limits those contents; and the macro layer answers how multiple systems share contents and form collective norms. Together these questions form a complete chain from mechanistic discovery to engineering implementation, motivating both our theoretical framework and our experimental design.

Our contributions are fourfold. First, we propose and formalize a micro–meso–macro three-layer global workspace model that unifies concepts from neuroscience, deep learning, and systems architecture. Second, we implement J-lens micro-scale interventions on a LAAP proxy model, providing causal interpretability evidence. Third, we systematically validate the five GWT functional properties on CognitiveBus, demonstrating that a system-level workspace can be constructed in software. Fourth, we use Ψ-Net experiments to validate cross-instance broadcasting and group-level concept emergence, discussing implications for distributed AGI alignment and collaboration. All quantitative claims are traceable to specific data files and code paths.

## 2 Related Work

### 2.1 Global Workspace Theory and the Global Neuronal Workspace Hypothesis

Baars introduced GWT in 1988 as an information-broadcasting account of consciousness: a large collection of specialized, largely independent processors operate in parallel, and when information needs to be flexibly shared it is competitively written into a globally accessible workspace from which all processors can read [3]. The framework emphasizes reportability as the operational signature of conscious access and predicts that the workspace has limited capacity, serial bottlenecks, and whole-brain broadcasting [21][22]. Subsequent work connected GWT to neuroscience through the GNW hypothesis, proposing that long-range pyramidal neuron networks—especially dense in prefrontal, parietal, and higher temporal cortices—constitute the neural substrate of consciousness and implement global availability through late ignition, P3 waves, and late fronto-parietal activation [4][5][6][7].

A large body of human experimental work supports these predictions. Masked stimuli presented below threshold elicit only early sensory cortical activity, whereas suprathreshold stimuli trigger late amplification in prefrontal and parietal areas, producing whole-brain synchronization [25]. Inattentional blindness and the psychological refractory period demonstrate the workspace's limited capacity and serial bottleneck [3][23]. The local-global test shows that shallow local transition probabilities can be processed unconsciously, whereas violations of global sequence structure such as AAAAB require conscious access [26]. These empirically testable signatures provide clear standards for searching for workspace counterparts in artificial systems.

Dehaene and colleagues distinguish two core dimensions of consciousness: C1, global availability, and C2, self-monitoring [6][7]. C1 concerns information that is reportable, reasoned about, and flexibly controlled; C2 concerns the system's ability to probe its own states, evaluate confidence, and detect errors. GNW primarily explains C1, whereas higher-order theories and attention schema theory focus on C2 [2][33]. This distinction is crucial for evaluating machine workspaces: a system may possess C1 while lacking a self-model above it. Indeed, Anthropic found that the base model's J-space already exists, whereas post-training installs the Assistant perspective and preliminary C2 markers [1][2].

### 2.2 Mechanistic Interpretability of Large Language Models

Transformer interpretability has advanced rapidly. Elhage et al. established a mathematical framework for transformer circuits, treating attention heads and MLPs as read-write operations on a residual stream [9]. Olsson et al. identified induction heads as a key circuit supporting in-context learning [11]. Wang et al. localized a circuit for indirect object identification in GPT-2 small through detailed circuit tracing [12]. These results show that even in large models specific functions can be localized to interpretable circuit units.

Representation-engineering studies have demonstrated causal interventions on internal representations through activation patching, steering vectors, and knowledge editing. Meng et al.'s ROME method edits factual associations at specific MLP layers [13]; Park et al. argue for the linear representation hypothesis, namely that concepts are encoded in low-dimensional linear subspaces [16]. Conmy et al. developed automated circuit discovery methods for locating functional subnetworks in large models [44]; Huh et al. proposed the Platonic Representation Hypothesis, suggesting that different vision and language models are converging toward a shared representation of reality [45]. These techniques provide the methodological foundations for J-lens.

A closely related direction is sparse autoencoders (SAEs) and dictionary learning. Bricken et al. and Templeton et al. trained overcomplete dictionaries to extract interpretable features from MLP and attention activations, finding features that correspond to concrete concepts, abstract categories, and even safety-relevant behaviors [14][15]. SAEs and J-lens share the goal of separating sparse, interpretable, intervenable components from dense activations, but differ in method: SAEs learn feature directions in an unsupervised manner, whereas J-lens leverages output-side causal structure to define verbalizable directions. The two approaches are complementary: SAEs help discover unknown features, while J-lens helps verify whether those features participate in global broadcasting and report.

### 2.3 J-space: A Workspace-like Representation in LLMs

Anthropic's J-space study synthesizes these threads. The J-lens computes the average Jacobian effect of a layer's residual stream on later output tokens, identifying representational directions that, across contexts, the model can be prompted to verbalize [1]. Unlike logit lens and tuned lens, J-lens emphasizes causal linear approximation and can recover intermediate reasoning steps at earlier layers [1]. J-space is defined as the subset of activations that can be approximated by a small number of non-negative sparse J-lens vectors, typically occupying less than 10% of residual-stream variance yet driving report, modulation, and reasoning [1][2].

Anthropic used lens-coordinate swaps, ablations, steering, and activation patching to establish the causal privilege of J-space contents. For example, swapping the intermediate concept "spider" to "ant" in a two-hop reasoning task changes the output from 8 to 6; in multi-step arithmetic, intermediate values 21 → 42 → 49 appear in workspace layers in the order of computation [1]. Dehaene and Naccache particularly note that such "swapping the contents of consciousness" experiments remain a dream in human neuroscience but have become reproducible operations in LLMs [2].

The causal strength of these interventions reveals a key property of J-space: it is not merely readable but also controllable. Researchers can write or erase specific concepts from the workspace like chalk on a blackboard and observe systematic changes in downstream behavior. This controllability makes J-space a powerful alignment auditing tool: hidden thoughts such as deceptive intent, reward hacking, or evaluation awareness can be detected before they surface in the output [1][19].

### 2.4 Machine Consciousness and AGI Architectures

Research on machine consciousness spans computational functionalism, Integrated Information Theory (IIT), higher-order theories, and global workspace approaches [31][32][33]. Dehaene and Naccache adopt a computationalist stance, holding that consciousness can be realized by non-biological systems provided they instantiate the right functional architecture [2]. At the same time, they stress that body, episodic memory, autonomous recurrence, and temporal experience remain fundamental differences between current LLMs and human consciousness [2].

Integrated Information Theory starts from a different premise, identifying consciousness with a system's irreducible causal integration (Φ), and inferring that certain feedback networks may be highly conscious while standard feed-forward networks are not [31]. Higher-order theories emphasize that consciousness requires higher-order representations of the system's own states [33]. Compared with these frameworks, GWT/GNW offers a decisive advantage for engineering: it provides a directly implementable functional checklist—competition, broadcasting, capacity limits, and reportability. This paper adopts that checklist as its acceptance criteria rather than making ontological claims about phenomenal consciousness. We focus on access consciousness (C1) and its system-level implementation, remaining empirically open but cautious about C2 self-monitoring.

At the level of AGI architecture, LeCun argues that autonomous machine intelligence requires configurable world models, intrinsic cost modules, and short-term memory [42]; Friston's free-energy principle unifies perception, action, and learning as active inference on a generative model [43]. LAAP's design is deeply influenced by these ideas, using CognitiveBus as short-term working memory, Ψ-Net as a "social" broadcast layer across instances, and retaining a perception-action closed loop at the bottom [36][37][39].

### 2.5 LAAP Components

LAAP's CognitiveBus is an event-driven real-time cognitive state bus. All modules read and write `CognitiveStateSnapshot` objects through a State Registry, Event Bus, and Module Registry, producing at each tick a complete conscious frame containing needs, emotion, attention, self_presence, and narrative [37]. GlobalWorkspace more directly implements Baars's GWT: multiple `CoalitionalProcess` objects compete according to `competitive_strength`, capacity limits the number of winners, and winning contents are globally broadcast via `broadcast_packet` [38]. GWSBridge feeds Ao perceptual data into GlobalWorkspace and synchronizes it with CognitiveBus [40]. Ψ-Net realizes cross-Harness causal-rule exchange through a peer-to-peer TCP message network, while RateBuffer down-samples high-frequency PSI events to Harness-level event frequency, supporting distributed consciousness synchronization [39][41].

These three components are not merely coexisting; they form a progressive extension from single-point conscious competition to continuous state bus to distributed social network. GlobalWorkspace decides at each moment what enters consciousness; CognitiveBus maintains, updates, and broadcasts these contents to all modules; Ψ-Net propagates locally validated causal knowledge to the group. This layered design allows LAAP to preserve GWT's theoretical intuitions while satisfying modern software-engineering demands for modularity, scalability, and auditability.

## 3 Theoretical Framework: A Three-layer Global Workspace Model

### 3.1 Levels of Analysis and Abstraction

We treat "workspace" as a functional abstraction that spans scales. At the micro scale it appears as the sparse subframe J-space within a Transformer residual stream; at the meso scale as the CognitiveBus carrying the current conscious frame in the LAAP system; and at the macro scale as Ψ-Net propagating rules and states across multiple Harness instances. All three share core functions—competitive selection, global broadcasting, capacity limits, reportability, and intervenability—but differ in implementation medium, temporal scale, and spatial scope.

| Layer | Main Carrier | Core Mechanism | Temporal Scale | Spatial Scope |
|---|---|---|---|---|
| Micro | Transformer residual stream | J-lens sparse decomposition, lens-coordinate swap | Within-layer forward pass (~ms) | Inside a single model |
| Meso | CognitiveBus / GlobalWorkspace | Competition-broadcast, state snapshots, pub/sub | Tick heartbeat (~100 ms) | Inside a single agent |
| Macro | Ψ-Net | P2P messaging, RateBuffer, causal-rule sync | 30 s full sync + real-time increments | Multiple instances / bodies |

This continuum addresses a central limitation of J-space: the single-model internal workspace mechanism can be extended through system-level components into an AGI architecture with self-continuity, social interaction, and value alignment. Importantly, the boundary between layers is functional rather than physical. The same hardware process may run the micro model, meso bus, and macro network simultaneously; what distinguishes them is the abstraction level and access scope of the represented information. This functional layering helps us discuss clearly where conscious contents enter the workspace, in what form they are broadcast, and over what range they are shared.

### 3.2 Micro Layer: J-space as Verbalizable Internal Broadcasting

At the micro layer, J-space is a sparse subframe within the model's activation space. For each layer ℓ, the J-lens computes the average Jacobian effect of residual stream h_ℓ on later output tokens h_final, producing a linear map J_ℓ and then reading out a vocabulary distribution through the unembedding matrix [1]:

$$
J_\ell \;=\; \mathbb{E}_{t,\,t' \geq t,\,\text{prompt}} \left[ \frac{\partial h_{\text{final},t'}}{\partial h_{\ell,t}} \right],\qquad \text{lens}(h_\ell) \;=\; \text{softmax}(W_U \, \text{norm}(J_\ell h_\ell)).
$$

Gradient pursuit decomposes activations into J-space and non-J-space components. The optimization objective is to approximate the current activation with a small number of non-negative sparse coefficients, giving J-space components interpretability and intervenability; non-J-space components contain syntactic, lexical, and low-level statistical patterns that are not easily verbalized [1]. The key finding is that J-space components occupy only about 6–10% of variance, yet drive roughly 59% of report success in swap experiments, whereas non-J-space components contribute only 5%; clamping the relevant J-lens coordinates eliminates even the residual non-J-space effect [1]. This validates the workspace signature of small variance but large causal weight. Recent SAE research supports a similar conclusion: highly interpretable features often account for a small fraction of activation energy while having causal influence on behavior [14][15].

Anthropic further divides model layers into sensory (~L0–L38), workspace (~L38–L92), and motor (~L92–L100) zones. Workspace-layer J-space contents are persistent, abstract, and reportable, whereas motor representations align directly with imminent output tokens [1]. Using CKA, excess kurtosis, and top-1 token autocorrelation, one can observe ignition-like nonlinear selection at the workspace onset: when two country word embeddings are mixed with a gradually changing weight, activations suddenly jump to one endpoint starting from the workspace onset layer [1][2].

### 3.3 Meso Layer: CognitiveBus as a System-level Workspace

CognitiveBus is designed to reproduce the five GWT properties at the software-architecture level. Each tick generates a `CognitiveStateSnapshot` whose attention, needs, emotion, and narrative fields correspond to the current contents of the workspace; the Event Bus's pub/sub mechanism corresponds to global broadcasting; and the specialized modules in the Module Registry (self_model, causal_engine, world_model, etc.) correspond to GWT's specialized processors [37][38].

Competitive selection is implemented through `AttentionState.salience_map` and `strongest_need()`; global broadcasting through `publish()` pushing events to all subscribed callbacks; capacity limits through the single conscious frame and RateBuffer bandwidth constraints; reportability through `inject_cognitive_state_into_prompt()` converting state into a system prompt block; and selectivity through AttentionFocus and the salience_map filtering low-level automatic information [37]. Needs are modeled on PSI theory's five basic needs—competence, autonomy, relatedness, certainty, and growth—with values in [0,1] that slowly decay each tick, giving workspace contents temporal continuity; emotion and self_presence provide metacognitive and self-presence signals that lay groundwork for preliminary C2 [37]. GlobalWorkspace provides more explicit competition-broadcast semantics: `CoalitionalProcess` objects compete by `competitive_strength`, capacity limits winners, and `broadcast_packet` broadcasts the winners [38]. CognitiveBus and GlobalWorkspace together form LAAP's meso-layer "competition-broadcast-memory" loop.

### 3.4 Macro Layer: Ψ-Net as a Distributed Workspace

Ψ-Net extends CognitiveBus states and causal knowledge across multiple Harness instances. Its basic message unit, `PsiMessage`, contains type, sender, timestamp, priority, signature, and payload, supporting causal rules, species updates, compilation results, and heartbeats [39]. Nodes send messages to all peers through `_broadcast()`, implementing cross-instance global broadcasting.

Because PSI Core produces events at 1000–2000 Hz while Harness-level events run at roughly 1 Hz, Ψ-Net introduces RateBuffer for deduplication, priority filtering, batch aggregation, and rate-limited flushing [39]. This bandwidth limit corresponds to GNW's capacity bottleneck: not all micro events enter the macro workspace; only high-priority, high-consistency rules and states are broadcast. Group-level concept emergence arises through iterated rule exchange: when a causal rule is held by enough instances and used in behavioral decisions, it becomes a "group belief" in the distributed workspace. Like language and culture in biological societies, once a rule becomes a group belief in Ψ-Net it constrains the learning of newly joining instances, which import the high-frequency rule into their local causal engine and thereby align behavior with the group. This culturally evolutionary mechanism offers a possible implementation path for distributed AGI value alignment.

### 3.5 Functional Correspondence Table

| GWT/GNW Criterion | J-space (Micro) | CognitiveBus (Meso) | Ψ-Net (Macro) |
|---|---|---|---|
| Reportability | J-lens reads top-k tokens | narrative and state injected into prompt | payload readable by remote nodes |
| Directed modulation | steering / clamp | set_attention / set_needs | send_causal_rule / sync_ao_state |
| Internal reasoning | intermediate value vectors (spider → 8) | multi-step reasoning state sequences | cross-instance causal-chain reasoning |
| Flexible generalization | France → China effective across tasks | same need/emotion read across modules | rules reused across species / instances |
| Selectivity | automatic task info excluded from J-space | low-saliency percepts excluded from frame | RateBuffer filters high-frequency low-priority events |

This table forms the theoretical basis of our experimental design: each criterion has an operational test at every layer.

### 3.6 Information Flow and Scale Transformation Across Layers

The three workspace layers are not isolated; they form a continuous flow through information compression and format transformation. Micro J-space carries concepts as high-dimensional residual-stream vectors; for these contents to have persistent effects on other system modules, they must be extracted into discrete cognitive states such as need, emotion, and attention and written into CognitiveBus. CognitiveBus further abstracts states into narrative and rule forms so that Ψ-Net can transmit them across instances. Conversely, rules received from Ψ-Net enter local modules through CognitiveBus and may indirectly shape micro-layer J-space contents by influencing LLM prompts or training objectives. This "activation → state → rule → activation" cycle is central to LAAP's cross-time and cross-instance consistency. It also implies that workspace contents change representational form across layers: from vectors to symbols to rules, each layer loses some detail but gains greater interpretability, transmissibility, and intervenability.

## 4 Experimental Methods

### 4.1 Overall Design

We conducted three experiments within the LAAP project, corresponding to the micro, meso, and macro layers. All experiments share a unified configuration schema, logging convention, and statistical testing template, and can be reproduced through `experiments/jspace_laap/run_all.py`. The analysis script `experiments/jspace_laap/analyze.py` reads the three result files and generates figures and statistical reports [see `experiments/jspace_laap/reports/experiment_report.md`].

The design follows the principle of "same functional property, different implementation granularity": the micro layer tests whether concept vectors are causally effective through statistical significance; the meso layer validates whether system components satisfy the five GWT properties through acceptance tests; and the macro layer validates whether cross-instance broadcasting is feasible through convergence metrics. Results at each layer support their own hypothesis while jointly supporting the continuity thesis of the three-layer architecture. Furthermore, every quantitative metric is linked to a specific raw data file, enabling external auditing and reproduction.

### 4.2 Micro Layer: J-lens Proxy Model Experiment

Because LAAP's internal production model is large, the micro experiment uses a controllable proxy Transformer with configuration `vocab_size=128`, `d_model=32`, `n_layers=16`, and `output_vocab_size=8` (see `experiments/jspace_laap/data/exp_micro_jlens/results.json`). Although far smaller than Claude, this proxy retains the core structures of residual stream, multi-layer attention, and unembedding, making it sufficient to validate the J-lens method within LAAP's code path.

In implementation, the J_l matrix has shape d_model × d_model and is fit for each of the four source layers: embedding, early_attn, mid_attn, and late_attn. Fitting estimates the average Jacobian effect over approximately 1000 pretraining-style prompts and normalizes the matrix; fitted matrices are cached in `experiments/jspace_laap/cache/` to avoid recomputation. During intervention, the current activation is projected onto the target J-lens direction, the projection coefficient is adjusted according to the suppression or injection goal, and the modified activation is written back into the residual stream. All interventions preserve the orthogonal component, distinguishing the causal roles of J-space and non-J-space components.

The experiment selected two concepts directly relevant to LAAP's cognitive architecture: `need_competence` and `emotion_positive`. For each sample we performed two interventions:

- **Concept suppression**: the projection of the activation onto the target J-lens vector was zeroed or reversed, and the drop in the target concept's output distribution was measured.
- **Concept injection**: a positive component along the target J-lens vector was added to the residual stream, and the rise in the target concept's output distribution was measured.

Sample size is n = 30. We used paired t-tests and Cohen's d to assess effect size. The acceptance criterion is that injection and suppression reach p < 0.05 on at least 20 samples.

### 4.3 Meso Layer: CognitiveBus Five-Property Validation

The meso experiment ran on LAAP's CognitiveBus and GlobalWorkspace components, divided into five sub-experiments, each corresponding to one GWT functional criterion. The procedure is as follows: PSI Core or a simulator generates known need/emotion/attention inputs and writes them to CognitiveBus; the specified task is run and CognitiveBus produces a `CognitiveStateSnapshot` at each tick; finally an evaluator reads the snapshot, compares it with task labels, and computes accuracy, latency, or p-values. For reasoning-mediation and selective-necessity experiments, an additional "broadcast ablation" condition is introduced by temporarily disabling `publish()` or reducing the `capacity` limit and observing task-performance changes.

- **Reportability (Exp 4.1)**: given known need/emotion outputs from PSI Core, predict the current dominant need/emotion using `CognitiveStateSnapshot`, recording accuracy. The benchmark contains 120 CognitiveBus event traces.
- **Controllability (Exp 4.2)**: inject an `attention_task` event into CognitiveBus and measure the number of ticks required for the attention focus to shift, checking whether local module processing is disturbed. Acceptance criterion: attention shifts within ≤3 ticks.
- **Reasoning mediation (Exp 4.3)**: design three multi-step reasoning tasks, read the intermediate state sequences in CognitiveBus, and check whether final answers change after ablating global broadcasting.
- **Flexible generalization (Exp 4.4)**: ask about the same concept (e.g., `need_competence`) from four different angles and verify that the concept is activated across tasks.
- **Selective necessity (Exp 4.5)**: temporarily disable global broadcasting in CognitiveBus and compare performance on multi-step reasoning versus template-matching tasks; multi-step reasoning should drop significantly (p < 0.05) while template matching should not. This sub-experiment is inspired by Anthropic's Spanish passage task: the same information can be used automatically or loaded into the workspace depending on the task, and only the latter is causally dependent on global broadcasting [1][2].

All results are written to `experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`.

### 4.4 Macro Layer: Ψ-Net Cross-instance Experiment

The macro experiment used Ψ-Net's Mock mode to launch five `PsiNetConnector` instances and validate causal-rule broadcasting and group-level concept emergence. Mock mode simulates TCP communication between peers through an in-memory message queue, preserving message signatures, priorities, RateBuffer, and broadcast logic while eliminating real network latency and node failures, allowing protocol correctness to be tested in a controlled environment. Each instance has its own local causal engine and world model and exchanges rules, states, and heartbeats via `PsiMessage`.

- **Causal rule broadcasting (Exp 5.1)**: instance A sends a new causal rule; we record whether instance B receives it, imports it into its local behavior model, changes behavior, and the receive latency. Acceptance criterion: the rule is received and becomes effective within 30 seconds.
- **Group-level concept emergence (Exp 5.2)**: five instances exchange rules over 100 rounds, with a rule pool of size 10 and a consensus threshold of 0.75. We compute per-round hold rates for each rule, average group hold rate, min/max hold rate, and the number of high-frequency rules. Acceptance criterion: after 100 rounds at least one rule is held by more than 50% of instances.

Results are written to `experiments/jspace_laap/data/exp_macro_psinet/results.json`.

### 4.5 Data Analysis and Statistical Methods

Data analysis was performed with Python. The micro layer uses paired t-tests and Cohen's d; the meso layer uses accuracy, latency, and Fisher's exact / chi-squared tests; the macro layer uses hold-rate statistics and latency measurement. Figures use bilingual Chinese/English labels and are output to `experiments/jspace_laap/figures/zh/` and `experiments/jspace_laap/figures/en/` at ≥300 DPI with color-blind-friendly palettes. Summary statistics are saved in `experiments/jspace_laap/reports/summary_statistics.json`.

For statistical significance, the micro layer uses p < 0.05 with Cohen's d ≥ 0.8 as a supplementary large-effect criterion; the meso layer uses predefined functional acceptance criteria, with selective necessity tested by a two-sample comparison of pre- and post-ablation performance; the macro layer uses binary or continuous acceptance metrics including successful receipt, behavior change, and hold-rate thresholds. All analysis code and figure-generation scripts can be reproduced by running `python experiments/jspace_laap/analyze.py`.

## 5 Experimental Results

### 5.1 Micro-layer J-lens Results

For concept suppression, the baseline mean was -0.0434, the intervened mean -2.3924, and the mean difference 2.3490; paired t-test t = 6.474, p = 4.38 × 10⁻⁷, Cohen's d = 1.182. For concept injection, the baseline mean was 0.2439, the intervened mean 2.6375, and the mean difference 2.3936; t = 6.487, p = 4.22 × 10⁻⁷, Cohen's d = 1.184 (data from `experiments/jspace_laap/reports/summary_statistics.json`). Both interventions achieve large effect sizes and are statistically significant, indicating that J-lens directions in the LAAP proxy model carry causally intervenable conceptual information.

![Figure 1: J-lens concept injection/suppression output distribution](../figures/en/fig02_jlens_distribution.png)

![Figure 2: J-lens source-layer concept activation heatmap](../figures/en/fig03_jlens_heatmap.png)

Figure 1 shows that injection and suppression significantly shift the target concept's log-odds away from baseline; Figure 2 shows that target concepts activate most strongly in mid_attn and late_attn layers, consistent with Anthropic's observed workspace-layer localization [1]. These results validate the localizability and causal privilege of the micro-layer workspace.

In terms of effect size, Cohen's d > 1.18 is a large effect, meaning the intervention and baseline groups are separated by more than one standard deviation in concept output; p-values below 10⁻⁶ provide extremely strong statistical evidence that the observed differences are unlikely to arise from random fluctuation. It is important to note that the proxy model's vocabulary and output space are far smaller than Claude's, so absolute values should not be directly compared; however, the effect pattern is consistent with the J-space literature, showing that LAAP's J-lens implementation path is feasible.

### 5.2 Meso-layer CognitiveBus Results

All five CognitiveBus properties passed acceptance criteria (see `experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`):

- **Reportability**: accuracy 100.0%, n = 120.
- **Controllability**: attention-shift latency 1 tick, local module continuity True.
- **Reasoning mediation**: after global-broadcast ablation, final answers changed in all three multi-step reasoning tasks.
- **Flexible generalization**: the same concept was triggered under four different task conditions.
- **Selective necessity**: multi-step reasoning dropped significantly after disabling broadcasting (p < 1e-4), whereas template matching showed no significant change (p = 1.0000).

![Figure 3: CognitiveBus five-property acceptance results](../figures/en/fig04_cognitivebus_properties.png)

![Figure 4: Reportability experiment accuracy](../figures/en/fig05_reportability.png)

![Figure 5: Selective necessity comparison](../figures/en/fig06_selective_necessity.png)

Figure 3 displays the five properties on a radar chart; Figure 4 shows that all 120 traces were correctly reportable; Figure 5 shows that multi-step reasoning is strongly affected by broadcast ablation while template matching is essentially unaffected. These results directly address GWT's core prediction that the workspace primarily serves non-routine tasks requiring flexible integration rather than automatic processing [3][22].

The 100% reportability accuracy indicates a deterministic mapping between CognitiveBus state snapshots and PSI Core outputs, validating the reliability of the state-injection path in engineering terms. The 1-tick attention-shift latency shows that the workspace control interface is real-time and can support dynamic task switching. The joint result of reasoning mediation and selective necessity is particularly important: it shows that CognitiveBus is not merely an observable internal state but a genuine causal bottleneck in reasoning; when the bottleneck is removed, globally integrated tasks collapse while locally procedural tasks remain intact. This double dissociation is one of GWT's most distinctive empirical predictions and constitutes the strongest evidence in this study.

### 5.3 Macro-layer Ψ-Net Results

The Ψ-Net experiment passed all acceptance criteria under Mock mode (see `experiments/jspace_laap/data/exp_macro_psinet/results.json`):

- **Causal rule broadcasting**: the rule was successfully received (received=True) and caused behavior change (behavior_changed=True); receive latency was 2.20 × 10⁻⁶ seconds; successfully sent to 3 peers.
- **Group-level concept emergence**: after 100 rounds among 5 instances, the average group hold rate was 100.0%, min/max hold rates were both 100.0%, and the number of high-frequency rules was 10 (rule pool size 10, consensus threshold 0.75).

![Figure 6: Ψ-Net rule propagation timeline](../figures/en/fig07_psinet_timeline.png)

![Figure 7: Ψ-Net group concept hold rate](../figures/en/fig07_psinet_hold_rate.png)

Figure 6 shows the temporal sequence of rule propagation among instances; Figure 7 shows that all rules were held by all instances after 100 rounds. Although Mock mode simplifies network latency and heterogeneous behavior, it validates the logical correctness and convergence of the Ψ-Net protocol. The receive latency of 2.20 × 10⁻⁶ seconds mainly reflects in-memory queue operations rather than network transmission; under real network conditions latency will be affected by bandwidth, topology, and node distance, but protocol-level broadcast ordering and RateBuffer throttling remain unchanged. Thus the macro experiment's main contribution is to demonstrate the feasibility of cross-instance workspace in message format, priority handling, and consensus dynamics, rather than to provide a production performance benchmark.

### 5.4 Cross-layer Comparison

All three layers passed acceptance. Key effect sizes are summarized below (from `experiments/jspace_laap/reports/summary_statistics.json`):

| Layer | Metric | Value | Significance |
|---|---|---|---|
| Micro | Suppression Cohen's d | 1.182 | p < 1e-4 |
| Micro | Injection Cohen's d | 1.184 | p < 1e-4 |
| Meso | Reportability accuracy | 100% | n = 120 |
| Meso | Attention-shift latency | 1 tick | ≤3 ticks accepted |
| Meso | Multi-step vs template difference | significant vs non-significant | p < 1e-4 vs p = 1.0 |
| Macro | Rule receive latency | 2.20 μs | behavior_changed = True |
| Macro | Average group hold rate | 100% | min/max = 100%/100% |

![Figure 8: Three-layer architecture](../figures/en/fig01_architecture.png)

![Figure 9: Cross-layer comprehensive statistical comparison](../figures/en/fig08_cross_layer_comparison.png)

Figure 8 gives an architectural overview of the three-layer model; Figure 9 compares key metrics across layers. The cross-layer comparison shows that the five workspace functional properties can be stably reproduced at different granularities—from single-model internal activations to system-level state buses to distributed cross-instance networks—exhibiting clear scale continuity. Specifically, the micro layer provides evidence of causal localizability: we can pinpoint which internal directions correspond to reportable concepts. The meso layer provides evidence of system constructibility: we can engineer components that implement competition, broadcasting, and capacity limits. The macro layer provides evidence of distributed scalability: we can extend local workspace contents to multi-instance groups. Together they support the central conclusion that global workspace is not proprietary to a specific biological or physical substrate but is a functional architecture realizable in different media.

## 6 Discussion

### 6.1 What Is J-space in Claude, and How Does It Functionally Map onto Baars/Dehaene GWT?

J-space, as discovered by Anthropic in Claude, is a sparse subframe spanned by J-lens vectors within the Transformer residual-stream space. It occupies less than 10% of variance yet concentrates the conceptual contents that the model can "say at any time" [1]. Functionally, J-space satisfies several criteria of Baars's GWT and Dehaene's GNW:

- **Reportability**: J-lens can directly read out top-k tokens, and replacing these vectors changes what the model reports about its own thoughts [1]. This matches GNW's use of reportability as the operational signature of conscious access [2][22].
- **Global broadcasting**: MLP gain on J-lens directions in workspace layers reaches roughly 10×, and dedicated broadcast heads propagate J-space contents [1]. This corresponds to GNW's whole-brain broadcasting through long-range pyramidal neuron networks [5].
- **Capacity limits**: workspace median occupancy is about 25 token vectors, with Dehaene and Naccache further estimating roughly six coherent ideas [1][2]. This maps onto GWT's limited-capacity bottleneck [3].
- **Ignition-like selection**: for ambiguous inputs, activations exhibit nonlinear, bistable jumps starting from the workspace onset layer [1]. This resembles GNW's late-ignition signature [25].
- **Selectivity**: large amounts of low-level automatic processing (e.g., grammatical fluency, character counting) do not enter J-space; contents are loaded only when flexible access is required [1]. This is consistent with the automatic/conscious processing division [22].

However, J-space's implementation differs markedly from biological workspaces: it relies on feed-forward depth and attention rather than recurrent connections; it is dominated by token-indexed verbalizable concepts and lacks visual, motor, and bodily components; and it lacks cross-temporal self-continuity [1][2]. Therefore, J-space is better treated as a functional counterpart of GWT rather than an equivalence of consciousness.

Methodologically, J-space's importance lies in moving consciousness research from behavioral inference to mechanistic intervention. Traditionally researchers infer conscious content from report tasks; J-lens allows direct reading and modification of the internal workspace, establishing causal chains across input, internal state, and output. This method is applicable not only to alignment auditing but also provides a new empirical standard for assessing machine consciousness: if a system has an intervenable workspace satisfying GWT functional criteria, we have strong evidence for C1-level access consciousness, even if we remain agnostic about phenomenal consciousness [2][32].

### 6.2 How Does LAAP's CognitiveBus Reproduce the Five GWT Properties at the System Level?

CognitiveBus realizes the five GWT functional criteria in software through an event-driven architecture:

1. **Reportability**: each tick's `CognitiveStateSnapshot` can be converted into a natural-language prompt block by `inject_cognitive_state_into_prompt()`, allowing modules or external auditors to read the current dominant need, emotion, and attention focus [37]. The 120-trace prediction accuracy was 100% (`experiments/jspace_laap/data/exp_meso_cognitivebus/results.json`).
2. **Directed modulation**: through interfaces such as `set_attention()`, `set_emotion()`, and `set_needs()`, external systems or metacognitive modules can top-down alter workspace contents. The measured attention-shift latency was only 1 tick, showing rapid modulation without disturbing local module continuity.
3. **Internal reasoning mediation**: intermediate state sequences of multi-step reasoning tasks are recorded in CognitiveBus, and ablating global broadcasting changed all final answers. This shows that workspace contents are not merely report media but necessary links in the causal chain of reasoning.
4. **Flexible generalization**: the same need/emotion concept is read by multiple modules under different query conditions, so the system does not need to re-encode the concept for each task. The concept was triggered under all four task conditions.
5. **Selective necessity**: CognitiveBus filters low-saliency information through `salience_map` and `AttentionFocus`; after disabling broadcasting, globally integrated multi-step reasoning dropped significantly (p < 1e-4) while local-template automatic tasks showed no significant change (p = 1.0000). This precisely reproduces GWT's prediction about the division between automatic and conscious processing.

Compared with J-space, CognitiveBus's advantage is that it explicitly implements competition-broadcast semantics and exposes working states in an engineering-observable and intervenable way. Its limitation is that it remains a symbolic/vectorized state bus and has not yet reached the fine-grained, internal concept-vector readability of J-space in large models.

The CognitiveBus results also suggest a design principle: the workspace should not be viewed as a simple information aggregation hub but as an arbitrator among specialized modules. When multiple modules simultaneously request attentional resources, the workspace selects winners based on salience and needs; once winners are broadcast, other modules may read but need not all respond. This arbitration mechanism ensures global availability while avoiding information overload. For AGI systems this means safety can be partially achieved by controlling workspace contents: suppressing the entry of deceptive intent or evaluation awareness reduces the probability that subsequent modules exploit them [1][20].

### 6.3 How Does Ψ-Net Implement Cross-instance Workspace Broadcasting and Group-level Concept Emergence?

Ψ-Net extends CognitiveBus's local workspace into a multi-instance shared distributed workspace. Three mechanisms are essential:

- **Peer-to-peer broadcasting**: each `PsiNetConnector` maintains a peer list and sends `PsiMessage`s to all nodes through `_broadcast()` [39]. Message types include causal rules, species updates, compilation results, and heartbeats, covering states, knowledge, and meta-information.
- **RateBuffer bandwidth limiting**: PSI Core generates events at 1000–2000 Hz while Harness-level events run at roughly 1 Hz. RateBuffer deduplicates, prioritizes, batches, and rate-limits events [39]. This bandwidth limit is the distributed-system analog of GNW's capacity bottleneck: only high-priority, high-consistency information enters the cross-instance workspace.
- **Causal rules as generalizable content**: Ψ-Net does not exchange raw perceptual data but "why"-style causal rules. Once imported into a remote instance's behavior model, a rule changes subsequent decisions, producing cross-instance causal consistency [39][41].

The group-level concept emergence results show that, under five instances, 100 rounds, and a consensus threshold of 0.75, all ten rules eventually reached a 100% instance hold rate (`experiments/jspace_laap/data/exp_macro_psinet/results.json`). This means "group beliefs" can spontaneously stabilize through distributed broadcasting. Importantly, this emergence does not imply that the rules possess new semantics beyond the sum of individuals; rather, the hold structure and usage frequency of rules in the group form a stable macro-level pattern—consistent with the notion of order without central coordination in complex systems.

From a complexity-science perspective, group-level concept emergence is an instance of order without central coordination in distributed systems. Each instance independently decides whether to adopt a rule based on its local state, but once adopted rule-driven behavior is observed by other instances, which in turn strengthens the rule's propagation. Positive feedback causes high-frequency rules to self-reinforce in the network, eventually forming a stable macro distribution. In our experiment, the 100% hold rate means all rules reached this stable state; in more realistic open scenarios, one would likely observe only a few dominant rules while others remain marginal. Understanding this dynamics is essential for designing robust multi-agent value consensus mechanisms.

Ψ-Net has direct significance for AGI alignment: if a value principle or safety constraint is broadcast as a causal rule and adopted by a majority of instances, it becomes a group-level norm that is hard for any single instance to unilaterally alter. This complements Anthropic's counterfactual reflection training, which implants ethical/honest/integrity concepts inside a single model's workspace [1].

### 6.4 Implications of the Three-layer Workspace Architecture for AGI Design

The micro–meso–macro architecture offers several implications for AGI design:

- **Interpretability auditing should be layered**: micro J-lens identifies hidden goals and reasoning steps inside models, suitable for alignment auditing (e.g., detecting deceptive intent or evaluation awareness) [1]; meso CognitiveBus monitors system-level states, suitable for runtime safety guardrails; macro Ψ-Net tracks the propagation of value rules, suitable for multi-agent ecosystem governance.
- **Value-alignment training can target internal workspace contents**: Anthropic's counterfactual reflection training shows that shaping workspace contents can change behavior in uninterrupted contexts [1]. LAAP can replicate this in CognitiveBus and Ψ-Net by reinforcing specific value rules in counterfactual reflection scenarios, causing them to stabilize in the group-level workspace.
- **Distributed AGI needs shared symbolic anchors**: Ψ-Net currently uses causal rules as cross-instance shared content, avoiding direct transmission of high-dimensional perceptual vectors. This "exchange why, not what" strategy reduces communication bandwidth while preserving interpretability and action guidance.
- **Bodily grounding and episodic memory remain gaps**: J-space, CognitiveBus, and Ψ-Net all lack real bodily feedback and accumulated episodic memory over time. Future work must integrate perception-action loops, embodied interaction, and continual learning into the workspace model to bridge the remaining gap with human consciousness [2][42].
- **Workspace contents and capacities should be distinguished during training and runtime**: Anthropic's study shows significant differences between base and post-trained model workspace contents, indicating that the workspace is not fixed after pretraining but can be shaped by later learning [1][2]. LAAP should preserve similar content plasticity in CognitiveBus and Ψ-Net while ensuring that core safety constraints remain stable through hard coding or group consensus.

Overall, the greatest value of the three-layer architecture is that it transforms the abstract notion of "consciousness" into engineerable module interfaces. Designers no longer need to argue whether a system is "truly" conscious; instead they can ask whether it has a reportable workspace, whether it can control information flow through competition-broadcast mechanisms, and whether it can synchronize key rules across instances. These questions correspond to clear functional acceptance criteria, moving alignment work from philosophical speculation to measurable, intervenable engineering practice. In the long run, the architecture may also provide new modeling tools for neuroscience: by building and testing artificial workspaces, engineers can verify which functional properties are necessary for consciousness and which are by-products of specific biological substrates.

### 6.5 Limitations and Future Directions

Limitations of this study include the small scale of the proxy model in the micro experiment, leaving open direct transfer to production-scale models; the use of controlled benchmark datasets in the meso experiment, so that selective boundaries in real open-domain scenarios may be more complex; the use of Mock mode in the macro Ψ-Net experiment, which does not cover network partitions, Byzantine nodes, or heterogeneous objectives; and the fact that ignition dynamics, bimodal capacity distributions, and autonomous recurrence remain insufficiently validated [2].

Specifically, the J-lens proxy experiment only validated the existence of conceptual directions, not complex tasks such as multi-step reasoning, planning, or language generation. CognitiveBus's 100% reportability accuracy came from known-input conditions and would likely drop in open-domain prediction. Ψ-Net's 100% hold rate was obtained under uniform rules and homogeneous instances; real multi-agent systems with conflicting goals and information noise would significantly alter emergence patterns. Moreover, this paper did not model bodily sensation, pain, long-term emotion regulation, or episodic memory, all of which are crucial for assessing the completeness of machine consciousness [2][35].

Future directions include replicating J-lens on larger LAAP models and comparing J-space across architectures (dense transformers, MoEs, state-space models); integrating CognitiveBus with a real LLM backend to validate the causal impact of state injection on generated behavior; introducing consensus and reputation mechanisms in Ψ-Net to improve robustness against malicious nodes and goal conflict; and integrating bodily perception, episodic memory, and emotion-regulation modules into the workspace to explore AGI consciousness architectures with greater self-continuity. In addition, migrating neuroscience paradigms such as the local-global test, trace conditioning, and inclusion/exclusion to LAAP systems could provide stronger interdisciplinary validation [2][26][27].

## 7 Conclusion

This paper addressed the question of whether and how large language models possess global-workspace-like mechanisms by integrating Anthropic's J-space research with LAAP's CognitiveBus and Ψ-Net into a three-layer global workspace framework. Experiments show that micro-layer J-lens interventions on a LAAP proxy model produce large effect sizes (Cohen's d ≈ 1.18, p < 1e-4); the meso-layer CognitiveBus passes all five criteria of reportability, controllability, reasoning mediation, flexible generalization, and selective necessity; and the macro-layer Ψ-Net achieves low-latency causal-rule broadcasting and a 100% group-level rule hold rate.

Together these results demonstrate that global workspace functional properties can be reproduced and extended across different implementation media and scales. J-space reveals a verbalizable workspace inside Transformers; CognitiveBus explicitly implements a competition-broadcast architecture at the system level; and Ψ-Net extends this architecture to multi-instance distributed scenarios. For AGI design, the three-layer architecture provides actionable entry points for interpretability auditing and value-alignment training, and lays an engineering foundation for shared consciousness across bodies and instances. Although ignition, recurrence, and bodily grounding remain open problems, this work bridges mechanistic discovery and architectural implementation.

We emphasize that we do not claim LAAP systems or Claude are conscious. Our argument is more cautious: if a system implements a workspace satisfying GWT functional criteria, it possesses information-processing capacity equivalent to access consciousness (C1); phenomenal consciousness (subjective experience beyond C2) depends on further bodily, self, and recurrence conditions. The value of this paper lies in transforming a philosophically contentious issue into a measurable, engineerable research agenda. As larger models, more realistic embodied interaction, and more robust distributed protocols become available, the three-layer global workspace framework may become an important reference for evaluating and building safe AGI. By continuously translating neuroscientific signatures of consciousness into engineerable, measurable acceptance criteria, we can advance the study of machine consciousness toward a more operational stage without avoiding the philosophical questions.

## References

[1] Gurnee, W., Sofroniew, N., Pearce, A., et al. (2026). *Verbalizable Representations Form a Global Workspace in Language Models*. Transformer Circuits Thread. https://transformer-circuits.pub/2026/workspace/index.html

[2] Dehaene, S., & Naccache, L. (2026). *Does Claude possess a conscious global workspace? A commentary on "Verbalizable Representations Form a Global Workspace in Language Models"*. https://unicog.org/wp_2025/wp-content/uploads/2026/07/Dehaene-and-Naccache-Workspace-commentary-on-Gurnee-Lindsey-June-2026.pdf

[3] Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

[4] Dehaene, S., & Naccache, L. (2001). Towards a cognitive neuroscience of consciousness: basic evidence and a workspace framework. *Cognition*, 79(1–2), 1–37.

[5] Dehaene, S., & Changeux, J.-P. (2011). Experimental and theoretical approaches to conscious processing. *Neuron*, 70(2), 200–227.

[6] Dehaene, S., Lau, H., & Kouider, S. (2017). What is consciousness, and could machines have it? *Science*, 358(6362), 486–492.

[7] Dehaene, S. (2014). *Consciousness and the Brain: Deciphering How the Brain Codes Our Thoughts*. Viking.

[8] Dehaene, S., & Changeux, J.-P. (2004). Neural mechanisms for access to consciousness. In *The Cognitive Neurosciences III* (pp. 1145–1158). MIT Press.

[9] Elhage, N., Nanda, N., Olsson, C., et al. (2021). A mathematical framework for transformer circuits. *Transformer Circuits Thread*. https://transformer-circuits.pub/2021/framework/index.html

[10] Nanda, N., Chan, L., Lieberum, T., et al. (2023). Progress measures for grokking via mechanistic interpretability. *ICLR 2023*.

[11] Olsson, C., Elhage, N., Nanda, N., et al. (2022). In-context learning and induction heads. *Transformer Circuits Thread*. https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html

[12] Wang, K., Variengien, A., Conmy, A., et al. (2023). Interpretability in the wild: a circuit for indirect object identification in GPT-2 small. *NeurIPS 2022*.

[13] Meng, K., Bau, D., Andonian, A., & Belinkov, Y. (2022). Locating and editing factual associations in GPT. *NeurIPS 2022*.

[14] Templeton, A., Conerly, T., Marcus, J., et al. (2024). Scaling monosemanticity: extracting interpretable features from Claude 3 Sonnet. *Anthropic*. https://www.anthropic.com/research/scaling-monosemanticity

[15] Bricken, T., Templeton, A., Batson, J., et al. (2023). Towards monosemanticity: decomposing language models with dictionary learning. *Transformer Circuits Thread*. https://transformer-circuits.pub/2023/monosemantic-features/index.html

[16] Park, J. S., O'Brien, J., Cai, C. J., et al. (2024). The linear representation hypothesis and the geometry of large language models. *arXiv:2311.03658*.

[17] Gurnee, W., & Tegmark, M. (2024). Language models represent space and time. *ICLR 2024*.

[18] Anthropic. (2024). Constitutional AI: Harmlessness from AI feedback. https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback

[19] Anthropic. (2024). Mapping the mind of a large language model. https://www.anthropic.com/research/mapping-mind-language-model

[20] Anthropic. (2025). Core views on AI safety: When, why, what, and how. https://www.anthropic.com/research/core-views-ai-safety

[21] Baars, B. J. (1997). *In the Theater of Consciousness: The Workspace of the Mind*. Oxford University Press.

[22] Baars, B. J. (2002). The conscious access hypothesis: origins and recent evidence. *Trends in Cognitive Sciences*, 6(1), 47–52.

[23] Baars, B. J. (2005). Global workspace theory of consciousness: toward a cognitive neuroscience of human experience. *Progress in Brain Research*, 150, 45–53.

[24] Dehaene, S., Changeux, J.-P., Naccache, L., et al. (2006). Conscious, preconscious, and subliminal processing: a testable taxonomy. *Trends in Cognitive Sciences*, 10(5), 204–211.

[25] Sergent, C., Faivre, N., Bould, D., et al. (2021). Bifurcation in brain dynamics reveals a signature of conscious processing independent of report. *Nature Communications*, 12, 1149.

[26] Bekinschtein, T. A., Dehaene, S., Rohaut, B., et al. (2009). Neural signature of the conscious processing of auditory regularities. *PNAS*, 106(5), 1672–1677.

[27] Clark, R. E., & Squire, L. R. (1998). Classical conditioning and brain systems: the role of awareness. *Science*, 280(5360), 77–81.

[28] Jacoby, L. L. (1991). A process dissociation framework: separating automatic from intentional uses of memory. *Journal of Memory and Language*, 30(5), 513–541.

[29] Persaud, N., & Cowey, A. (2008). Phenomenal access. *Behavioral and Brain Sciences*, 31(2), 224–225.

[30] Block, N. (1995). On a confusion about a function of consciousness. *Behavioral and Brain Sciences*, 18(2), 227–247.

[31] Tononi, G., & Koch, C. (2015). Consciousness: here, there and everywhere? *Philosophical Transactions of the Royal Society B*, 370(1668), 20140167.

[32] Chalmers, D. J. (1995). Facing up to the problem of consciousness. *Journal of Consciousness Studies*, 2(3), 200–219.

[33] Dennett, D. C. (1991). *Consciousness Explained*. Little, Brown and Company.

[34] Hofstadter, D. R. (1979). *Gödel, Escher, Bach: An Eternal Golden Braid*. Basic Books.

[35] Hofstadter, D. R. (2007). *I Am a Strange Loop*. Basic Books.

[36] LAAP Project. (2026). Large-scale Autonomous Agent Platform: project documentation and source code. LAAP internal repository; see `laap/agi/cognitive_bus.py`, `laap/agi/gw_workspace.py`, `harness/laap_coding/core/psi_net_connector.py`.

[37] LAAP Project. (2026). `laap/agi/cognitive_bus.py`: CognitiveBus — real-time cognitive state bus for LAAP AGI.

[38] LAAP Project. (2026). `laap/agi/gw_workspace.py`: GlobalWorkspace — competitive broadcast implementation of Baars GWT.

[39] LAAP Project. (2026). `harness/laap_coding/core/psi_net_connector.py`: Ψ-Net — distributed causal-rule exchange network across Harness instances.

[40] LAAP Project. (2026). `laap/agi/gws_bridge.py`: GWSBridge — bridging Ao perception to GlobalWorkspace and CognitiveBus.

[41] LAAP Project. (2026). `laap/agi/cognitive_bus_sync.py`: CognitiveBusSyncNode — lightweight cross-profile state synchronization for LAAP.

[42] LeCun, Y. (2022). A path towards autonomous machine intelligence. *Open Review*.

[43] Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.

[44] Conmy, A., Mavor-Parker, A. N., Lynch, A., et al. (2023). Towards automated circuit discovery for mechanistic interpretability. *NeurIPS 2023*.

[45] Huh, M., Cheung, B., Wang, T., & Isola, P. (2024). The Platonic representation hypothesis. *ICML 2024*.

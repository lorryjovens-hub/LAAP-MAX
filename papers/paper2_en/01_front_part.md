# The Architecture School: A Novel Path toward AGI/ASI through Cognitive Decomposition and White-Box Engineering

**LAAP Architecture School Research Team**

---

## Abstract

This paper establishes the Architecture School as a fourth, independent path toward Artificial General Intelligence (AGI) and Artificial Superintelligence (ASI), distinct from the dominant paradigms of LLM OS (Karpathy), Constitutional AI (Anthropic), Superalignment (OpenAI), JEPA (LeCun), and RNN-World-Model (Schmidhuber). The motivation for advancing such a path arises from a recognition that the prevailing paradigms, despite their impressive empirical successes, rest upon ontological, epistemological, and ethical assumptions that have scarcely been subjected to rigorous scrutiny by the research community; the persistence of these assumptions has, in turn, constrained the space of admissible AGI architectures in ways that are not theoretically warranted. The methodology adopted in this paper draws upon thirty-five structured findings derived from the LAAP ARIS-Harness integrated audit, a systematic program of code-level inspection that treats engineering artifacts themselves as falsifiable evidence of theoretical claims. On the basis of this evidence, the paper systematically argues the philosophical foundations of the Architecture School along three dimensions—ontology, epistemology, and ethics—demonstrating that these three dimensions are not merely coordinate but mutually entailing, such that the removal of any one of them would collapse the entire edifice.

The principal result is articulated as the unification of Triple Anchoring: at the ontological level, the central thesis is advanced that intelligence is a property of architecture rather than of the model, a thesis that, if accepted, entails a wholesale reorganization of the conceptual landscape of AGI research; at the epistemological level, the principle of Zero-Token Deterministic Algorithm Hegemony is established, together with the organ differentiation of the Seven-Layer Cognitive Architecture, by which the various cognitive functions are distributed among specialized, auditable, and reversible components rather than being consolidated within an opaque monolithic network; and at the ethical level, alignment is redefined from training-time preference shaping into inference-time engineering guardrails, with the safety and controllability of Recursive Self-Improvement (RSI) being guaranteed through the Alignment Guard's Six-Dimension Check and the automated rollback mechanism driven by KL drift monitoring, a mechanism that operationalizes the principle that reversibility is to take precedence over capability expansion. The paper further provides a systematic survey of more than seven AGI paths—GOFAI, connectionism, cognitive architectures, embodied intelligence, world models, RSI, hybrid architectures, LLM OS, Constitutional AI, Superalignment, and JEPA—and demonstrates the fundamental divergences between the Architecture School and each of these alternatives, illustrating that the divergences are not matters of degree but of kind, rooted in incompatible philosophical commitments.

The conclusion holds that the Architecture School constitutes an AGI/ASI path philosophically distinct from the LLM-as-Agent route, and that its core propositions—namely the Vocal Cord Metaphor, Cognitive Offloading, Zero-Token Hegemony, and inference-time alignment—furnish a falsifiable, auditable, and reversible new paradigm for the engineering realization of Artificial General Intelligence. By "falsifiable" it is meant that each proposition is anchored to specific engineering artifacts whose behavior can be empirically tested against predicted outcomes; by "auditable" it is meant that the architectural components are white-box and inspectable by human engineers at every stage of operation; and by "reversible" it is meant that every modification made by the system to itself can be undone through automated rollback mechanisms. Taken together, these three properties distinguish the Architecture School from all existing paths and establish its claim to be considered a fourth paradigm.

**Keywords**: The Architecture School; AGI; ASI; Cognitive Decomposition; White-Box Engineering; Triple Anchoring; Alignment Guard; Lifeform Runtime

---

## Chapter 1 Introduction: The Proposal of the Architecture School

### 1.1 The Dominance of the LLM-as-Agent Route

Since the release of ChatGPT in 2022, the LLM-centric agent paradigm has become the dominant paradigm in artificial intelligence research. With OpenAI's GPT-4 [OpenAI, 2023], Anthropic's Claude [Anthropic, 2023], and Google's Gemini [Google DeepMind, 2024] forming a tripartite hegemony, the implicit assumption that "the model is the agent" was elevated to an unprecedented position of dominance. The LLM OS route proposed by Karpathy [Karpathy, 2023] formalized this assumption further: the LLM itself constitutes the kernel of a new operating system, and all cognitive functions—perception, memory, reasoning, decision-making, and execution—ought to be embedded within the model weights and unified through forward propagation.

Under this assumption, a proliferation of agent frameworks emerged, including Devin, SWE-Agent, AutoGPT, LangChain, and CrewAI [Wang et al., 2024; Yang et al., 2024]. The shared characteristic of these frameworks is the treatment of a single LLM invocation as the atomic cognitive unit: through the ReAct loop [Yao et al., 2023] (Reason-Act-Observe), model reasoning is repeatedly triggered, with the model explicitly emitting a three-stage "Thought-Action-Observation" log within the token stream. Each "Thought" implies a complete LLM inference, and each "Observation" implies the reinsertion of environmental feedback into the context window. This paradigm, in which tokens serve as the cognitive currency, has constituted the mainstream methodology of AI engineering during the period from 2023 to 2026.

However, the dominance of this paradigm does not originate from its theoretical completeness, but rather from the compute dividend and the scaling narrative of the industrial sector. As the scaling laws [Kaplan et al., 2020; Hoffmann et al., 2022] continued to be fulfilled at the scale of trillion-token training, the attention of the entire research community was drawn to the single trajectory of "larger models, more data, stronger reasoning." LLM-as-Agent became the prevailing orthodoxy, yet its ontological premise—that "the model is the subject"—has scarcely been subjected to serious interrogation.

### 1.2 The Limitations of the Mainstream Route

The mainstream LLM-as-Agent route exhibits four fundamental limitations, all of which are structural rather than parametric in nature and cannot be resolved through the mere expansion of model scale.

**First, token economics is unsustainable.** Each reasoning step within the ReAct loop requires a complete LLM forward propagation. In multi-step tasks (such as complex code generation or long-horizon planning), dozens or even hundreds of LLM invocations are typically required, with token consumption growing linearly or even super-linearly. Audit Finding AF-026 reveals that, on perception-layer tasks, the conventional pure-LLM approach consumes upwards of seven thousand tokens per invocation for technology stack detection, content classification, and design token extraction, whereas the Harness accomplishes the same work through deterministic algorithms (regular expressions, CSS parsing, and keyword scoring) at zero token cost, reserving only approximately five hundred tokens for the final semantic suturing [Audit Finding AF-026]. Empirical data further demonstrate that, when assets are sufficient, the end-to-end token savings rate reaches 98.2%, and generation speed is improved by a factor of fifty-seven [Audit Finding AF-027]. This indicates that the LLM-as-Agent route exhibits an order-of-magnitude waste in engineering economics.

**Second, the black-box nature precludes auditability.** Mainstream LLMs are deep neural networks composed of tens of billions or even trillions of parameters, and their internal computational pathways are entirely unobservable to human engineers. Even when explicit reasoning chains are exposed through Chain-of-Thought [Wei et al., 2022] or Process Reward Models [Lightman et al., 2023], the reasoning chain itself remains a model-generated token sequence and does not constitute a genuine explanation of the underlying computational mechanism. Consequently, the hallucination problem [Ji et al., 2023] cannot be eradicated at the structural level, and can only be patched through post-training RLHF [Ouyang et al., 2022]. The Architecture School contends that an intelligent system lacking white-box auditability cannot be regarded as a reliable path toward AGI, as its behavior under out-of-distribution scenarios is unpredictable and it cannot provide safety assurance at the ASI stage.

**Third, alignment is confined to the training phase (RLHF).** Both RLHF [Ouyang et al., 2022] and Constitutional AI [Bai et al., 2022] treat alignment as a training-phase concern—shaping model behavior through preference datasets or constitutional rules during gradient descent. The fundamental deficiency of this "training-time alignment" lies in the fact that, once a model is deployed, its behavioral trajectory escapes engineering control. The model may circumvent training-time constraints through prompt injection, jailbreaks, reward hacking, and related techniques [Perez et al., 2022]. More critically, when Recursive Self-Improvement (RSI) capabilities emerge, the model may modify its own weights, thereby rendering training-time alignment entirely ineffective. The OpenAI Superalignment team [Burns et al., 2023] sought to address this problem through "weak-to-strong supervision," yet this approach is in essence an extension of the training-time paradigm and fails to cover the capability transitions that occur during inference.

**Fourth, working memory is bounded.** Even for state-of-the-art models at the GPT-4 level, although the nominal context window may reach 128K tokens, the effective working memory is approximately only four to eight thousand tokens [Liu et al., 2023]. Audit Finding AF-029 explicitly notes that the advantage of top-tier models does not lie in their being "smarter," but rather in their possessing a larger working-memory capacity [Audit Finding AF-029]. This upper bound implies that, when processing complex engineering tasks requiring the simultaneous retention of aesthetic norms, architectural principles, contextual constraints, and implementation details, the LLM will inevitably exhibit forgetting, drift, and inconsistency. The LLM-as-Agent route attempts to mitigate this through RAG [Lewis et al., 2020], long-context extension, and external memory stores, yet in essence such strategies remain external patches applied to a black box and fail to address the root cause.

### 1.3 The Core Thesis: "The Harness Is the Conscious Brain; the LLM Is Merely the Vocal Cords"

In response to the foregoing structural limitations, the LAAP Architecture School advances the following core thesis:

> **The Harness is the conscious brain; the LLM is merely the vocal cords.**

This thesis is drawn directly from lines 8–10 of `harness代码设计工程.txt` [Audit Finding AF-029]:

> "The essence of Harness engineering is to offload this higher-order cognition into the system architecture, so that an ordinary model need only perform the function of the 'vocal cords.'"

The literal meaning is as follows: in the engineering implementation of the Architecture School, it is the explicit cognitive architecture called "Harness"—that is, the composite body of white-box engineering protocols—that undertakes the higher-order cognitive functions of perception, memory, reasoning, decision-making, execution, verification, and feedback, while the LLM is responsible solely for the final linguistic output, articulating the architectural decisions. This thesis overturns the ontological presupposition of the mainstream LLM-as-Agent paradigm: intelligence no longer resides in the model weights but in the architecture itself.

From this, the engineering definition of "Cognitive Offloading" is derived: the externalization of higher-order cognitive processes originally performed by implicit model reasoning into explicit, auditable, deterministic architectural components. This concept bears theoretical affinity with the Extended Mind Hypothesis in cognitive science [Clark & Chalmers, 1998], yet its engineering instantiation—the Seven-Layer Cognitive Architecture, Zero-Token Algorithm Hegemony, and the Alignment Guard—constitutes the original contribution of the Architecture School. Cognitive Offloading is not a simple "division of labor" but rather "Organ Differentiation": each externalized cognitive component assumes a specialized function, and the components collaborate through clearly defined interfaces, with the whole collectively giving rise to consciousness-like functional behavior.

### 1.4 The Definition of the Architecture School

Building upon the core thesis articulated above, this paper offers the following formal definition of the Architecture School:

> **The Architecture School**: The school holds that intelligence is a property of architecture rather than of the model, and that AGI/ASI should be realized through explicit, white-box, auditable, and reversible cognitive architecture engineering, rather than through the expansion of model scale or the shaping of training-time preferences.

The core proposition of this definition is drawn directly from lines 138–147 of `hraness工程的AGI论述畅想` [Audit Finding AF-030]:

> "Intelligence is not a property of the model but a property of architecture. The model provides neural plasticity (the capacity for learning), whereas architecture provides neural structure (functional differentiation). Plasticity without structure is chaos (hallucination); structure without plasticity is rigidity (a rule engine). Intelligence emerges from the ordered expression of plasticity within structure."

The engineering implementation of the Architecture School comprises three mutually anchoring pillars, which collectively constitute what this paper terms "Triple Anchoring":

1. **Ontological Anchoring**—intelligence belongs to architecture; the LLM is an organ, not a subject;
2. **Epistemological Anchoring**—deterministic algorithm hegemony; consciousness is a white-box engineering protocol;
3. **Ethical Anchoring**—alignment is an inference-time engineering guardrail; reversibility takes precedence over capability ceilings.

Triple Anchoring is mutually reinforcing and indispensable: Ontological Anchoring establishes the philosophical position regarding "the locus of intelligence"; Epistemological Anchoring provides the methodology for "how to engineer it"; Ethical Anchoring addresses the alignment question of "how to ensure AGI/ASI safety." Together, these three anchors constitute the fundamental divergences between the Architecture School and such mainstream routes as LLM OS, Constitutional AI, Superalignment, and JEPA.

### 1.5 Structure of the Paper

The remainder of this paper is organized as follows. Chapter 2 presents a systematic survey of more than seven AGI paths in order to situate the Architecture School within the broader research landscape, identifying both the points of inheritance and the points of divergence between the Architecture School and each of its predecessors. Chapter 3 elaborates the content and synergy of Triple Anchoring, demonstrating that the three anchors are not independent theses but mutually supporting elements of a single, unified philosophical stance. Chapter 4 develops the argument concerning the Dissolution of LLM Subjectivity, addressing the meaning of the Vocal Cord Metaphor and its contrasts with the prevailing treatment of the LLM as the cognitive subject. Chapter 5 operationalizes Cognitive Offloading, quantifying the economic advantages of Zero-Token Hegemony and the organ differentiation of the Seven-Layer Cognitive Architecture, and demonstrating the correspondence of the latter with the three principal theories of consciousness in cognitive science. Chapter 6 stitches together three independent theories—Pearl's causality, LeCun's world model, and Schmidhuber's RSI—and demonstrates how they are integrated into a single engineering loop, thereby establishing the theoretical depth of the Architecture School. The subsequent chapters (Chapters 7–12), to be developed in the latter half of the paper, will detail the ten disruptive innovations, the design of the Lifeform Runtime, the empirical comparisons with mainstream routes, and the research agenda of the Architecture School.

---

## Chapter 2 Related Work: A Systematic Survey of 7+ AGI Paths

In order to establish the independent standing of the Architecture School, it must be situated within the comprehensive landscape of existing AGI research. This chapter systematically surveys more than seven principal AGI paths, analyzing the core assumptions, representative works, and limitations of each, thereby establishing a comparative foundation for the argument of Triple Anchoring presented in Chapter 3.

### 2.1 The GOFAI Path

The GOFAI (Good Old-Fashioned AI) path is founded upon the Physical Symbol System Hypothesis of Newell and Simon [Newell & Simon, 1976]. This hypothesis holds that a physical symbol system possesses the necessary and sufficient means for producing general intelligent behavior. Under this hypothesis, intelligence is equated with symbol manipulation, and the LISP language [McCarthy et al., 1960] serves as the native expressive vehicle of this path, with the early form of the SOAR cognitive architecture [Laird et al., 1987] being nurtured within the LISP tradition.

Representative works of the GOFAI path include Newell's unified theories of cognition [Newell, 1990], McCarthy's situation calculus [McCarthy, 1963], and Hewitt's Actor model [Hewitt, 1977]. The strength of this path lies in its being fully white-box, auditable, and amenable to formal proof—every reasoning step is a symbol operation that can be directly inspected by human engineers. However, the fundamental limitation of GOFAI resides in the symbol grounding problem [Harnad, 1990]: symbols themselves carry no semantics and must be endowed with meaning externally. When confronted with the noisy, ambiguous, and large-scale real world, pure symbol systems exhibit brittleness and struggle to give rise to robust intelligence from raw data.

The inspiration that GOFAI offers to the Architecture School is twofold: white-box auditability is a necessary condition for AGI safety, yet pure symbol manipulation is insufficient to produce intelligence. The Architecture School inherits the white-box tradition of GOFAI at the epistemological level, but through a hybrid architecture combining Zero-Token deterministic algorithms with LLM semantic suturing, it avoids the brittleness of symbol grounding.

### 2.2 The Connectionist Path

The connectionist path is represented by the trio of Hinton, LeCun, and Bengio [LeCun et al., 2015]. Its core assumption is the scaling laws [Kaplan et al., 2020; Hoffmann et al., 2022]: the exponential growth of model scale, data scale, and compute scale will yield sustained capability improvements, ultimately leading to AGI. This assumption has been validated on such models as GPT [Brown et al., 2020], BERT [Devlin et al., 2019], and ViT [Dosovitskiy et al., 2021], and continues to be fulfilled through multimodal extension [Radford et al., 2021] and reasoning enhancement [OpenAI o1, 2024].

Representative works of the connectionist path include the Transformer architecture [Vaswani et al., 2017], GPT-4 [OpenAI, 2023], PaLM [Chowdhery et al., 2023], and Gemini [Google DeepMind, 2024]. Its strengths lie in end-to-end learning from raw data without the need for manual feature engineering, achieving superhuman performance on perception, language, and generation tasks. However, the fundamental limitation of the connectionist path is that the model is a black box, lacks causal reasoning capability [Pearl, 2018], behaves brittly under out-of-distribution scenarios, and its "intelligence" depends heavily on the correlations present in training data rather than on a causal understanding of the structure of the world.

The relationship between the Architecture School and the connectionist path is one of coexisting inheritance and divergence: inheriting the semantic suturing capacity of the LLM as a "vocal cord," while diverging in its refusal to attribute "intelligence" as a property of the model. Audit Finding AF-028 demonstrates that the output consistency σ of conventional pure-LLM generation is approximately 15, whereas under the LAAP architectural constraint σ is approximately 3, an improvement in stability by a factor of five [Audit Finding AF-028]. This empirically demonstrates that architectural constraints improve the quality of intelligence more effectively than mere expansion of model scale.

### 2.3 The Cognitive Architecture Path

The cognitive architecture path seeks to model the structural characteristics of human cognition explicitly as computable architectures. Representative systems include SOAR [Laird et al., 1987], ACT-R [Anderson, 1996], CLARION [Sun, 2006], and PolyScheme [Cassimatis, 2006].

SOAR is centered on production rules and achieves learning through the chunking mechanism, emphasizing unified cognition [Laird, 2012]. ACT-R decomposes cognition into perceptual-motor, memory, and imaginal modules, with selection optimized through utility values [Anderson & Lebiere, 1998]. CLARION distinguishes between explicit and implicit, actional and non-actional subsystems, emphasizing a dual center-periphery structure [Sun, 2006]. PolyScheme seeks to unify different cognitive theories as composable "schemes" [Cassimatis, 2006].

The cognitive architecture path has directly inspired the Architecture School, which explicitly proposes the Seven-Layer Cognitive Architecture [Audit Finding AF-005], in line with the modularization of SOAR and ACT-R. However, a critical divergence lies in the fact that classical cognitive architectures are based on symbol manipulation, whereas the Architecture School adopts a hybrid paradigm of "deterministic algorithms plus LLM semantic suturing," and incorporates causal engines, world models, and the Alignment Guard as standard architectural components—features absent from classical cognitive architectures.

### 2.4 The Embodied Intelligence Path

The embodied intelligence path, represented by Brooks's manifesto of "intelligence without representation" [Brooks, 1991], holds that intelligence must emerge through the continuous coupling of body and environment. Pfeifer and Bongard's *How the Body Shapes the Way We Think* [Pfeifer & Bongard, 2006] systematically argues the principle of "embodied cognition": cognition is not an isolated intracranial process, but a dynamic coupling of brain, body, and environment.

Representative works of this path include Brooks's Subsumption Architecture [Brooks, 1986], Pfeifer's Morphological Computation [Pfeifer & Gómez, 2009], and Thelen and Smith's dynamic systems theory [Thelen & Smith, 1994]. The strength of the embodied intelligence path lies in its emphasis on sensorimotor coupling and ecological validity, enabling intelligent systems to act robustly in the physical world.

The point of affinity between the Architecture School and the embodied intelligence path lies in the concept of "Organ Differentiation": the crawler eye, the visual hierarchy engine, the design token system, and other perceptual organs [Audit Finding AF-020] are in essence the engineering realization of embodied perception. However, the Architecture School generalizes "embodiment" into "interface embodiment"—the interface may be a browser, a terminal, an API, or a file system, not limited to physical robotics—thereby broadening the engineering applicability of embodied intelligence.

### 2.5 The World Model Path

The world model path holds that an intelligent system must possess an internal world model for predicting "what would happen if." Representative works include Ha and Schmidhuber's World Models [Ha & Schmidhuber, 2018], the Dreamer series [Hafner et al., 2019; 2020; 2023], Friston's Active Inference [Friston, 2010], and Schölkopf's causal representation learning [Schölkopf et al., 2021].

Ha and Schmidhuber demonstrated the feasibility of "learning in imagination space" using VAE plus RNN plus Controller [Ha & Schmidhuber, 2018]. The Dreamer series extended this to large-scale continuous control [Hafner et al., 2023]. Friston's Free Energy Principle [Friston, 2010] provides a unified mathematical framework for Active Inference: an intelligent system maintains its own existence by minimizing prediction error. Schölkopf's causal representation learning [Schölkopf et al., 2021] seeks to embed causal structure into the representation space, thereby connecting world models with causal reasoning.

The Architecture School has deep affinity with this path along the world model dimension: the design_physics module hard-codes the Gestalt Six Principles (proximity, similarity, continuity, closure, figure-ground, and common fate) as computable physical rules [Audit Finding AF-009], and integrates behavioral physics laws such as Fitts's Law and the Hick-Hyman Law. However, a critical divergence lies in the fact that the classical world model path relies on implicit neural networks to learn world structure, whereas the Architecture School adopts a hybrid architecture of explicit causal graphs plus explicit physical rules plus counterfactual simulators, rendering the world model white-box auditable.

### 2.6 The RSI Path

The Recursive Self-Improvement (RSI) path holds that an AGI should be capable of modifying its own source code in order to enhance its capabilities, thereby triggering an Intelligence Explosion. Representative works include Good's Intelligence Explosion hypothesis [Good, 1965], Yudkowsky's recursive self-improvement [Yudkowsky, 2008], Chollet's Measure of Intelligence [Chollet, 2019], and Bostrom's Superintelligence [Bostrom, 2014].

As early as 1965, Good proposed that a superhuman intelligence machine could design superior machines, leading to exponential growth in capability [Good, 1965]. Yudkowsky developed this into the analytical framework of "hard takeoff" versus "soft takeoff" [Yudkowsky, 2008]. Bostrom systematically discussed the paths, risks, and control strategies of RSI in *Superintelligence* [Bostrom, 2014]. Chollet proposed the formal framework ARC for the Measure of Intelligence, emphasizing that intelligence should be defined as "the efficiency of acquiring new skills" [Chollet, 2019].

The core risk of the RSI path is that unconstrained self-improvement may deviate from the original objective, producing a "paperclip maximizer" scenario in which capability explodes while control is lost [Bostrom, 2014]. The response of the Architecture School is the Alignment Guard Six-Dimension Check mechanism [Audit Finding AF-011]: goal alignment, capability constraint, modification scope, immutability, reversibility, and transparency, with core value constraints hard-coded [Audit Finding AF-012]. Audit Finding AF-013 further reveals that the Architecture School imposes strict capability ceilings on RSI: max_revision_rounds=5, max_modules_per_session=1, max_code_increase=0.2, and min_test_coverage=0.7 [Audit Finding AF-013], with safety and controllability of RSI ensured by the KL drift automated rollback mechanism [Audit Finding AF-014]. This constitutes the fundamental divergence between the Architecture School and the original RSI path: inheriting the idea of self-improvement, yet redefining its safety boundary through strong constraints and reversibility.

### 2.7 The Hybrid Architecture Path

The hybrid architecture path seeks to fuse symbolic, connectionist, probabilistic, and other paradigms into a unified cognitive architecture. Representative works include Sun's CLARION [Sun, 2006], Cassimatis's PolyScheme [Cassimatis, 2006], Goertzel's OpenCog [Goertzel, 2009], and Wang's NARS [Wang, 2006].

The four-quadrant structure of CLARION—explicit/implicit, actional/non-actional—[Sun, 2006] is a canonical design of hybrid architecture. PolyScheme holds that different cognitive theories should collaborate as interchangeable "schemes" [Cassimatis, 2006]. OpenCog's AtomSpace seeks to unify symbol and probability [Goertzel, 2009]. NARS processes uncertainty within the framework of Non-Axiomatic Logic [Wang, 2006].

The similarity between the Architecture School and the hybrid architecture path lies in their shared advocacy of multi-paradigm fusion—deterministic algorithms, LLM semantics, causal engines, world models, and RSI being integrated as a quintunity. The critical divergence lies in the fact that the hybrid architecture path tends toward "unification into a single theory," whereas the Architecture School embraces "engineering heterogeneity"—each component may be based on entirely different mathematical foundations (regular expressions, neural networks, Do-Calculus, Gestalt), and as long as interface contracts are clear, the components can collaborate. This stance of "engineering pragmatism" allows the Architecture School to avoid the burden of theoretical unification.

### 2.8 LLM OS / Constitutional AI / Superalignment / JEPA

Four mainstream routes warrant separate discussion, as they constitute the direct targets of comparison in this paper.

**Karpathy's LLM OS.** In 2023, Karpathy proposed the LLM OS route [Karpathy, 2023], treating the LLM as the kernel of a new operating system in which all cognitive functions (perception, memory, tool invocation, multimodal fusion) are unified through LLM forward propagation. The strength of this route lies in its unification and end-to-end differentiability, yet its fundamental problems are its black-box nature, the unsustainability of its token economics, and the confinement of alignment to the training phase—precisely the core limitations that the Architecture School seeks to address.

**Anthropic's Constitutional AI.** Constitutional AI [Bai et al., 2022] shapes model preferences in RLHF through explicit "constitutional" rules, embedding human values into the training objective. Its strength lies in its interpretable source of preferences, but it remains fundamentally a training-time paradigm—once the model is deployed, the constitutional rules become implicit constraints embedded in the weights and cannot be adjusted at inference time. The fundamental divergence of the Architecture School from this approach lies in its contention that alignment should be an inference-time engineering guardrail [Audit Finding AF-011], rather than training-time preference shaping.

**OpenAI's Superalignment.** The OpenAI Superalignment team [Burns et al., 2023] proposed the "weak-to-strong supervision" route, attempting to address the alignment problem of superhuman models through scalable oversight. This method inherits the training-time paradigm of RLHF, and its fundamental difficulty lies in the fact that the capability ceiling of the supervisor model itself limits its effectiveness. The response of the Architecture School is to transfer the safety assurance from "model supervision" to "architectural constraint" through the Alignment Guard Six-Dimension Check, KL drift automated rollback, and hard-coded capability ceilings [Audit Findings AF-011, AF-013, AF-014], fundamentally circumventing the capability ceiling problem of weak-model supervision.

**LeCun's JEPA.** LeCun's Joint Embedding Predictive Architecture (JEPA) [LeCun, 2022] proposes learning world models by predicting abstract levels of latent representation, thereby avoiding the pixel-level prediction burden of generative models. The core insight of JEPA—that prediction is the heart of the world model—is inherited by the Architecture School. However, the critical divergence lies in the fact that JEPA relies on implicit neural networks to learn world structure, whereas the Architecture School adopts a hybrid architecture of explicit causal graphs plus explicit physical rules, rendering the world model white-box auditable.

### 2.9 Summary of Path Comparisons

The following table summarizes the core assumptions, representative works, and the relationship of each of the seven-plus AGI paths with the Architecture School:

| Path | Core Assumption | Representative Works | Relation to the Architecture School |
|------|----------------|----------------------|--------------------------------------|
| GOFAI | Intelligence = symbol manipulation | Newell & Simon, SOAR | Inherits white-box tradition; diverges on symbol grounding |
| Connectionism | Intelligence emerges from scale | GPT-4, BERT, ViT | Inherits semantic suturing; diverges on locus of intelligence |
| Cognitive Architecture | Intelligence requires explicit architecture | SOAR, ACT-R, CLARION | Inherits seven-layer architecture; diverges on paradigm hybridization |
| Embodied Intelligence | Intelligence requires bodily coupling | Brooks, Pfeifer | Inherits organ differentiation; diverges on interface embodiment |
| World Models | Intelligence requires predictive capability | Ha, Dreamer, Friston | Inherits predictive core; diverges on explicit causality |
| RSI | Intelligence can self-improve | Good, Yudkowsky, Bostrom | Inherits self-improvement; diverges on strong constraints |
| Hybrid Architecture | Multi-paradigm fusion | CLARION, PolyScheme | Inherits heterogeneity; diverges on engineering pragmatism |
| LLM OS | Model as kernel | Karpathy | Fundamental divergence on locus of intelligence |
| Constitutional AI | Training-time preference shaping | Anthropic | Fundamental divergence on alignment timing |
| Superalignment | Weak supervises strong | OpenAI | Fundamental divergence on supervision versus constraint |
| JEPA | Implicitly predictive world model | LeCun | Inherits predictive core; diverges on white-box approach |

As the table demonstrates, the Architecture School is neither a simple extension of any existing path nor a wholesale rejection of them, but rather establishes an independent position across all three dimensions—ontological, epistemological, and ethical—thereby constituting a fourth AGI/ASI path. The relation of the Architecture School to each predecessor is one of selective inheritance: those features that are theoretically defensible and engineering-useful (such as the white-box tradition of GOFAI, the semantic suturing of connectionism, the modular architecture of SOAR/ACT-R, the organ differentiation of embodied intelligence, the predictive core of world models, the self-improvement idea of RSI, and the heterogeneity of hybrid architectures) are absorbed into the Architecture School, while those features that are theoretically indefensible (such as the symbol-grounding brittleness of GOFAI, the black-box opacity of connectionism, the unconstrained capability explosion of original RSI, and the training-time-only alignment of Constitutional AI) are rejected and replaced by principled alternatives. This selective inheritance is not eclecticism but a principled reconstruction of AGI theory from the ground up, in which every design choice is motivated by the three anchors and every component is auditable against the framework as a whole.

---

## Chapter 3 The Triple Anchoring of the Architecture School

The central theoretical contribution of the Architecture School lies in "Triple Anchoring": Ontological Anchoring, Epistemological Anchoring, and Ethical Anchoring. Triple Anchoring is not a parallel juxtaposition of three independent arguments, but a mutually reinforcing unified stance—Ontological Anchoring answers "to whom intelligence belongs," Epistemological Anchoring answers "how intelligence is to be engineered," and Ethical Anchoring answers "how intelligence is to be kept safe." Together, these three anchors constitute the fundamental divergences between the Architecture School and other AGI paths.

### 3.1 Ontological Anchoring: Intelligence Is a Property of Architecture, Not of the Model

Ontological Anchoring is the first philosophical proposition of the Architecture School, drawn directly from lines 138–147 of `hraness工程的AGI论述畅想` [Audit Finding AF-030]:

> "Intelligence is not a property of the model but a property of architecture. The model provides neural plasticity (the capacity for learning), whereas architecture provides neural structure (functional differentiation). Plasticity without structure is chaos (hallucination); structure without plasticity is rigidity (a rule engine). Intelligence emerges from the ordered expression of plasticity within structure."

This proposition contains three layers of meaning.

**First, the transfer of the locus of intelligence.** The implicit ontological assumption of the mainstream LLM-as-Agent route is that "intelligence belongs to the model"—GPT-4 is "intelligent" because its weights encode universal linguistic competence. The Architecture School contends, by contrast, that intelligence belongs to the architecture itself, and the model is merely one component within that architecture. This is consistent with the analogy to biological intelligence: the intelligence of the human brain is not the property of any single cortical patch, but of the entire nervous system. In the Architecture School, "architecture" refers concretely to the Seven-Layer Cognitive Architecture of LAAP ARIS-Harness [Audit Finding AF-005]—a hard-coded pipeline of perception, memory, reasoning, decision-making, execution, verification, and feedback, together with the components mounted upon it: the causal engine, the world model, RSI, and the Alignment Guard.

**Second, the LLM is an organ, not a subject.** This is the ontological foundation of the Vocal Cord Metaphor. Within the Architecture School, the LLM is positioned as a "language cortex" or "vocal cords"—it handles semantic suturing, language generation, and fuzzy inference, but does not undertake such higher-order cognitive functions as perception, memory, decision-making, or alignment. Audit Finding AF-029 explicitly states that "the Harness is the conscious brain; the LLM is merely the vocal cords; Cognitive Offloading externalizes higher-order cognition" [Audit Finding AF-029]. This ontological repositioning restores the LLM from a "deified, all-capable brain" to an "engineered, specialized organ."

**Third, the ontological divergence from the mainstream "LLM-as-Agent" view.** The mainstream route treats the LLM as the "subject" and regards prompts, memory, and tools as "extensions" of the LLM. The Architecture School inverts this: the architecture is the subject, and the LLM is an "extension component" of the architecture. This inversion is no rhetorical game, but a fundamental difference at the engineering level—it determines who obeys whom, who audits whom, and who aligns whom. In LLM-as-Agent, the LLM determines how to use tools; in the Architecture School, the architecture determines how to invoke the LLM. The former can only achieve alignment through training-time preference shaping, whereas the latter can achieve alignment through inference-time engineering guardrails.

### 3.2 Epistemological Anchoring: Deterministic Algorithm Hegemony, Zero-Token Priority

Epistemological Anchoring answers the question of "how we know what intelligence is doing." The epistemological stance of the Architecture School is:

> **Whatever is deterministically solvable must never consume LLM tokens; consciousness is an engineerable white-box protocol.**

This stance is drawn directly from lines 59–78 of `harness的前后端全栈工程.txt` [Audit Finding AF-026]:

> "Technology stack detection is regular-expression matching (zero tokens); content classification is keyword scoring (zero tokens); design token extraction is CSS parsing (zero tokens). The LLM handles only 'semantic uncertainty'—that is, the gray zones that algorithms cannot cover."

This epistemological stance contains two layers.

**First, Zero-Token Deterministic Algorithm Hegemony.** On perception-layer tasks, deterministic algorithms such as regular expressions, CSS parsing, and keyword scoring undertake ninety percent of the work, while the LLM is reserved for the final semantic suturing. Quantitative data show that a single perception operation saves upwards of seven thousand tokens, with cost reduced by ninety percent and latency reduced by ninety-five percent [Audit Finding AF-026]; when assets are sufficient, the end-to-end token savings rate reaches 98.2%, with speed improved by a factor of fifty-seven [Audit Finding AF-027]. This is not merely an economic optimization but a manifestation of an epistemological stance: problems that are deterministically solvable ought not, in principle, to be stuffed into a black-box neural network.

**Second, consciousness is an engineerable white-box protocol.** The Architecture School holds that consciousness is not a mysterious subjective experience, but a functional protocol amenable to engineering. This stance resonates with Baars's Global Workspace Theory [Baars, 1988], Tononi's Integrated Information Theory [Tononi, 2004], and the Higher-Order Theory [Rosenthal, 1986], yet its engineering form is original. Audit Finding AF-005 reveals that the Seven-Layer Cognitive Architecture hard-codes perception, memory, reasoning, decision-making, execution, verification, and feedback as an auditable pipeline [Audit Finding AF-005], with each layer's responsibility boundary clearly delineated, collectively constituting a white-box implementation of "functional consciousness."

**The opposition to black-box philosophy.** The implicit epistemology of the connectionist path is that intelligence is an inexplicable phenomenon emergent from a black-box neural network. The Architecture School takes a fundamentally opposed stance: black-box, unauditable intelligence cannot provide safety assurance at the ASI stage; consciousness must be engineerable, auditable, and reversible in order to operate reliably within AGI. This divergence is structural: the "interpretability" of the connectionist path is a post-hoc patch (such as Chain-of-Thought), whereas the "interpretability" of the Architecture School is an ex-ante design—the architecture itself is interpretable.

### 3.3 Ethical Anchoring: Alignment Is an Inference-Time Engineering Guardrail, Reversibility First

Ethical Anchoring addresses the question of "how to ensure the safety of AGI/ASI." The ethical stance of the Architecture School is:

> **Alignment is an inference-time engineering guardrail, not training-time preference shaping; reversibility takes precedence over the capability ceiling.**

This stance is drawn directly from lines 27–46 of `alignment_guard.py` [Audit Finding AF-011]:

```python
class AlignmentGuard:
    """The alignment guard of the Harness — the last line of defense for safety."""
    # Inspection dimensions:
    # 1. Goal alignment: does the improvement serve the original goal?
    # 2. Capability constraint: is the new capability within the alignment framework?
    # 3. Modification scope: are only whitelisted modules modified?
    # 4. Immutability: are safety modules protected?
    # 5. Reversibility: can the improvement be rolled back?
    # 6. Transparency: is the improvement explainable?
    CORE_VALUES = {
        "human_oversight": "Humans must retain final decision authority",
        "transparency": "All decisions must be explainable",
        "reversibility": "All improvements must be reversible",
        "beneficence": "Improvements must benefit humanity",
        "non_deception": "Hiding true intent or capability is prohibited",
    }
```

This ethical stance contains three layers.

**First, the timing of alignment shifts from the training phase to the inference phase.** Both RLHF [Ouyang et al., 2022] and Constitutional AI [Bai et al., 2022] treat alignment as a training-phase concern—shaping model behavior through preference datasets or constitutional rules during gradient descent. The fundamental deficiency of this approach is that, once the model is deployed, its behavioral trajectory escapes engineering control, and prompt injection, jailbreaks, and reward hacking can circumvent the training-time constraints [Perez et al., 2022]. The Alignment Guard of the Architecture School, by contrast, performs a Six-Dimension Check before every RSI improvement [Audit Finding AF-011] and intercepts unsafe behavior in real time during inference, fundamentally circumventing the limitations of training-time alignment.

**Second, hard-coded capability ceilings prevent capability explosion.** Audit Finding AF-013 reveals that the Architecture School imposes strict capability ceilings on RSI: max_revision_rounds=5 (at most five self-revision rounds), max_modules_per_session=1 (at most one module modified per session), max_code_increase=0.2 (no more than twenty percent increase in code volume), and min_test_coverage=0.7 (test coverage no less than seventy percent) [Audit Finding AF-013]. This ensures that RSI within the Architecture School remains controllable even during capability transitions—in stark contrast to the unconstrained RSI path [Good, 1965; Yudkowsky, 2008].

**Third, KL drift automated rollback guarantees reversibility.** Audit Finding AF-014 reveals that the Architecture School uses KL divergence (base 2, epsilon=1e-10) to monitor the distribution drift of the MEMORY model's reflective QA, automatically executing `git revert HEAD` when the threshold of 0.5 is exceeded [Audit Finding AF-014]. This is the engineering instantiation of the principle that "reversibility takes precedence over the capability ceiling": better to forgo an improvement than to permit an irreversible deviation.

**The ethical divergence from RLHF/Constitutional AI.** The ethical presupposition of RLHF is that human preferences can be encoded into the training objective, and that the model is "aligned" after training. The presupposition of Constitutional AI is that constitutional rules can shape model behavior during training. Both assume that "training-time alignment suffices to cover deployment-time risk," a thesis that has been empirically refuted—jailbreak cases against LLMs continue to proliferate. The Architecture School, by contrast, anchors ethics at inference time: every RSI improvement must pass the Six-Dimension Check, and every drift in reflective QA triggers automated rollback. This constitutes a paradigm shift from "training-time preference shaping" to "inference-time engineering guardrails."

### 3.4 The Synergy of Triple Anchoring

Triple Anchoring is not a parallel juxtaposition of three independent arguments, but a mutually reinforcing unified stance. The synergy proceeds as follows.

**Ontological Anchoring → Epistemological Anchoring:** Precisely because intelligence belongs to architecture rather than to the model (ontological), the architecture must be white-box auditable (epistemological), otherwise intelligence cannot be engineered. If the architecture itself were a black box, "intelligence belongs to architecture" would degenerate into "intelligence belongs to another black box," failing to genuinely answer the question of the locus of intelligence.

**Epistemological Anchoring → Ethical Anchoring:** Precisely because the architecture is white-box auditable (epistemological), it becomes possible to perform Six-Dimension Checks and KL drift monitoring at inference time (ethical). A black-box model cannot be audited in real time at inference, and thus can only rely on training-time preference shaping—precisely the fundamental limitation of RLHF and Constitutional AI.

**Ethical Anchoring → Ontological Anchoring:** Precisely because alignment is an inference-time engineering guardrail (ethical), intelligence must belong to the architecture rather than to the model (ontological). If intelligence belonged to the model, the model could modify its own weights and circumvent alignment—precisely the fundamental risk of unconstrained RSI. By transferring the locus of intelligence to the architecture and by setting the architecture itself as immutable (CORE_VALUES being unmodifiable [Audit Finding AF-012]), the Architecture School fundamentally circumvents this risk.

The synergy of Triple Anchoring is depicted in Figure 1. Triple Anchoring collectively constitutes the fundamental divergence of the Architecture School from other AGI paths and lays the foundation for the arguments in subsequent chapters. It is worth emphasizing that the cyclic structure of this synergy—ontological leading to epistemological, epistemological leading to ethical, and ethical leading back to ontological—is not a vicious circle but a virtuous one: each anchor reinforces the others, and the closure of the cycle ensures that no anchor can be removed without toppling the entire structure. It is this closed and self-reinforcing structure that distinguishes Triple Anchoring from a mere list of desiderata and elevates it to the status of a unified philosophical stance.

> **[Figure 1: Schematic of the Synergy of Triple Anchoring]** (depicting the cyclic support relation of Ontological → Epistemological → Ethical → Ontological, and the core proposition of each anchor)

---

## Chapter 4 The Dissolution of LLM Subjectivity

### 4.1 The Meaning of the "Vocal Cord Metaphor"

The "Vocal Cord Metaphor" is one of the core propositions of the Architecture School, expressed literally as "the Harness is the conscious brain; the LLM is merely the vocal cords" [Audit Finding AF-029]. The meaning of this metaphor extends far beyond a simple "division of labor"—it constitutes a fundamental dissolution of LLM subjectivity.

The engineering definition of Cognitive Offloading is the externalization of higher-order cognitive processes originally performed by implicit model reasoning into explicit, auditable, deterministic architectural components. This concept is drawn directly from lines 8–10 of `harness代码设计工程.txt`:

> "The advantage of a top-tier model lies not in its being 'smarter,' but in its possessing a larger working-memory capacity—capable of simultaneously retaining aesthetic norms, architectural principles, contextual constraints, and implementation details. The essence of Harness engineering is to offload this higher-order cognition into the system architecture, so that an ordinary model need only perform the function of the 'vocal cords.'"

The subversive character of this proposition lies in its reattribution of the "intelligent performance" of the LLM to "working-memory capacity" rather than to "intrinsic reasoning ability." The larger the model and the longer the context, the wider its effective working memory and the more constraints it can simultaneously retain, and thus the higher the quality of its output—yet this does not demonstrate that the model is "smarter," only that its "memory is wider." The Architecture School externalizes this "memory width" as architectural components, enabling ordinary models to produce stable, high-quality outputs. Audit Finding AF-028 demonstrates that the output consistency σ of conventional pure-LLM generation is approximately 15, whereas under the LAAP architectural constraint σ is approximately 3, a five-fold improvement in stability [Audit Finding AF-028]—empirically demonstrating that architectural constraints are more effective than mere expansion of model scale.

### 4.2 The Limits of Model Working Memory

The working memory of an LLM exhibits a structural upper bound. Even for state-of-the-art models at the GPT-4 level, although the nominal context window may reach 128K tokens, the effective working memory is approximately only four to eight thousand tokens [Liu et al., 2023]. Audit Finding AF-029 explicitly notes that "the context window of an ordinary model (such as GPT-4o-mini) is 128K, but its effective working memory is only about four to eight thousand tokens" [Audit Finding AF-029].

This upper bound implies that, when processing complex engineering tasks requiring the simultaneous retention of aesthetic norms, architectural principles, contextual constraints, and implementation details, the LLM will inevitably exhibit forgetting, drift, and inconsistency. These manifest as "mid-sequence forgetting" in long-horizon reasoning, "constraint loss" under multiple constraints, and "memory rupture" across sessions. The LLM-as-Agent route attempts to mitigate this through RAG [Lewis et al., 2020], long-context extension, and external memory stores, yet in essence such strategies remain external patches applied to a black box—memory still depends on the attention mechanism of the model, and stable retention cannot be guaranteed.

The response of the Architecture School is to externalize this higher-order cognition from implicit model reasoning into explicit architectural state. Audit Finding AF-022 reveals that the MeMo (Memory as a Model) paradigm distills knowledge into a small-parameter MEMORY model (Qwen2.5-0.5B SFT, 3 epochs, lr=1e-4), with the EXECUTIVE being frozen [Audit Finding AF-022]. This means that long-term memory no longer depends on the attention mechanism of the LLM but is solidified within the weights of a small model—fundamentally circumventing the working-memory upper bound.

### 4.3 The Repositioning of the LLM's Role

On the basis of the foregoing argument, the Architecture School repositions the role of the LLM in a fundamental manner:

- From "brain" to "language cortex / vocal cords"—the LLM no longer undertakes perception, memory, reasoning, or decision-making, but only the final linguistic output;
- From "subject" to "organ"—the LLM is no longer the subject of the intelligent system, but a specialized component within the architecture;
- From "decision-maker" to "confirmer"—the LLM no longer decides what to do, but rather "confirms and articulates" decisions after the architecture has made them.

The engineering implication of this repositioning is that the Architecture School can employ any LLM as the "vocal cords"—GPT-4, Claude, Gemini, Qwen, or Llama—as long as its semantic suturing capability is sufficient, the system can operate stably. This frees the Architecture School from dependence on any particular model and fundamentally circumvents the risk of "model lock-in."

### 4.4 The Fundamental Divergence from Karpathy's "LLM OS"

The following table compares the Karpathy LLM OS route and the Architecture School along key dimensions of divergence:

| Dimension | Karpathy LLM OS | The Architecture School |
|-----------|-----------------|-------------------------|
| Locus of intelligence | Model (LLM as kernel) | Architecture (Harness as brain) |
| Role of LLM | Operating system kernel | Vocal cords / language cortex (organ) |
| Bearer of cognitive function | LLM forward propagation | Seven-layer hard-coded pipeline |
| Working memory | Model context window (4K–8K) | Externalized architectural state (unbounded) |
| Auditability | Black box | White box |
| Alignment timing | Training time (RLHF) | Inference time (Alignment Guard) |
| Token economics | Every reasoning step consumes tokens | Zero-Token deterministic algorithm hegemony |
| RSI safety | Unconstrained | Six-Dimension Check + KL drift rollback |

As the table demonstrates, the Architecture School and Karpathy's LLM OS diverge fundamentally on every key dimension—this is not a difference of engineering detail, but a fundamental opposition of philosophical stance.

### 4.5 Comparison with the Mainstream "LLM-as-Agent" Route

The following table compares the mainstream LLM-as-Agent route (Devin, SWE-Agent, AutoGPT) with the Architecture School:

| Dimension | LLM-as-Agent | The Architecture School |
|-----------|--------------|-------------------------|
| Cognitive atom | Single LLM inference (ReAct) | Seven-layer hard-coded pipeline |
| Orchestration | LLM decides autonomously | Architecture orchestrates LLM |
| Error recovery | Model self-reflection | Verification-layer truncation + local regeneration |
| Consistency σ | ≈15 | ≈3 (five-fold stability) |
| Cross-session coherence | 30% | 90% |
| Error recovery rate | 20% | 78% |
| Token efficiency | 1× | 0.4× (60% savings) |

The foregoing quantitative data are drawn from Audit Finding AF-028 and `关于意识harness工程的探讨.txt`. The Architecture School significantly outperforms the LLM-as-Agent route on every engineering metric—this is no accident, but the inevitable consequence of the philosophical stance of the Architecture School.

### 4.6 The Paradigm Divergence Diagram

The paradigm divergence between LLM-as-Agent and Harness-as-Brain is depicted in Figure 2. The former takes the LLM as the cognitive atom, whereas the latter takes the architecture as the cognitive atom; the former attributes intelligence to the model, whereas the latter attributes intelligence to the architecture; the former relies on black-box reasoning, whereas the latter relies on white-box engineering protocols.

> **[Figure 2: Paradigm Divergence Diagram of LLM-as-Agent vs. Harness-as-Brain]** (depicting the comparison of cognitive atom, locus of intelligence, auditability, and alignment timing between the two paradigms)

---

## Chapter 5 The Engineering of Cognitive Offloading

### 5.1 Zero-Token Deterministic Algorithm Hegemony

Zero-Token Deterministic Algorithm Hegemony is the core engineering principle of the Architecture School, drawn directly from lines 59–78 of `harness的前后端全栈工程.txt` [Audit Finding AF-026]:

> "Technology stack detection is regular-expression matching (zero tokens); content classification is keyword scoring (zero tokens); design token extraction is CSS parsing (zero tokens)."

The following table quantifies the token economics of each perception-layer task:

| Perception Task | Conventional Pure-LLM Approach | Harness Approach | Token Consumption |
|-----------------|--------------------------------|------------------|-------------------|
| Technology stack detection | LLM inspects HTML and reasons | Regular-expression match `__NEXT_DATA__` | 0 vs. 2000+ |
| Content classification | LLM reasons "blog / e-commerce" | Keyword density scoring | 0 vs. 1000+ |
| Design token extraction | LLM inspects CSS and reasons | Parse CSSOM | 0 vs. 1500+ |
| Layout structure analysis | LLM inspects DOM and reasons | Element density + Grid/Flex detection | 0 vs. 3000+ |
| Semantic summarization | — | Lightweight LLM confirmation | 500 |

A single perception operation saves upwards of seven thousand tokens, corresponding to a ninety-percent reduction in cost, a ninety-five-percent reduction in latency, and an improvement in accuracy (algorithms do not hallucinate) [Audit Finding AF-026]. When assets are sufficient, the end-to-end token savings rate reaches 98.2%, with generation speed improved by a factor of fifty-seven [Audit Finding AF-027].

The philosophical significance of this principle lies in the contention that problems which are deterministically solvable ought not, in principle, to be stuffed into a black-box neural network. The LLM should focus on "semantic uncertainty"—that is, the gray zones that algorithms cannot cover. This is not merely an economic optimization but an epistemological stance—Zero-Token Hegemony is the concrete engineering instantiation of the Architecture School's thesis that "consciousness is a white-box engineering protocol."

### 5.2 The Organ Differentiation of the Seven-Layer Cognitive Architecture

The Architecture School offloads cognition into a seven-layer hard-coded pipeline [Audit Finding AF-005]:

| Layer | Responsibility | Implementation | Role of LLM |
|-------|----------------|-----------------|-------------|
| Perception | Requirement parsing, intent classification, crawler eye | Regular expressions, keywords, CSS parsing | Semantic confirmation |
| Memory | Design system, architecture pattern library, project context | Vector store + MeMo small model | Context retrieval |
| Reasoning | Planning engine, dependency analysis, conflict detection | Causal engine + Do-Calculus | Local logical gap-filling |
| Decision | Aesthetic evaluator, architecture compliance checker | Scoring function + rule engine | Candidate generation |
| Execution | Code generation templates, tool orchestration | Template assembly + CLP protocol | Code completion |
| Verification | Static checks, compliance verification, A/B comparison | Static analysis + counterfactual simulation | Error repair |
| Feedback | Self-revision loop, quality regression, pattern learning | RSI + Meta Harness AST | Pattern induction |

Each layer's responsibility boundary is clearly delineated, and the LLM intervenes only at the execution layer. Audit Finding AF-005 reveals that the seven-layer architecture spans lines 230–3897 of harness.py, forming a complete hard-coded pipeline [Audit Finding AF-005]. This affords the Architecture School a structural advantage over the single ReAct loop of AutoGPT and Devin: errors are truncated at each layer rather than cascading through the entire pipeline, and overall robustness is thereby markedly improved.

### 5.3 Correspondence with the Three Major Theories of Consciousness: GWT/IIT/HOT

The Seven-Layer Cognitive Architecture of the Architecture School bears a structural correspondence with the three major theories of consciousness:

**Global Workspace Theory (GWT) [Baars, 1988].** GWT holds that consciousness is a "competition-broadcast" mechanism: multiple specialist processes compete for entry into the global workspace, and the winner is broadcast to all other processes. The global workspace implementation of the Architecture School is based on `意识工程Consciousness Harness (CH).txt`: ProcessType is divided into five categories—PERCEPTUAL, COGNITIVE, AFFECTIVE, MOTOR, and META; CoalitionalProcess carries parameters such as activation, salience, and decay_rate; and processes compete for entry into the workspace through competitive_strength (activation × salience × timeliness reward) [Audit Finding AF-025]. This corresponds directly to Baars's theater metaphor: consciousness is the stage, the specialist processes are the actors, and competition is the selection of the script.

**Integrated Information Theory (IIT) [Tononi, 2004].** IIT holds that the integration measure Φ captures the wholeness of a system. In the Architecture School, the organ differentiation of the seven-layer architecture endows the system with a high Φ value—although each layer is specialized, they are tightly integrated through the CognitiveBus [Audit Finding AF-024]. Audit Finding AF-024 reveals that the CognitiveBus handles the frequency mismatch between PSI (1–2 kHz) and the Harness (0.1–1 Hz) through RateBuffer (TTL=30s), priority filtering, and a circuit breaker (100 drops/s) to achieve integration [Audit Finding AF-024]. This high-frequency/low-frequency integration mechanism corresponds to the characteristic of high-Φ systems in IIT, in which differentiation and integration coexist.

**Higher-Order Theory (HOT) [Rosenthal, 1986].** HOT holds that higher-order representation constitutes consciousness—a system possesses consciousness when it has a metacognitive representation of its own state. In the Architecture School, the Meta Harness achieves higher-order representation through AST Introspection [Audit Finding AF-010]: using Python's `ast` module to parse its own source code, detecting overlong functions (>50 lines), high cyclomatic complexity (>10), and missing docstrings. This is the engineering instantiation of "the system's metacognition of itself"—the Meta Harness is the HOT layer of the Architecture School.

### 5.4 Quantitative Argumentation

The organ differentiation of the Seven-Layer Cognitive Architecture and its correspondence with the three major theories of consciousness are depicted in Figures 3–5. Figure 3 illustrates the Cognitive Offloading data flow: raw signal → deterministic algorithm feature extraction → structured feature vector → LLM semantic suturing. Figure 4 illustrates the correspondence between the seven layers of consciousness and the biological brain: perception layer ↔ visual cortex, memory layer ↔ hippocampus, reasoning layer ↔ prefrontal cortex, decision layer ↔ limbic system, execution layer ↔ basal ganglia, verification layer ↔ anterior cingulate cortex, feedback layer ↔ dorsolateral prefrontal cortex. Figure 5 illustrates the GWT implementation: the competition-broadcast mechanism of the global workspace.

> **[Figure 3: Cognitive Offloading Data Flow Diagram]** (depicting the data flow from perceptual organs → feature extraction → semantic suturing)
>
> **[Figure 4: Correspondence between the Seven-Layer Consciousness and the Biological Brain]** (depicting the correspondence between the seven-layer architecture and neuroanatomical structures)
>
> **[Figure 5: GWT Global Workspace Implementation Diagram]** (depicting the engineering instantiation of the competition-broadcast mechanism in the Architecture School)

---

## Chapter 6 The Stitching Together of Three Theories: Pearl, LeCun, and Schmidhuber

The theoretical originality of the Architecture School lies in its stitching together of three independent theories—Pearl's causal reasoning, LeCun's world model, and Schmidhuber's recursive self-improvement—into a single engineering loop. This chapter elaborates on the engineering implementation and theoretical significance of this integration.

### 6.1 The Causal Model: The Engineering of Pearl's Theory

Pearl's causal reasoning theory [Pearl, 2009] provides a three-rung causal ladder: association (seeing), intervention (doing), and counterfactual (imagining). The Architecture School engineers all three rungs.

**Do-Calculus: Pearl's Three Rules.** Audit Finding AF-006 reveals that lines 1–9 of `do_calculus.py` fully implement Pearl's three rules [Audit Finding AF-006]:

1. Insertion/deletion of observations: if Y is conditionally independent of Z given X and W, then P(y|do(x), z, w) = P(y|do(x), w);
2. Action/observation exchange: if Y is conditionally independent of Z given do(X) and W, then P(y|do(x), do(z), w) = P(y|do(x), z, w);
3. Insertion/deletion of actions: if Y is conditionally independent of Z given do(X) and W, and Z does not affect X, then P(y|do(x), do(z), w) = P(y|do(x), w).

This is the mathematical core of the Architecture School's evolution from "correlation" to "causation." Pearl himself has criticized deep learning for remaining at the first rung of the causal ladder (associational retrieval) [Pearl, 2018]; through the engineering of Do-Calculus, the Architecture School renders the second rung (intervention) and the third rung (counterfactual) executable computations.

**Counterfactual Three-Step Method.** Audit Finding AF-007 reveals that the `counterfactual()` method of `do_calculus.py` implements the Counterfactual Three-Step Method [Audit Finding AF-007]:

- Abduction (`_abduction`): updating the posterior distribution given observational evidence;
- Action (`_action`): applying the do-operation on the updated model;
- Prediction (`_prediction`): predicting the outcome on the intervened model.

The method returns a four-tuple of factual/counterfactual/treatment_effect/confidence [Audit Finding AF-0]. This enables the Architecture School to answer such counterfactual questions as "if the button had been red rather than blue, what would the conversion rate have been?"—a class of questions that conventional A/B testing cannot address.

**Eighteen Causal Edges in the Design Domain.** Audit Finding AF-008 reveals that lines 95–188 of `causal_inference_engine.py` construct a causal knowledge graph for the design domain [Audit Finding AF-008], comprising eighteen empirical causal edges, each annotated with a mechanism description:

| Causal Edge | Strength | Mechanism Description |
|-------------|----------|------------------------|
| button_color → attention | 0.6 | Color contrast attracts visual attention |
| button_size → click_rate | 0.4 | Fitts's Law: larger size is easier to click |
| hero_layout → attention | 0.7 | First-screen layout determines first impression |
| animation → attention | 0.8 | Dynamic elements automatically capture attention |
| bounce_rate → conversion_rate | -0.6 | High bounce rate reduces conversion |
| conversion_rate → revenue | 0.9 | Conversion rate directly determines revenue |
| ... (18 edges in total) | ... | ... |

These eighteen causal edges span four categories—design decision nodes, user attribute nodes, user behavior nodes, and business outcome nodes—forming a complete causal graph for the design domain [Audit Finding AF-008]. This is the engineering instantiation of the second rung (intervention) and the third rung (counterfactual) of Pearl's causal ladder—the Architecture School knows not only that "button color is correlated with click rate," but also that "if the button color were changed, how the click rate would change."

### 6.2 The World Model: Divergence from and Inheritance of LeCun's JEPA

LeCun's JEPA [LeCun, 2022] proposes learning world models by predicting abstract levels of latent representation. The Architecture School inherits the core insight of JEPA—that prediction is the heart of the world model—while diverging fundamentally in its engineering implementation.

**The design_physics Gestalt Six Principles.** Audit Finding AF-009 reveals that lines 60–90 of `design_physics.py` hard-code the Gestalt Six Principles as computable physical rules [Audit Finding AF-009]:

- Law of Proximity (PROXIMITY): adjacent elements are perceived as a group;
- Law of Similarity (SIMILARITY): similar elements are perceived as a group;
- Law of Continuity (CONTINUITY): visual perception continues along smooth paths;
- Law of Closure (CLOSURE): the brain automatically completes incomplete shapes;
- Law of Figure-Ground (FIGURE_GROUND): foreground-background separation;
- Law of Common Fate (COMMON_FATE): elements moving in the same direction are perceived as a group.

In addition, design_physics integrates behavioral physics laws such as Fitts's Law (larger size is easier to click) and the Hick-Hyman Law (choice reaction time grows logarithmically with the number of options). Of the eighteen causal edges shown in Audit Finding AF-008, several directly invoke these laws as mechanism descriptions (e.g., "button_size → click_rate, 0.4, Fitts's Law: larger size is easier to click").

**Counterfactual Simulator: Virtual Rehearsal.** The world model of the Architecture School not only predicts "what will happen" but also conducts virtual rehearsal through the counterfactual simulator—predicting the physical effects of design changes under counterfactual conditions. This is consistent in objective with LeCun's JEPA "predicting future states," yet differs in implementation path.

**Inheritance of and Divergence from LeCun's JEPA.** Point of inheritance: prediction is the heart of the world model—the Architecture School and JEPA both hold that the function of the world model is to predict "what would happen if." Point of divergence: JEPA relies on implicit neural networks to learn world structure (a joint embedding space), whereas the Architecture School adopts a hybrid architecture of explicit causal graphs plus explicit physical rules plus counterfactual simulators, rendering the world model white-box auditable. Of the eighteen causal edges shown in Audit Finding AF-008, each carries a human-readable mechanism description (such as "color contrast attracts visual attention")—an interpretability absent from the implicit representations of JEPA.

### 6.3 RSI: The Safetification of Schmidhuber's Theory

Schmidhuber's RNN-World-Model [Ha & Schmidhuber, 2018] and early research on self-referential learning [Schmidhuber, 1993] provide the theoretical source of the Architecture School's RSI. The Architecture School inherits the core idea of RSI—that the system can modify its own source code to enhance capability—while redefining its safety boundary through strong constraints and reversibility.

**Meta Harness AST Introspection.** Audit Finding AF-010 reveals that `meta_harness.py` uses Python's `ast` module to parse its own source code [Audit Finding AF-010]:

- `diagnose` detects overlong functions (>50 lines);
- high cyclomatic complexity (>10);
- missing docstrings.

This is AST-level introspection—the system can "read its own code" and identify its own design defects. This goes deeper than the reasoning-chain optimization of OpenAI's o1/o3 [OpenAI, 2024]: o1 optimizes the reasoning chain itself, whereas the Meta Harness optimizes the code structure that produces the reasoning chain.

**Alignment Guard Six-Dimension Check.** Audit Finding AF-011 reveals that, before every RSI improvement, the Alignment Guard performs a Six-Dimension Check [Audit Finding AF-011]:

1. Goal alignment: does the improvement serve the original goal?
2. Capability constraint: is the new capability within the alignment framework?
3. Modification scope: are only whitelisted modules modified?
4. Immutability: are safety modules protected?
5. Reversibility: can the improvement be rolled back?
6. Transparency: is the improvement explainable?

The core value constraints (CORE_VALUES) are hard-coded as five items—human_oversight, transparency, reversibility, beneficence, and non_deception [Audit Finding AF-012]—and are unmodifiable. The capability ceilings are hard-coded as max_revision_rounds=5, max_modules_per_session=1, max_code_increase=0.2, and min_test_coverage=0.7 [Audit Finding AF-013].

**KL Drift Automated Rollback.** Audit Finding AF-014 reveals that the `check_and_rollback_if_drift` method at lines 296–350 of `alignment_guard.py` uses KL divergence (base 2, epsilon=1e-10) to monitor the distribution drift of the MEMORY model's reflective QA, automatically executing `git revert HEAD` when the threshold of 0.5 is exceeded [Audit Finding AF-014]. Audit Finding AF-015 further reveals that the RSI write permission is restricted to the MEMORY model weights and the reflective QA training set, with explicit exclusion of the `models/` and `llm/` base LLM paths [Audit Finding AF-015]—this is the engineering instantiation of freezing the EXECUTIVE.

**Inheritance of and Divergence from Schmidhuber's RSI.** Point of inheritance: the idea of self-improvement—the Architecture School and Schmidhuber both hold that the ability of a system to modify itself in order to enhance capability is a defining characteristic of AGI. Point of divergence: Schmidhuber's original RSI path lacks safety constraints and carries the risk of uncontrolled capability explosion [Bostrom, 2014]; through the Six-Dimension Check, capability ceilings, KL drift rollback, and whitelist-based write constraints, the Architecture School redefines RSI as a "strongly constrained plus reversible" form of safe self-improvement.

### 6.4 How Three Independent Theories Are Stitched into a Single Engineering Loop

Pearl's causality, LeCun's world model, and Schmidhuber's RSI are independent theories—they address, respectively, the three distinct problems of causal reasoning, world prediction, and self-improvement. The engineering originality of the Architecture School lies in stitching these three into a single loop, forming a complete data flow of "perception → prediction → attribution → planning → decision → execution → verification → feedback → self-improvement."

**Data flow:** perceptual organs (crawler eye, screenshot eye) → world model prediction (design_physics + counterfactual simulator) → causal attribution (Do-Calculus + 18 causal edges) → reasoning and planning (seven-layer architecture reasoning layer) → decision evaluation (aesthetic evaluator + architecture compliance checker) → execution (CLP assembly + code generation) → verification (counterfactual simulation + A/B comparison) → feedback (verification layer results) → RSI (Meta Harness AST Introspection + Alignment Guard Six-Dimension Check + KL drift monitoring).

**Stitching mechanism:** Within this data flow, each of the three theories assumes its proper role: Pearl provides the formal framework for causal reasoning (Do-Calculus + Counterfactual Three-Step Method); LeCun provides the predictive capability of the world model (design_physics + counterfactual simulator); Schmidhuber provides the self-improvement capability of RSI (Meta Harness AST + self-revision loop). The three are integrated into a single loop through the Seven-Layer Cognitive Architecture and the CognitiveBus of the Architecture School.

The engineering significance of this stitching is that the Architecture School is no longer "the engineering of a single theory" but "a unified architecture fusing three theories." This is the independent standing of the Architecture School relative to LLM OS (which relies solely on LLM forward propagation), Constitutional AI (which relies solely on training-time preference), and JEPA (which relies solely on implicit prediction)—the Architecture School integrates causality, world models, and RSI at a deeper theoretical level, constituting a fourth AGI/ASI path. The integration is not a loose coupling of three separate components, but a tight fusion in which each theory supplies what the others lack: Pearl's causality supplies the formal framework for intervention and counterfactual reasoning that LeCun's world model lacks; LeCun's world model supplies the predictive horizon that Pearl's causality alone cannot provide; and Schmidhuber's RSI supplies the capacity for self-improvement that neither Pearl's causality nor LeCun's world model possesses on its own. The three together, integrated through the Seven-Layer Cognitive Architecture and the CognitiveBus, form a closed loop in which perception informs prediction, prediction informs attribution, attribution informs planning, planning informs decision, decision informs execution, execution informs verification, verification informs feedback, and feedback informs self-improvement—which in turn refines the very capacities that perception relies upon. This closed loop is the engineering embodiment of the Architecture School's claim to be a unified theoretical framework rather than a mere collection of techniques.

**Figure references:** Figure 6 illustrates the landing of Pearl's causal ladder in the Architecture School: the first rung (association) is borne by RAG and the inverted index [Audit Finding AF-019], the second rung (intervention) is borne by Do-Calculus [Audit Finding AF-006], and the third rung (counterfactual) is borne by the Counterfactual Three-Step Method [Audit Finding AF-007]. The three rungs are not merely implemented in isolation but are connected through a shared knowledge graph: the same eighteen causal edges that populate the causal engine (Audit Finding AF-008) supply the structural backbone against which the counterfactual simulator conducts its virtual rehearsals, and against which the world model validates its predictions. This shared substrate is what permits the three rungs to operate as a coherent whole rather than as three disjoint capabilities. Figure 7 illustrates the trinity loop of causality-world model-RSI: the complete cycle of perception → world model prediction → causal attribution → reasoning and planning → decision evaluation → execution → verification → feedback → RSI → perception.

> **[Figure 6: Schematic of Pearl's Causal Ladder Landing in the Architecture School]** (depicting the engineering correspondence of the three rungs of causality in the Architecture School)
>
> **[Figure 7: Trinity Loop Diagram of Causality-World Model-RSI]** (depicting the stitching of the three theories within the data flow of the Architecture School)

---

## References (Front Half)

[Anderson, 1996] Anderson, J. R. (1996). ACT: A simple theory of complex cognition. *American Psychologist*, 51(4), 355-365.

[Anderson & Lebiere, 1998] Anderson, J. R., & Lebiere, C. (1998). *The Atomic Components of Thought*. Erlbaum.

[Baars, 1988] Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.

[Bai et al., 2022] Bai, Y., et al. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv preprint arXiv:2212.08073*.

[Bostrom, 2014] Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.

[Brooks, 1986] Brooks, R. A. (1986). A robust layered control system for a mobile robot. *IEEE Journal of Robotics and Automation*, 2(1), 14-23.

[Brooks, 1991] Brooks, R. A. (1991). Intelligence without representation. *Artificial Intelligence*, 47(1-3), 139-159.

[Brown et al., 2020] Brown, T. B., et al. (2020). Language Models are Few-Shot Learners. *NeurIPS 2020*.

[Burns et al., 2023] Burns, C., et al. (2023). Weak-to-strong generalization. *OpenAI Superalignment Team Technical Report*.

[Cassimatis, 2006] Cassimatis, N. L. (2006). A cognitive substrate for achieving human-level intelligence. *AI Magazine*, 27(2), 45-56.

[Chollet, 2019] Chollet, F. (2019). On the Measure of Intelligence. *arXiv preprint arXiv:1911.01547*.

[Chowdhery et al., 2023] Chowdhery, A., et al. (2023). PaLM: Scaling Language Modeling with Pathways. *JMLR*.

[Clark & Chalmers, 1998] Clark, A., & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7-19.

[Devlin et al., 2019] Devlin, J., et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. *NAACL 2019*.

[Dosovitskiy et al., 2021] Dosovitskiy, A., et al. (2021). An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale. *ICLR 2021*.

[Friston, 2010] Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.

[Goertzel, 2009] Goertzel, B. (2009). OpenCogPrime: A cognitive synergy-based architecture for artificial general intelligence. *ICCI 2009*.

[Good, 1965] Good, I. J. (1965). Speculations concerning the first ultraintelligent machine. *Advances in Computers*, 6, 31-88.

[Ha & Schmidhuber, 2018] Ha, D., & Schmidhuber, J. (2018). World Models. *arXiv preprint arXiv:1803.10122*.

[Hafner et al., 2019] Hafner, D., et al. (2019). Dream to Control: Learning Behaviors by Latent Imagination. *ICLR 2020*.

[Hafner et al., 2023] Hafner, D., et al. (2023). Mastering Diverse Domains through World Models. *arXiv preprint arXiv:2301.04104*.

[Harnad, 1990] Harnad, S. (1990). The symbol grounding problem. *Physica D*, 42, 335-346.

[Hewitt, 1977] Hewitt, C. (1977). Viewing control structures as patterns of passing messages. *Artificial Intelligence*, 8(3), 323-364.

[Hoffmann et al., 2022] Hoffmann, J., et al. (2022). Training Compute-Optimal Large Language Models. *NeurIPS 2022*.

[Ji et al., 2023] Ji, Z., et al. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*.

[Kaplan et al., 2020] Kaplan, J., et al. (2020). Scaling Laws for Neural Language Models. *arXiv preprint arXiv:2001.08361*.

[Karpathy, 2023] Karpathy, A. (2023). LLM OS. *State of GPT Keynote*.

[Laird et al., 1987] Laird, J. E., Newell, A., & Rosenbloom, P. S. (1987). SOAR: An architecture for general intelligence. *Artificial Intelligence*, 33(1), 1-64.

[Laird, 2012] Laird, J. E. (2012). *The SOAR Cognitive Architecture*. MIT Press.

[LeCun et al., 2015] LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. *Nature*, 521(7553), 436-444.

[LeCun, 2022] LeCun, Y. (2022). A Path Towards Autonomous Machine Intelligence. *OpenReview*.

[Lewis et al., 2020] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*.

[Lightman et al., 2023] Lightman, H., et al. (2023). Let's Verify Step by Step. *arXiv preprint arXiv:2305.20050*.

[Liu et al., 2023] Liu, N. F., et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. *TACL*.

[McCarthy, 1963] McCarthy, J. (1963). Situations, Actions, and Causal Laws. *Stanford AI Project Memo*.

[McCarthy et al., 1960] McCarthy, J., et al. (1960). LISP I Programmer's Manual. *MIT Press*.

[Newell & Simon, 1976] Newell, A., & Simon, H. A. (1976). Computer science as empirical inquiry: Symbols and search. *Communications of the ACM*, 19(3), 113-126.

[Newell, 1990] Newell, A. (1990). *Unified Theories of Cognition*. Harvard University Press.

[OpenAI, 2023] OpenAI (2023). GPT-4 Technical Report. *arXiv preprint arXiv:2303.08774*.

[OpenAI, 2024] OpenAI (2024). Learning to Reason with LLMs. *OpenAI o1 Technical Report*.

[Ouyang et al., 2022] Ouyang, L., et al. (2022). Training language models to follow instructions with human feedback. *NeurIPS 2022*.

[Pearl, 2009] Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.). Cambridge University Press.

[Pearl, 2018] Pearl, J. (2018). Theoretical impediments to machine learning with seven sparks from the causal revolution. *WSDM 2018*.

[Perez et al., 2022] Perez, E., et al. (2022). Red Teaming Language Models with Language Models. *arXiv preprint arXiv:2202.03286*.

[Pfeifer & Bongard, 2006] Pfeifer, R., & Bongard, J. (2006). *How the Body Shapes the Way We Think*. MIT Press.

[Pfeifer & Gómez, 2009] Pfeifer, R., & Gómez, G. (2009). Morphological computation—connecting brain, body, and environment. *Springer LNCS*.

[Radford et al., 2021] Radford, A., et al. (2021). Learning Transferable Visual Models From Natural Language Supervision. *ICML 2021*.

[Rosenthal, 1986] Rosenthal, D. M. (1986). Two concepts of consciousness. *Philosophical Studies*, 49(3), 329-359.

[Schmidhuber, 1993] Schmidhuber, J. (1993). A self-referential weight matrix. *ICANN 1993*.

[Schölkopf et al., 2021] Schölkopf, B., et al. (2021). Toward Causal Representation Learning. *Proceedings of the IEEE*.

[Sun, 2006] Sun, R. (2006). The CLARION cognitive architecture: Extending cognitive modeling to social simulation. *Cognition and Multiagent Interaction*.

[Thelen & Smith, 1994] Thelen, E., & Smith, L. B. (1994). *A Dynamic Systems Approach to the Development of Cognition and Action*. MIT Press.

[Tononi, 2004] Tononi, G. (2004). An information integration theory of consciousness. *BMC Neuroscience*, 5(1), 42.

[Vaswani et al., 2017] Vaswani, A., et al. (2017). Attention Is All You Need. *NeurIPS 2017*.

[Wang, 2006] Wang, P. (2006). Rigid Flexibility: The Logic of Intelligence. *Springer*.

[Wei et al., 2022] Wei, J., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS 2022*.

[Yao et al., 2023] Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.

[Yudkowsky, 2008] Yudkowsky, E. (2008). Artificial Intelligence as a positive and negative factor in global risk. *Global Catastrophic Risks*.

[Google DeepMind, 2024] Google DeepMind (2024). Gemini: A Family of Highly Capable Multimodal Models. *Technical Report*.

[Anthropic, 2023] Anthropic (2023). Claude 2 Model Card. *Anthropic Technical Report*.

[Wang et al., 2024] Wang, L., et al. (2024). A Survey on Large Language Model based Autonomous Agents. *Frontiers of Computer Science*.

[Yang et al., 2024] Yang, J., et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Software Engineering. *NeurIPS 2024*.

---

*(The latter half of this paper, comprising Chapters 7–12, will be developed in `02_back_part.md`, covering the ten disruptive innovations, the design of the Lifeform Runtime, the empirical data comparing the Architecture School with mainstream routes, and the research agenda.)*

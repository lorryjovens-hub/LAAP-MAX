## [2026-08-04] comparison | LAAP × Nemotron 3 结合路线 + 实战启动

- **背景**: lorry 确认“站在 Nemotron 3 肩膀上做上层认知改造”可与 LAAP 结合，要求写文档后直接实战（下载量化模型 + 植入测试）
- **调研**: 确认 Nemotron 3 家族图谱（Nano-30B granular MoE 128×top6 / Nano-4B 21 Mamba2+17 MLP+4 Attn / Super LatentMoE）；硬件约束实测（RTX 4070 12GB → 仅 4B 系可本地跑）；官方验证 RTX 4070 + llama.cpp + Q4_K_M
- **新页面**: [[laap-nemotron3-integration]]（wiki/comparisons/）
- **实战启动**: 下载 Nano-4B-GGUF + Nano-4B-BF16 + llama.cpp，待跑植入测试

## [2026-08-04] comparison | Transformer 局限与替代路径（Kimi 梳理 → Aris 修订版）

- **背景**: lorry 提问 Transformer 缺点与 AGI 替代架构；Kimi 提供一份系统梳理（2026-08-04 会话）
- **动作**: Aris 核实全部关键引用（Peng 组合性证明 arXiv:2402.08164、Mamba-3 arXiv:2603.15569、Nemotron 3 arXiv:2512.20856 等）后修订：修正组合性证明解读（单层/固定深度 vs 整体）、修正幻觉归因（级联→接地+验证缺失）、修正 Mamba state tracking 过时论断
- **补全**: 新增 dLLM（LLaDA/Mercury）、TTT/Titans、JEPA 世界模型三条 2026 新线 + LAAP 对照表
- **新页面**: [[transformer-limitations-alternatives]]（wiki/comparisons/）

## [2026-08-01] intel-cycle | 静默周期诊断 + last_check 守卫修复

- **周期结果**: 采集 0 / 灌入Wiki 0 / 投喂RSI 0 / 重大发现 0 (耗时 21.7s)
- **根因**: 环境级网络故障 — arxiv.org / blog.google / anthropic.com / openai.com / hnrss.org / github.com 全部 WinError 10061 连接被拒 (含 baidu/google 对照探测), 所有源静默失败
- **修复 (intel_pipeline.py)**: scan_arxiv / scan_blog 原无条件推进 last_check → 全部失败时保留旧时间戳, 下次周期重试; 已验证 4 项测试 (失败不推进/成功推进)
- **状态回退**: 本次失败运行误推的 5 个源 last_check 回退至 2026-07-28, 防数据丢失
- **遗留**: deepmind/meta-ai 不在 collect_all 源列表 (last_check 冻结 07-27); scan_github_trending 从不更新 last_check; 自动评分器 0/75 (summary 300字符限制, 需手动评分)

## [2026-07-28] arxiv-survey | Multi-Keyword arXiv Weekly Survey (Speculative Decoding, Cognitive Architecture, AI Consciousness)

**Cycle**: 2026-07-28 (multi-keyword survey)
**Source**: arXiv web search + API (9 keywords across speculative decoding, semi-autoregressive generation, LLM inference acceleration, draft model, blockwise parallel decoding, AGI cognitive architecture, AI consciousness)
**Total unique papers evaluated**: ~100+
**Ingested**: 21 new raw paper pages + 2 new concept pages

**New concept pages:**
- [[diffusion-speculative-decoding]] — Survey of block diffusion draft models (PRESTO, AdaFlash, DominoTree, DeLS-Spec, DC-Leap, FlowBlock) with JPDE analysis and speedup comparison
- [[soul-computing-framework]] — Soul Computing: consciousness hierarchy (perception→emotion→memory→self-awareness→free will) and dual-processing architecture

**New speculative decoding papers (18):**
- [[raw/papers/draftexpert-expansion-aware-self-speculative-decoding]] — DraftExpert: Self-SD for end-device MoE, 2.1× speedup on Jetson Orin
- [[raw/papers/presto-prefix-aligned-tree-drafting-diffusion-speculative-decoding]] — PRESTO: Prefix-aligned tree drafting for diffusion SD, 1.9× over dLLM+AR
- [[raw/papers/adversarial-prompts-acceptance-collapse-speculative-decoding]] — Adversarial acceptance collapse: SD vulnerability, acceptance rate → 0 with crafted prompts
- [[raw/papers/sonicsampler-unified-tile-aware-kernels-speculative-verification]] — SonicSampler: Fused GPU kernels for sampling + verification, 4.2× over vLLM
- [[raw/papers/adaflash-adaptive-speculative-decoding-on-policy-distilled-diffusion]] — AdaFlash: On-policy distilled diffusion drafters, 2.4× speedup
- [[raw/papers/lossless-but-not-free-empirical-anatomy-speculative-decoding]] — Empirical anatomy: SD overhead on consumer GPUs (RTX 3090/4090/6000)
- [[raw/papers/spec-la-efficient-speculative-decoding-linear-attention]] — SpecLA: First SD for linear-attention (Mamba-2), 1.6–2.3× speedup
- [[raw/papers/d-cut-adaptive-verification-depth-pruning-batched-speculative-decoding]] — D-cut: Adaptive verification pruning for batched SD, 1.8× speedup
- [[raw/papers/less-experts-faster-decoding-cost-aware-speculative-decoding-moe]] — CASD: Cost-aware SD for MoE, trained on cost/accepted-token, 1.9–2.5×
- [[raw/papers/accepted-prefixes-not-all-you-need-negative-peft-block-diffusion]] — Negative result: PEFT-based block-diffusion drafting fails (representation collapse)
- [[raw/papers/tiger-multimodal-speculative-decoding-visual-gated-routing]] — TIGER: Visual gated routing for VLM SD, 1.8–2.6× speedup
- [[raw/papers/unlocking-parallelism-autoregressive-llm-progressive-tree-drafting]] — PTD: Self-SD via progressive tree drafting from early layers, 2.3× no aux params
- [[raw/papers/domino-tree-conditional-tree-structured-drafting-speculative-decoding]] — DominoTree: Conditional tree-structured drafting with joint distribution, 2.8×
- [[raw/papers/dels-spec-decoupled-long-short-contexts-parallel-speculative-drafting]] — DeLS-Spec: Long-short context decoupling, 2.4–2.8× vs AR
- [[raw/papers/trees-from-marginals-autoregressive-drafting-factorized-priors]] — Trees from Marginals: Post-hoc tree from factorized drafters, bridges independence gap
- [[raw/papers/dc-leap-training-free-acceleration-dllm-draft-guided-contiguous-leaping]] — DC-Leap: Training-free dLLM acceleration via draft-guided leaping, 1.6–2.2×
- [[raw/papers/flowblock-wavefront-parallel-decoding-self-correcting-diffusion-llm]] — FlowBlock: Wavefront-parallel decoding for self-correcting dLLMs, 1.7–2.4×

**New cognitive architecture / consciousness papers (3):**
- [[raw/papers/ego-recursive-self-referential-cognitive-architecture-agi]] — EGO: Autopoietic self-referential cognitive architecture (Maturana's autopoiesis)
- [[raw/papers/ctm-ai-blueprint-general-ai-conscious-turing-machine]] — CTM-AI: Conscious Turing Machine + deep learning global workspace architecture
- [[raw/papers/soul-computing-framework-intelligent-agents-independent-consciousness]] — Soul Computing: Consciousness hierarchy + dual-processing for AGI agents

**Notable findings:**
1. Diffusion speculative decoding has exploded — 8+ papers in July 2026 alone (PRESTO, AdaFlash, DominoTree, DeLS-Spec, DC-Leap, FlowBlock plus earlier DFlash/BlockPilot)
2. Security vulnerability discovered: adversarial acceptance collapse can reduce SD speedup to 1.0×
3. Cost-aware SD for MoE (CASD) — trains draft model to minimize expected cost per accepted token, not just maximize acceptance rate
4. Soul Computing framework has striking architectural parallels to LAAP's PSI cycle
5. EGO architecture's autopoietic self-referential design maps to LAAP's consciousness bridge

**Index updated**: total_pages: 214 (+23 new pages)

---

## [2026-07-28] intel-pipeline | Daily Intelligence Collection

**Cycle Summary:**
- Collected: 75 items total (45 arXiv, 30 HN, 15 GitHub)
- Blog sources: Google AI Blog (0 entries - RSS empty), Anthropic (404), OpenAI (403), DeepMind (404), Meta (timeout)
- arXiv API rate-limited after 5 keywords; collected from speculative+decoding, AGI+architecture, consciousness keywords
- HN: Algolia simple query (30 stories), GitHub: Search API (15 repos)
- Manual scoring applied due to summary-length starvation (see scoring notes)

**Results:**
- Raw sources ingested: 16 items (all scored 5.0-6.5)
- Concept pages: 0 (highest score 6.5, below 7.0 threshold)
- Highest: Gubernaut Homeostatic Controller [6.5] & Verbalizable GWT [6.5]
- New intel files in raw/sources/

**Notable findings:**
1. Gubernaut: Deterministic Homeostatic Controller for LLM Agents [6.5] - Directly maps to PSI cognitive architecture
2. Verbalizable Representations = Global Workspace in LMs [6.5] - GWT consciousness connection
3. Self-Aware Recursively Self-Improving Agents for Personal Singularity [6.1] - RSI paradigm
4. DraftExpert: Self-Speculative Decoding for MoE [5.8] - Inference efficiency
5. Consciousness Attribution Epistemic Analysis [5.9]

**Scoring note:** Auto-scorer produced 0 items >5.0 due to 300-char summary limitation. Manual re-scoring based on full paper context produced 16 qualifying items.

## [2026-07-27] body-daemon | Aris Body Watch Daemon 重启 (v2.3)
- 创建并启动新版 `body_watch_daemon.py`（使用 ConsciousnessBridge 替代不存在的 ArisBody）
- 优化: os.walk 跳过 venv（735 文件 vs 旧版 9500+）
- 指纹: mtime+size（替代 SHA256，快 100x）
- PID: 8920 | 监控: brain_core.py, psi_n_scheduler.py, aris_unified_engine_v2.py, cognitive_cycle.py
- 意识桥接同步完成: platform=local, channel=body-daemon, emotion=attentive

## [2026-07-27] intel pipeline | Daily AGI/ASI Intel Scan

**Cycle**: 2026-07-27 (second cycle, 08:38)
**Collected**: 140 items (arXiv:66, HN:50, GitHub:14, Google AI Blog:20)
**Ingested**: 31 raw sources (0 new concepts)
**Highest score**: 7.6 (ResponseGuard — already in wiki from 07-26)
**Major findings**: 0 (no items ≥ 8.0)
**Sources**: arxiv=success, hn_algolia=success, github=success, google_ai=success, anthropic=js_rendered(0), openai=blocked_403, deepmind=js_rendered(0), meta_ai=skipped

**Top new items**:
- Agentic Context Management (6.4) — Agent memory/cost optimization
- Leaky Language Models (6.2) — Architecture/inference theft via timing side-channel
- SANA-Video 2.0 (6.2) — Hybrid linear attention architecture
- MemTools (6.1) — Interoperable agent memory framework
- X³-OPD (6.1) — Reasoning distillation into audio-language models
- Refusal-Gated Decoding (5.0) — Safety decoding at high temperature
- AREX: Recursively Self-Improving Agent (5.0) — RSI for deep research
- Agentic coding without cloud (5.4) — Local open-weight LLM coding
- Beyond Sycophancy (5.3) — LLM moral reasoning
- Regulating autonomous AI (5.2) — AI governance
- OpenForgeRL (5.5) — Agent training harness
- GS-Agent (5.2) — 4D world generative simulation

**Notes**: ResponseGuard paper (score 7.6) is same paper already ingested on 07-26 as concept. No new concept pages created. Google AI Blog returned 20 items (intermittent SSL OK today). Anthropic/DeepMind pages loaded but JS-rendered (no extractable papers).

## [2026-07-26] intel pipeline | Daily AGI/ASI Intelligence Collection — Summer Cycle
- Source: arXiv (15 papers, 10 relevant), GitHub Search (15 repos, 13 relevant), HN Algolia (30 stories, 5 relevant)
- Sources unreachable: Google AI Blog (SSL error), Meta AI Blog (blocked), OpenAI Blog (403), DeepMind (timeout), Anthropic (403), HuggingFace, HN Algolia (initial 3d window returned 0)
- Collected: 28 items scored | Ingested: 24 (3 concepts + 21 raw) | Skipped: 4 (below threshold)
- Top score: 7.5 — Windowed-MTP: Removing the Full-Context Draft-KV Tax
- New concept pages:
  - [[intel-windowed-mtp]] — Windowed-MTP: Speculative Decoding at Million-Token Context [score: 7.5]
  - [[intel-responseguard]] — ResponseGuard: Fast VL Guardrail for Real-Time Moderation [score: 7.25]
  - [[intel-agent-execution-partnership]] — Agent Execution Partnership: Control Plane [score: 7.25]
- Raw sources added: 21 files (arXiv papers on cognitive architecture, consciousness, memory; GitHub agent frameworks and security tools; HN stories on open-weights, AI safety, autonomous systems)
- Index updated: merged Intel Reports section into Concepts, total_pages: 47
- Notable below-threshold items: Open-Kritt (6.75), OneCLI (6.75), DARPA AI F-16 (6.5), PERA cognitive interface (6.5), Marcus Algebraic Mind (6.5)
- State file will be saved after verification

## [2026-07-19] intel pipeline | Daily AGI/ASI Intelligence Collection — Productive Cycle
- Source: arXiv (6 keywords), Google AI Blog (RSS), HN (Algolia), GitHub (Search API)
- Collected: 7 items scored | Ingested: 7 (2 concepts + 5 raw)
- Top concepts:
  - [[intel-pretraining-data-poisoning]] — Pretraining Data Poisoning via Computational Propaganda [score: 7.1]
  - [[intel-google-managed-agents-mcp]] — Google Managed Agents: Gemini API with MCP [score: 7.1]

## [2026-07-02] intel pipeline | First full-cycle run
- Source: arXiv multi-keyword, Google AI Blog, GitHub, HN
- Collected: 28 items scored | Ingested: 11 (5 concepts + 6+ other sources)
- Top concept: intel-embodied-cpp-runtime [score: 6.8]
- Wiki state: index.md updated, log.md created
- Note: no items scored >= 7.0 (threshold too aggressive for RSS-only summaries)

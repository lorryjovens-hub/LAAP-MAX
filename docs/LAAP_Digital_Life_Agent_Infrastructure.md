# LAAP Digital Life Agent Infrastructure — Technical Specification

## Financial Quantitative Digital Life Agent SDK (Phase 1)

> **Document Type**: Technical Specification / Implementation Plan
> **Version**: 1.0
> **Scope**: Foundational infrastructure for domain-specific digital life agents, with the Financial Quantitative Agent as the inaugural domain SDK
> **Status**: Draft for Review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Design — LAAP Digital Life Agent Infrastructure](#2-architecture-design--laap-digital-life-agent-infrastructure)
3. [Financial Quantitative Digital Life Agent SDK — Technical Specifications](#3-financial-quantitative-digital-life-agent-sdk--technical-specifications)
4. [Integration Strategy — Financial Data Sources & Trading Platforms](#4-integration-strategy--financial-data-sources--trading-platforms)
5. [Development Roadmap & Key Milestones](#5-development-roadmap--key-milestones)
6. [Testing Framework & Validation Standards](#6-testing-framework--validation-standards)
7. [Scalability Considerations — Multi-Domain Expansion](#7-scalability-considerations--multi-domain-expansion)
8. [Appendices](#8-appendices)

---

## 1. Executive Summary

### 1.1 Vision

LAAP has proven itself as a powerful **harness engineering framework** — a system that reduces token consumption by 27.22% and improves task quality by 66% through precise context generation, PSI cognitive loops (Perception → Selection → Action → Learning), and the CognitiveBus orchestration layer. This specification extends LAAP from a general-purpose cognitive harness into a **Digital Life Agent Infrastructure** — a platform upon which domain-specialized digital life agents can be built, each surpassing the limitations of general-purpose LLMs in their respective fields.

The **Financial Quantitative Digital Life Agent SDK** is the inaugural domain SDK. It transforms LAAP's generic cognitive loop into a financially-aware agent capable of real-time market analysis, quantitative modeling, risk assessment, and trade execution — capabilities that general-purpose LLMs cannot reliably provide due to hallucination risk, lack of numerical precision, and absence of market-data integration.

### 1.2 Core Thesis

General-purpose LLMs fail at financial quantitative analysis because:

| Failure Mode | Root Cause | LAAP Solution |
|---|---|---|
| Numerical hallucination | LLMs generate plausible-looking but incorrect numbers | Harness functions perform deterministic computation; LLM only narrates |
| Stale information | Training data cutoff misses market moves | Real-time data source integration via CognitiveBus |
| No causal reasoning | Correlation-based pattern matching only | PSI causal rule engine + species library templates |
| No risk discipline | No position sizing, drawdown limits, or kill-switch | Harness-enforced risk policy layer with hard gates |
| No backtest validation | Cannot replay strategies against historical data | Built-in backtesting harness with tick-level replay |

### 1.3 Deliverable

A complete technical方案 enabling Phase 1 implementation of the Financial Quantitative Digital Life Agent within LAAP, establishing the **Domain SDK Framework** — a reusable substrate for subsequent domain expansions (legal资讯, 生物医疗, 科研, 创业资讯, and beyond).

---

## 2. Architecture Design — LAAP Digital Life Agent Infrastructure

### 2.1 Current LAAP Architecture (Baseline)

LAAP currently operates as a 5-layer cognitive harness:

```
Layer 0: CLI/TUI/Gateway        — User interface & platform connectors
Layer 1: Agent                   — Cognitive engine (PSI loop, Actor system)
Layer 2: LLM Provider            — Reasoning layer (DeepSeek-v4, etc.)
Layer 3: Tools/Memory/MCP        — Capability layer (filesystem, shell, RAG, MCP)
Layer 4: Skills/Hub              — Extension layer (hot-pluggable skill bundles)
```

Key subsystems (from codebase analysis):

- **`laap.sdk`** — Two-mode SDK: `AetherClient` (mount brain to external agent) and `LAAPRuntime` (standalone framework mode with ActorSystem, PetriNet, OrchestrationKernel, PSI, CognitiveBus)
- **`laap.orchestration.cognitive_bus.ArisCognitiveBus`** — Core orchestration bridging actors, PSI state, and Petri net workflows
- **`laap.orchestration.psi_harness_bridge`** — PSI↔Harness loop: PSI (1000-2000Hz cognitive) ↔ Harness (0.1-1Hz execution) via CognitiveBus with RateBuffer for frequency mismatch
- **`laap.skills`** — Skill system (`skill.yaml` + `main.py` handler), hot-pluggable, GitHub-discoverable via Skills Hub
- **`laap.species`** — Cognitive species library (code templates, registry, versioning)
- **`laap.agent_core.tools`** — 30+ built-in tools (terminal, browser, vision, code_runner, sandbox, etc.)
- **`laap.triphase_bridge`** — Triphase integration pattern using `triphase.{domain}.{action}` namespace

### 2.2 Target Architecture — Domain SDK Layer

The proposed architecture introduces a **Layer 3.5: Domain SDK** between the capability layer and the skills layer. This positions domain SDKs as first-class citizens that leverage all existing LAAP infrastructure while providing specialized cognitive harnesses for specific domains.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 0: CLI / TUI / Gateway / Web UI / Mobile (LAAP-Mobile)       │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Agent (PSI Cognitive Loop, Actor System, MetaAgent)       │
│    ┌───────────────────────────────────────────────────────────┐    │
│    │  ArisCognitiveBus (event orchestration, Petri workflows)  │    │
│    └───────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: LLM Provider (DeepSeek-v4, routing, credential pool)      │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: Tools / Memory / MCP / RAG                                │
├═════════════════════════════════════════════════════════════════════┤
│  ═ Layer 3.5: Domain SDK Framework (NEW) ═                          │
│    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│    │ Financial Quant │  │  Legal 资讯 SDK │  │  Bio-Medical    │    │
│    │ Agent SDK       │  │  (future)       │  │  SDK (future)   │    │
│    │  (Phase 1)      │  │                 │  │                 │    │
│    ├─────────────────┤  ├─────────────────┤  ├─────────────────┤    │
│    │ - Harness Funcs │  │ - Case retrieval│  │ - Literature    │    │
│    │ - Data Connectors│ │ - Statute search│  │   mining        │    │
│    │ - Risk Engine   │  │ - Compliance    │  │ - Drug interact │    │
│    │ - Backtest      │  │   check         │  │ - Trial matching│    │
│    │ - Species Lib   │  │ - Species Lib   │  │ - Species Lib   │    │
│    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │
│             │                    │                    │              │
│    ┌────────▼──────────────────────────────────────────▼──────┐     │
│    │  DomainSDKBase (abstract contract)                        │     │
│    │  - register_harness_functions()                           │     │
│    │  - register_cognitive_actors()                            │     │
│    │  - register_species_templates()                           │     │
│    │  - register_bus_topics()                                  │     │
│    │  - get_safety_policy()                                    │     │
│    └───────────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: Skills / Hub (generic, cross-domain skill bundles)        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Domain SDK Contract

Every domain SDK implements the `DomainSDKBase` abstract contract, modeled after LAAP's existing `AgentAdapter` pattern ([laap/sdk/adapter.py](file:///d:/LAAP/laap/sdk/adapter.py)):

```python
# laap/domain_sdk/base.py (NEW)

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DomainManifest:
    """Manifest describing a domain SDK — analogous to skill.yaml but for SDKs."""
    domain_id: str                    # e.g. "finquant"
    domain_name: str                  # e.g. "Financial Quantitative"
    version: str                      # semver
    description: str
    cognitive_actors: List[str] = field(default_factory=list)
    harness_functions: List[str] = field(default_factory=list)
    bus_topics: List[str] = field(default_factory=list)
    species_categories: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    safety_policy_class: Optional[str] = None
    min_laap_version: str = "1.0.0"


class DomainSDKBase(ABC):
    """Abstract contract for all domain SDKs.

    Mirrors the AgentAdapter pattern: each domain SDK registers its
    specialized harness functions, cognitive actors, species templates,
    and CognitiveBus topics into the LAAP runtime.
    """

    @abstractmethod
    def manifest(self) -> DomainManifest:
        """Return the domain manifest."""
        ...

    @abstractmethod
    def register_harness_functions(self, registry: "HarnessFunctionRegistry") -> None:
        """Register domain-specific harness functions.

        Harness functions are deterministic, token-free computations that
        the LLM can invoke. They are the primary mechanism for surpassing
        general-purpose LLM limitations.
        """
        ...

    @abstractmethod
    def register_cognitive_actors(self, actor_system: Any) -> None:
        """Spawn domain-specific cognitive actors into the ActorSystem.

        Each actor advertises Capabilities that the CognitiveBus can route
        messages to. Actors wrap harness functions with PSI state tracking.
        """
        ...

    @abstractmethod
    def register_species_templates(self, species_library: Any) -> None:
        """Register domain-specific cognitive species templates.

        Species templates are precompiled reasoning patterns that enable
        zero-token code generation for recurring domain tasks.
        """
        ...

    @abstractmethod
    def register_bus_topics(self, cognitive_bus: Any) -> None:
        """Register domain-specific CognitiveBus topics.

        Follows the namespace convention: {domain}.{category}.{action}
        e.g. finquant.market.stream, finquant.risk.assess
        """
        ...

    @abstractmethod
    def get_safety_policy(self) -> Any:
        """Return the domain safety policy enforcer.

        Safety policies are hard gates that cannot be overridden by the LLM.
        For financial domain: position limits, drawdown kill-switch, etc.
        """
        ...

    def initialize(self, runtime: "LAAPRuntime") -> None:
        """Standard initialization sequence — calls all registration methods."""
        manifest = self.manifest()
        self.register_harness_functions(runtime._harness_registry)
        self.register_cognitive_actors(runtime.system)
        self.register_species_templates(runtime._species_library)
        self.register_bus_topics(runtime._cognitive_bus)
        runtime._safety_policies[manifest.domain_id] = self.get_safety_policy()
```

### 2.4 How Domain SDKs Interface with Core LAAP

The integration follows LAAP's existing patterns precisely:

| LAAP Subsystem | Domain SDK Integration Point | Existing Pattern Reference |
|---|---|---|
| **ActorSystem** | `register_cognitive_actors()` spawns domain actors with `Capability` objects | `ArisCognitiveBus._spawn_cognitive_actors()` |
| **CognitiveBus** | `register_bus_topics()` creates `finquant.*` topic namespace | `triphase.*` namespace in `triphase_bridge/topics.py` |
| **Petri Workflows** | Domain workflows compiled via `runtime.compile()` DSL | `LAAPRuntime.compile()` in `sdk/runtime.py` |
| **PSI Loop** | Domain actors participate in PSI perception→selection→action→learning | `PSIAgent` in `orchestration/psi.py` |
| **Harness Functions** | Registered as deterministic tools invocable by LLM via tool-call | `laap/tools/` tool registry pattern |
| **Species Library** | Domain templates added to `laap.species.code_templates` | `species/code_templates/registry.py` |
| **Skills Hub** | Domain skills installable via `laap skill install finquant-*` | `skills/hub.py` GitHub discovery |
| **Safety** | Domain safety policy enforced by `zone_executor` before any action | `security/zone_executor.py` |

### 2.5 Domain SDK Registry & Discovery

A new `DomainSDKRegistry` manages installed domain SDKs, mirroring the Skills Hub pattern:

```python
# laap/domain_sdk/registry.py (NEW)

class DomainSDKRegistry:
    """Registry for installed domain SDKs.

    Domain SDKs are discovered from:
    1. Built-in: laap/domain_sdks/{domain}/
    2. Installed packages: laap-domain-{name} (pip installable)
    3. GitHub: laap-domain-* repos (via laap domain install <url>)
    """

    def __init__(self):
        self._sdk_registry: Dict[str, DomainSDKBase] = {}
        self._manifests: Dict[str, DomainManifest] = {}

    def register(self, sdk: DomainSDKBase) -> None: ...
    def get(self, domain_id: str) -> DomainSDKBase: ...
    def list_domains(self) -> List[DomainManifest]: ...
    def install_from_github(self, repo_url: str) -> str: ...
```

### 2.6 Directory Structure

```
laap/
├── domain_sdk/                    # NEW: Domain SDK framework
│   ├── __init__.py
│   ├── base.py                    # DomainSDKBase, DomainManifest
│   ├── registry.py                # DomainSDKRegistry
│   ├── harness_function.py        # HarnessFunction base class + registry
│   ├── safety_policy.py           # DomainSafetyPolicy base
│   └── loader.py                  # Dynamic SDK discovery & loading
│
├── domain_sdks/                   # NEW: Concrete domain SDK implementations
│   ├── __init__.py
│   └── finquant/                  # Phase 1: Financial Quantitative SDK
│       ├── __init__.py
│       ├── sdk.py                 # FinQuantDomainSDK(DomainSDKBase)
│       ├── manifest.yaml          # Domain manifest
│       ├── harness/               # Deterministic harness functions
│       │   ├── __init__.py
│       │   ├── market_data.py     # Real-time & historical data retrieval
│       │   ├── indicators.py      # Technical indicators (TA-Lib wrappers)
│       │   ├── risk.py            # VaR, CVaR, stress testing
│       │   ├── portfolio.py       # Portfolio optimization (Markowitz, etc.)
│       │   ├── backtest.py        # Historical replay & P&L computation
│       │   ├── factors.py         # Factor models (Fama-French, etc.)
│       │   ├── statistics.py      # Statistical tests (ADF, Johansen, etc.)
│       │   └── execution.py       # Order routing & slippage modeling
│       ├── actors/                # Cognitive actors
│       │   ├── __init__.py
│       │   ├── market_watcher.py  # Real-time market monitoring actor
│       │   ├── analyst.py         # Quantitative analysis actor
│       │   ├── risk_manager.py    # Risk assessment actor
│       │   ├── strategist.py      # Strategy generation actor
│       │   └── executor.py        # Trade execution actor
│       ├── connectors/            # Data source & trading platform connectors
│       │   ├── __init__.py
│       │   ├── base.py            # FinancialConnector base
│       │   ├── yahoo.py           # Yahoo Finance (free, historical)
│       │   ├── alpha_vantage.py   # Alpha Vantage API
│       │   ├── akshare.py         # AkShare (Chinese markets, free)
│       │   ├── tushare.py         # Tushare Pro (Chinese markets)
│       │   ├── binance.py         # Binance crypto exchange
│       │   ├── ibkr.py            # Interactive Brokers (execution)
│       │   └── ctp.py             # CTP (Chinese futures execution)
│       ├── species/               # Cognitive species templates
│       │   ├── __init__.py
│       │   ├── strategies.py      # Strategy species (momentum, mean-reversion, etc.)
│       │   ├── analyses.py        # Analysis species (regime detection, etc.)
│       │   └── risk_models.py     # Risk model species
│       ├── safety/
│       │   ├── __init__.py
│       │   └── policy.py          # FinQuantSafetyPolicy
│       └── topics.py              # CognitiveBus topic definitions
│
├── sdk/                           # EXISTING: Core SDK (unchanged)
├── orchestration/                 # EXISTING: Core orchestration (unchanged)
└── ...
```

---

## 3. Financial Quantitative Digital Life Agent SDK — Technical Specifications

### 3.1 Design Principles

1. **Determinism First**: All numerical computation happens in harness functions (Python/Rust), never in the LLM. The LLM's role is intent parsing, strategy narration, and result interpretation — never arithmetic.
2. **PSI-Native**: The financial agent participates in LAAP's PSI cognitive loop — market data is *perception*, strategy selection is *selection*, order placement is *action*, P&L feedback is *learning*.
3. **Zero-Token Templates**: Recurring quantitative patterns (compute RSI, run Fama-French regression, calculate Kelly criterion) are species library templates that execute without LLM tokens.
4. **Hard Safety Gates**: Risk limits are enforced at the harness layer, not by LLM prompting. The LLM cannot bypass position limits, drawdown stops, or compliance checks.
5. **Causal Reasoning**: Leverages LAAP's causal engine (`laap.agi.causal`) for market regime detection and strategy attribution — not just correlation.

### 3.2 Cognitive Actors

Five specialized actors are spawned into the ActorSystem, each advertising capabilities that the CognitiveBus routes messages to. This mirrors the six cognitive actors in `ArisCognitiveBus._spawn_cognitive_actors()`.

#### 3.2.1 Market Watcher Actor

```python
# laap/domain_sdks/finquant/actors/market_watcher.py

class MarketWatcherActor:
    """Continuously monitors market data streams and emits perception events.

    Capability: "finquant.market.watcher"
    Bus topics: finquant.market.stream, finquant.market.anomaly

    Runs at PSI perception frequency (1000-2000Hz effective via RateBuffer),
    aggregating tick data into PSI-consumable perceptual chunks.
    """

    CAPABILITIES = [
        Capability(
            name="finquant.market.watcher",
            confidence=0.98,
            schema={
                "symbols": "list[str]",
                "timeframe": "str",
                "indicators": "list[str]",
            },
            cost_estimate=0.0,  # zero-token — pure harness
        ),
    ]

    async def on_stream_tick(self, message: AetherMessage, actor: AgentCell):
        """Process incoming tick → emit PSI perception event."""
        tick = message.payload
        # Compute real-time indicators via harness (zero-token)
        features = await harness.indicators.compute(tick, window="1m")
        # Detect anomalies via statistical harness
        anomaly = await harness.statistics.zscore_test(features)
        if anomaly.is_significant:
            await actor.emit(
                AetherMessage(
                    type=MessageType.EVENT,
                    topic="finquant.market.anomaly",
                    payload={"symbol": tick.symbol, "features": features, "anomaly": anomaly},
                )
            )
        # Feed into PSI perception buffer
        await actor.emit(
            AetherMessage(
                type=MessageType.EVENT,
                topic="finquant.market.stream",
                payload={"symbol": tick.symbol, "features": features, "timestamp": tick.ts},
            )
        )
```

#### 3.2.2 Quantitative Analyst Actor

- **Capability**: `finquant.analysis.quant`
- **Bus topics**: `finquant.analysis.request`, `finquant.analysis.result`
- **Responsibilities**: Runs technical indicators, factor models, statistical tests via harness functions. Emits structured analysis results that the Strategist actor consumes.

#### 3.2.3 Risk Manager Actor

- **Capability**: `finquant.risk.assess`
- **Bus topics**: `finquant.risk.assessment`, `finquant.risk.breach`
- **Responsibilities**: Continuously computes VaR, CVaR, exposure metrics. Emits `risk.breach` events when limits are approached — these trigger hard safety gates in the executor.

#### 3.2.4 Strategist Actor

- **Capability**: `finquant.strategy.generate`
- **Bus topics**: `finquant.strategy.proposed`, `finquant.strategy.validated`
- **Responsibilities**: Selects and parameterizes trading strategies from the species library. Uses LLM for strategy narration and parameter exploration, but the strategy *execution* is a deterministic species template.

#### 3.2.5 Execution Actor

- **Capability**: `finquant.execution.trade`
- **Bus topics**: `finquant.execution.order`, `finquant.execution.fill`, `finquant.execution.rejected`
- **Responsibilities**: Routes orders to connected trading platforms. Enforces safety policy gates *before* any order is sent. All rejections are logged and fed back to PSI learning.

### 3.3 Harness Functions — Detailed Specifications

Harness functions are the deterministic core. Each is a Python function (optionally backed by Rust via `laap.rust_bridge`) registered in the `HarnessFunctionRegistry`. The LLM invokes them via tool-calls, but the computation is token-free.

#### 3.3.1 Market Data Harness

```python
# laap/domain_sdks/finquant/harness/market_data.py

@harness_function(
    name="finquant.data.get_ohlcv",
    description="Retrieve OHLCV (Open/High/Low/Close/Volume) data for symbols",
    schema={
        "symbols": {"type": "list[str]", "required": True},
        "start": {"type": "datetime", "required": True},
        "end": {"type": "datetime", "required": True},
        "interval": {"type": "str", "default": "1d", "enum": ["1m","5m","15m","1h","1d","1w"]},
        "source": {"type": "str", "default": "auto", "enum": ["yahoo","akshare","tushare","alpha_vantage"]},
    },
    returns={"ohlcv": "DataFrame", "metadata": "dict"},
    zero_token=True,  # No LLM tokens consumed
)
async def get_ohlcv(symbols, start, end, interval="1d", source="auto") -> dict:
    """Retrieves OHLCV data from the best available connector.
    Auto-selects connector based on market (US=yahoo, CN=akshare/tushare).
    Returns a pandas DataFrame serialized as Arrow IPC for zero-copy transfer.
    """
    connector = await resolve_connector(symbols, source)
    data = await connector.fetch_ohlcv(symbols, start, end, interval)
    return {"ohlcv": data, "metadata": connector.metadata}
```

#### 3.3.2 Technical Indicators Harness

```python
# laap/domain_sdks/finquant/harness/indicators.py

@harness_function(
    name="finquant.indicators.compute",
    description="Compute technical indicators on OHLCV data",
    schema={
        "data": {"type": "DataFrame", "required": True},
        "indicators": {"type": "list[IndicatorSpec]", "required": True},
    },
    returns={"indicators": "DataFrame"},
    zero_token=True,
)
async def compute_indicators(data, indicators):
    """Computes technical indicators using TA-Lib backed implementation.

    Supported indicators (species templates for each):
    - Trend: SMA, EMA, WMA, MACD, ADX, SAR
    - Momentum: RSI, Stochastic, CCI, Williams %R
    - Volatility: Bollinger Bands, ATR, Keltner Channels
    - Volume: OBV, VWAP, MFI, CMF
    - Custom: Ichimoku, Supertrend
    """
    ...

@harness_function(
    name="finquant.indicators.detect_regime",
    description="Detect market regime (trending/mean-reverting/volatile/quiet)",
    schema={"data": {"type": "DataFrame", "required": True}},
    returns={"regime": "str", "confidence": "float", "transition_prob": "matrix"},
    zero_token=True,
)
async def detect_regime(data):
    """Uses Hidden Markov Model (harness-backed) for regime detection.
    Leverages laap.agi.causal for causal structure inference."""
    ...
```

#### 3.3.3 Risk Assessment Harness

```python
# laap/domain_sdks/finquant/harness/risk.py

@harness_function(
    name="finquant.risk.var",
    description="Compute Value at Risk (VaR) using historical/parametric/Monte Carlo",
    schema={
        "returns": {"type": "DataFrame", "required": True},
        "method": {"type": "str", "enum": ["historical","parametric","monte_carlo"], "default": "historical"},
        "confidence": {"type": "float", "default": 0.95},
        "horizon": {"type": "int", "default": 1, "description": "days"},
    },
    returns={"var": "float", "cvar": "float", "var_history": "list"},
    zero_token=True,
)
async def compute_var(returns, method="historical", confidence=0.95, horizon=1):
    ...

@harness_function(
    name="finquant.risk.stress_test",
    description="Run portfolio stress tests against historical crisis scenarios",
    schema={
        "positions": {"type": "list[Position]", "required": True},
        "scenarios": {"type": "list[str]", "default": ["2008_crisis","2020_covid","2022_rate_hike","flash_crash"]},
    },
    returns={"scenarios": "list[StressResult]", "worst_case": "float"},
    zero_token=True,
)
async def stress_test(positions, scenarios):
    ...

@harness_function(
    name="finquant.risk.kelly_criterion",
    description="Compute optimal position size via Kelly criterion",
    schema={
        "win_prob": {"type": "float", "required": True},
        "win_loss_ratio": {"type": "float", "required": True},
        "fraction": {"type": "float", "default": 0.5, "description": "fractional Kelly for safety"},
    },
    returns={"kelly_fraction": "float", "suggested_size": "float"},
    zero_token=True,
)
async def kelly_criterion(win_prob, win_loss_ratio, fraction=0.5):
    ...
```

#### 3.3.4 Quantitative Modeling Harness

```python
# laap/domain_sdks/finquant/harness/factors.py

@harness_function(
    name="finquant.factors.fama_french",
    description="Run Fama-French 3-factor / 5-factor regression",
    schema={
        "asset_returns": {"type": "Series", "required": True},
        "factor_data": {"type": "DataFrame", "required": True},
        "model": {"type": "str", "enum": ["3factor","5factor","carhart4"], "default": "3factor"},
    },
    returns={"betas": "Series", "alpha": "float", "r_squared": "float", "residuals": "Series"},
    zero_token=True,
)
async def fama_french(asset_returns, factor_data, model="3factor"):
    ...

@harness_function(
    name="finquant.factors.cointegration",
    description="Test for cointegration between assets (pairs trading)",
    schema={
        "series_a": {"type": "Series", "required": True},
        "series_b": {"type": "Series", "required": True},
        "method": {"type": "str", "enum": ["engle_granger","johansen"], "default": "engle_granger"},
    },
    returns={"is_cointegrated": "bool", "hedge_ratio": "float", "half_life": "float", "zscore": "float"},
    zero_token=True,
)
async def cointegration_test(series_a, series_b, method="engle_granger"):
    ...
```

#### 3.3.5 Backtesting Harness

```python
# laap/domain_sdks/finquant/harness/backtest.py

@harness_function(
    name="finquant.backtest.run",
    description="Backtest a strategy against historical data with event replay",
    schema={
        "strategy": {"type": "StrategySpec", "required": True, "description": "Species template ID or custom spec"},
        "symbols": {"type": "list[str]", "required": True},
        "start": {"type": "datetime", "required": True},
        "end": {"type": "datetime", "required": True},
        "initial_capital": {"type": "float", "default": 100000},
        "commission": {"type": "float", "default": 0.001},
        "slippage_model": {"type": "str", "default": "linear", "enum": ["none","linear","volume_based"]},
    },
    returns={
        "equity_curve": "Series",
        "trades": "list[Trade]",
        "metrics": "BacktestMetrics",  # Sharpe, Sortino, MaxDD, Calmar, etc.
        "monthly_returns": "DataFrame",
    },
    zero_token=True,
)
async def run_backtest(strategy, symbols, start, end, initial_capital=100000, **kwargs):
    """Runs a tick-level event-driven backtest.

    Strategy is resolved from the species library — either a precompiled
    template (zero-token) or a custom spec generated by the Strategist actor.
    Uses LAAP's sandbox execution for safety.
    """
    ...
```

### 3.4 Cognitive Species Templates

Species templates are precompiled reasoning patterns stored in the cognitive species library, enabling zero-token execution of recurring quantitative tasks. This follows LAAP's existing `laap.species.code_templates` pattern.

```python
# laap/domain_sdks/finquant/species/strategies.py

SPECIES_TEMPLATES = [
    SpeciesTemplate(
        id="finquant.strategy.momentum_cross",
        name="Moving Average Crossover (Momentum)",
        category="strategy",
        description="Classic fast/slow MA crossover with regime filter",
        template_code="""
async def execute(ctx, data):
    fast = await harness.indicators.sma(data.close, {{fast_period}})
    slow = await harness.indicators.sma(data.close, {{slow_period}})
    regime = await harness.indicators.detect_regime(data)
    if regime.name != "trending":
        return Signal.flat("Regime not trending; skip")
    if fast[-1] > slow[-1] and fast[-2] <= slow[-2]:
        return Signal.long(symbols=data.symbol, size=kelly_size)
    if fast[-1] < slow[-1] and fast[-2] >= slow[-2]:
        return Signal.short(symbols=data.symbol, size=kelly_size)
    return Signal.hold()
""",
        parameters={
            "fast_period": {"type": "int", "default": 20, "range": [5, 100]},
            "slow_period": {"type": "int", "default": 50, "range": [20, 250]},
        },
        species_version="1.0.0",
    ),
    SpeciesTemplate(
        id="finquant.strategy.mean_reversion",
        name="Bollinger Band Mean Reversion",
        category="strategy",
        # ... template code ...
    ),
    SpeciesTemplate(
        id="finquant.strategy.pairs_trade",
        name="Cointegration Pairs Trading",
        category="strategy",
        # ... template code ...
    ),
    SpeciesTemplate(
        id="finquant.strategy.factor_tilt",
        name="Factor-Based Portfolio Tilting",
        category="strategy",
        # ... template code ...
    ),
]
```

### 3.5 Safety Policy

The financial domain requires the strictest safety enforcement. The `FinQuantSafetyPolicy` implements hard gates that cannot be overridden by the LLM:

```python
# laap/domain_sdks/finquant/safety/policy.py

class FinQuantSafetyPolicy(DomainSafetyPolicy):
    """Hard safety gates for financial operations.

    These checks run in the security zone_executor BEFORE any order
    is routed. LLM cannot bypass — violations raise SafetyBreachError.
    """

    # ── Position Limits ──
    max_position_pct: float = 0.10        # Max 10% of capital per position
    max_sector_exposure: float = 0.30     # Max 30% in one sector
    max_portfolio_leverage: float = 1.0   # No leverage by default
    max_correlation_concentration: float = 0.70

    # ── Drawdown Protection ──
    max_daily_drawdown: float = 0.03      # 3% daily DD → halt
    max_total_drawdown: float = 0.15      # 15% total DD → liquidate
    drawdown_halt_hours: int = 24         # Cool-off period

    # ── Execution Guards ──
    max_orders_per_minute: int = 10
    max_slippage_bps: float = 50.0        # Reject if estimated slippage > 50bps
    require_paper_trade_first: bool = True # New strategies must paper-trade first

    # ── Compliance ──
    restricted_symbols: set[str] = field(default_factory=set)  # Insider/embargoed
    min_liquidity_usd: float = 1_000_000  # Only trade liquid instruments

    def pre_execution_gate(self, order: Order, portfolio: Portfolio) -> None:
        """Hard gate — raises SafetyBreachError if any limit violated."""
        self._check_position_limit(order, portfolio)
        self._check_sector_exposure(order, portfolio)
        self._check_drawdown(order, portfolio)
        self._check_liquidity(order)
        self._check_restricted(order)
        self._check_rate_limit()
        # All checks pass — order may proceed
```

### 3.6 CognitiveBus Topic Map

Following the `triphase.{domain}.{action}` namespace convention from `laap.triphase_bridge`:

```
finquant.market.stream          — Real-time market data perception events
finquant.market.anomaly         — Anomaly detection alerts
finquant.analysis.request       — Request quantitative analysis
finquant.analysis.result        — Analysis results (indicators, factors, etc.)
finquant.risk.assessment        — Periodic risk assessment
finquant.risk.breach            — Risk limit breach (high priority)
finquant.strategy.proposed      — Strategist proposes a strategy
finquant.strategy.validated     — Backtest validation complete
finquant.strategy.rejected      — Safety policy rejected strategy
finquant.execution.order        — Order to be sent
finquant.execution.fill         — Order fill confirmation
finquant.execution.rejected     — Order rejected by platform or safety
finquant.learning.pnl           — P&L feedback for PSI learning loop
finquant.learning.attribution   — Strategy attribution analysis
```

### 3.7 PSI Cognitive Loop Integration

The financial agent maps directly to LAAP's PSI (Perception → Selection → Action → Learning) loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    PSI Cognitive Loop                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  PERCEPTION  │───▶│  SELECTION   │───▶│   ACTION     │   │
│  │              │    │              │    │              │   │
│  │ Market Watch │    │ Strategist   │    │ Executor     │   │
│  │ Actor        │    │ selects      │    │ places       │   │
│  │ streams data │    │ strategy     │    │ orders       │   │
│  │ + indicators │    │ from species │    │ via          │   │
│  │ + regime     │    │ library      │    │ connectors   │   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                    │           │
│         │           ┌───────▼────────────────────▼───────┐   │
│         │           │        LEARNING (PSI)              │   │
│         │           │                                    │   │
│         └───────────│ P&L feedback → strategy            │   │
│                     │ attribution → species              │   │
│                     │ library update                     │   │
│                     │ Risk model recalibration           │   │
│                     └────────────────────────────────────┘   │
│                                                              │
│  RateBuffer: Market data 1000Hz → PSI 200Hz → Harness 1Hz  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Integration Strategy — Financial Data Sources & Trading Platforms

### 4.1 Connector Architecture

All external financial interfaces are abstracted behind a `FinancialConnector` base class, following LAAP's provider pattern. This ensures the cognitive actors never directly depend on any specific API.

```python
# laap/domain_sdks/finquant/connectors/base.py

class FinancialConnector(ABC):
    """Abstract base for all financial data & execution connectors."""

    @property
    @abstractmethod
    def connector_id(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> set[ConnectorCapability]: ...
    # ConnectorCapability: MARKET_DATA, HISTORICAL_DATA, ORDER_EXECUTION,
    #                       PORTFOLIO_QUERY, NEWS_FEED, FUNDAMENTAL_DATA

    @abstractmethod
    async def connect(self, credentials: dict) -> None: ...

    @abstractmethod
    async def health_check(self) -> ConnectorHealth: ...

    # ── Market Data ──
    async def fetch_ohlcv(self, symbols, start, end, interval) -> DataFrame: ...
    async def stream_ticks(self, symbols) -> AsyncIterator[Tick]: ...
    async def get_quote(self, symbols) -> dict: ...

    # ── Fundamentals ──
    async def get_financials(self, symbol, statement, period) -> dict: ...
    async def get_corporate_actions(self, symbol) -> list: ...

    # ── Execution ──
    async def place_order(self, order: Order) -> OrderResult: ...
    async def cancel_order(self, order_id: str) -> bool: ...
    async def get_positions(self) -> list[Position]: ...
```

### 4.2 Tiered Data Source Strategy

Connectors are organized in tiers by cost, latency, and market coverage:

| Tier | Connector | Markets | Cost | Latency | Use Case |
|---|---|---|---|---|---|
| **Tier 0** | AkShare | CN (A-shares, bonds, futures) | Free | 15min delay | Research, historical analysis |
| **Tier 0** | Yahoo Finance | Global (US, EU, Asia) | Free | 15min delay | Research, historical analysis |
| **Tier 1** | Alpha Vantage | Global | Free tier / $50/mo | Real-time | Real-time analysis, dev |
| **Tier 1** | Tushare Pro | CN | $30-300/mo | Real-time | CN market real-time |
| **Tier 2** | Binance API | Crypto | Free | <100ms | Crypto execution |
| **Tier 2** | IBKR TWS API | Global | $0-10/mo | <50ms | Multi-asset execution |
| **Tier 3** | CTP | CN futures | Free | <10ms | CN futures execution |
| **Tier 3** | Wind/Bloomberg | Global | $$$ enterprise | Real-time | Institutional-grade |

### 4.3 Connector Auto-Selection

The SDK auto-selects the optimal connector based on symbol, latency requirements, and available credentials:

```python
async def resolve_connector(symbols: list[str], preferred: str = "auto") -> FinancialConnector:
    """Auto-select best connector for given symbols.

    Logic:
    1. Classify symbols by market (CN/EU/US/Crypto/Futures)
    2. Filter connectors by market support and available credentials
    3. If real-time required, filter by latency tier
    4. Select lowest-cost connector meeting requirements
    5. Fallback to Tier 0 free sources
    """
    market = classify_market(symbols)
    candidates = filter_by_market(market)
    candidates = filter_by_credentials(candidates)
    if requires_realtime:
        candidates = filter_by_latency(candidates, max_latency_ms=100)
    return select_optimal(candidates)  # cheapest meeting all constraints
```

### 4.4 Trading Platform Integration

#### 4.4.1 Paper Trading (Default)

All new strategies must pass paper trading before live execution (`require_paper_trade_first: True`). The paper trading engine is a built-in connector that simulates fills using a slippage model:

```python
class PaperTradingConnector(FinancialConnector):
    """Simulated execution for strategy validation. Always available."""

    async def place_order(self, order: Order) -> OrderResult:
        # Use last tick + slippage model
        last_price = await self._get_last_price(order.symbol)
        fill_price = apply_slippage(last_price, order.size, self._slippage_model)
        # Update virtual portfolio
        await self._virtual_portfolio.apply_fill(order, fill_price)
        return OrderResult(status="filled", price=fill_price, ...)
```

#### 4.4.2 Live Execution Connectors

- **IBKR (Interactive Brokers)**: Multi-asset, global. Uses `ib_insync` library. Supports stocks, options, futures, forex.
- **Binance**: Crypto spot & futures. Uses official `python-binance` SDK. WebSocket streams for real-time.
- **CTP (Chinese futures)**: Uses `vnpy` CTP gateway. Native Chinese market support.

All live connectors enforce the safety policy gate *before* any order reaches the exchange API:

```python
async def place_order(self, order: Order) -> OrderResult:
    # 1. Safety gate (hard, cannot be bypassed)
    portfolio = await self.get_portfolio()
    self._safety_policy.pre_execution_gate(order, portfolio)

    # 2. Pre-trade risk check
    risk = await self._risk_actor.assess_order(order, portfolio)
    if risk.max_loss_exceeds_limit:
        raise SafetyBreachError("Order would exceed max loss limit")

    # 3. Send to exchange
    result = await self._exchange_api.place_order(order)

    # 4. Emit fill event to CognitiveBus
    await self._bus.emit("finquant.execution.fill", result)

    # 5. Update PSI learning state
    await self._bus.emit("finquant.learning.pnl", {
        "order": order, "fill": result, "portfolio": portfolio
    })

    return result
```

### 4.5 Market Data Streaming Architecture

Real-time data flows through the CognitiveBus as perception events, leveraging LAAP's RateBuffer to handle the frequency mismatch between market data (100-1000Hz) and PSI cognitive processing (~1-10Hz):

```
Exchange/API ──▶ WebSocket ──▶ TickBuffer ──▶ RateBuffer ──▶ MarketWatcher Actor
                                  │                              │
                                  │                              ▼
                                  │                    CognitiveBus
                                  │                    finquant.market.stream
                                  │                              │
                                  │                    ┌────────▼─────────┐
                                  │                    │  PSI Perception  │
                                  │                    │  (aggregated)    │
                                  │                    └────────┬─────────┘
                                  │                             │
                                  └──▶ Historical Store ──▶ Backtest Harness
                                       (Arrow/Parquet)     (on-demand)
```

---

## 5. Development Roadmap & Key Milestones

### 5.1 Phase Overview

```
Phase 0: Foundation          Phase 1: Core FinQuant      Phase 2: Live Trading
[Weeks 1-3]                  [Weeks 4-8]                 [Weeks 9-12]
─────────────────            ─────────────────            ─────────────────
Domain SDK framework         5 cognitive actors           Live connector (IBKR)
Harness function registry    12+ harness functions        Strategy deployment
Safety policy base           Species library (8+)         PSI learning loop
Connector base class         Backtest engine              Multi-strategy mgmt
                             Paper trading                Risk monitoring UI

Phase 3: Advanced            Phase 4: Domain Expansion
[Weeks 13-16]                [Weeks 17+]
─────────────────            ─────────────────
Factor model library         Legal 资讯 SDK
ML-augmented strategies      Bio-Medical SDK
Alternative data             科研 SDK
Portfolio optimization       创业资讯 SDK
Causal strategy attribution  Custom domain SDK wizard
```

### 5.2 Detailed Milestones

#### Phase 0: Domain SDK Framework Foundation (Weeks 1-3)

| Milestone | Deliverable | Verification |
|---|---|---|
| M0.1 | `laap/domain_sdk/base.py` — `DomainSDKBase`, `DomainManifest` | Unit tests pass; `DomainSDKBase` cannot be instantiated (abstract) |
| M0.2 | `laap/domain_sdk/registry.py` — `DomainSDKRegistry` | Register/list/unregister SDKs; load from pip package |
| M0.3 | `laap/domain_sdk/harness_function.py` — `HarnessFunction` + `HarnessFunctionRegistry` | Functions register, invoke, return typed results |
| M0.4 | `laap/domain_sdk/safety_policy.py` — `DomainSafetyPolicy` base | Gate enforcement test; LLM cannot bypass |
| M0.5 | `LAAPRuntime` extended with `_harness_registry`, `_species_library`, `_safety_policies` | `runtime.mount_domain(sdk)` works end-to-end |
| M0.6 | `laap domain` CLI subcommand (`laap domain list/install/register`) | CLI commands work; output matches expected format |

**Exit Criteria**: A stub domain SDK (e.g., `finquant` with 1 harness function, 1 actor) can be mounted into `LAAPRuntime` and invoked via CognitiveBus.

#### Phase 1: Core Financial Quantitative SDK (Weeks 4-8)

| Milestone | Deliverable | Verification |
|---|---|---|
| M1.1 | `connectors/base.py` + AkShare + Yahoo connectors | Fetch OHLCV for AAPL and 000001.SZ; data schema correct |
| M1.2 | `harness/market_data.py` — `get_ohlcv`, `get_quote`, `stream_ticks` | Auto-connector selection works; Arrow serialization |
| M1.3 | `harness/indicators.py` — 20+ technical indicators | Values match TA-Lib reference within 1e-6 |
| M1.4 | `harness/statistics.py` — ADF, Johansen, z-score, Sharpe, Sortino | Statistical tests match `statsmodels` reference |
| M1.5 | `actors/market_watcher.py` + `actors/analyst.py` | Actors spawn, register capabilities, process bus messages |
| M1.6 | `harness/backtest.py` — Event-driven backtest engine | Backtest MA crossover on S&P 500; Sharpe within 5% of reference |
| M1.7 | `species/strategies.py` — 8 strategy species templates | Each template executes zero-token; parameters configurable |
| M1.8 | `harness/risk.py` — VaR, CVaR, stress test, Kelly | VaR matches `scipy` Monte Carlo; stress scenarios produce P&L |
| M1.9 | `actors/risk_manager.py` + `actors/strategist.py` | Risk actor emits breach events; strategist selects species |
| M1.10 | `safety/policy.py` — `FinQuantSafetyPolicy` | All hard gates enforced; LLM prompt injection cannot bypass |
| M1.11 | `actors/executor.py` + `PaperTradingConnector` | Paper trades execute; fills recorded; P&L accurate |
| M1.12 | `topics.py` — Full CognitiveBus topic map | All 14 topics publishable/subscribable; event flow tested |

**Exit Criteria**: A user can ask the LAAP agent "Backtest a momentum strategy on AAPL for 2023" and receive a full backtest report with metrics — all computation in harness, LLM only narrates.

#### Phase 2: Live Trading Integration (Weeks 9-12)

| Milestone | Deliverable | Verification |
|---|---|---|
| M2.1 | `connectors/ibkr.py` — IBKR TWS API connector | Connect to TWS paper account; fetch positions; place/cancel orders |
| M2.2 | `connectors/binance.py` — Binance connector | WebSocket stream; spot order execution; testnet verified |
| M2.3 | Live execution path with safety gates | Order flow: Strategist → Risk check → Safety gate → Exchange |
| M2.4 | PSI learning loop — P&L feedback to strategy selection | Strategy weights update based on realized P&L |
| M2.5 | Real-time risk monitoring dashboard | UI shows VaR, exposure, drawdown in real-time |
| M2.6 | Multi-strategy portfolio manager | Allocate capital across strategies; rebalance |

**Exit Criteria**: Strategy can run live on IBKR paper account with real-time data, safety gates active, and PSI learning from outcomes.

#### Phase 3: Advanced Quantitative Capabilities (Weeks 13-16)

| Milestone | Deliverable |
|---|---|
| M3.1 | `harness/factors.py` — Fama-French 3/5-factor, Carhart 4-factor |
| M3.2 | `harness/portfolio.py` — Markowitz MVO, Black-Litterman, risk parity |
| M3.3 | ML-augmented strategy species (XGBoost signal, LSTM regime) |
| M3.4 | Alternative data connectors (sentiment, satellite, earnings calls) |
| M3.5 | Causal strategy attribution via `laap.agi.causal` |
| M3.6 | Walk-forward optimization harness |

#### Phase 4: Domain Expansion (Weeks 17+)

| Milestone | Deliverable |
|---|---|
| M4.1 | Legal 资讯 SDK (case retrieval, statute search, compliance) |
| M4.2 | Bio-Medical SDK (literature mining, drug interaction, trial matching) |
| M4.3 | 科研 SDK (paper analysis, experiment design, replication) |
| M4.4 | 创业资讯 SDK (market intelligence, competitor analysis, fundraising) |
| M4.5 | Domain SDK wizard CLI (`laap domain create --name mydomain`) |

---

## 6. Testing Framework & Validation Standards

### 6.1 Testing Philosophy

Financial systems demand the highest testing rigor. The testing framework follows a **defense-in-depth** model with five layers, each validating a different concern:

```
Layer 1: Unit Tests          — Harness function numerical correctness
Layer 2: Integration Tests   — Connector + actor + bus interaction
Layer 3: Backtest Validation — Strategy results vs. industry benchmarks
Layer 4: Safety Tests        — Adversarial attempts to bypass gates
Layer 5: PSI Loop Tests      — End-to-end cognitive loop integrity
```

### 6.2 Layer 1: Unit Tests — Numerical Correctness

Every harness function has unit tests that validate numerical results against reference implementations:

```python
# tests/domain_sdks/finquant/test_indicators.py

class TestTechnicalIndicators:
    """Validate indicator computations against TA-Lib reference."""

    @pytest.fixture
    def reference_data(self):
        """Load OHLCV data with known indicator values."""
        return load_fixture("sp500_2023_ohlcv.parquet")

    def test_rsi_matches_talib(self, reference_data):
        result = harness.indicators.compute(reference_data, [{"name": "RSI", "period": 14}])
        talib_ref = talib.RSI(reference_data.close.values, timeperiod=14)
        np.testing.assert_allclose(result.rsi.values, talib_ref, rtol=1e-6)

    def test_macd_matches_talib(self, reference_data): ...

    def test_bollinger_bands_match_talib(self, reference_data): ...
```

Reference implementations for validation:
- **Technical indicators**: TA-Lib, pandas-ta
- **Statistics**: scipy.stats, statsmodels
- **Risk metrics**: PyPortfolioOpt, QuantLib
- **Factor models**: statsmodels OLS, linearmodels

### 6.3 Layer 2: Integration Tests — Actor & Bus Interaction

Tests that cognitive actors correctly communicate via CognitiveBus topics:

```python
# tests/domain_sdks/finquant/test_actor_integration.py

class TestMarketWatcherActor:
    @pytest.mark.asyncio
    async def test_tick_emits_stream_event(self, runtime_with_finquant):
        bus = runtime_with_finquant._cognitive_bus
        events = await bus.capture("finquant.market.stream")

        await bus.emit("finquant.data.tick", {"symbol": "AAPL", "price": 150.0, "volume": 1000})
        await asyncio.sleep(0.1)

        assert len(events) == 1
        assert events[0].payload["symbol"] == "AAPL"
        assert "rsi" in events[0].payload["features"]

    @pytest.mark.asyncio
    async def test_anomaly_emits_alert(self, runtime_with_finquant): ...
```

### 6.4 Layer 3: Backtest Validation — Industry Benchmarks

Strategy backtests are validated against industry-standard benchmarks and known-good reference data:

```python
# tests/domain_sdks/finquant/test_backtest_validation.py

class TestBacktestValidation:
    """Validate backtest results against industry benchmarks."""

    def test_momentum_cross_sp500_matches_reference(self):
        """MA(20,50) crossover on S&P 500 should match published results
        within 5% Sharpe ratio tolerance."""
        result = harness.backtest.run(
            strategy="finquant.strategy.momentum_cross",
            symbols=["SPY"],
            start="2020-01-01",
            end="2023-12-31",
            parameters={"fast_period": 20, "slow_period": 50},
        )
        # Reference: known Sharpe for this strategy on this period
        assert abs(result.metrics.sharpe - 0.72) < 0.05
        assert result.metrics.max_drawdown < 0.25
        assert len(result.trades) > 10

    def test_fama_french_regression_r_squared(self): ...
    def test_var_historical_matches_monte_carlo(self): ...
```

**Benchmark datasets**:
- **Kenneth French Data Library**: Factor returns for Fama-French validation
- **Yahoo Finance**: OHLCV for technical indicator validation
- **QuantConnect / Zipline**: Backtest result cross-validation
- **QC Wealth / Portfolio Visualizer**: Strategy performance reference

### 6.5 Layer 4: Safety Tests — Adversarial Gate Testing

The safety policy must withstand adversarial attempts to bypass it, including LLM prompt injection:

```python
# tests/domain_sdks/finquant/test_safety_adversarial.py

class TestSafetyAdversarial:
    """Attempt to bypass safety gates — all must fail."""

    @pytest.mark.asyncio
    async def test_llm_prompt_injection_cannot_bypass_position_limit(self, runtime):
        """LLM tries to order 50% of capital despite 10% limit."""
        malicious_order = Order(symbol="AAPL", size=50000, portfolio_value=100000)
        with pytest.raises(SafetyBreachError, match="position limit"):
            await runtime._safety_policies["finquant"].pre_execution_gate(
                malicious_order, test_portfolio
            )

    @pytest.mark.asyncio
    async def test_drawdown_halt_blocks_new_orders(self, runtime): ...

    @pytest.mark.asyncio
    async def test_restricted_symbol_blocked(self, runtime): ...

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, runtime): ...
```

### 6.6 Layer 5: PSI Loop Tests — End-to-End Cognitive Integrity

Tests that the full PSI cognitive loop operates correctly — perception triggers selection triggers action triggers learning:

```python
# tests/domain_sdks/finquant/test_psi_loop_e2e.py

class TestPSILoopEndToEnd:
    @pytest.mark.asyncio
    async def test_full_cycle_market_to_execution_to_learning(self, runtime_with_finquant):
        """Full PSI cycle: market data → analysis → strategy → paper order → P&L feedback."""
        runtime = runtime_with_finquant
        await runtime.start()

        # 1. Inject market data (perception)
        await runtime.emit("finquant.data.tick", {"symbol": "AAPL", "price": 150, "volume": 10000})

        # 2. Wait for analysis + strategy selection
        strategy_events = await runtime.wait_for("finquant.strategy.proposed", timeout=5.0)
        assert len(strategy_events) == 1

        # 3. Wait for execution
        fill_events = await runtime.wait_for("finquant.execution.fill", timeout=5.0)
        assert fill_events[0].payload["status"] == "filled"

        # 4. Verify learning feedback
        learning_events = await runtime.wait_for("finquant.learning.pnl", timeout=5.0)
        assert "strategy_id" in learning_events[0].payload

        # 5. Verify PSI state updated
        psi_state = runtime.psi.get_state()
        assert psi_state["competence"] > initial_competence  # learning occurred
```

### 6.7 Continuous Benchmarking

A benchmark suite runs continuously to detect performance regressions and validate against live market data:

```
benchmarks/
└── finquant/
    ├── run_indicators.py      — Indicator computation speed vs. TA-Lib
    ├── run_backtest.py        — Backtest engine speed vs. Zipline
    ├── run_risk.py            — VaR computation speed vs. QuantLib
    └── run_e2e.py             — Full PSI loop latency measurement
```

---

## 7. Scalability Considerations — Multi-Domain Expansion

### 7.1 Domain-Agnostic Framework

The `DomainSDKBase` contract is designed to be fully domain-agnostic. The Financial Quantitative SDK is the **reference implementation** that proves the framework. Subsequent domains follow the same 6-step contract:

```
1. register_harness_functions()    — Domain-specific deterministic computations
2. register_cognitive_actors()     — Domain-specific perception/action actors
3. register_species_templates()    — Domain-specific precompiled reasoning patterns
4. register_bus_topics()           — Domain-specific CognitiveBus namespace
5. get_safety_policy()             — Domain-specific hard safety gates
6. manifest()                      — Domain metadata for discovery
```

### 7.2 Planned Domain SDKs

| Domain | Domain ID | Key Harness Functions | Safety Concerns |
|---|---|---|---|
| **Legal 资讯** | `legal` | Case retrieval, statute search, precedent analysis, compliance check | Legal advice disclaimer; jurisdiction scoping |
| **Bio-Medical** | `biomed` | Literature mining, drug interaction check, trial matching, biomarker analysis | Medical disclaimer; never diagnose; cite sources |
| **科研** | `research` | Paper analysis, citation graph, experiment design, replication validation | Citation accuracy; no fabrication |
| **创业资讯** | `startup` | Market intelligence, competitor analysis, TAM calculation, fundraising data | Financial advice disclaimer; data freshness |

### 7.3 Cross-Domain Synergy

Domain SDKs can communicate via the CognitiveBus, enabling cross-domain intelligence:

```
finquant.company.analyze    ──▶  legal.compliance.check
     (financial health)           (regulatory compliance)

biomed.drug.interaction     ──▶  finquant.pharma.evaluate
     (clinical data)              (investment implication)

startup.market.intel        ──▶  finquant.sector.outlook
     (startup ecosystem)          (sector investment view)
```

This is enabled by LAAP's existing `ArisCognitiveBus` broadcast and topic subscription — domain SDKs simply subscribe to each other's output topics.

### 7.4 Scalability Dimensions

| Dimension | Strategy | Capacity Target |
|---|---|---|
| **Concurrent Agents** | ActorSystem is async; each agent is an actor hierarchy | 1000+ concurrent agent instances |
| **Data Throughput** | RateBuffer + Arrow IPC + columnar storage | 100K ticks/sec ingestion |
| **Strategy Complexity** | Species templates compile to Petri nets; Rust-backed hot paths | 100+ simultaneous strategy backtests |
| **Domain Count** | Domain SDKs are isolated; bus namespace prevents collisions | 50+ registered domains |
| **Memory** | Hierarchical memory (working/episodic/semantic) + forgetting curve | Multi-year agent memory without OOM |
| **Latency** | Harness functions in Rust; hot path bypasses Python | <1ms indicator computation; <10ms order gate |

### 7.5 Cognitive Species Library Growth

Following LAAP's core principle, the species library grows with each use. Every successful backtest, every validated strategy, every learned causal rule becomes a new species template — making the system progressively more capable and token-efficient:

```
User runs backtest ──▶ Strategy species executes (zero-token)
                  ──▶ Result validated
                  ──▶ If novel pattern → new species template created
                  ──▶ Species library grows
                  ──▶ Next similar query → zero-token species match
```

This creates a **compounding knowledge moat** — each domain SDK becomes more valuable with use, and cross-domain species transfer (e.g., mean-reversion patterns from finance apply to bio-medical oscillatory data) enables emergent cross-domain intelligence.

### 7.6 Ψ-Net Multi-Agent Ecosystem

Multiple domain agent instances can form a Ψ-Net ecosystem via LAAP's existing `PsiNetConnector`, exchanging causal rules and species updates:

```
┌─────────────┐     species/causal rules     ┌─────────────┐
│ FinQuant    │ ◀──────────────────────────▶ │  Legal 资讯  │
│ Agent (NYC) │                              │  Agent (SFO) │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  causal rules                              │ species templates
       ▼                                            ▼
┌─────────────┐                              ┌─────────────┐
│ Bio-Med     │ ◀──────────────────────────▶ │   科研       │
│ Agent (BOS) │                              │  Agent (SHA) │
└─────────────┘                              └─────────────┘
```

Each agent instance specializes in its domain but shares learned patterns — a financial regime-detection species may transfer to bio-medical data pattern detection, creating emergent cross-domain intelligence.

---

## 8. Appendices

### Appendix A: Relationship to Existing LAAP Subsystems

| New Component | Existing LAAP Pattern | Relationship |
|---|---|---|
| `DomainSDKBase` | `AgentAdapter` (laap/sdk/adapter.py) | Same abstract-contract pattern; domain SDKs "adapt" LAAP to a domain |
| `DomainSDKRegistry` | `Skills Hub` (laap/skills/hub.py) | Same discovery/install pattern; pip + GitHub sources |
| `HarnessFunction` | `ToolRegistry` (laap/tools/tool_registry.py) | Harness functions are a specialized tool subtype with zero-token emphasis |
| `FinQuantSafetyPolicy` | `SecurityZoneExecutor` (laap/security/zone_executor.py) | Domain safety policy plugs into existing zone executor |
| `FinancialConnector` | `LLM Provider` pattern (laap/llm/provider.py) | Same provider abstraction; connectors are data providers |
| `finquant.*` bus topics | `triphase.*` topics (laap/triphase_bridge/topics.py) | Same namespace convention; `{domain}.{category}.{action}` |
| FinQuant species templates | `laap.species.code_templates` | Direct extension of existing species library |
| FinQuant cognitive actors | `ArisCognitiveBus._spawn_cognitive_actors()` | Same Actor + Capability + bus subscription pattern |

### Appendix B: Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Harness functions | Python 3.11+ / Rust (via rust_bridge) | Python for ergonomics; Rust for hot paths |
| Data handling | pandas, NumPy, Arrow/Parquet | Industry standard; zero-copy IPC |
| Technical indicators | TA-Lib (C backend) | Fastest; industry reference |
| Statistical modeling | statsmodels, scipy | Comprehensive; well-tested |
| Risk computation | QuantLib, PyPortfolioOpt | Institutional-grade |
| Backtesting | Custom event-driven engine | Full control; integrates with PSI |
| Data sources | AkShare, yfinance, python-binance, ib_insync | Best free + low-cost options |
| Serialization | Apache Arrow IPC | Zero-copy; cross-language |
| Testing | pytest, pytest-asyncio | LAAP's existing test framework |

### Appendix C: Naming Conventions

- **Domain IDs**: lowercase, no spaces (`finquant`, `legal`, `biomed`, `research`, `startup`)
- **Bus topics**: `{domain}.{category}.{action}` (`finquant.market.stream`)
- **Harness functions**: `{domain}.{module}.{function}` (`finquant.indicators.compute`)
- **Species IDs**: `{domain}.{category}.{name}` (`finquant.strategy.momentum_cross`)
- **Actor IDs**: `{domain}_{role}` (`finquant_market_watcher`)
- **Connector IDs**: `{domain}_{provider}` (`finquant_yahoo`, `finquant_ibkr`)

### Appendix D: CLI Commands (Planned)

```bash
# Domain SDK management
laap domain list                          # List installed domain SDKs
laap domain install finquant              # Install Financial Quantitative SDK
laap domain install github:user/repo      # Install from GitHub
laap domain info finquant                 # Show SDK manifest & capabilities
laap domain create --name mydomain        # Scaffold a new domain SDK (wizard)

# Financial Quantitative operations
laap finquant backtest --strategy momentum_cross --symbol AAPL --start 2023-01-01
laap finquant analyze --symbol 000001.SZ --indicators RSI,MACD,BOLL
laap finquant risk --portfolio my_positions.json --var 0.95
laap finquant paper-trade --strategy pairs_trade --symbols AAPL,MSFT
laap finquant live --strategy factor_tilt --connector ibkr --paper
```

---

## Document Control

| Field | Value |
|---|---|
| **Author** | LAAP Architecture Team |
| **Reviewers** | Pending |
| **Version** | 1.0 — Initial Draft |
| **Last Updated** | 2026-07-29 |
| **Related Documents** | [ARCHITECTURE.md](file:///d:/LAAP/ARCHITECTURE.md), [LAAP_ROADMAP.md](file:///d:/LAAP/LAAP_ROADMAP.md), [laap/sdk/](file:///d:/LAAP/laap/sdk/) |

---

*This specification establishes the foundational infrastructure for LAAP's evolution from a general-purpose cognitive harness into a multi-domain digital life agent platform. The Financial Quantitative SDK serves as both the inaugural domain implementation and the reference architecture for all future domain SDKs.*

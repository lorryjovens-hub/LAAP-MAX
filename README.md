# LAAP — Language-Action-Architecture-Protocol

LAAP is a modular cognitive-agent framework. It is designed around two main layers:

- **Aether orchestration layer** (`laap.orchestration`, `laap.agent`, `laap.agi`) — decides what to do and why, using Petri nets, actors, and optional cognitive state.
- **Body execution layer** (`laap.body`) — provides the concrete capabilities for how to do it: tools, LLM transports, MCP, skills, plugins, and message gateways.

> **Status:** Active development. Some modules are stable and tested; others are experimental stubs or placeholders. See `laap/body/README.md` for an honest capability list.

## Architecture

```
User Message
    → Aether orchestration (Petri net + Actor system)
        → Body layer tools / LLM / MCP / skills
            → Output
```

### Layers

| Layer | Responsibilities | Key packages |
|-------|------------------|--------------|
| **Aether orchestration** | Intent routing, workflow compilation, actor dispatch, cognitive loop | `laap.orchestration.*`, `laap.agent`, `laap.agi` |
| **Body execution** | Tool execution, LLM calls, MCP, skills, plugins, gateways | `laap.body`, `laap.tools`, `laap.llm`, `laap.mcp`, `laap.skills`, `laap.plugins`, `laap.gateway` |

### Body Layer

`laap.body` is the stable public entry point for the execution layer. It re-exports the underlying tool, LLM, MCP, skill, plugin, and gateway implementations so that Aether modules can import a single namespace.

```python
from laap.body import create_default_body_system

body = create_default_body_system()
print(body.tools.list_tools())  # list registered tools
```

For details on what is implemented, stable, beta, or placeholder, see [`laap/body/README.md`](laap/body/README.md).

### Key Principles

- **Compiled workflows:** Deterministic intents can be compiled directly into Petri-net tool workflows without calling an LLM.
- **Hybrid execution:** The orchestration layer can fall back to an LLM transport when an intent is ambiguous.
- **Actor-based dispatch:** Tools and capabilities are advertised by actors and dispatched through the actor system.
- **Pluggable providers:** LLM, gateway, and skill providers can be added or swapped via the registry pattern.

## Quick Start

```bash
# Install in editable mode
pip install -e ".[dev]"

# Run the orchestration/body/tool tests
python -m pytest tests/unit/test_laap_body_e2e.py tests/unit/test_orchestration_*.py tests/unit/test_body_*.py -q

# List capabilities
python -m laap --capabilities
```

### Prerequisites

- Python 3.10+
- Optional: `playwright` for browser tools, `fastapi` for API mode, `mcp` for MCP support.

## Project Structure

```
D:/LAAP/
├── laap/
│   ├── body/              # Public body-layer entry point
│   ├── orchestration/     # Aether: actors, Petri nets, kernel, cognitive bus
│   ├── tools/             # Native tools (filesystem, search, browser, shell, ...)
│   ├── llm/               # LLM provider abstractions and transports
│   ├── mcp/               # Model Context Protocol client/server
│   ├── skills/            # Skill loading and management
│   ├── plugins/           # Plugin manager and registry
│   ├── gateway/           # Gateway adapters (Feishu, base interface)
│   └── agent/             # Agent and standalone-agent implementations
├── aris_brain/            # Related cognitive research code (separate package)
├── tests/                 # Unit and integration tests
├── demos/                 # Demonstration scripts
├── .trae/specs/           # Spec-driven design documents
├── pyproject.toml
├── .env.example
└── LICENSE
```

## Environment Configuration

Copy `.env.example` to `.env` and fill in optional credentials:

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` — Feishu bot credentials
- `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — LLM API keys

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Author

Created by **Lorry** and **Aris**.

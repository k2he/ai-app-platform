# Product Requirements Document: Agentic AI Application Platform

## 1. Overview

An internal platform enabling multiple teams in a financial/insurance company to rapidly build agentic AI applications (LangGraph-based) with minimal AI infrastructure knowledge. The platform provides shared modules (guardrails, observability, authentication, common workflows) while allowing per-application customization.

## 2. Problem Statement

Multiple teams need to build conversational AI agents with overlapping infrastructure needs (PII detection, content safety, observability, human handoff). Without a platform, each team duplicates effort, introduces inconsistencies, and requires deep AI/MLOps expertise.

## 3. Goals

- **Reduce time-to-production** for new AI applications to days, not weeks
- **Minimize code per application** — teams write only business logic
- **Enforce compliance** via shared guardrails (PII, harmful content) by default
- **Allow customization** — teams can override/extend any shared module
- **Centralize observability** via Langfuse across all applications

## 4. Target Users

| Team | Application | Unique Logic |
|------|------------|--------------|
| Team 1 | Address Change Bot | Address validation, account update |
| Team 2 | Account Activation Bot | Identity verification, activation flow |
| Team 3 | Card Replacement Bot | Card cancellation, replacement issuance |

All share: guardrails, authentication, Langfuse tracing, human handoff ("transfer to agent").

## 5. Architecture

### 5.1 High-Level Structure

```
ai-app-platform/
├── platform/                    # Shared platform code (installed as package)
│   ├── guardrails/
│   │   ├── pii_detection.py     # PII detect & redact (Presidio-based)
│   │   ├── content_safety.py    # Harmful content filter
│   │   ├── base.py              # Guardrail base class & registry
│   │   └── config.py            # Default guardrail config
│   ├── observability/
│   │   ├── langfuse_client.py   # Shared Langfuse integration
│   │   └── tracing.py           # Decorator/middleware for auto-tracing
│   ├── auth/
│   │   ├── base.py              # Auth interface
│   │   └── jwt_auth.py          # Default JWT implementation
│   ├── nodes/
│   │   ├── human_handoff.py     # "Transfer to agent" shared node
│   │   ├── input_guard.py       # Input guardrail node
│   │   └── output_guard.py      # Output guardrail node
│   ├── graph/
│   │   ├── builder.py           # Graph factory — builds LangGraph from YAML + code
│   │   └── state.py             # Base state schema
│   ├── llm/
│   │   ├── provider.py          # LLM provider abstraction (OpenAI, Azure, Bedrock)
│   │   └── config.py            # Model selection config
│   └── runner.py                # FastAPI app factory / entrypoint builder
├── features/                    # Per-team applications
│   ├── address_change/
│   │   ├── workflow.yaml        # Declares nodes, edges, LLM, guardrails config
│   │   ├── nodes.py             # Business logic nodes
│   │   ├── state.py             # Extended state (optional)
│   │   └── config.py            # Overrides (model, guardrails, auth)
│   ├── account_activation/
│   │   └── ...
│   └── card_replacement/
│       └── ...
├── pyproject.toml               # UV/pip project — single monorepo
├── uv.lock
└── README.md
```

### 5.2 Design Principles

1. **Convention over configuration** — sensible defaults, override via `workflow.yaml` or `config.py`
2. **Plugin/registry pattern** — guardrails, auth, LLM providers registered; teams select by name
3. **Composition via LangGraph** — platform provides reusable nodes; teams compose graphs declaratively
4. **YAML-driven workflow** — each feature declares its graph structure in YAML; platform compiles to LangGraph

### 5.3 Workflow YAML Schema (per feature)

```yaml
name: address_change
description: "Customer address change workflow"

llm:
  provider: azure_openai
  model: gpt-4o
  temperature: 0.1

guardrails:
  input:
    - pii_detection          # uses platform default
    - content_safety
  output:
    - pii_redaction

auth:
  strategy: jwt              # or "none", "api_key", custom class path

nodes:
  - name: classify_intent
    type: custom
    handler: nodes.classify_intent
  - name: update_address
    type: custom
    handler: nodes.update_address
  - name: human_handoff
    type: platform            # uses platform.nodes.human_handoff

edges:
  - from: START
    to: classify_intent
  - from: classify_intent
    to: update_address
    condition: "intent == 'address_change'"
  - from: classify_intent
    to: human_handoff
    condition: "intent == 'transfer'"
  - from: update_address
    to: END
  - from: human_handoff
    to: END
```

### 5.4 Graph Builder (Core Platform Logic)

The `platform.graph.builder` module:
1. Reads `workflow.yaml`
2. Automatically injects `input_guard` node before first node, `output_guard` before END
3. Resolves `type: platform` nodes from registry
4. Imports `type: custom` handlers from feature's `nodes.py`
5. Builds and compiles a `StateGraph`

### 5.5 Customization Points

| What | How to Customize |
|------|-----------------|
| LLM model/provider | Set in `workflow.yaml` → `llm` section |
| Guardrails | Add/remove in `workflow.yaml`; or subclass `BaseGuardrail` |
| Authentication | Set `auth.strategy` or point to custom class |
| State schema | Extend `platform.graph.state.BaseState` in feature's `state.py` |
| Nodes | Write Python functions; reference in YAML |
| Entire graph | Skip YAML; build graph manually using platform nodes as imports |

## 6. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Agent framework | LangGraph | Stateful, graph-based agents; conditional routing |
| Observability | Langfuse | LLM-specific tracing, cost tracking, prompt management |
| PII Detection | Microsoft Presidio | Best-in-class PII detection, supports custom recognizers |
| Content Safety | LLM-based classifier + regex rules | Flexible, layered approach |
| API Layer | FastAPI | Async, typed, auto-docs |
| Package/Dependency Mgmt | UV | Fast, deterministic, monorepo-friendly |
| State Persistence | PostgreSQL + LangGraph checkpointer | Conversation continuity |
| Configuration | Pydantic Settings + YAML | Type-safe, validated config |

## 7. Shared Platform Modules — Detail

### 7.1 Guardrails

- **Input guardrails**: Run before LLM call. Detect PII, block harmful prompts, validate input format.
- **Output guardrails**: Run after LLM response. Redact leaked PII, block harmful outputs, ensure format compliance.
- **Registry pattern**: `@register_guardrail("pii_detection")` — teams reference by name.
- **Custom guardrails**: Teams subclass `BaseGuardrail` and register in their `config.py`.

### 7.2 Langfuse Integration

- Auto-traces every node execution, LLM call, guardrail check
- Per-feature project/session tagging
- Cost attribution by team/feature
- Prompt versioning via Langfuse prompt management

### 7.3 Human Handoff Node

- Shared node that marks conversation for live agent transfer
- Configurable: escalation message, metadata passed to CRM/ticketing system
- Teams customize via `handoff_config` in YAML

### 7.4 Authentication

- Default: JWT validation middleware
- Pluggable: teams can swap to API key, OAuth2, or custom
- Auth context injected into graph state for downstream use

## 8. Developer Experience (DX)

### 8.1 Creating a New Feature

```bash
# 1. Scaffold
uv run python -m platform scaffold --name dispute_resolution

# 2. Edit generated workflow.yaml and nodes.py

# 3. Run locally
uv run python -m platform serve --feature dispute_resolution

# 4. Test
uv run pytest features/dispute_resolution/tests/
```

### 8.2 CLI Commands

| Command | Description |
|---------|-------------|
| `platform scaffold --name <name>` | Generate feature boilerplate |
| `platform serve --feature <name>` | Run single feature locally |
| `platform serve --all` | Run all features |
| `platform validate --feature <name>` | Validate workflow.yaml + config |

## 9. Deployment Model

- Each feature deploys as an independent FastAPI service (or combined)
- Shared platform code is a Python package dependency
- Environment config via `.env` / secrets manager
- Containerized with Docker; orchestrated via K8s or cloud-native (ECS, Cloud Run)

## 10. Security & Compliance

- PII never stored in logs (redacted by default)
- All LLM interactions traced in Langfuse (audit trail)
- Auth enforced at platform level; features inherit
- Guardrails active by default; teams can only add, not fully disable without explicit config flag

## 11. Success Metrics

| Metric | Target |
|--------|--------|
| Time to launch new AI feature | < 3 days (business logic only) |
| Lines of code per feature | < 200 (excluding tests) |
| Guardrail coverage | 100% of features have input + output guardrails |
| Observability coverage | 100% of LLM calls traced |

## 12. Milestones

| Phase | Scope | Duration |
|-------|-------|----------|
| Phase 1 | Platform core: graph builder, guardrails (PII + content safety), Langfuse integration, human handoff node, CLI scaffold | 4 weeks |
| Phase 2 | First feature (address change) on platform; auth module; deployment pipeline | 2 weeks |
| Phase 3 | Remaining features (account activation, card replacement); load testing; docs | 2 weeks |
| Phase 4 | Advanced: prompt management via Langfuse, A/B testing, custom guardrail marketplace | 3 weeks |

## 13. Open Questions

1. Should features share a single LangGraph checkpointer DB or each have their own?
2. Multi-tenant vs single-tenant deployment per feature?
3. Should the platform support streaming responses from day one?
4. Preferred cloud provider for LLM (Azure OpenAI vs AWS Bedrock vs direct OpenAI)?


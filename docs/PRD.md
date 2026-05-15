# Product Requirements Document: Agentic AI Application Platform

**Version:** 2.0  
**Date:** May 15, 2026  
**Status:** Draft

---

## 1. Executive Summary

Build a **shared Python platform** that enables multiple teams within an insurance/financial services organization to rapidly develop agentic AI chatbots using **LangGraph** and **Langfuse**. The platform provides all cross-cutting concerns (guardrails, observability, authentication, human handoff) as configurable, overridable modules — so feature teams write **only business logic** while inheriting production-grade infrastructure.

---

## 2. Problem Statement

| Pain Point | Impact |
|---|---|
| Each team rebuilds guardrails, auth, tracing from scratch | 3–6 month lead time per chatbot |
| Inconsistent PII handling across applications | Compliance & audit risk |
| Teams need deep LangGraph/LLM deployment knowledge | High hiring bar, slow onboarding |
| No standard observability | Debugging conversations is ad-hoc |
| Shared behaviors (human handoff) reimplemented per app | Code drift, inconsistent UX |

**Desired outcome:** A team with domain expertise (e.g., "how to change an address in our CRM") can ship a production chatbot in **2–4 weeks** by writing **< 200 lines of Python** — no AI infrastructure expertise required.

---

## 3. Goals & Non-Goals

### Goals

1. Provide a **plugin-style architecture** where each feature is a self-contained directory (workflow config + handlers + prompts).
2. Ship **shared modules** for: guardrails pipeline, Langfuse tracing, identity verification, human handoff, LLM provider abstraction.
3. Allow teams to **override or extend** any shared module (swap guardrails, change auth method, pick different LLM) via configuration or subclassing.
4. Use **YAML-driven workflow definitions** so teams declare LangGraph structure without writing graph-building code.
5. Auto-discover and load feature plugins at runtime from a `features/` directory.
6. Provide a CLI / entry-point to run any feature locally or deploy it.

### Non-Goals (v1)

- Visual/drag-and-drop workflow builder
- Real-time WebSocket live-agent bridge (we provide an abstract interface only)
- Multi-language (English only in v1)
- Fine-tuning infrastructure
- Per-team billing/metering

---

## 4. Architecture

### 4.1 High-Level Design

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PLATFORM CORE (shared library)                 │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Guardrails │  │  Langfuse  │  │   Auth   │  │  Human Handoff  │  │
│  │  Pipeline  │  │  Tracing   │  │  Module  │  │   Interface     │  │
│  └────────────┘  └────────────┘  └──────────┘  └─────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           WORKFLOW ENGINE                                       │  │
│  │  YAML Parser → Graph Builder → Node Registry → State Manager   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           BUILT-IN NODE TYPES                                   │  │
│  │  llm_response │ llm_conversation │ auth_challenge │ subgraph   │  │
│  │  human_handoff │ custom (user handler)                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           ROUTER TYPES                                          │  │
│  │  llm_intent │ direct │ validation_result │ custom               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           LLM PROVIDER ABSTRACTION                              │  │
│  │  OpenAI │ Anthropic │ Azure OpenAI │ Bedrock (pluggable)        │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ address_change│   │ account_activ.│   │card_replacement│
│  workflow.yaml│   │  workflow.yaml│   │  workflow.yaml │
│  handlers.py  │   │  handlers.py  │   │  handlers.py   │
│  prompts/     │   │  prompts/     │   │  prompts/      │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 4.2 Key Design Decisions

| Decision | Rationale |
|---|---|
| **YAML workflow definitions** | Declarative; teams don't learn LangGraph internals; schema-validatable |
| **Plugin directory convention** (`features/<name>/`) | Auto-discovery, self-contained, easy to extract to separate repo later |
| **Layered guardrails** (mandatory → optional → custom) | Platform enforces compliance minimums; teams add domain-specific rules |
| **Handler interface (async function)** | Simplest contract — pure function of `(state, config) → result` |
| **UV for package management** | Fast, reproducible; single lockfile; workspace support for monorepo |
| **Single repo first, extractable later** | Fastest iteration now; clear module boundaries enable future library extraction |

### 4.3 Customization Model

The platform uses a **"convention over configuration, override anything"** approach:

```
Priority (highest → lowest):
  1. Feature-level override (in workflow.yaml or handlers.py)
  2. Feature-level config (guardrails.optional, model selection)
  3. Platform defaults (mandatory guardrails, default model, default auth)
```

**What teams can customize:**

| Aspect | How to Customize |
|---|---|
| LLM model | `model:` field in workflow.yaml |
| Guardrails | Enable/disable optional; add custom guardrail classes |
| Auth method | `config.method:` on auth_challenge node |
| Node behavior | Write a `custom` handler function |
| Routing logic | Provide a custom router function |
| Prompts | Jinja2 templates in feature's `prompts/` directory |
| State schema | Define `schemas:` section in workflow.yaml |
| Human handoff | Override handoff adapter class |

---

## 5. Technology Stack

| Component | Technology | Why |
|---|---|---|
| Workflow orchestration | **LangGraph** | Industry-standard for stateful agentic graphs; supports subgraphs, conditional edges, interrupts |
| Observability | **Langfuse** | Purpose-built LLM tracing; prompt management; evaluations; cost tracking |
| Guardrails | **Guardrails AI** (structural validation) + **LangChain/custom** (content filtering) | Best-of-breed: Guardrails AI for schema enforcement, custom pipeline for PII/toxicity |
| Language | **Python 3.11+** | LangGraph/Langfuse ecosystem; team familiarity |
| Package mgmt | **UV** | Fast resolver, workspace support, reproducible builds |
| Config format | **YAML** (with JSON Schema validation) | Human-readable, git-diffable |
| LLM providers | OpenAI, Anthropic, Azure OpenAI (via LangChain chat models) | Unified interface, swap via config |
| Testing | **pytest + pytest-asyncio** | Standard; supports async handlers |

---

## 6. Guardrails Architecture (Deep Dive)

Guardrails are the platform's most critical shared module. The design must balance **mandatory compliance** with **team flexibility**.

### 6.1 Three-Tier Pipeline

```
Input (user message)
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ TIER 1: MANDATORY (platform-enforced, non-removable)│
│  • pii_detection — flag SSN, credit card, DOB       │
│  • harmful_content — block toxic/violent/illegal     │
│  • prompt_injection — detect jailbreak attempts      │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ TIER 2: OPTIONAL (platform-provided, team toggles)  │
│  • pii_redaction — mask detected PII before LLM     │
│  • address_format_validation                        │
│  • fraud_signal_detection                           │
│  • document_verification                            │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ TIER 3: CUSTOM (team-defined, additive)             │
│  • Domain-specific validators                       │
│  • Business rule checks                             │
└─────────────────────────────────────────────────────┘
  │
  ▼
Output → LLM / next node
```

### 6.2 Guardrail Interface

```python
from dataclasses import dataclass

@dataclass
class GuardrailResult:
    passed: bool
    modified_text: str | None = None  # if redaction applied
    violations: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

class BaseGuardrail:
    """Teams subclass this to create custom guardrails."""

    def __init__(self, config: dict):
        self.config = config

    async def check(self, text: str, context: dict) -> GuardrailResult:
        raise NotImplementedError
```

### 6.3 Configuration in workflow.yaml

```yaml
guardrails:
  mandatory:           # cannot remove — platform always runs these
    - pii_detection
    - harmful_content
    - prompt_injection
  optional:            # team chooses which to enable
    - pii_redaction
    - fraud_detection
  custom:              # team-defined classes
    - handler: "features.card_replacement.guardrails.CardNumberValidator"
      config:
        mask_full_number: true
```

---

## 7. Workflow Configuration Schema

```yaml
workflow:
  name: string                       # unique identifier
  description: string
  model: string                      # default LLM (gpt-4o, claude-3.5-sonnet, etc.)

  global_edges:                      # available from ANY node (e.g., human handoff)
    - trigger: llm_intent
      intent: string
      to: node_id

  guardrails:
    mandatory: [string]
    optional: [string]
    custom: [{handler: string, config: object}]

  nodes:
    - id: string
      type: llm_response | llm_conversation | auth_challenge | platform.human_handoff | subgraph | custom
      handler: string                # Python dotted path (for custom type)
      prompt_template: string        # Jinja2 file in feature's prompts/ dir
      output_schema: string          # reference to schemas section
      config: object                 # type-specific settings

  edges:
    - from: string
      to: string

  conditional_edges:
    - from: string
      router: llm_intent | direct | validation_result | custom
      routes:
        key: node_id

subgraphs:
  name:
    description: string
    nodes: [...]
    edges: [...]
    conditional_edges: [...]

schemas:
  SchemaName:
    type: object
    properties: {...}
    required: [...]
```

---

## 8. Platform Node Types

| Type | Purpose | Key Config |
|---|---|---|
| `llm_response` | Single LLM generation | `prompt_template` |
| `llm_conversation` | Multi-turn extraction with structured output | `prompt_template`, `output_schema` |
| `auth_challenge` | Identity verification (account #, DOB, SSN last 4) | `method`, `max_attempts` |
| `platform.human_handoff` | Transfer to live agent | `priority`, `reason`, `metadata` |
| `subgraph` | Delegate to a named subgraph | `subgraph` |
| `custom` | Team-provided async Python function | `handler` |

---

## 9. Handler Contract

Every custom handler is a simple async function:

```python
from platform_core.state import ConversationState
from typing import Any

async def my_handler(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """
    Args:
        state: Full conversation state (messages, extracted_data, user_context)
        config: Node config from workflow.yaml

    Returns:
        {
            "result": str,       # routing key (e.g., "success", "invalid")
            "data": dict,        # merged into state.extracted_data
            "message": str|None  # optional assistant message
        }
    """
```

This is intentionally minimal — teams import nothing beyond `ConversationState` and return a dict.

---

## 10. Project Structure

```
ai-app-platform/
├── pyproject.toml                     # UV workspace root
├── src/
│   └── platform_core/                 # The shared platform library
│       ├── __init__.py
│       ├── engine/
│       │   ├── workflow_parser.py     # YAML → internal model
│       │   ├── graph_builder.py       # Internal model → LangGraph StateGraph
│       │   ├── node_executor.py       # Execute node with tracing + guardrails
│       │   └── state.py              # ConversationState definition
│       ├── nodes/
│       │   ├── base.py
│       │   ├── llm_response.py
│       │   ├── llm_conversation.py
│       │   ├── auth_challenge.py
│       │   └── human_handoff.py
│       ├── routers/
│       │   ├── base.py
│       │   ├── llm_intent.py
│       │   └── validation_result.py
│       ├── guardrails/
│       │   ├── base.py               # BaseGuardrail + GuardrailResult
│       │   ├── pipeline.py           # Orchestrates tier 1→2→3
│       │   ├── pii_detection.py
│       │   ├── pii_redaction.py
│       │   ├── harmful_content.py
│       │   └── prompt_injection.py
│       ├── observability/
│       │   ├── langfuse_tracer.py    # Auto-wraps all nodes with Langfuse spans
│       │   └── metrics.py
│       ├── auth/
│       │   ├── base.py
│       │   └── identity_verifier.py
│       ├── llm/
│       │   ├── provider.py           # Unified interface
│       │   └── config.py             # Model registry
│       └── discovery.py              # Scans features/ and loads workflows
│
├── features/                          # One directory per feature (team-owned)
│   ├── address_change/
│   │   ├── __init__.py
│   │   ├── workflow.yaml
│   │   ├── handlers.py               # validate_with_usps, update_address_in_crm
│   │   └── prompts/
│   │       ├── greeting.jinja2
│   │       ├── collect_address.jinja2
│   │       └── confirm_address.jinja2
│   ├── account_activation/
│   │   ├── __init__.py
│   │   ├── workflow.yaml
│   │   ├── handlers.py               # check_eligibility, activate_account
│   │   └── prompts/
│   ├── card_replacement/
│   │   ├── __init__.py
│   │   ├── workflow.yaml
│   │   ├── handlers.py               # block_card, create_replacement_order
│   │   └── prompts/
│   └── _template/                     # Scaffold for new features
│       ├── __init__.py
│       ├── workflow.yaml.template
│       ├── handlers.py.template
│       └── prompts/
│
├── tests/
│   ├── platform_core/
│   └── features/
├── docs/
│   ├── PRD.md                         # ← this document
│   └── onboarding.md
└── scripts/
    ├── new_feature.py                 # CLI: scaffold a new feature
    └── run_feature.py                 # CLI: run a feature locally
```

---

## 11. Example: What a Team Actually Writes

**Team #1 (Address Change)** writes only:

### `features/address_change/workflow.yaml` (~60 lines)

Declares nodes, edges, which guardrails to enable, and which model to use.

### `features/address_change/handlers.py` (~80 lines)

```python
async def validate_with_usps(state, config):
    address = state.extracted_data
    result = await usps_client.validate(address)
    if result.valid:
        return {"result": "valid", "data": {"standardized": result.standardized}}
    return {"result": "invalid", "message": "That address couldn't be verified."}

async def update_address_in_crm(state, config):
    await crm_client.update_address(state.user_id, state.extracted_data["standardized"])
    return {"result": "success", "message": "Your address has been updated!"}
```

### `features/address_change/prompts/*.jinja2` (~30 lines total)

Prompt templates for each conversational node.

**Total team-owned code: ~170 lines.** Everything else (LangGraph wiring, guardrails, tracing, auth, handoff) comes from the platform.

---

## 12. Shared "Transfer to Support" — Platform-Level Feature

All three teams need "transfer to human support." This is a **platform-provided node type** (`platform.human_handoff`) and a **global edge pattern**:

```yaml
# In ANY workflow.yaml — just declare the global edge:
global_edges:
  - trigger: llm_intent
    intent: transfer_support
    to: human_handoff

nodes:
  - id: human_handoff
    type: platform.human_handoff
    config:
      priority: normal
      reason: customer_requested
```

The platform's LLM intent router automatically checks every user message against global edge intents **before** routing to the current node's local edges. If the user says "I want to talk to a person," the platform routes to `human_handoff` regardless of which node the conversation is currently in.

Teams write **zero code** for this capability.

---

## 13. Observability (Langfuse Integration)

The platform auto-instruments every workflow execution:

| What's Traced | Langfuse Concept | Automatic? |
|---|---|---|
| Full conversation | **Trace** | ✅ |
| Each node execution | **Span** | ✅ |
| LLM calls | **Generation** | ✅ |
| Guardrail checks | **Span** (nested) | ✅ |
| Handler duration + result | **Span** | ✅ |
| Token usage + cost | **Generation metadata** | ✅ |
| Prompt templates | **Prompt management** | ✅ (opt-in) |

Teams get full observability **for free** — no code required. They can add custom Langfuse events in handlers if needed:

```python
from platform_core.observability import current_trace

async def my_handler(state, config):
    current_trace().event(name="crm_call", metadata={"account": state.user_id})
    ...
```

---

## 14. Authentication Module

Platform provides a configurable auth challenge node:

| Method | What It Verifies | Config Key |
|---|---|---|
| `account_number_dob` | Account # + date of birth | Team #1 uses this |
| `account_number_ssn_last4` | Account # + last 4 of SSN | Team #2, #3 use this |
| `mfa_code` | One-time code sent to phone/email | Future |
| `custom` | Team provides own verification handler | Full flexibility |

Teams select method in workflow.yaml. Platform handles retry logic, lockout, and audit logging.

---

## 15. Deployment Model

### Phase 1: Single Process (Monolith)

All features run together in one process. The platform's discovery mechanism loads all `features/*/workflow.yaml` at startup and exposes them via a unified API (FastAPI/Starlette):

```
POST /api/v1/{feature_name}/chat
```

### Phase 2: Feature Isolation (Optional)

Features can be deployed as isolated containers. Since each feature is self-contained in its directory, extraction is trivial:

```bash
# Deploy only card_replacement
uv run scripts/run_feature.py --feature card_replacement --port 8001
```

### Future: Library Extraction

Platform core becomes a published package:

```bash
uv add ai-app-platform-core
```

Teams create their own repos with just their `features/` directory + a thin entry point.

---

## 16. Developer Experience

### Scaffolding a New Feature

```bash
uv run scripts/new_feature.py --name dispute_resolution
# Creates features/dispute_resolution/ with workflow.yaml template, handlers.py, prompts/
```

### Running Locally

```bash
uv run scripts/run_feature.py --feature address_change
# Starts local server with hot-reload, connects to Langfuse dev project
```

### Testing

```bash
uv run pytest tests/features/test_address_change.py
# Runs with mocked LLM, verifies conversation flows end-to-end
```

---

## 17. Testing Strategy

| Layer | Type | What to Verify |
|---|---|---|
| Platform engine | Unit | YAML parsing, graph construction, state management |
| Built-in nodes | Unit | Correct LLM calls, output formatting |
| Guardrails | Unit | Detection accuracy, redaction correctness |
| Feature handlers | Unit | Business logic in isolation (mock external services) |
| Feature workflows | Integration | End-to-end conversation with mocked LLM |
| Full stack | E2E | Real LLM, real Langfuse, smoke tests |

---

## 18. Success Metrics

| Metric | Target |
|---|---|
| Time from kickoff to production for new feature | < 4 weeks |
| Lines of team-written code per feature | < 200 |
| Conversation completion rate | > 80% |
| Human handoff rate | < 15% |
| Guardrail false positive rate | < 5% |
| Langfuse trace coverage | 100% of conversations |

---

## 19. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| YAML config becomes complex for advanced flows | Provide schema validation, IDE autocomplete via JSON Schema, scaffold tooling |
| LLM intent routing misclassifies | Tunable intent prompts per feature; fallback to "ask_clarification" node; monitoring in Langfuse |
| Guardrails false positives block legitimate requests | Per-feature threshold tuning; Langfuse dashboard for guardrail trigger rates |
| Platform becomes bottleneck (all teams depend on core team) | Clear API contracts; teams can always drop to `custom` node/router type; semantic versioning |
| Vendor lock-in (OpenAI) | LLM provider abstraction; swap model via single config change |

---

## 20. Phase 1 Deliverables

1. **Platform Core Engine** — YAML parser, graph builder, node executor, state manager
2. **Built-in Node Types** — llm_response, llm_conversation, auth_challenge, human_handoff, subgraph, custom
3. **Router Types** — llm_intent, direct, validation_result, custom
4. **Guardrails Pipeline** — Mandatory (PII detection, harmful content, prompt injection) + optional + custom
5. **Langfuse Integration** — Automatic tracing for all nodes, LLM calls, guardrail checks
6. **LLM Provider Abstraction** — OpenAI + Anthropic via config
7. **Three Reference Features** — address_change, account_activation, card_replacement
8. **Developer Tooling** — `new_feature.py` scaffold, `run_feature.py` local runner
9. **Documentation** — This PRD, architecture guide, feature onboarding guide
10. **Test Suite** — Unit + integration tests for platform and all reference features

---

## 21. Open Questions

1. **State persistence** — Use LangGraph's built-in checkpointing (SQLite/Postgres) or custom?
2. **Multi-turn session management** — WebSocket vs. stateless HTTP with session ID?
3. **Secrets management** — Vault, AWS Secrets Manager, or env vars for v1?
4. **CI/CD** — Shared pipeline or per-feature pipelines?
5. **Rate limiting** — Platform-level or delegated to API gateway?

---

## Appendix: Feature Workflow Examples

See existing workflows:
- [`features/address_change/workflow.yaml`](../features/address_change/workflow.yaml)
- [`features/account_activation/workflow.yaml`](../features/account_activation/workflow.yaml)
- [`features/card_replacement/workflow.yaml`](../features/card_replacement/workflow.yaml)


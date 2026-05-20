# Product Requirements Document: AI Application Platform

**Version:** 1.1  
**Date:** May 19, 2026  
**Status:** Implemented  
**Type:** Demo / Proof-of-Concept  

---

## Demo Scope & Implementation Depth

> **This is a demo/proof-of-concept project.** The goal is to validate the platform architecture and workflow engine — not to ship production-ready integrations for every module.

### Implementation Depth by Module

| Module | Depth | What to Implement |
|--------|-------|-------------------|
| **Workflow Engine** | ✅ Full | YAML parser, graph builder, node executor, state manager — this is the core of the platform |
| **Guardrails** | ✅ Working examples | Implement **PII detection** (Presidio-based) and **max length check** (block inputs over 250 words). Enough to demonstrate the guardrail pipeline, registry pattern, and how teams enable/disable them. |
| **Langfuse** | 🔲 Stub/interface only | Define the tracing interface and decorators. Actual Langfuse client setup is deferred — use print/logging as placeholder. |
| **Auth Module** | 🔲 Stub/interface only | Define the `auth_challenge` node interface. Implement a mock verifier that always succeeds (or checks hardcoded values). No real JWT/OAuth. |
| **Human Handoff** | 🔲 Stub/interface only | Define the `human_handoff` node interface. Implementation logs the handoff event and returns a message — no real WebSocket/CRM integration. |
| **LLM Provider** | ✅ Working | Implement OpenAI/Azure OpenAI provider with the abstraction layer. Other providers are stubs. |
| **Tests** | 🔲 Deferred | No test cases for the demo. Testing strategy and examples below are kept as reference for future implementation. |

### Implementation Depth by Feature

| Feature | Depth | What to Implement |
|---------|-------|-------------------|
| **Reduce Credit Limit** | ✅ Full implementation | Complete workflow with all handlers, templates, subgraphs (reduce flow + tracking flow). This is the **reference feature** demonstrating the full platform capability. |
| **Address Change** | 🔲 Minimal demo | Workflow YAML fully defined. Handlers return mock/hardcoded data. Templates are simple placeholders. Enough to show a second feature running on the platform. |
| **Account Activation** | 🔲 Minimal demo | Same as address change — workflow YAML defined, stub handlers, placeholder templates. Demonstrates a third feature with different guardrails (document_verification). |

---

## Problem Statement

Enterprise teams in insurance and financial services organizations want to build agentic AI applications (customer service chatbots) but face significant barriers:

1. **Duplicated effort** — Each team rebuilds common capabilities (guardrails, authentication, observability, human handoff) from scratch
2. **AI expertise required** — Teams need deep knowledge of LangGraph, LLM orchestration, and AI deployment patterns
3. **Inconsistent security** — PII detection, content filtering, and compliance controls vary across applications
4. **No observability standard** — Each team implements their own logging/tracing, making cross-application monitoring difficult
5. **Slow time-to-market** — Building foundational infrastructure delays business value delivery

Development teams should focus on their **business logic** (address changes, account activation, credit limit management) while the platform handles cross-cutting concerns. The codebase is organized by **features**, not by team names, enabling clean separation and future multi-repository extraction.

---

## Solution

Build an **Agentic AI Application Platform** in a single repository where teams define workflows in **YAML configuration** and implement only their custom business logic in Python. The platform provides all common modules (guardrails, authentication, observability, LLM orchestration) as an internal library.

**Repository Organization:** The codebase is organized by **features** (address_change, account_activation, reduce_credit_limit), not by team names. This enables:
- Clean separation of concerns
- Feature ownership by different teams
- Easy extraction to multi-repo when needed

**Phase 1:** All features in a single repository with modular platform architecture.  
**Future:** The platform core can be extracted as a published library, enabling teams to work in separate repositories with their owned features.

### Core Value Proposition

| Without Platform | With Platform |
|------------------|---------------|
| Teams write ~2000+ lines of LangGraph boilerplate | Teams write ~50-100 lines of custom Python |
| Each team implements guardrails differently | Platform enforces consistent security controls |
| No standard observability | Built-in Langfuse tracing for all applications |
| 3-6 months to deploy a chatbot | 2-4 weeks to deploy a chatbot |
| Deep AI/ML expertise required | Business logic expertise sufficient |

---

## User Stories

### Platform Team (Builders)

1. As a **platform engineer**, I want to define reusable node types (llm_response, auth_challenge, human_handoff), so that application teams don't reinvent common patterns.
2. As a **platform engineer**, I want to configure mandatory guardrails at the platform level, so that all applications meet compliance requirements.
3. As a **platform engineer**, I want to build the platform as an internal library/module, so that it can be extracted as a published package in the future.
4. As a **platform engineer**, I want to provide a workflow schema validator, so that teams get immediate feedback on configuration errors.
5. As a **platform engineer**, I want to version platform components independently of feature implementations, so that features can be updated without platform changes.
6. As a **security engineer**, I want to enforce PII detection and redaction across all applications, so that sensitive data is never exposed to LLMs inappropriately.
7. As a **security engineer**, I want certain guardrails to be non-overridable, so that features cannot accidentally disable critical protections.
8. As a **DevOps engineer**, I want to support both shared and isolated deployments, so that features can be deployed based on their requirements.
9. As a **platform engineer**, I want clear module boundaries between platform and features, so that future extraction to separate repos is straightforward.

### Application Teams (Users)

10. As an **application developer**, I want to define my workflow in YAML, so that I don't need to learn LangGraph internals.
11. As an **application developer**, I want to write only my business logic handlers in Python, so that I can focus on domain expertise.
12. As an **application developer**, I want to use LLM-based routing for conditional edges, so that my chatbot can dynamically respond to user intent.
13. As an **application developer**, I want to define subgraphs for complex flows, so that I can organize multi-step processes cleanly.
14. As an **application developer**, I want to specify which LLM model my workflow uses, so that I can balance cost and capability.
15. As an **application developer**, I want to add team-specific guardrails on top of platform defaults, so that I can enforce domain-specific rules.
16. As an **application developer**, I want to override optional guardrails when my use case requires it, so that I have flexibility within safety bounds.
17. As an **application developer**, I want to use platform-provided prompt templates, so that I maintain consistent user experience.
18. As an **application developer**, I want to define structured output schemas, so that LLM responses are typed and validated.
19. As an **application developer**, I want global edges for human handoff, so that users can transfer to support from any point in the conversation.
20. As an **application developer**, I want to reuse platform authentication modules, so that I don't implement identity verification myself.

### End Users (Customers)

21. As a **customer**, I want to change my address through the chatbot, so that I don't have to call customer service.
22. As a **customer**, I want to activate my account through the chatbot, so that I can start using services immediately.
23. As a **customer**, I want to reduce my credit card limit through the chatbot, so that I can better manage my spending.
24. As a **customer**, I want to transfer to a human agent at any time, so that I can get help with complex issues.
25. As a **customer**, I want the chatbot to verify my identity securely, so that my account is protected.
26. As a **customer**, I want clear confirmation before changes are made, so that I don't accidentally make mistakes.
27. As a **customer**, I want to track the status of my requests, so that I know when to expect resolution.

### Observability & Operations

28. As an **operations engineer**, I want all LLM calls traced in Langfuse, so that I can debug conversation flows.
29. As an **operations engineer**, I want to see which guardrails triggered for each conversation, so that I can tune false positive rates.
30. As an **operations engineer**, I want to monitor latency per node, so that I can identify performance bottlenecks.
31. As an **operations engineer**, I want to view conversation transcripts with PII redacted, so that I can troubleshoot without exposure risk.
32. As a **product manager**, I want to see completion rates per workflow, so that I can measure chatbot effectiveness.
33. As a **product manager**, I want to see human handoff rates, so that I can identify flows that need improvement.

---

## Implementation Decisions

### Architecture Overview

**Current State:** Single repository with modular platform architecture  
**Future State:** Platform can be extracted as a library for multi-repo teams

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI APPLICATION PLATFORM                            │
│                         (Single Repo, Modular Design)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Guardrails │  │   Langfuse  │  │    Auth     │  │   Human Handoff     │ │
│  │   Module    │  │  Tracing    │  │   Module    │  │     Interface       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                          WORKFLOW ENGINE (LangGraph)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  YAML Parser → Graph Builder → Node Executor → State Manager            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│                          PLATFORM NODE TYPES                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │llm_response│ │llm_convers.│ │auth_challen│ │human_handof│ │  subgraph  ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│                          ROUTER TYPES                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────────┐ ┌──────────────────────────┐│
│  │ llm_intent │ │   direct   │ │validation_result│ │    custom (team)       ││
│  └────────────┘ └────────────┘ └────────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│ Address Change  │        │ Account Activ.  │        │ Reduce Credit   │
│  Config         │        │  Config         │        │  Limit Config   │
│  + Handlers     │        │  + Handlers     │        │  + Handlers     │
│                 │        │                 │        │                 │
│ Workflow        │        │ Workflow        │        │ Workflow        │
└─────────────────┘        └─────────────────┘        └─────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Workflow Engine | LangGraph | Industry standard for agentic workflows, supports subgraphs and conditional routing |
| Observability | Langfuse | Purpose-built for LLM observability, supports tracing, evaluation, and prompt management |
| Guardrails | Guardrails AI + LangChain | Combine structural validation (Guardrails AI) with content filtering (LangChain) |
| Package Manager | UV | Fast, reliable Python dependency management |
| Configuration | YAML | Human-readable, version-controllable, easy to validate |
| LLM Providers | OpenAI, Anthropic, Azure OpenAI | Support multiple providers with unified interface |

### Workflow Configuration Format

Teams define workflows in YAML with the following structure:

```yaml
extends: ../../platform/workflows/_base.yaml  # Optional — inherit from a base workflow

workflow:
  name: string                    # Unique workflow identifier
  description: string             # Human-readable description

  llm:                            # Default LLM configuration (overrides base field-by-field)
    provider: string              # azure_openai | openai | anthropic | bedrock
    model: string                 # gpt-4o, claude-3-opus, etc.
    temperature: float            # 0.0 - 1.0 (default: 0.1)

  global_edges:                   # Edges available from ANY node (concatenated with base)
    - trigger: llm_intent
      intent: string
      to: node_id

  guardrails:
    mandatory: [string]           # Appended to base mandatory list (cannot remove base guardrails)
    optional: [string]            # Appended to base optional list

  nodes:
    - id: string
      type: platform_node_type | custom
      handler: string             # Python handler path (for custom nodes)
      prompt_template: string     # Jinja2 template path
      output_schema: string       # Schema name for structured output
      config: object              # Node-specific configuration

  edges:
    # Unconditional edge — always routes to target
    - from: string
      to: string

    # Conditional edge — explicit router type for auditability
    - from: string
      router: router_type         # llm_intent | validation_result | direct | custom
      description: string         # Optional: explains the routing decision (shown in Langfuse)
      routes:
        route_key: node_id                 # Short form
        route_key:                         # Long form (when clarity matters)
          to: node_id
          label: "Human-readable reason"   # Shown in debug logs & Langfuse

subgraphs:
  subgraph_name:
    description: string
    nodes: [...]
    edges: [...]                  # Same edge format as above

schemas:
  SchemaName:
    type: object
    properties: {...}
    required: [...]
```

**`extends` Key — Workflow Inheritance:**

A feature workflow can inherit from a base workflow using `extends: <relative-path>`. The parser applies the following merge rules:

| Section | Merge Rule |
|---------|------------|
| `llm` | Feature fields override base field-by-field |
| `global_edges` | Concatenated — base first |
| `guardrails.mandatory` | Concatenated, deduped — features can **add**, never remove |
| `guardrails.optional` | Concatenated, deduped |
| `nodes` | Merged by `id` — same id deep-merges `config`; new ids appended |
| `edges` | Concatenated — base edges first, feature edges after |
| `subgraphs` / `schemas` | Feature keys override base keys |

The base workflow `platform/workflows/_base.yaml` defines the shared auth flow, common nodes (greet, verify_identity, collect_intent, human_handoff, farewell), and platform-wide guardrails. Feature workflows only declare their unique nodes and edges.

**Edge Format — Two Styles in One List:**

All edges live in a single `edges` list. Each edge is either:
- **Unconditional**: `from` + `to` — always routes to the target node
- **Conditional**: `from` + `router` + `routes` — routes based on the named router mechanism

**Route Value — Short and Long Form:**

Both forms are valid and can be mixed within the same `routes` block:
```yaml
routes:
  valid: show_confirmation                  # Short: just the target node
  invalid:                                  # Long: target + human-readable label
    to: collect_address
    label: "Address failed USPS validation"
```
The `label` is optional and used for debugging, Langfuse trace metadata, and non-technical reviewers.

**`description` Field:**

Optional on every conditional edge. Describes *what question is being decided*. Appears in:
- Langfuse trace spans (searchable, filterable)
- Debug logs
- Workflow documentation auto-generation

### Platform Node Types

| Type | Description | Config Options |
|------|-------------|----------------|
| `llm_response` | Generate a single LLM response | `prompt_template` |
| `llm_conversation` | Multi-turn extraction with structured output | `prompt_template`, `output_schema` |
| `auth_challenge` | Verify user identity | `method`, `max_attempts` |
| `platform.human_handoff` | Transfer to human agent | `priority`, `reason` |
| `subgraph` | Execute a named subgraph | `subgraph` |
| `custom` | Team-provided Python handler | `handler` |

### Router Types

| Type | Description | How It Works | LLM Cost |
|------|-------------|--------------|----------|
| `llm_intent` | LLM classifies user intent | Platform sends conversation to LLM with intent options, returns matched route key | $$$ (1 LLM call per routing decision) |
| `validation_result` | Route based on handler return | Handler returns `{result: "valid"}`, router matches to route key | Free |
| `direct` | Unconditional routing | Always routes to the single specified node | Free |
| `custom` | Team-defined routing logic | Handler returns route key directly | Depends on implementation |

**Choosing a router type:**
- Use `llm_intent` when routing depends on **what the user said** (natural language understanding)
- Use `validation_result` when routing depends on **what a handler computed** (code logic) — e.g. `auth_challenge` routes `verified → collect_intent`, `failed → greet`, `max_attempts_exceeded → human_handoff`
- Use `direct` for unconditional transitions (can also use simple `from`/`to` edge instead)
- Use `custom` for complex routing that doesn't fit the above patterns

> **Auth flow pattern:** After `verify_identity` (`auth_challenge` node), always use `validation_result` to check whether authentication succeeded. Using `llm_intent` here would skip the auth result and route based on user message content instead.

### Guardrails Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GUARDRAILS PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│  INPUT                                                           │
│    │                                                             │
│    ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ MANDATORY GUARDRAILS (Platform-enforced, cannot disable)    ││
│  │  • pii_detection        - Detect SSN, credit cards, etc.    ││
│  │  • harmful_content      - Block toxic/harmful content        ││
│  │  • prompt_injection     - Detect injection attempts          ││
│  └─────────────────────────────────────────────────────────────┘│
│    │                                                             │
│    ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ OPTIONAL GUARDRAILS (Team can enable/disable/configure)     ││
│  │  • pii_redaction        - Redact detected PII               ││
│  │  • address_validation   - Validate address format           ││
│  │  • fraud_detection      - Flag suspicious patterns          ││
│  │  • document_verification- Verify uploaded documents         ││
│  └─────────────────────────────────────────────────────────────┘│
│    │                                                             │
│    ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TEAM GUARDRAILS (Team-defined, additive)                    ││
│  │  • Custom validators                                        ││
│  │  • Domain-specific rules                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│    │                                                             │
│    ▼                                                             │
│  OUTPUT (to LLM or next node)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Model

The platform supports two deployment modes from a single repository:

**Shared Deployment** (Default)
- Multiple feature workflows run in the same process
- Shared resources, lower infrastructure cost
- Suitable for features with similar security requirements
- Configuration-based isolation

**Isolated Deployment** (On Request)
- Feature workflow runs as separate process/container
- Full resource isolation
- Required for high-security or high-volume workflows
- Independent scaling

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHARED DEPLOYMENT                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Platform Process                              │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │  │
│  │  │  Address    │ │  Account    │ │  Reduce     │          │  │
│  │  │  Change     │ │  Activation │ │  Credit Lmt │          │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ISOLATED DEPLOYMENT                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Process 1  │  │  Process 2  │  │  Process 3  │             │
│  │  Address    │  │  Account    │  │  Reduce     │             │
│  │  Change     │  │  Activation │  │  Credit Lmt │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

**Future Multi-Repo Support:**

The platform is designed with clear module boundaries. In the future, `src/platform/` can be:
1. Extracted as a separate package (`ai-app-platform`)
2. Published to PyPI / private registry
3. Imported by teams in their own repositories

This requires no changes to the core platform code—only packaging and distribution setup.

### Project Structure

```
ai-app-platform/
├── pyproject.toml                    # UV project configuration
├── platform/
│   └── workflows/
│       └── _base.yaml                # Shared base workflow (auth flow, common nodes, guardrails)
├── src/
│   └── ai_platform/
│       ├── __init__.py
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── workflow_parser.py    # YAML → ParsedWorkflow (supports extends)
│       │   ├── graph_builder.py      # Build StateGraph from config
│       │   ├── node_executor.py      # Execute nodes with tracing
│       │   └── state_manager.py      # Conversation state
│       ├── nodes/
│       │   ├── __init__.py
│       │   ├── llm_response.py       # llm_response node type
│       │   ├── llm_conversation.py   # llm_conversation node type
│       │   ├── auth_challenge.py     # auth_challenge node type
│       │   └── human_handoff.py      # human_handoff node type
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── llm_intent.py         # LLM-based intent routing
│       │   └── base.py               # Router interface
│       ├── guardrails/
│       │   ├── __init__.py
│       │   ├── pipeline.py           # Guardrails orchestration
│       │   ├── pii_detection.py
│       │   ├── harmful_content.py
│       │   └── prompt_injection.py
│       ├── observability/
│       │   ├── __init__.py
│       │   └── langfuse_tracer.py    # Langfuse integration
│       └── auth/
│           ├── __init__.py
│           └── identity_verifier.py  # End-user authentication
├── features/                          # Complete feature modules (one directory per feature)
│   ├── address_change/
│   │   ├── __init__.py
│   │   ├── workflow.yaml             # extends _base.yaml; overrides auth method to account_number_dob
│   │   ├── handlers.py               # validate_with_usps, update_address_in_crm
│   │   └── templates/
│   │       ├── greeting.jinja2
│   │       ├── collect_intent.jinja2  # Post-auth intent collection
│   │       ├── collect_address.jinja2
│   │       ├── confirm_address.jinja2
│   │       └── address_updated.jinja2
│   ├── account_activation/
│   │   ├── __init__.py
│   │   ├── workflow.yaml             # extends _base.yaml
│   │   ├── handlers.py               # check_activation_eligibility, activate_account
│   │   └── templates/
│   │       ├── greeting.jinja2
│   │       ├── collect_intent.jinja2  # Post-auth intent collection
│   │       ├── account_preferences.jinja2
│   │       └── activation_complete.jinja2
│   └── reduce_credit_limit/
│       ├── __init__.py
│       ├── workflow.yaml             # extends _base.yaml; adds credit_validation guardrail
│       ├── handlers.py               # validate_reduction_request, apply_credit_reduction, etc.
│       └── templates/
│           ├── greeting.jinja2
│           ├── collect_intent.jinja2  # Post-auth intent collection (reduce vs track)
│           ├── current_limit_info.jinja2
│           ├── enter_new_limit.jinja2
│           ├── confirm_reduction.jinja2
│           ├── reduction_complete.jinja2
│           ├── limit_too_low.jinja2
│           ├── pending_changes_status.jinja2
│           ├── no_pending_changes.jinja2
│           └── cancel_confirmation.jinja2
├── tests/
│   ├── platform/
│   │   ├── test_workflow_parser.py
│   │   ├── test_graph_builder.py
│   │   └── test_guardrails.py
│   └── features/
│       ├── test_address_change.py
│       ├── test_account_activation.py
│       └── test_reduce_credit_limit.py
└── docs/
    ├── PRD.md                        # This document
    ├── architecture.md
    └── feature-onboarding.md
```

**Complete Feature Encapsulation:**

Each feature directory contains **everything** related to that feature:
- ✅ `workflow.yaml` — Workflow configuration
- ✅ `handlers.py` — Custom business logic
- ✅ `templates/` — Jinja2 prompt templates
- ✅ `__init__.py` — Python module marker

**Benefits:**
- 🎯 **Single location** — Team works in one directory
- 📦 **Easy extraction** — Just copy the feature folder to a new repo
- 🔍 **Clear boundaries** — All feature code is self-contained
- 🚀 **Simple onboarding** — New developers understand the structure instantly

**Platform Discovery:**

The platform discovers all features by scanning:
```python
# Platform automatically finds all features
features = glob("features/*/workflow.yaml")
```

### API Contracts

**Handler Interface**

All custom handlers must follow this interface:

```python
from typing import Any
from platform.engine.state_manager import ConversationState

async def handler_name(
    state: ConversationState,
    config: dict[str, Any]
) -> dict[str, Any]:
    """
    Args:
        state: Current conversation state (messages, extracted data, user context)
        config: Node configuration from YAML
    
    Returns:
        dict with:
          - 'result': string key for routing (e.g., 'valid', 'invalid', 'success')
          - 'data': any data to merge into state
          - 'message': optional message to add to conversation
    """
    pass
```

**Guardrail Interface**

```python
from typing import Any
from platform.guardrails.base import GuardrailResult

class CustomGuardrail:
    def __init__(self, config: dict[str, Any]):
        self.config = config
    
    async def check(self, input_text: str, context: dict) -> GuardrailResult:
        """
        Returns:
            GuardrailResult with:
              - passed: bool
              - modified_text: str (if redaction applied)
              - violations: list of detected issues
        """
        pass
```

---

## Testing Decisions

> ⚠️ **Deferred for demo.** No test cases will be implemented in the initial demo. The strategy and examples below are kept as reference for future implementation.

### What Makes a Good Test

Tests should verify **external behavior**, not implementation details:
- Test that a workflow produces expected outputs for given inputs
- Test that guardrails block/allow appropriate content
- Test that handlers return correct results and state updates
- Do NOT test internal method calls or LangGraph internals

### Testing Strategy

| Layer | Test Type | What to Test |
|-------|-----------|--------------|
| Platform Engine | Unit | YAML parsing, graph building, state management |
| Platform Nodes | Unit | Each node type produces correct output |
| Platform Routers | Unit | Intent classification, route selection |
| Guardrails | Unit | PII detection accuracy, content filtering |
| Feature Handlers | Unit | Business logic in isolation |
| Feature Workflows | Integration | End-to-end conversation flows with mocked LLM |
| Full Platform | E2E | Real LLM calls, complete workflows |

### Test Examples

```python
# Platform node test
async def test_auth_challenge_success():
    state = ConversationState(user_id="test_user")
    node = AuthChallengeNode(config={"method": "account_number_dob"})
    
    # Simulate correct answers
    state.add_message("user", "My account is 12345 and DOB is 01/15/1990")
    result = await node.execute(state)
    
    assert result["result"] == "verified"
    assert state.identity_verified == True

# Feature handler test
async def test_validate_with_usps_valid_address():
    state = ConversationState()
    state.extracted_data = {features/address_change/workflow
        "street_address": "1600 Pennsylvania Ave NW",
        "city": "Washington",
        "state": "DC",
        "zip_code": "20500"
    }
    
    result = await validate_with_usps(state, {})
    
    assert result["result"] == "valid"
    assert result["data"]["standardized_address"] is not None

# Workflow integration test
async def test_address_change_happy_path(mock_llm):
    workflow = load_workflow("workflows/address_change.yaml")
    
    conversation = [
        ("user", "Hi, I want to change my address"),
        ("user", "Account 12345, DOB 01/15/1990"),  # Auth
        ("user", "123 New Street, Springfield, IL 62701"),  # Address
        ("user", "Yes, that's correct"),  # Confirm
    ]
    
    result = await run_workflow(workflow, conversation)
    
    assert result.completed == True
    assert result.final_node == "farewell"
    assert "address_updated" in result.state.completed_actions
```

---

## Out of Scope

The following are explicitly **out of scope** for the initial platform release:

1. **Real-time human handoff** — Platform provides an abstract interface; actual WebSocket/live agent integration is deferred
2. **Multi-language support** — Initial release supports English only
3. **Voice channel** — Text-based chatbot only; voice/telephony integration is future work
4. **Custom LLM fine-tuning** — Teams use pre-trained models; fine-tuning infrastructure not provided
5. **Visual workflow builder** — Teams define workflows in YAML; GUI editor is future enhancement
6. **A/B testing framework** — Workflow variants and experimentation not included in v1
7. **Billing/metering** — No per-team usage tracking or chargeback in initial release
8. **Self-service deployment** — Central platform team deploys all applications

---

## Further Notes

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| YAML complexity grows | Teams struggle with large configs | Provide schema validation, IDE extension, and examples |
| LLM routing unreliable | Conversations go to wrong nodes | Fine-tune intent prompts, add fallback handling, monitor routing accuracy |
| Guardrails false positives | Legitimate requests blocked | Tune thresholds per workflow, provide bypass for verified users |
| Performance bottlenecks | Slow response times | Cache LLM responses where appropriate, optimize guardrails pipeline |

### Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Time to deploy new workflow | < 4 weeks | Track from kickoff to production |
| Lines of custom code per feature | < 200 | Count feature-specific Python lines |
| Conversation completion rate | > 80% | Langfuse funnel analysis |
| Human handoff rate | < 15% | Track transfers per workflow |
| Guardrail false positive rate | < 5% | Sample and review blocked conversations |

### Phase 1 Deliverables (Demo)

1. Platform engine (YAML parser, graph builder, node executor)
   - `extends` support in YAML parser — feature workflows inherit from `platform/workflows/_base.yaml`
   - Merge rules: scalars override, lists concatenate, nodes merge by id, config dicts deep-merge
2. Core node types (llm_response, llm_conversation, auth_challenge stub, human_handoff stub)
3. Core routers (llm_intent, direct, validation_result)
   - Debug logging: `[ROUTER]` and `[EDGE]` log lines for every routing decision
4. Guardrails — working implementations:
   - `pii_detection` — Presidio-based PII detection
   - `max_length_check` — Blocks user input exceeding 250 words
   - Guardrail pipeline, registry pattern, and per-feature enable/disable
5. Langfuse — interface/stubs only (print/logging placeholder)
6. Auth — mock verifier only (hardcoded values)
7. Human handoff — stub that logs event and returns message
8. **Base workflow template** (`platform/workflows/_base.yaml`):
   - Shared LLM config, global transfer-to-support edge, mandatory guardrails
   - Common nodes: greet, verify_identity, collect_intent, human_handoff, farewell
   - Correct auth flow: `verify_identity` routes via `validation_result` (verified → collect_intent, failed → greet, max_attempts_exceeded → human_handoff)
9. **Reduce Credit Limit** — fully implemented (reference feature):
   - All handlers with real business logic (validate, check limits, apply reduction, track pending changes)
   - All Jinja2 templates (including collect_intent.jinja2)
   - Both subgraphs (reduce flow + limit change tracking)
   - Optional guardrail: `credit_validation`
10. **Address Change** — minimal demo (extends _base.yaml, overrides auth method to `account_number_dob`, stub handlers)
11. **Account Activation** — minimal demo (extends _base.yaml, stub handlers)
12. Documentation and feature onboarding guide

---

## Appendix: Example Feature Workflows

See the following feature directories for complete implementations:

- [platform/workflows/_base.yaml](../platform/workflows/_base.yaml) — ✅ Shared base workflow (auth flow, common nodes, platform guardrails)
- [Reduce Credit Limit Feature](../features/reduce_credit_limit/) — ✅ **Fully implemented** reference feature (extends _base.yaml, handlers, templates, both subgraphs, credit_validation guardrail)
- [Address Change Feature](../features/address_change/) — ✅ Minimal demo (extends _base.yaml, overrides auth method to `account_number_dob`, stub handlers)
- [Account Activation Feature](../features/account_activation/) — ✅ Minimal demo (extends _base.yaml, stub handlers)

---

## Future: Multi-Repository Architecture

The platform is designed to support future extraction into separate repositories:

**Phase 2: Library Extraction**
1. Extract `src/platform/` as standalone package
2. Publish to PyPI / private registry as `ai-app-platform`
3. Teams create their own repositories (organized by features they own)
4. Teams install via: `uv add ai-app-platform`
simply takes their feature directory:
- Team A Repository: Copy entire `address_change/` directory (workflow.yaml + handlers.py + templates/)
- Team B Repository: Copy entire `account_activation/` directory
- Team C Repository: Copy entire `reduce_credit_limit/` directory

**Benefits of Future Multi-Repo:**
- ✅ Team autonomy (own repo, deployment, schedule)
- ✅ Independent scaling per feature
- ✅ Version flexibility (upgrade library independently)
- ✅ Blast radius containment (issues in one feature don't affect others)
- ✅ Deployment freedom (K8s, Lambda, VMs)
- ✅ **Zero refactoring** — feature directory structure stays the same

**No Code Changes Required:**  
The modular design ensures that when teams move to separate repos:
1. Install the platform library: `uv add ai-app-platform`
2. Copy entire feature directory: `cp -r features/address_change/ team-repo/`
3. Import platform: `from ai_app_platform import WorkflowEngine`
4. Load workflow: `engine.load("address_change/workflow.yaml")
2. Copy their feature's workflow YAML and handlers
3. Import: `from platform import WorkflowEngine`

from __future__ import annotations

import asyncio
import functools
import logging
import uuid
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from ai_platform.engine.node_executor import NodeExecutor
from ai_platform.engine.state_manager import ConversationState
from ai_platform.engine.workflow_parser import (
    EdgeConfig,
    NodeConfig,
    ParsedWorkflow,
    RouteTarget,
    SubgraphConfig,
    WorkflowConfig,
    parse_workflow_file,
)
from ai_platform.routers.llm_intent import LLMIntentRouter

logger = logging.getLogger(__name__)

_executor = NodeExecutor()


def _resolve_node_id(name: str) -> str:
    if name == "START":
        return START
    if name == "END":
        return END
    return name


def _get_route_target(value: str | RouteTarget) -> str:
    if isinstance(value, RouteTarget):
        return _resolve_node_id(value.to)
    return _resolve_node_id(value)


def _make_node_fn(
    node_config: NodeConfig,
    workflow_config: WorkflowConfig,
    parsed_workflow: ParsedWorkflow,
    templates_dir: Path | None,
) -> Any:
    async def node_fn(state: ConversationState) -> dict[str, Any]:
        cfg = dict(node_config.config)
        if templates_dir:
            cfg["templates_dir"] = str(templates_dir)
        if node_config.prompt_template:
            cfg["prompt_template"] = node_config.prompt_template
        if node_config.output_schema:
            cfg["output_schema"] = node_config.output_schema
        return await _executor.execute_node(node_config, state, workflow_config, parsed_workflow)

    node_fn.__name__ = node_config.id
    return node_fn


def _make_validation_condition(routes: dict[str, str | RouteTarget]) -> Any:
    route_map = {k: _get_route_target(v) for k, v in routes.items()}

    def condition(state: ConversationState) -> str:
        last_result = state.user_context.get("_last_result", "")
        return route_map.get(last_result, next(iter(route_map.values())))

    return condition, route_map


def _make_llm_intent_condition(
    routes: dict[str, str | RouteTarget],
    description: str | None,
    workflow_config: WorkflowConfig,
) -> Any:
    route_map = {k: _get_route_target(v) for k, v in routes.items()}
    router = LLMIntentRouter(
        provider=workflow_config.llm.provider,
        model=workflow_config.llm.model,
        temperature=0.0,
    )

    async def condition(state: ConversationState) -> str:
        key = await router.route(state, routes={k: k for k in routes}, description=description)
        return route_map.get(key, next(iter(route_map.values())))

    return condition, route_map


class GraphBuilder:
    def _build_from_config(
        self,
        nodes: list[NodeConfig],
        edges: list[EdgeConfig],
        workflow_config: WorkflowConfig,
        parsed_workflow: ParsedWorkflow,
        global_edges: list | None = None,
        templates_dir: Path | None = None,
    ) -> StateGraph:
        graph = StateGraph(ConversationState)

        node_ids = {n.id for n in nodes}

        for node in nodes:
            fn = _make_node_fn(node, workflow_config, parsed_workflow, templates_dir)
            graph.add_node(node.id, fn)

        for edge in edges:
            src = _resolve_node_id(edge.from_node)
            if edge.to and not edge.router:
                dst = _resolve_node_id(edge.to)
                graph.add_edge(src, dst)
                continue

            if not edge.router or not edge.routes:
                continue

            if edge.router == "validation_result":
                condition, route_map = _make_validation_condition(edge.routes)
                graph.add_conditional_edges(src, condition, route_map)

            elif edge.router in ("llm_intent", "direct", "custom"):
                condition, route_map = _make_llm_intent_condition(
                    edge.routes, edge.description, workflow_config
                )
                graph.add_conditional_edges(src, condition, route_map)

        # Wire global edges from every named node
        if global_edges:
            for node in nodes:
                for global_edge in global_edges:
                    # global edges are intent-based; handled by adding conditional from each node
                    pass  # Graph-level global edges need a wrapper; handled at run time via pre-processing

        return graph

    def build(self, parsed_workflow: ParsedWorkflow) -> StateGraph:
        workflow_config = parsed_workflow.workflow

        # Determine templates_dir from the workflow location (resolved at build time)
        # Features live at features/{feature_name}/ — templates subdir
        # We'll leave templates_dir resolution to runtime (node_executor passes it)
        templates_dir = None

        return self._build_from_config(
            nodes=workflow_config.nodes,
            edges=workflow_config.edges,
            workflow_config=workflow_config,
            parsed_workflow=parsed_workflow,
            global_edges=workflow_config.global_edges,
            templates_dir=templates_dir,
        )

    async def run_workflow(
        self,
        workflow_path: str,
        initial_message: str,
        session_id: str | None = None,
    ) -> ConversationState:
        parsed = parse_workflow_file(workflow_path)
        graph = self.build(parsed)
        compiled = graph.compile()

        state = ConversationState(session_id=session_id or uuid.uuid4().hex)
        state.workflow_name = parsed.workflow.name
        state.add_message("user", initial_message)

        trace_id = state.session_id
        state.user_context["_trace_id"] = trace_id

        try:
            result = await compiled.ainvoke(state)
            if isinstance(result, dict):
                return ConversationState.model_validate(result)
            return result
        except Exception as exc:
            logger.error("Workflow execution error: %s", exc)
            return state

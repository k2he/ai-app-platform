from __future__ import annotations

import importlib
import logging
from typing import Any

from ai_platform.engine.state_manager import ConversationState
from ai_platform.engine.workflow_parser import NodeConfig, ParsedWorkflow, WorkflowConfig
from ai_platform.guardrails.pipeline import GuardrailPipeline
from ai_platform.nodes.auth_challenge import AuthChallengeNode
from ai_platform.nodes.human_handoff import HumanHandoffNode
from ai_platform.nodes.llm_conversation import LLMConversationNode
from ai_platform.nodes.llm_response import LLMResponseNode
from ai_platform.observability.langfuse_tracer import LangfuseTracer

logger = logging.getLogger(__name__)

_tracer = LangfuseTracer()


class NodeExecutor:
    async def execute_node(
        self,
        node_config: NodeConfig,
        state: ConversationState,
        workflow_config: WorkflowConfig,
        parsed_workflow: ParsedWorkflow,
    ) -> dict[str, Any]:
        # Run guardrails before executing the node
        last_message = state.get_last_user_message() or ""
        if last_message:
            guardrail_result = await GuardrailPipeline.run(
                input_text=last_message,
                mandatory=workflow_config.guardrails.mandatory,
                optional=workflow_config.guardrails.optional,
                context={"session_id": state.session_id, "node_id": node_config.id},
            )
            if not guardrail_result.passed:
                logger.warning(
                    "Guardrail blocked input at node=%s violations=%s",
                    node_config.id, guardrail_result.violations,
                )
                return {"result": "guardrail_blocked", "violations": guardrail_result.violations}

        state.current_node = node_config.id

        node_config_dict = dict(node_config.config)
        node_config_dict["llm"] = {
            "provider": workflow_config.llm.provider,
            "model": workflow_config.llm.model,
            "temperature": workflow_config.llm.temperature,
        }
        node_config_dict["schemas"] = parsed_workflow.schemas

        try:
            result = await self._dispatch(node_config, state, node_config_dict, parsed_workflow)
        except Exception as exc:
            logger.exception("Node %s raised an exception", node_config.id)
            return {"result": "error", "message": str(exc)}

        state.completed_actions.append(node_config.id)
        state.user_context["_last_result"] = result.get("result", "")

        trace_id = state.user_context.get("_trace_id", "")
        if trace_id:
            _tracer.log_span(
                trace_id=trace_id,
                name=node_config.id,
                input={"node_type": node_config.type},
                output=result,
            )

        return result

    async def _dispatch(
        self,
        node_config: NodeConfig,
        state: ConversationState,
        config: dict[str, Any],
        parsed_workflow: ParsedWorkflow,
    ) -> dict[str, Any]:
        node_type = node_config.type

        if node_type == "llm_response":
            return await LLMResponseNode().execute(state, config)

        if node_type == "llm_conversation":
            if node_config.prompt_template:
                config["prompt_template"] = node_config.prompt_template
            if node_config.output_schema:
                config["output_schema"] = node_config.output_schema
            return await LLMConversationNode().execute(state, config)

        if node_type == "auth_challenge":
            return await AuthChallengeNode().execute(state, config)

        if node_type in ("platform.human_handoff", "human_handoff"):
            return await HumanHandoffNode().execute(state, config)

        if node_type == "subgraph":
            return {"result": "subgraph", "subgraph": node_config.subgraph}

        if node_type == "custom":
            handler_path = node_config.handler
            if not handler_path:
                return {"result": "error", "message": "custom node missing handler"}
            module_path, func_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, func_name)
            return await handler(state, config)

        return {"result": "error", "message": f"Unknown node type: {node_type}"}

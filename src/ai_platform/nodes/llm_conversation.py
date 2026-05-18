from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ai_platform.engine.state_manager import ConversationState
from ai_platform.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)


class LLMConversationNode:
    async def execute(self, state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
        templates_dir = config.get("templates_dir")
        if not templates_dir:
            raise ValueError("config['templates_dir'] is required for LLMConversationNode")

        template_name = config.get("prompt_template", "")
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            autoescape=False,
        )
        template = env.get_template(template_name)
        rendered = template.render(**state.extracted_data, **state.user_context)

        llm_config = config.get("llm", {})
        provider = llm_config.get("provider", "openai")
        model = llm_config.get("model", "gpt-4o")
        temperature = llm_config.get("temperature", 0.1)

        if provider == "azure_openai":
            llm = AzureChatOpenAI(
                azure_deployment=model,
                temperature=temperature,
                model_kwargs={"response_format": {"type": "json_object"}},
            )
        else:
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                model_kwargs={"response_format": {"type": "json_object"}},
            )

        messages = [
            SystemMessage(content="You must respond with valid JSON only."),
            HumanMessage(content=rendered),
        ]
        response = await llm.ainvoke(messages)
        trace_llm_call(model=model)

        try:
            parsed = json.loads(response.content)
        except (json.JSONDecodeError, ValueError) as exc:
            return {"result": "invalid", "message": f"Schema validation failed: {exc}"}

        schema_name = config.get("output_schema")
        if schema_name:
            schemas = config.get("schemas", {})
            schema = schemas.get(schema_name, {})
            required_fields = schema.get("required", [])
            missing = [f for f in required_fields if f not in parsed]
            if missing:
                return {
                    "result": "invalid",
                    "message": f"Schema validation failed: missing fields {missing}",
                }

        state.merge_extracted_data(parsed)
        return {"result": "success", "data": parsed}

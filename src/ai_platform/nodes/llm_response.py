from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage

from ai_platform.engine.state_manager import ConversationState
from ai_platform.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)


class LLMResponseNode:
    async def execute(self, state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
        templates_dir = config.get("templates_dir")
        if not templates_dir:
            raise ValueError("config['templates_dir'] is required for LLMResponseNode")

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
            llm = AzureChatOpenAI(azure_deployment=model, temperature=temperature)
        else:
            llm = ChatOpenAI(model=model, temperature=temperature)

        response = await llm.ainvoke([HumanMessage(content=rendered)])
        response_text = response.content
        trace_llm_call(model=model)

        state.add_message("assistant", response_text)

        return {"result": "success", "message": response_text}

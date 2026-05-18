from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ai_platform.routers.base import BaseRouter

if TYPE_CHECKING:
    from ai_platform.engine.state_manager import ConversationState

logger = logging.getLogger(__name__)


def build_intent_prompt(routes: dict[str, str], description: str | None) -> str:
    route_list = "\n".join(f"- {key}" for key in routes)
    desc_line = f"\nContext: {description}" if description else ""
    return (
        f"You are a routing assistant.{desc_line}\n"
        f"Based on the user's message, choose exactly one of these route keys:\n"
        f"{route_list}\n\n"
        f"Respond with ONLY the route key, nothing else."
    )


class LLMIntentRouter(BaseRouter):
    def __init__(self, provider: str, model: str, temperature: float = 0.0):
        self.provider = provider
        self.model = model
        self.temperature = temperature

    def _get_llm(self) -> Any:
        if self.provider == "azure_openai":
            return AzureChatOpenAI(
                azure_deployment=self.model,
                temperature=self.temperature,
            )
        return ChatOpenAI(model=self.model, temperature=self.temperature)

    async def route(
        self,
        state: "ConversationState",
        routes: dict[str, str],
        description: str | None = None,
    ) -> str:
        user_message = state.get_last_user_message() or ""
        system_prompt = build_intent_prompt(routes, description)
        llm = self._get_llm()
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = await llm.ainvoke(messages)
        route_key = response.content.strip().lower()
        if route_key not in routes:
            fallback = next(iter(routes))
            logger.warning(
                "LLMIntentRouter: '%s' not in routes %s — falling back to '%s'",
                route_key, list(routes.keys()), fallback,
            )
            return fallback
        return route_key

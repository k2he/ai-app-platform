from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_platform.engine.state_manager import ConversationState


@dataclass
class RouterResult:
    route_key: str
    target_node: str
    confidence: float | None = None
    reasoning: str | None = None


class BaseRouter(ABC):
    @abstractmethod
    async def route(
        self,
        state: "ConversationState",
        routes: dict[str, str],
        description: str | None = None,
    ) -> str:
        ...

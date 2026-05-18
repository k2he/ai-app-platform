from __future__ import annotations

import logging
from typing import Any

from ai_platform.engine.state_manager import ConversationState

logger = logging.getLogger(__name__)


class HumanHandoffNode:
    async def execute(self, state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
        priority = config.get("priority", "normal")
        reason = config.get("reason", "user_requested")

        logger.info(
            "HANDOFF session_id=%s current_node=%s priority=%s reason=%s",
            state.session_id, state.current_node, priority, reason,
        )

        state.add_message("system", f"HANDOFF: Transferring to human agent. Reason: {reason}")

        return {
            "result": "handoff_initiated",
            "message": "Connecting you with a human agent. Please hold.",
        }

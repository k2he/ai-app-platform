from __future__ import annotations

import random
from datetime import datetime
from typing import Any

from ai_platform.engine.state_manager import ConversationState


async def check_activation_eligibility(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "result": "eligible",
        "data": {
            "account_type": "checking",
            "eligible_products": ["online_banking", "mobile_app", "debit_card"],
        },
        "message": "Your account is eligible for activation.",
    }


async def activate_account_in_system(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    confirmation_code = "ACT-" + "".join([str(random.randint(0, 9)) for _ in range(6)])
    return {
        "result": "success",
        "data": {
            "activated_at": datetime.utcnow().isoformat(),
            "account_number": state.user_context.get("account_number", "****1234"),
            "confirmation_code": confirmation_code,
        },
        "message": "Account activated successfully.",
    }

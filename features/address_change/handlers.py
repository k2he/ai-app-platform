from __future__ import annotations

import random
from datetime import datetime
from typing import Any

from ai_platform.engine.state_manager import ConversationState


async def validate_with_usps(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    street = state.extracted_data.get("street_address", "123 Main St")
    return {
        "result": "valid",
        "data": {
            "standardized_address": street,
            "usps_validated": True,
        },
        "message": "Address validated successfully.",
    }


async def update_address_in_crm(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    confirmation_number = "ADDR-" + "".join([str(random.randint(0, 9)) for _ in range(6)])
    return {
        "result": "success",
        "data": {
            "updated_at": datetime.utcnow().isoformat(),
            "confirmation_number": confirmation_number,
        },
        "message": "Address updated in our system.",
    }

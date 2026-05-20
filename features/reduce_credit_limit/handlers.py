from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from ai_platform.engine.state_manager import ConversationState

# Mock account data — replace with real CRM/core-banking calls in production
_MOCK_ACCOUNT = {
    "current_limit": 10_000,
    "current_balance": 3_200,
    "minimum_limit": 1_000,
    "currency": "USD",
}


async def validate_reduction_request(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Check that the requested_limit extracted from the conversation is a positive number."""
    requested = state.extracted_data.get("requested_limit")
    if requested is None or not isinstance(requested, (int, float)) or requested < 0:
        return {
            "result": "invalid",
            "message": "I wasn't able to read the amount. Please enter a dollar amount, e.g. 5000.",
        }
    state.user_context["requested_limit"] = float(requested)
    return {
        "result": "valid",
        "data": {"requested_limit": float(requested)},
    }


async def check_minimum_limit(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Ensure the new limit is at or above the account's minimum allowed limit."""
    requested = state.user_context.get("requested_limit", 0)
    minimum = _MOCK_ACCOUNT["minimum_limit"]
    current = _MOCK_ACCOUNT["current_limit"]

    if requested >= current:
        return {
            "result": "below_minimum",
            "message": (
                f"The requested limit of ${requested:,.0f} is not lower than your current limit "
                f"of ${current:,.0f}. Please enter an amount below your current limit."
            ),
        }
    if requested < minimum:
        return {
            "result": "below_minimum",
            "data": {"minimum_limit": minimum},
            "message": (
                f"The requested limit of ${requested:,.0f} is below the minimum allowed limit "
                f"of ${minimum:,.0f} for your account."
            ),
        }
    return {
        "result": "valid",
        "data": {"requested_limit": requested, "minimum_limit": minimum},
    }


async def check_current_balance(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Ensure the new limit is at or above the customer's current outstanding balance."""
    requested = state.user_context.get("requested_limit", 0)
    balance = _MOCK_ACCOUNT["current_balance"]

    if requested < balance:
        return {
            "result": "below_balance",
            "data": {"current_balance": balance},
            "message": (
                f"Your current balance is ${balance:,.2f}. "
                f"The new limit must be at least ${balance:,.0f} to cover your outstanding balance."
            ),
        }
    return {
        "result": "valid",
        "data": {
            "requested_limit": requested,
            "current_balance": balance,
            "current_limit": _MOCK_ACCOUNT["current_limit"],
        },
    }


async def apply_credit_reduction(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Apply the approved credit limit reduction."""
    confirmed = state.extracted_data.get("confirmed", False)
    if not confirmed:
        return {"result": "error", "message": "Reduction was not confirmed."}

    requested = state.user_context.get("requested_limit")
    if requested is None:
        return {"result": "error", "message": "No limit amount found to apply."}

    change_id = str(uuid.uuid4())
    effective_date = datetime.utcnow().date().isoformat()
    old_limit = _MOCK_ACCOUNT["current_limit"]

    # In production: call core-banking API here
    _MOCK_ACCOUNT["current_limit"] = requested

    return {
        "result": "success",
        "data": {
            "change_id": change_id,
            "old_limit": old_limit,
            "new_limit": requested,
            "effective_date": effective_date,
        },
        "message": (
            f"Your credit limit has been reduced from ${old_limit:,.0f} "
            f"to ${requested:,.0f}, effective {effective_date}."
        ),
    }


async def get_pending_limit_changes(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Retrieve any pending (not-yet-effective) credit limit change requests."""
    if state.user_context.get("force_no_pending"):
        return {"result": "not_found", "data": {"changes": []}}

    return {
        "result": "found",
        "data": {
            "changes": [
                {
                    "change_id": "CHG-001",
                    "requested_limit": 6_000,
                    "status": "Pending Review",
                    "submitted_at": "2026-05-19T14:30:00Z",
                    "estimated_effective": "2026-05-22",
                }
            ]
        },
    }


async def cancel_pending_change(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    """Cancel a pending credit limit change request."""
    if state.user_context.get("cancel_unavailable"):
        return {
            "result": "error",
            "message": "This change has already been processed and cannot be cancelled.",
        }
    return {
        "result": "success",
        "data": {"cancelled_change_id": "CHG-001"},
        "message": "Your pending credit limit change request has been cancelled.",
    }
from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from ai_platform.engine.state_manager import ConversationState


async def block_stolen_card(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    card_last_four = state.extracted_data.get("card_last_four")
    card_type = state.extracted_data.get("card_type", "card")
    if not card_last_four:
        return {"result": "error", "message": "Card information not found"}
    return {
        "result": "blocked",
        "data": {
            "blocked_card": card_last_four,
            "block_timestamp": datetime.utcnow().isoformat(),
        },
        "message": f"Your {card_type} card ending in {card_last_four} has been blocked.",
    }


async def calculate_replacement_fee(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    reason = state.extracted_data.get("reason", "")
    if reason in ("stolen", "expired"):
        return {
            "result": "no_fee",
            "data": {"fee_amount": "$0.00", "fee_currency": "USD"},
            "message": "There is no fee for this replacement.",
        }
    return {
        "result": "fee_applies",
        "data": {"fee_amount": "$15.00", "fee_currency": "USD"},
        "message": "A $15.00 replacement fee applies.",
    }


async def create_card_replacement_order(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    order_id = str(uuid.uuid4())
    estimated_delivery = (date.today() + timedelta(days=7)).isoformat()
    tracking_number = "1Z" + "".join([str(random.randint(0, 9)) for _ in range(12)])
    return {
        "result": "success",
        "data": {
            "order_id": order_id,
            "estimated_delivery": estimated_delivery,
            "tracking_number": tracking_number,
        },
        "message": f"Replacement card ordered. Order ID: {order_id}.",
    }


async def get_active_card_orders(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    if state.user_context.get("force_no_orders"):
        return {"result": "not_found", "data": {"orders": []}}
    estimated_delivery = (date.today() + timedelta(days=3)).isoformat()
    return {
        "result": "found",
        "data": {
            "orders": [
                {
                    "order_id": "ORD-001",
                    "card_type": "credit",
                    "status": "In Transit",
                    "tracking_number": "1Z9999999999999999",
                    "estimated_delivery": estimated_delivery,
                }
            ]
        },
    }


async def expedite_card_shipment(state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
    if state.user_context.get("expedite_unavailable"):
        return {"result": "not_available", "message": "Expedited shipping is not available for this order."}
    new_delivery_date = (date.today() + timedelta(days=1)).isoformat()
    return {
        "result": "success",
        "data": {"new_delivery_date": new_delivery_date, "expedite_fee": "$25.00"},
        "message": f"Shipment expedited. New delivery: {new_delivery_date}.",
    }
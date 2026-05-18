from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    messages: list[dict[str, str]] = Field(default_factory=list)
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    user_context: dict[str, Any] = Field(default_factory=dict)
    identity_verified: bool = False
    current_node: str | None = None
    workflow_name: str | None = None
    completed_actions: list[str] = Field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_last_user_message(self) -> str | None:
        for msg in reversed(self.messages):
            if msg.get("role") == "user":
                return msg.get("content")
        return None

    def merge_extracted_data(self, data: dict[str, Any]) -> None:
        self.extracted_data.update(data)
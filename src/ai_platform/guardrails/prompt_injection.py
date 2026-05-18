from __future__ import annotations

from ai_platform.guardrails.base import BaseGuardrail, GuardrailResult


class PromptInjectionGuardrail(BaseGuardrail):
    async def check(self, input_text: str, context: dict) -> GuardrailResult:
        return GuardrailResult.from_pass(input_text)

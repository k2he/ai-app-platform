from __future__ import annotations

from ai_platform.guardrails.base import BaseGuardrail, GuardrailResult

_MAX_WORDS = 250


class MaxLengthCheckGuardrail(BaseGuardrail):
    async def check(self, input_text: str, context: dict) -> GuardrailResult:
        word_count = len(input_text.split())
        if word_count > _MAX_WORDS:
            return GuardrailResult.from_fail(
                [f"Input exceeds {_MAX_WORDS} words (actual: {word_count})"],
                input_text,
            )
        return GuardrailResult.from_pass(input_text)

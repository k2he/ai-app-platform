from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from ai_platform.guardrails.base import BaseGuardrail, GuardrailResult

_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
    "US_SSN", "CREDIT_CARD", "US_BANK_NUMBER", "DATE_TIME",
]

_analyzer = AnalyzerEngine()


class PiiDetectionGuardrail(BaseGuardrail):
    async def check(self, input_text: str, context: dict) -> GuardrailResult:
        results = _analyzer.analyze(text=input_text, entities=_ENTITIES, language="en")
        if results:
            violations = list({r.entity_type for r in results})
            return GuardrailResult.from_fail(violations, input_text)
        return GuardrailResult.from_pass(input_text)

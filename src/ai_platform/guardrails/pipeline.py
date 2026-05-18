from __future__ import annotations

import logging
from typing import ClassVar

from ai_platform.guardrails.base import BaseGuardrail, GuardrailResult

logger = logging.getLogger(__name__)


class GuardrailPipeline:
    _registry: ClassVar[dict[str, type[BaseGuardrail]]] = {}

    @classmethod
    def register(cls, name: str, guardrail_cls: type[BaseGuardrail]) -> None:
        cls._registry[name] = guardrail_cls

    @classmethod
    async def run(
        cls,
        input_text: str,
        mandatory: list[str],
        optional: list[str],
        context: dict,
    ) -> GuardrailResult:
        current_text = input_text

        for name in mandatory:
            guardrail_cls = cls._registry.get(name)
            if guardrail_cls is None:
                logger.warning("Unknown mandatory guardrail: %s — skipping", name)
                continue
            result = await guardrail_cls().check(current_text, context)
            if not result.passed:
                logger.info("Mandatory guardrail '%s' blocked input: %s", name, result.violations)
                return result
            if result.modified_text is not None:
                current_text = result.modified_text

        for name in optional:
            guardrail_cls = cls._registry.get(name)
            if guardrail_cls is None:
                logger.warning("Unknown optional guardrail: %s — skipping", name)
                continue
            result = await guardrail_cls().check(current_text, context)
            if result.modified_text is not None:
                current_text = result.modified_text

        return GuardrailResult.from_pass(current_text)


# Register all built-in guardrails
def _register_defaults() -> None:
    from ai_platform.guardrails.pii_detection import PiiDetectionGuardrail
    from ai_platform.guardrails.max_length_check import MaxLengthCheckGuardrail
    from ai_platform.guardrails.harmful_content import HarmfulContentGuardrail
    from ai_platform.guardrails.prompt_injection import PromptInjectionGuardrail

    GuardrailPipeline.register("pii_detection", PiiDetectionGuardrail)
    GuardrailPipeline.register("max_length_check", MaxLengthCheckGuardrail)
    GuardrailPipeline.register("harmful_content", HarmfulContentGuardrail)
    GuardrailPipeline.register("prompt_injection", PromptInjectionGuardrail)


_register_defaults()

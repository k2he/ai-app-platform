from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GuardrailResult:
    passed: bool
    modified_text: str | None
    violations: list[str] = field(default_factory=list)

    @classmethod
    def from_pass(cls, text: str) -> "GuardrailResult":
        return cls(passed=True, modified_text=text, violations=[])

    @classmethod
    def from_fail(cls, violations: list[str], original_text: str) -> "GuardrailResult":
        return cls(passed=False, modified_text=original_text, violations=violations)


class BaseGuardrail(ABC):
    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def check(self, input_text: str, context: dict) -> GuardrailResult:
        ...

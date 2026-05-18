from __future__ import annotations

import logging
import re
from typing import Any

from ai_platform.engine.state_manager import ConversationState
from ai_platform.auth.identity_verifier import IdentityVerifier

logger = logging.getLogger(__name__)

_ACCOUNT_RE = re.compile(r"account\s*[#:]?\s*(\d+)", re.IGNORECASE)
_DOB_RE = re.compile(r"(?:dob|date of birth)[:\s]*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE)
_SSN_RE = re.compile(r"(?:ssn|last\s*4|last four)[:\s]*(\d{4})", re.IGNORECASE)


def _normalize_dob(raw: str) -> str:
    for fmt, pattern in [
        ("%Y-%m-%d", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
        ("%m/%d/%Y", re.compile(r"^\d{2}/\d{2}/\d{4}$")),
    ]:
        if pattern.match(raw):
            try:
                from datetime import datetime
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
    return raw


def _extract_credentials(text: str, method: str) -> dict[str, str]:
    credentials: dict[str, str] = {}
    account_match = _ACCOUNT_RE.search(text)
    if account_match:
        credentials["account_number"] = account_match.group(1)
    if method == "account_number_dob":
        dob_match = _DOB_RE.search(text)
        if dob_match:
            credentials["dob"] = _normalize_dob(dob_match.group(1))
    elif method == "account_number_ssn_last4":
        ssn_match = _SSN_RE.search(text)
        if ssn_match:
            credentials["ssn_last4"] = ssn_match.group(1)
    return credentials


class AuthChallengeNode:
    async def execute(self, state: ConversationState, config: dict[str, Any]) -> dict[str, Any]:
        method = config.get("method", "account_number_dob")
        max_attempts = config.get("max_attempts", 3)

        last_message = state.get_last_user_message() or ""
        credentials = _extract_credentials(last_message, method)

        verifier = IdentityVerifier()
        verified = verifier.verify(method, credentials)

        if verified:
            state.identity_verified = True
            return {"result": "verified"}

        attempts = state.user_context.get("auth_attempts", 0) + 1
        state.user_context["auth_attempts"] = attempts
        logger.info("Auth attempt %d/%d failed for method=%s", attempts, max_attempts, method)

        if attempts >= max_attempts:
            return {"result": "max_attempts_exceeded"}

        return {"result": "failed", "message": "Verification failed. Please try again."}

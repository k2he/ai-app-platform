from __future__ import annotations

MOCK_CREDENTIALS: dict = {
    "account_number_dob": {
        "account_number": "12345",
        "dob": "1990-01-15",
    },
    "account_number_ssn_last4": {
        "account_number": "12345",
        "ssn_last4": "6789",
    },
}


class IdentityVerifier:
    def verify(self, method: str, credentials: dict[str, str]) -> bool:
        expected = MOCK_CREDENTIALS.get(method)
        if expected is None:
            return False
        try:
            return all(credentials.get(k) == v for k, v in expected.items())
        except Exception:
            return False

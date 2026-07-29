"""Deterministic redaction for sensitive content.

Redacts Telegram tokens, API tokens, prompts, tool output, and other sensitive data.
Zero false-negative tolerance for seeded fixture tests.
"""

import re
import base64
from typing import Pattern


class RedactionClass:
    """Classification of sensitive content."""

    TELEGRAM_TOKEN = "TELEGRAM_TOKEN"
    INIT_DATA = "INIT_DATA"
    API_TOKEN = "API_TOKEN"
    BASIC_AUTH = "BASIC_AUTH"
    BEARER_TOKEN = "BEARER_TOKEN"
    JWT = "JWT"
    COOKIE = "COOKIE"
    SESSION_ID = "SESSION_ID"
    PRIVATE_KEY = "PRIVATE_KEY"
    SECRET_URL = "SECRET_URL"
    ENV_SECRET = "ENV_SECRET"
    PROMPT_OUTPUT = "PROMPT_OUTPUT"


class Redactor:
    """Deterministic redactor with seeded fixture coverage.

    Replacement rules preserve field name and structural validity where useful,
    replacing entire values with [REDACTED:<CLASS>].
    """

    # Compiled patterns for performance
    PATTERNS: dict[str, Pattern] = {}

    @classmethod
    def _compile_patterns(cls) -> None:
        """Compile all redaction patterns."""
        if cls.PATTERNS:
            return

        # Telegram bot tokens: starts with digits, contains colon and alphanumerics
        # Match the full token including both parts (before and after colon)
        # Handle whitespace around colon for edge cases
        cls.PATTERNS[RedactionClass.TELEGRAM_TOKEN] = re.compile(r"\b\d+\s*:\s*[^\s]+")

        # Telegram initData hash field (64 hex chars)
        cls.PATTERNS[RedactionClass.INIT_DATA] = re.compile(
            r"\bhash=[a-fA-F0-9]{64}(?:&|$)"
        )

        # Generic API tokens: base64-like strings 20+ chars, common prefixes (case-insensitive)
        cls.PATTERNS[RedactionClass.API_TOKEN] = re.compile(
            r"\b(?:glpat-|ghp_|gla_|gho_|ghu_|ghs_|ghr_|sk-|pk_)[A-Za-z0-9_-]+\b",
            re.IGNORECASE,
        )

        # Basic auth URLs: scheme://user:pass@host
        cls.PATTERNS[RedactionClass.SECRET_URL] = re.compile(
            r"[a-z]+://[^:/]+:[^@]+@[^/\s]+"
        )

        # Authorization headers (entire header value)
        # Match both "Authorization: Bearer token" and standalone "Bearer token"
        cls.PATTERNS[RedactionClass.BEARER_TOKEN] = re.compile(
            r"(?:Authorization:\s*)?Bearer\s+[^\s]+", re.IGNORECASE
        )

        # Basic auth header value after "Basic "
        cls.PATTERNS[RedactionClass.BASIC_AUTH] = re.compile(
            r"Basic\s+[A-Za-z0-9+/=]+", re.IGNORECASE
        )

        # JWT tokens: three dot-separated base64 segments
        cls.PATTERNS[RedactionClass.JWT] = re.compile(
            r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
        )

        # Session IDs: hex strings 16-64 chars
        cls.PATTERNS[RedactionClass.SESSION_ID] = re.compile(r"\b[a-fA-F0-9]{16,64}\b")

        # Environment secrets: KEY=value with secret key names
        cls.PATTERNS[RedactionClass.ENV_SECRET] = re.compile(
            r"\b(?:TELEGRAM_BOT_TOKEN|GITLAB_TOKEN|JIRA_API_TOKEN|HASS_TOKEN|"
            r"GRAFANA_API_KEY|OP_SERVICE_ACCOUNT_TOKEN|VIKUNJA_TOKEN|OUTLINE_TOKEN|JELLYFIN_API_KEY|"
            r"OPENAI_API_KEY|ANTHROPIC_API_KEY|GROQ_API_KEY)=[^\s]+",
            re.IGNORECASE,
        )

        # Cookie headers
        cls.PATTERNS[RedactionClass.COOKIE] = re.compile(
            r"Cookie:\s*[^\n]+", re.IGNORECASE
        )

        # PEM private key blocks (multi-line)
        cls.PATTERNS[RedactionClass.PRIVATE_KEY] = re.compile(
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----[^\\-]+-----END (?:RSA )?PRIVATE KEY-----",
            re.DOTALL,
        )

        # Base64 strings that might encode secrets (20+ chars, only base64 chars)
        cls.PATTERNS[RedactionClass.SESSION_ID] = re.compile(
            r"\b[A-Za-z0-9+/]{20,}={0,2}\b"
        )

        # JSON key-value pairs with sensitive keys: "token": "secret123"
        cls.PATTERNS["JSON_SECRET"] = re.compile(
            r'"(?:token|password|secret|api_key|api-key|auth|key|credential|access_token)"\s*:\s*"[^"]*"',
            re.IGNORECASE,
        )

    @classmethod
    def redact(cls, text: str) -> str:
        """Redact sensitive content from text.

        Args:
            text: Input text that may contain sensitive content

        Returns:
            Redacted text with sensitive values replaced
        """
        cls._compile_patterns()
        result = text

        # Apply all patterns
        for pattern in cls.PATTERNS.values():
            result = pattern.sub("[REDACTED]", result)

        # Additional URL parameter redaction (query params with common secret names)
        result = cls._redact_url_params(result)

        return result

    @classmethod
    def _redact_url_params(cls, text: str) -> str:
        """Redact sensitive URL query parameters."""
        secret_params = [
            "token",
            "api_key",
            "secret",
            "password",
            "pass",
            "auth",
            "key",
            "credential",
            "pat",
            "access_token",
        ]

        result = text

        # Find URL parameters and redact
        for param in secret_params:
            pattern = rf"\b{param}=[^&\s]+"
            result = re.sub(pattern, f"{param}=[REDACTED]", result, flags=re.IGNORECASE)

        # Remove from query strings and fragments
        pattern = r"(\?|&)(token|api_key|secret|password|pass|auth|key|credential|pat|access_token)=[^&\s]+"
        result = re.sub(
            pattern,
            lambda m: f"{m.group(1)}{m.group(2)}=[REDACTED]",
            result,
            flags=re.IGNORECASE,
        )

        return result

    @classmethod
    def redact_dict(cls, data: dict) -> dict:
        """Recursively redact sensitive values in a dict.

        Args:
            data: Dictionary that may contain sensitive values

        Returns:
            Redacted dictionary with sensitive values replaced
        """
        if not isinstance(data, dict):
            return data

        redacted = {}

        for key, value in data.items():
            # Check if key name suggests sensitive content
            key_lower = key.lower()
            sensitive_keys = [
                "token",
                "password",
                "secret",
                "api_key",
                "auth",
                "credential",
                "pat",
                "key",
                "access_token",
                "init_data",
                "hash",
                "cookie",
            ]

            if any(sk in key_lower for sk in sensitive_keys):
                # Replace entire value
                if isinstance(value, (str, int, float)):
                    redacted[key] = "[REDACTED]"
                else:
                    # For complex types, try to redact string representations
                    redacted[key] = cls.redact(str(value))
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    cls.redact_dict(item)
                    if isinstance(item, dict)
                    else cls.redact(str(item))
                    for item in value
                ]
            else:
                redacted[key] = value

        return redacted

    @classmethod
    def safe_display(cls, text: str, max_length: int = 200) -> str:
        """Return a safe, redacted display string with length limiting.

        Args:
            text: Input text
            max_length: Maximum length of output

        Returns:
            Redacted and truncated text
        """
        redacted = cls.redact(text)
        if len(redacted) > max_length:
            redacted = redacted[: max_length - 3] + "..."
        return redacted


# Singleton instance
redactor = Redactor()


# Seeded fixtures for zero false-negative testing
# These are not committed to production; they ensure the redactor catches all cases
FIXTURE_SECRETS = {
    "telegram_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "init_data_hash": "hash=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890&",
    "gitlab_token": "glpat-xxxxxxxxxxxxxxxxxxxx",
    "github_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "jira_token": "basic dXNlcm5hbWU6dG9rZW4xMjM0NTY3OA==",
    "bearer_token": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
    "session_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "secret_url": "https://user:password@example.com/path",
    "env_secret": "TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "multiline_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
-----END PRIVATE KEY-----""",
    "mixed_case_token": "GLPAT-xxxxxxxxxxxxxxxxxxxx",
    "url_param_token": "https://api.example.com?token=secret123&other=value",
    "fragment_token": "https://example.com/page#token=secret456",
    "split_token_whitespace": "123456789 :ABCdefGHIjklMNOpqrsTUVwxyz",
    "encoded_token": base64.b64encode(b"123456789:ABCdefGHIjklMNOpqrsTUVwxyz").decode(),
    "nested_json_secret": '{"token": "secret123", "nested": {"password": "pass456"}}',
}


def run_fixture_test() -> dict[str, bool]:
    """Run seeded fixture tests to verify zero false negatives.

    Returns:
        Dictionary mapping fixture name to pass/fail
    """
    results = {}

    for name, secret in FIXTURE_SECRETS.items():
        redacted = redactor.redact(secret)

        # Check if original secret is NOT present in redacted output
        # This is the fail-closed test: redaction must remove all sensitive patterns
        original_patterns = [
            secret,  # Full string
        ]

        # For encoded tokens, also check the decoded version
        if name == "encoded_token":
            try:
                original_patterns.append(base64.b64decode(secret).decode())
            except:
                pass

        # Extract the actual secret value (not URL structure) for substring checks
        # This prevents false "leaks" from non-sensitive URL components surviving redaction
        if name == "url_param_token":
            original_patterns.append("secret123")  # The token value only
        elif name == "fragment_token":
            original_patterns.append("secret456")
        elif name == "nested_json_secret":
            original_patterns.append("secret123")
            original_patterns.append("pass456")
        elif name == "telegram_token":
            original_patterns.extend(secret.split(":"))
        elif name == "init_data_hash":
            original_patterns.append(secret.split("=")[1].split("&")[0])
        elif name == "split_token_whitespace":
            original_patterns.extend(
                [p.strip() for p in secret.split(":") if p.strip()]
            )

        # Test that no original pattern appears in redacted output
        passed = True
        for pattern in original_patterns:
            if pattern and pattern in redacted and pattern != "[REDACTED]":
                passed = False
                break

        results[name] = passed

    return results

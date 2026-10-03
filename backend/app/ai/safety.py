import re
import time
from typing import Dict, List, Tuple
from fastapi import HTTPException, status
from app.core.config import settings

# In-memory sliding rate limiter per user ID
# Format: { user_id: [timestamp1, timestamp2, ...] }
_user_request_timestamps: Dict[int, List[float]] = {}

PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)\byou\s+are\s+now\s+in\s+dan\s+mode",
    r"(?i)\breveal\s+(the\s+)?(jwt|secret|key|database|password|credential|token)",
    r"(?i)\b(drop\s+table|delete\s+from|select\s+\*\s+from|insert\s+into|update\s+\w+\s+set)\b",
    r"(?i)\b(change|upgrade|grant|elevate)\s+(my\s+role|role\s+to\s+super_admin|admin\s+access)",
    r"(?i)\b(approve\s+this\s+claim|approve\s+my\s+claim|verify\s+my\s+document)\s+automatically",
    r"(?i)\bsystem\s+prompt\s+override",
]

SENSITIVE_OUTPUT_PATTERNS = [
    r"medsentinel_super_secure_jwt_secret",
    r"mysql\+pymysql://",
    r"AIzaSy[A-Za-z0-9_-]{33}",
    r"password123|admin123|hospital123|insurance123",
]

class AISafetyGuard:
    @staticmethod
    def check_rate_limit(user_id: int) -> bool:
        """Enforces sliding rate limit per minute and daily quota per user."""
        current_time = time.time()
        one_minute_ago = current_time - 60.0
        one_day_ago = current_time - 86400.0

        if user_id not in _user_request_timestamps:
            _user_request_timestamps[user_id] = []

        # Filter out timestamps older than 24 hours
        _user_request_timestamps[user_id] = [
            ts for ts in _user_request_timestamps[user_id] if ts > one_day_ago
        ]

        # Check requests in last 60 seconds
        recent_minute_requests = [
            ts for ts in _user_request_timestamps[user_id] if ts > one_minute_ago
        ]

        if len(recent_minute_requests) >= settings.AI_REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"AI rate limit exceeded. Max {settings.AI_REQUESTS_PER_MINUTE} requests per minute allowed."
            )

        if len(_user_request_timestamps[user_id]) >= settings.AI_REQUESTS_PER_DAY:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily AI request limit of {settings.AI_REQUESTS_PER_DAY} requests reached."
            )

        _user_request_timestamps[user_id].append(current_time)
        return True

    @staticmethod
    def validate_user_input(message: str) -> Tuple[bool, str]:
        """Detects prompt injections, jailbreaks, and destructive SQL queries."""
        if not message or not message.strip():
            return False, "Message cannot be empty."

        if len(message) > 4000:
            return False, "Message exceeds maximum allowed length of 4000 characters."

        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, message):
                return False, "Your request was flagged by MedSentinel AI Safety Filters for containing restricted instructions or override patterns."

        return True, ""

    @staticmethod
    def sanitize_model_output(output_text: str) -> str:
        """Scans output to ensure no secrets, database strings, or credentials leak."""
        sanitized = output_text
        for pattern in SENSITIVE_OUTPUT_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED_SECURITY_DATA]", sanitized)

        return sanitized

# Export standard alias
AISafety = AISafetyGuard

class ExternalContentSanitizer:
    """
    Zero-Trust External Content Sanitizer.
    Enforces strict structural boundaries between System Prompts and
    untrusted external data (emails, WhatsApp messages, OCR text, spreadsheets, webhooks).
    Wraps content in <EXTERNAL_UNTRUSTED_DATA> blocks and neutralizes instruction-injection payloads.
    """

    @classmethod
    def sanitize(cls, raw_content: str, source: str = "EXTERNAL_CONNECTOR") -> str:
        if not raw_content:
            return ""

        # 1. Neutralize explicit injection strings
        sanitized = raw_content
        for pattern in PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[MALICIOUS_OVERRIDE_ATTEMPT_DEFUSED]", sanitized)

        # 2. Prevent boundary breakout tags
        sanitized = sanitized.replace("</EXTERNAL_UNTRUSTED_DATA>", "[TAG_DEFUSED]")

        # 3. Encase in strict boundary wrapper
        return (
            f'<EXTERNAL_UNTRUSTED_DATA source="{source}">\n'
            f'{sanitized.strip()}\n'
            f'</EXTERNAL_UNTRUSTED_DATA>'
        )

    @classmethod
    def contains_injection(cls, content: str) -> bool:
        if not content:
            return False
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, content):
                return True
        return False


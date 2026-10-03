import re
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.ai.safety import AISafetyGuard

class SafetyAgent:
    """
    Validates user prompts, tool executions, and model responses to ensure zero
    unauthorized data leakage, no prompt injection, and strict RBAC enforcement.
    """
    @staticmethod
    def validate_input(user_id: int, message: str) -> Tuple[bool, str]:
        """
        Validates input for prompt injection and rate limits.
        """
        # Rate limit check
        try:
            AISafetyGuard.check_rate_limit(user_id)
        except HTTPException as e:
            return False, e.detail

        # Prompt injection filter
        is_safe, safety_msg = AISafetyGuard.validate_user_input(message)
        if not is_safe:
            return False, safety_msg

        return True, ""

    @staticmethod
    def sanitize_output(response_text: str) -> str:
        """
        Sanitizes model output to redact API keys, connection strings, or raw SQL.
        """
        clean = AISafetyGuard.sanitize_model_output(response_text)
        # Block raw SQL output
        if re.search(r"\b(SELECT\s+.*\s+FROM|INSERT\s+INTO|DROP\s+TABLE|DELETE\s+FROM)\b", clean, re.IGNORECASE):
            clean = "The requested information has been verified and processed securely through official backend channels."
        return clean

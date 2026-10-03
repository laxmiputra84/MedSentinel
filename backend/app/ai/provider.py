import time
import httpx
from typing import Dict, Any, Optional, List
from app.core.config import settings

class AIProviderError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AIProvider:
    """
    Enterprise AI Provider Manager supporting Google Gemini with
    strict error classification and latency tracking.
    """
    @staticmethod
    def get_health() -> Dict[str, Any]:
        """Returns the health and readiness of configured AI provider."""
        key = settings.GEMINI_API_KEY.strip()
        has_key = bool(key and len(key) > 8)
        return {
            "ai_enabled": settings.AI_ENABLED,
            "provider": settings.AI_PROVIDER,
            "model": settings.AI_MODEL,
            "configured": has_key,
            "status": "healthy" if (settings.AI_ENABLED and has_key) else "unconfigured",
            "rag_enabled": settings.RAG_ENABLED,
            "vector_db_provider": settings.VECTOR_DB_PROVIDER
        }

    @staticmethod
    async def generate_response(
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Executes generation request against Gemini model with accurate error mapping.
        """
        if not settings.AI_ENABLED:
            raise AIProviderError(
                code="AI_DISABLED",
                message="The MedSentinel AI service is currently disabled in system settings.",
                status_code=503
            )

        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise AIProviderError(
                code="AI_CONFIGURATION_ERROR",
                message="AI provider API key is not configured. Please set GEMINI_API_KEY in environment settings.",
                status_code=500
            )

        model_name = settings.AI_MODEL or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(url, json=payload)
                latency_ms = round((time.time() - start_time) * 1000, 2)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join([p.get("text", "") for p in content_parts])
                        return {
                            "text": text,
                            "latency_ms": latency_ms,
                            "tokens_used": data.get("usageMetadata", {}).get("totalTokenCount", 0),
                            "model": model_name,
                            "provider": "gemini"
                        }
                    raise AIProviderError("AI_EMPTY_RESPONSE", "Provider returned no candidate response.", 502)

                # Classify HTTP Error codes accurately
                error_body = {}
                try:
                    error_body = response.json().get("error", {})
                except Exception:
                    pass
                err_msg = error_body.get("message", response.text[:200])

                if response.status_code == 401 or response.status_code == 400 and "API_KEY_INVALID" in err_msg:
                    raise AIProviderError("AI_CONFIGURATION_ERROR", f"Invalid Gemini API key: {err_msg}", 401)
                elif response.status_code == 403:
                    raise AIProviderError("AI_PROVIDER_PERMISSION_DENIED", f"Permission denied by AI provider: {err_msg}", 403)
                elif response.status_code == 429 or "RESOURCE_EXHAUSTED" in err_msg:
                    raise AIProviderError("AI_PROVIDER_RATE_LIMITED", "AI provider rate limit reached. Please wait a moment before sending another request.", 429)
                elif response.status_code == 503 or response.status_code == 502:
                    raise AIProviderError("AI_PROVIDER_UNAVAILABLE", "AI provider service is temporarily unreachable.", 503)
                else:
                    raise AIProviderError("AI_INTERNAL_ERROR", f"Provider error ({response.status_code}): {err_msg}", 500)

        except httpx.TimeoutException:
            raise AIProviderError("AI_TIMEOUT", "AI provider request timed out. Please try again.", 504)
        except httpx.ConnectError:
            raise AIProviderError("AI_PROVIDER_UNAVAILABLE", "Network connection to AI provider failed.", 503)
        except AIProviderError:
            raise
        except Exception as ex:
            raise AIProviderError("AI_INTERNAL_ERROR", f"Unexpected AI generation error: {str(ex)}", 500)

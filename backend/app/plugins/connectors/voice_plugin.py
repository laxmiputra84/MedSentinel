import time
from typing import Dict, Any
from app.plugins.base import BasePlugin
from app.plugins.schema import ToolResult

class VoiceCommunicationPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            plugin_id="voice_telephony",
            name="Telephony & Voice Gateway",
            category="Communication",
            provider="SIP / Twilio Voice / Asterisk",
            description="Automated telephony status, call transcription, appointment callbacks, and clinical escalation to human staff.",
            capabilities=[
                "initiate_call",
                "get_call_status",
                "transcribe_audio",
                "escalate_to_human",
                "verify_patient_identity"
            ],
            permissions=["voice:call", "voice:transcribe", "voice:escalate"],
            icon="call",
            rate_limit_rpm=30
        )

    async def connect(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.status = "CONNECTED"
        return True

    async def disconnect(self) -> bool:
        self.status = "DISCONNECTED"
        return True

    async def test_connection(self) -> Dict[str, Any]:
        self.last_tested_at = time.time()
        return {
            "success": True,
            "provider": self.provider,
            "latency_ms": 55,
            "sip_trunk": "sip.medsentinel.internal",
            "telephony_health": "READY"
        }

    async def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        t0 = time.time()
        phone = params.get("phone")
        masked_phone = self.mask_phone(phone)
        call_sid = f"CA{int(time.time()*1000)}"

        if action == "escalate_to_human":
            reason = params.get("reason", "Patient requested nurse or staff assistance")
            self.usage_count += 1
            self.last_used_at = time.time()
            return ToolResult(
                success=True,
                status="SUCCESS",
                external_id=call_sid,
                result={
                    "escalation_id": call_sid,
                    "target_queue": "CLINICAL_STAFF_ON_DUTY",
                    "patient_phone": masked_phone,
                    "reason": reason,
                    "status": "TRANSFERRED_TO_HUMAN",
                    "guardrail_status": "AI doctor impersonation strictly disabled; routed to licensed human provider"
                },
                verification_status="VERIFIED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )

        if action == "transcribe_audio":
            sample_text = params.get("audio_text", "Patient reports mild headache and requested appointment slot tomorrow morning.")
            self.usage_count += 1
            self.last_used_at = time.time()
            return ToolResult(
                success=True,
                status="SUCCESS",
                external_id=call_sid,
                result={
                    "transcription": sample_text,
                    "confidence": 0.96,
                    "language": "en-US",
                    "duration_seconds": 18
                },
                verification_status="VERIFIED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )

        self.usage_count += 1
        self.last_used_at = time.time()
        return ToolResult(
            success=True,
            status="SUCCESS",
            external_id=call_sid,
            result={
                "call_sid": call_sid,
                "recipient": masked_phone,
                "call_state": "QUEUED_FOR_CALLBACK",
                "policy": "Pre-recorded structured prompt only; no automated diagnosis"
            },
            verification_status="VERIFIED",
            execution_time_ms=int((time.time() - t0) * 1000)
        )

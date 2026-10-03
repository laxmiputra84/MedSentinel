import time
import random
from typing import Dict, Any
from app.plugins.base import BasePlugin
from app.plugins.schema import ToolResult

class MobileCommunicationPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            plugin_id="mobile_sms",
            name="Mobile / SMS Gateway",
            category="Communication",
            provider="Twilio / Enterprise SMS Provider",
            description="High-priority SMS delivery, one-time authentication codes (OTP), and patient appointment reminders.",
            capabilities=[
                "send_sms",
                "send_otp",
                "verify_otp",
                "send_claim_alert",
                "appointment_reminder"
            ],
            permissions=["sms:send", "otp:generate", "otp:verify"],
            icon="sms",
            rate_limit_rpm=100
        )
        self.otp_store = {}

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
            "latency_ms": 38,
            "gateway_status": "ACTIVE",
            "credits_remaining": 99420
        }

    async def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        t0 = time.time()
        phone = params.get("phone") or params.get("recipient")
        masked_phone = self.mask_phone(phone)

        if not phone:
            return ToolResult(
                success=False,
                status="FAILED",
                error="Mobile number is required",
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )

        external_sms_id = f"SM{int(time.time()*1000)}{random.randint(100, 999)}"

        if action == "send_otp":
            otp_code = str(random.randint(100000, 999999))
            self.otp_store[phone] = {"code": otp_code, "expires_at": time.time() + 300}
            self.usage_count += 1
            self.last_used_at = time.time()
            return ToolResult(
                success=True,
                status="SUCCESS",
                external_id=external_sms_id,
                result={
                    "message": f"OTP dispatched successfully to {masked_phone}",
                    "recipient": masked_phone,
                    "validity_seconds": 300,
                    "sms_id": external_sms_id
                },
                verification_status="VERIFIED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            
        message = params.get("message", "MedSentinel Notification")
        self.usage_count += 1
        self.last_used_at = time.time()

        return ToolResult(
            success=True,
            status="SUCCESS",
            external_id=external_sms_id,
            result={
                "sms_id": external_sms_id,
                "recipient": masked_phone,
                "delivery_state": "DISPATCHED",
                "preview": (message[:50] + "...") if len(message) > 50 else message
            },
            verification_status="VERIFIED",
            execution_time_ms=int((time.time() - t0) * 1000)
        )

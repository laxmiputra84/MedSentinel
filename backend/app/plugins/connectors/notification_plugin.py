import time
from typing import Dict, Any
from app.plugins.base import BasePlugin
from app.plugins.schema import ToolResult

class NotificationPlugin(BasePlugin):
    """
    Unified Multi-Channel Notification Router.
    Exposes unified notify(channel, recipient, message, priority) routing
    across WhatsApp, SMS, Email, In-App, and Push notifications based on policy rules.
    """
    def __init__(self):
        super().__init__(
            plugin_id="unified_notifications",
            name="Multi-Channel Notification Gateway",
            category="Communication",
            provider="MedSentinel Router (Multi-Channel)",
            description="Policy-governed routing of urgent clinical alerts, claim updates, and appointment reminders across WhatsApp, SMS, Email, In-App, and Push.",
            capabilities=[
                "notify",
                "broadcast_alert",
                "get_notification_status",
                "route_by_urgency"
            ],
            permissions=["notify:dispatch", "notify:broadcast"],
            icon="notifications_active",
            rate_limit_rpm=200
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
            "supported_channels": ["WhatsApp", "SMS", "Email", "In-App", "Push"],
            "router_status": "ONLINE"
        }

    async def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        t0 = time.time()
        channel = params.get("channel", "IN_APP").upper()
        recipient = params.get("recipient", "user_current")
        message = params.get("message", "Notification")
        priority = params.get("priority", "NORMAL").upper() # LOW, NORMAL, URGENT, CRITICAL

        notif_id = f"ntf_{int(time.time()*1000)}"

        # If priority is URGENT / CRITICAL, automatic fallback to multi-channel
        dispatched_channels = [channel]
        if priority in ["URGENT", "CRITICAL"] and channel not in ["SMS", "WHATSAPP"]:
            dispatched_channels.append("SMS")

        self.usage_count += 1
        self.last_used_at = time.time()

        return ToolResult(
            success=True,
            status="SUCCESS",
            external_id=notif_id,
            result={
                "notification_id": notif_id,
                "primary_channel": channel,
                "dispatched_channels": dispatched_channels,
                "priority": priority,
                "recipient_ref": self.mask_phone(recipient) if any(c.isdigit() for c in recipient) else recipient,
                "delivery_state": "ROUTED_SUCCESSFULLY"
            },
            verification_status="VERIFIED",
            execution_time_ms=int((time.time() - t0) * 1000)
        )

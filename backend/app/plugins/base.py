import re
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.plugins.schema import ToolResult
from app.models.plugin import PluginStatus

class BasePlugin(ABC):
    def __init__(
        self,
        plugin_id: str,
        name: str,
        category: str,
        provider: str,
        description: str,
        capabilities: List[str],
        permissions: List[str],
        icon: str = "extension",
        rate_limit_rpm: int = 60,
        version: str = "1.0.0",
    ):
        self.plugin_id = plugin_id
        self.name = name
        self.category = category
        self.provider = provider
        self.description = description
        self.capabilities = capabilities
        self.permissions = permissions
        self.icon = icon
        self.rate_limit_rpm = rate_limit_rpm
        self.version = version
        
        self.status: PluginStatus = PluginStatus.CONNECTED
        self.is_enabled: bool = True
        self.config: Dict[str, Any] = {}
        self.usage_count: int = 0
        self.error_count: int = 0
        self.last_used_at: Optional[float] = None
        self.last_tested_at: Optional[float] = None

    def configure(self, credentials: Dict[str, Any]) -> None:
        """Store connection credentials safely in instance config."""
        self.config.update(credentials)

    @abstractmethod
    async def connect(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Connect and authenticate plugin with credentials / parameters."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect and revoke active sessions."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Perform a synthetic health/ping check against the provider."""
        pass

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute a tool action and return a standardized ToolResult."""
        pass

    def validate_permissions(self, required_permission: Optional[str]) -> bool:
        """Verify that the requested action is within this plugin's allowed permission scopes."""
        if not required_permission:
            return True
        return required_permission in self.permissions or "*" in self.permissions

    @staticmethod
    def mask_phone(phone: Optional[str]) -> str:
        """Masks patient phone numbers (e.g., +91 9876543210 -> +91 ******3210)."""
        if not phone:
            return ""
        cleaned = re.sub(r'[\s\-()]', '', phone)
        if len(cleaned) <= 4:
            return "****"
        prefix = cleaned[:3] if cleaned.startswith('+') else cleaned[:2]
        suffix = cleaned[-4:]
        return f"{prefix} ******{suffix}"

    @staticmethod
    def mask_pii(params: Dict[str, Any]) -> Dict[str, Any]:
        """Deep masks sensitive fields in input parameters before logging or auditing."""
        masked = {}
        sensitive_keys = {"password", "secret", "token", "api_key", "jwt", "cvv", "card_number", "ssn", "auth"}
        
        for k, v in params.items():
            k_lower = k.lower()
            if any(sk in k_lower for sk in sensitive_keys):
                masked[k] = "[REDACTED]"
            elif "phone" in k_lower or "mobile" in k_lower:
                masked[k] = BasePlugin.mask_phone(str(v))
            elif isinstance(v, dict):
                masked[k] = BasePlugin.mask_pii(v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                masked[k] = [BasePlugin.mask_pii(item) for item in v]
            else:
                masked[k] = v
        return masked

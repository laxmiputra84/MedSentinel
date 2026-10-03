import os
import time
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models import User
from app.models.plugin import PluginConnection, PluginStatus
from app.plugins.base import BasePlugin
from app.plugins.schema import ToolRequest, ToolResult, PluginInfo
from app.plugins.gateway import ToolGateway
from app.plugins.emergency import emergency_controller
from app.plugins.registry import tool_registry

# Import all 18 concrete connectors
from app.plugins.connectors import (
    WhatsAppBusinessPlugin,
    MobileCommunicationPlugin,
    VoiceCommunicationPlugin,
    GmailPlugin,
    EmailPlugin,
    SecureFilePlugin,
    ExcelPlugin,
    ImageProcessingPlugin,
    PDFPlugin,
    DocumentPlugin,
    StoragePlugin,
    CalendarPlugin,
    NotificationPlugin,
    PaymentPlugin,
    HospitalIntegrationPlugin,
    InsuranceIntegrationPlugin,
    CSVPlugin,
    CustomAPIPlugin,
)

logger = logging.getLogger("medsentinel.plugins.manager")

class PluginManager:
    """
    Central MedSentinel Plugin Manager.
    Coordinates 18 modular connectors, manages lifecycle states
    (NOT_CONFIGURED, CONNECTING, CONNECTED, PAUSED, DISCONNECTED, REVOKED, MOCK/SANDBOX),
    validates credentials, and forwards tool executions through the zero-trust ToolGateway.
    """

    def __init__(self, gateway: Optional[ToolGateway] = None):
        self.gateway = gateway or ToolGateway()
        self._plugins: Dict[str, BasePlugin] = {}
        self._tool_to_plugin_map: Dict[str, str] = {}
        self._initialize_default_plugins()

    def _initialize_default_plugins(self):
        default_instances = [
            WhatsAppBusinessPlugin(),
            MobileCommunicationPlugin(),
            VoiceCommunicationPlugin(),
            GmailPlugin(),
            EmailPlugin(),
            SecureFilePlugin(),
            ExcelPlugin(),
            CSVPlugin(),
            ImageProcessingPlugin(),
            PDFPlugin(),
            DocumentPlugin(),
            StoragePlugin(),
            CalendarPlugin(),
            NotificationPlugin(),
            PaymentPlugin(),
            HospitalIntegrationPlugin(),
            InsuranceIntegrationPlugin(),
            CustomAPIPlugin(),
        ]
        for p in default_instances:
            self.register_plugin(p)

    def register_plugin(self, plugin: BasePlugin):
        self._plugins[plugin.plugin_id] = plugin
        for cap in plugin.capabilities:
            self._tool_to_plugin_map[cap.lower()] = plugin.plugin_id

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        if not plugin_id:
            return None
        clean_id = plugin_id.lower().strip()
        if clean_id in self._plugins:
            return self._plugins[clean_id]
        aliases = {
            "whatsapp": "whatsapp_business",
            "sms": "mobile_sms",
            "mobile": "mobile_sms",
            "voice": "voice_telephony",
            "files": "secure_files",
            "images": "image_processing",
            "image": "image_processing",
            "pdf": "pdf_engine",
            "word": "document_word",
            "document": "document_word",
            "hospitals": "hospital_network",
            "hospital": "hospital_network",
            "insurances": "insurance_integration",
            "insurance": "insurance_integration",
            "payments": "payment_gateway",
            "payment": "payment_gateway",
            "notifications": "notification_service",
            "notification": "notification_service",
        }
        target = aliases.get(clean_id)
        if target and target in self._plugins:
            return self._plugins[target]
        for p in self._plugins.values():
            if clean_id in p.plugin_id.lower() or clean_id in p.name.lower():
                return p
        return None

    def get_plugin_for_tool(self, tool_name: str) -> Optional[BasePlugin]:
        plugin_id = self._tool_to_plugin_map.get(tool_name.lower())
        if plugin_id:
            return self._plugins.get(plugin_id)
        # Search capabilities dynamically
        for p in self._plugins.values():
            if any(tool_name.lower() in c.lower() for c in p.capabilities):
                return p
        return None

    def get_all_plugins(self) -> List[PluginInfo]:
        infos = []
        for p in self._plugins.values():
            infos.append(
                PluginInfo(
                    plugin_id=p.plugin_id,
                    name=p.name,
                    category=p.category,
                    provider=p.provider,
                    status=p.status.value if isinstance(p.status, PluginStatus) else str(p.status),
                    is_enabled=p.is_enabled,
                    icon=p.icon,
                    description=p.description,
                    capabilities=p.capabilities,
                    permissions=p.permissions,
                    rate_limit_rpm=p.rate_limit_rpm,
                    usage_count=p.usage_count,
                    error_count=p.error_count,
                    last_used_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.last_used_at)) if p.last_used_at else None,
                    last_tested_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.last_tested_at)) if p.last_tested_at else None,
                )
            )
        return infos

    async def connect_plugin(
        self,
        plugin_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Authenticates and connects a plugin provider.
        Updates state to CONNECTED upon verification.
        """
        p = self.get_plugin(plugin_id)
        if not p:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        p.status = PluginStatus.CONNECTING
        if credentials:
            p.configure(credentials)

        try:
            connected = await p.connect(credentials)
            if connected:
                p.status = PluginStatus.CONNECTED
                p.is_enabled = True
                p.last_tested_at = time.time()
                
                if db:
                    conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
                    if conn:
                        conn.status = PluginStatus.CONNECTED.value
                        conn.is_enabled = True
                        conn.last_tested_at = time.strftime('%Y-%m-%d %H:%M:%S')
                        db.commit()
                return {"success": True, "status": "CONNECTED", "message": f"{p.name} connected successfully"}
            else:
                p.status = PluginStatus.ERROR
                return {"success": False, "status": "ERROR", "error": f"Failed to authenticate with {p.provider}"}
        except Exception as e:
            p.status = PluginStatus.ERROR
            return {"success": False, "status": "ERROR", "error": str(e)}

    async def disconnect_plugin(self, plugin_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Safely disconnects a plugin and revokes session tokens.
        """
        p = self.get_plugin(plugin_id)
        if not p:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        await p.disconnect()
        p.status = PluginStatus.DISCONNECTED
        p.is_enabled = False

        if db:
            conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
            if conn:
                conn.status = PluginStatus.DISCONNECTED.value
                conn.is_enabled = False
                db.commit()

        return {"success": True, "status": "DISCONNECTED", "message": f"{p.name} disconnected"}

    def get_plugin_permissions(self, plugin_id: str) -> List[str]:
        p = self.get_plugin(plugin_id)
        return p.permissions if p else []

    def update_plugin_permissions(
        self,
        plugin_id: str,
        permissions: List[str],
        db: Optional[Session] = None
    ) -> bool:
        p = self.get_plugin(plugin_id)
        if not p:
            return False
        p.permissions = permissions
        if db:
            conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
            if conn:
                conn.permissions = permissions
                db.commit()
        return True

    def toggle_plugin(self, plugin_id: str, enabled: bool, status: Optional[str] = None, db: Optional[Session] = None) -> bool:
        p = self.get_plugin(plugin_id)
        if not p:
            return False
        p.is_enabled = enabled
        if status:
            try:
                p.status = PluginStatus(status)
            except Exception:
                p.status = PluginStatus.CONNECTED if enabled else PluginStatus.DISCONNECTED
        else:
            p.status = PluginStatus.CONNECTED if enabled else PluginStatus.DISCONNECTED

        if db:
            try:
                conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
                if not conn:
                    conn = PluginConnection(
                        plugin_id=plugin_id,
                        name=p.name,
                        category=p.category,
                        provider=p.provider,
                    )
                    db.add(conn)
                conn.is_enabled = enabled
                conn.status = p.status.value
                db.commit()
            except Exception as e:
                logger.error(f"Error persisting plugin toggle: {e}")
                db.rollback()
        return True

    async def test_plugin(self, plugin_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        p = self.get_plugin(plugin_id)
        if not p:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}
        res = await p.test_connection()
        p.last_tested_at = time.time()
        if db:
            try:
                conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
                if conn:
                    conn.last_tested_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    db.commit()
            except Exception:
                pass
        return res

    def revoke_plugin(self, plugin_id: str, db: Optional[Session] = None) -> bool:
        p = self.get_plugin(plugin_id)
        if not p:
            return False
        p.is_enabled = False
        p.status = PluginStatus.REVOKED
        if db:
            try:
                conn = db.query(PluginConnection).filter(PluginConnection.plugin_id == plugin_id).first()
                if conn:
                    conn.is_enabled = False
                    conn.status = PluginStatus.REVOKED.value
                    db.commit()
            except Exception:
                pass
        return True

    async def execute_tool(
        self,
        request: ToolRequest,
        db: Optional[Session] = None,
        current_user: Optional[User] = None
    ) -> ToolResult:
        """
        Routes the tool request to the appropriate registered plugin via the ToolGateway.
        """
        plugin = self.get_plugin_for_tool(request.tool_name)
        if not plugin:
            return ToolResult(
                success=False,
                status="FAILED",
                error=f"No active plugin found matching tool action '{request.tool_name}'",
                verification_status="FAILED"
            )

        return await self.gateway.execute_tool(request, plugin, db=db, current_user=current_user)

    def sync_with_db(self, db: Session):
        """Syncs plugin states from database records on startup."""
        try:
            records = db.query(PluginConnection).all()
            record_map = {r.plugin_id: r for r in records}
            
            for p_id, plugin in self._plugins.items():
                if p_id in record_map:
                    rec = record_map[p_id]
                    plugin.is_enabled = rec.is_enabled
                    try:
                        plugin.status = PluginStatus(rec.status)
                    except Exception:
                        pass
                    if rec.permissions:
                        plugin.permissions = rec.permissions
                else:
                    new_rec = PluginConnection(
                        plugin_id=p_id,
                        name=plugin.name,
                        category=plugin.category,
                        provider=plugin.provider,
                        status=plugin.status.value,
                        is_enabled=plugin.is_enabled,
                        permissions=plugin.permissions,
                        rate_limit_rpm=plugin.rate_limit_rpm
                    )
                    db.add(new_rec)
            db.commit()
        except Exception as e:
            logger.error(f"Error syncing plugins with database: {e}")
            db.rollback()

# Global singleton instance
plugin_manager = PluginManager()

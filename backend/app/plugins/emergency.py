from typing import Tuple, Dict, Set, Optional
import time

class EmergencyController:
    """
    Global Emergency Action Control & Kill Switch Manager.
    Enforces instantaneous circuit breaking on all autonomous agents,
    specific plugins, or outbound communication channels.
    """

    def __init__(self):
        self._global_paused: bool = False
        self._paused_plugins: Set[str] = set()
        self._paused_agents: Set[str] = set()
        self._paused_scopes: Set[str] = set() # e.g. "OUTBOUND", "EXTERNAL_API"
        self._pause_reason: Optional[str] = None
        self._last_updated: float = time.time()

    @property
    def is_global_paused(self) -> bool:
        return self._global_paused

    @property
    def paused_plugins(self) -> Set[str]:
        return set(self._paused_plugins)

    @property
    def paused_agents(self) -> Set[str]:
        return set(self._paused_agents)

    @property
    def pause_reason(self) -> Optional[str]:
        return self._pause_reason

    def set_global_pause(self, pause: bool, reason: Optional[str] = None):
        self._global_paused = pause
        self._pause_reason = reason if pause else None
        self._last_updated = time.time()

    def set_plugin_pause(self, plugin_id: str, pause: bool, reason: Optional[str] = None):
        if pause:
            self._paused_plugins.add(plugin_id)
        else:
            self._paused_plugins.discard(plugin_id)
        self._last_updated = time.time()

    def set_agent_pause(self, agent_id: str, pause: bool, reason: Optional[str] = None):
        if pause:
            self._paused_agents.add(agent_id)
        else:
            self._paused_agents.discard(agent_id)
        self._last_updated = time.time()

    def set_scope_pause(self, scope: str, pause: bool):
        if pause:
            self._paused_scopes.add(scope.upper())
        else:
            self._paused_scopes.discard(scope.upper())
        self._last_updated = time.time()

    def is_action_allowed(self, agent_id: str, plugin_id: str, tool_name: str) -> Tuple[bool, str]:
        """
        Determines whether the execution is permitted under current emergency controls.
        """
        if self._global_paused:
            return False, f"EMERGENCY KILL SWITCH ACTIVE: All autonomous operations are paused. Reason: {self._pause_reason or 'Admin intervention'}"

        if agent_id in self._paused_agents:
            return False, f"CIRCUIT BREAKER: Calling agent '{agent_id}' is currently paused by administrator."

        if plugin_id in self._paused_plugins:
            return False, f"CIRCUIT BREAKER: Target plugin '{plugin_id}' is currently paused by administrator."

        # Outbound communication checks
        outbound_tools = {"send_whatsapp_message", "send_sms", "send_email", "telephony_outbound_call", "send_notification"}
        if "OUTBOUND" in self._paused_scopes and tool_name.lower() in outbound_tools:
            return False, "EMERGENCY CONTROL: All outbound patient communications are temporarily paused."

        return True, "Allowed"

    def get_status_dict(self) -> Dict:
        return {
            "global_paused": self._global_paused,
            "paused_plugins": list(self._paused_plugins),
            "paused_agents": list(self._paused_agents),
            "paused_scopes": list(self._paused_scopes),
            "pause_reason": self._pause_reason,
            "last_updated": self._last_updated,
        }

# Global singleton instance
emergency_controller = EmergencyController()

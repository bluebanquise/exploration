# common/plugin_base.py

from typing import Any, Dict, List, Optional
from .errors import PluginError
from .responses import api_ok, api_error


class BasePlugin:
    """
    Generic plugin base class.

    Subclasses:
      - define SUPPORTED_ACTIONS (optional)
      - implement handle_action(action, payload)
      - optionally override parse_cli_payload(action, args)
    """

    SUPPORTED_ACTIONS: List[str] = []

    def __init__(self, action_args, config, logger, global_args) -> None:
        self.action_args: List[str] = action_args or []
        self.config: Dict[str, Any] = config or {}
        self.logger = logger
        self.global_args = global_args or {}

    # -------- CLI entry point --------

    def run(self) -> Dict[str, Any]:
        """
        CLI entry point.

        Expects self.action_args to be: [action, ...rest...]
        """
        if not self.action_args:
            return api_error("No action specified")

        action = self.action_args[0]
        try:
            payload = self.parse_cli_payload(action, self.action_args[1:])
            return self.execute(action, payload)
        except PluginError as e:
            self.logger.error("Plugin error: %s", e)
            return api_error(str(e))
        except Exception as e:
            self.logger.exception("Unhandled exception in plugin")
            return api_error(str(e))

    # -------- Programmatic / REST entry point --------

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Programmatic entry point, used by REST API or other callers.
        """
        if self.SUPPORTED_ACTIONS and action not in self.SUPPORTED_ACTIONS:
            return api_error(f"Unsupported action '{action}'")

        try:
            result = self.handle_action(action, payload)

            # If plugin returns a full response, pass it through
            if isinstance(result, dict) and "status" in result:
                return result

            # If plugin returns plain data
            if isinstance(result, dict):
                return api_ok(data=result)
            if isinstance(result, str):
                return api_ok(message=result)
            if result is None:
                return api_ok()

            return api_ok(data={"result": result})
        except PluginError as e:
            self.logger.error("Plugin error in action %s: %s", action, e)
            return api_error(str(e))
        except Exception as e:
            self.logger.exception("Unhandled exception in action %s", action)
            return api_error(str(e))

    # -------- Methods for subclasses --------

    def parse_cli_payload(self, action: str, args: List[str]) -> Dict[str, Any]:
        """
        Default CLI parser: no payload.

        Subclasses override to parse args into a payload dict.
        """
        return {}

    def handle_action(self, action: str, payload: Dict[str, Any]) -> Any:
        """
        Subclasses must implement this.

        Should return:
          - dict (data) or
          - string (message) or
          - full response dict with 'status'
        """
        raise NotImplementedError("handle_action must be implemented by plugin")

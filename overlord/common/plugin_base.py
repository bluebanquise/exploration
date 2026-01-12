# common/plugin_base.py

from typing import Any, Dict, List
from common.errors import PluginError


class BasePlugin:
    """
    Generic plugin base class.
    Optional.
    """

    def __init__(self, action_args, config, logger, global_args):
        self.action_args = action_args or []
        self.config = config or {}
        self.logger = logger
        self.global_args = global_args or {}

    # Allow nested value update
    def set_deep(self, data: dict, path: str, value: Any):
        keys = path.split(".")
        d = data
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def api_ok(self, data=None, message=None):
        response = {"status": "ok"}
        if data is not None:
            response["data"] = data
        if message is not None:
            response["message"] = message
        return response

    def api_error(self, message, data=None):
        response = {"status": "error", "message": message}
        if data is not None:
            response["data"] = data
        return response



    # ------------------------------------------------------------
    # Deep path setter 
    # ------------------------------------------------------------

    def set_deep_path(root: Dict[str, Any], path: str, value: Any) -> None:
        """
        Set a value in a nested dict using a dot-separated path.
        Example:
            set_deep_path(data, "vars.networks.admin.ip", "10.0.0.1")
        """
        keys = path.split(".")
        d = root
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value


    # ------------------------------------------------------------
    # Deep merge
    # ------------------------------------------------------------

    def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge dict b into dict a.
        Values in b override values in a.
        Returns a new dict (does not mutate inputs).
        """
        result = dict(a)
        for key, value in b.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result


    # ------------------------------------------------------------
    # Deep diff
    # ------------------------------------------------------------

    def deep_diff(a: Any, b: Any) -> Any:
        """
        Compute a recursive diff between a and b.

        Returns a structure describing:
        - added keys
        - removed keys
        - changed values

        Examples:
        deep_diff({"x":1}, {"x":2})
            -> {"x": {"from":1, "to":2}}

        deep_diff({"a":1}, {"a":1})
            -> None

        deep_diff({"a":1}, {"a":1, "b":2})
            -> {"b": {"added":2}}
        """
        # Both dicts → recurse
        if isinstance(a, dict) and isinstance(b, dict):
            diff: Dict[str, Any] = {}
            keys = set(a.keys()) | set(b.keys())

            for key in keys:
                if key not in a:
                    diff[key] = {"added": b[key]}
                elif key not in b:
                    diff[key] = {"removed": a[key]}
                else:
                    sub = deep_diff(a[key], b[key])
                    if sub not in (None, {}):
                        diff[key] = sub

            return diff or None

        # Scalars → compare directly
        if a != b:
            return {"from": a, "to": b}

        return None
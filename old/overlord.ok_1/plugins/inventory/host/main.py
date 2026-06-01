# plugins/inventory/host/main.py

import json
from typing import Any, Dict, List, Optional

from inventory import AnsibleInventory


class Plugin:
    def __init__(self, action_args, inventory: AnsibleInventory, config, logger, global_args):
        """
        action_args: list of tokens, e.g. ["add", "c001", '{"c001": {"alias": "compute-1"}}']
        inventory: AnsibleInventory instance
        config: plugin-specific config (unused for now)
        logger: shared logger
        global_args: dict with context (diff, check, inventory_root, etc.)
        """
        self.action_args: List[str] = action_args
        self.inventory = inventory
        self.config = config or {}
        self.logger = logger
        self.global_args = global_args


    # Allow nested value update
    def set_deep(self, data: dict, path: str, value: Any):
        keys = path.split(".")
        d = data
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value



    # ---------------------
    # Public entry points
    # ---------------------

    def run(self) -> Dict[str, Any]:
        """
        CLI entry: parse self.action_args, build a payload, and delegate to execute().
        """
        if not self.action_args:
            return self._error("No action specified. Use: list|add|get|update|delete")

        action = self.action_args[0]
        try:
            payload = self._parse_cli_payload(action, self.action_args[1:])
        except ValueError as e:
            return self._error(str(e))

        try:
            return self.execute(action, payload)
        except Exception as e:
            self.logger.exception("Error in host plugin")
            return self._error(str(e))

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Programmatic entry: used by REST API.
        payload structure depends on action:

        - list: {}
        - add: { "hosts": { "c001": { ... }, ... } }
        - get: { "hostname": "c001" }
        - update: { "hostname": "c001", "data": { ... } }
        - delete: { "hostname": "c001" }
        """
        if action == "list":
            return self._action_list(payload)
        elif action == "add":
            return self._action_add(payload)
        elif action == "get":
            return self._action_get(payload)
        elif action == "update":
            return self._action_update(payload)
        elif action == "delete":
            return self._action_delete(payload)
        else:
            return self._error(f"Unknown action: {action}. Use: list|add|get|update|delete")

    # ---------------------
    # Internal helpers
    # ---------------------

    def _ok(self, data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Dict[str, Any]:
        res: Dict[str, Any] = {"status": "ok"}
        if data is not None:
            res["data"] = data
        if message is not None:
            res["message"] = message
        return res

    def _error(self, message: str) -> Dict[str, Any]:
        return {"status": "error", "message": message}

    def _parse_cli_payload(self, action: str, args: List[str]) -> Dict[str, Any]:
        """
        Convert CLI arguments into the generic payload format used by execute().
        """
        if action == "list":
            return {}

        if action in ("add", "get", "update", "delete"):
            if not args:
                raise ValueError(f"{action} requires at least HOSTNAME")

            hostname = args[0]

            if action == "get" or action == "delete":
                return {"hostname": hostname}

            if action == "add":
                if len(args) < 2:
                    # No JSON provided: minimal data
                    hosts = {hostname: {}}
                else:
                    hosts = self._parse_add_json(hostname, args[1])
                return {"hosts": hosts}

            if action == "update":
                if len(args) < 2:
                    raise ValueError("update requires JSON or key=value pairs")

                first_payload = args[1]
                if first_payload.strip().startswith("{"):
                    data = self._parse_update_json(hostname, first_payload)
                else:
                    data = self._parse_update_kv(args[1:])
                return {"hostname": hostname, "data": data}

        raise ValueError(f"Unknown action: {action}")

    def _parse_add_json(self, hostname: str, payload: str) -> Dict[str, Dict[str, Any]]:
        try:
            json_data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(json_data, dict) or hostname not in json_data:
            raise ValueError(f"JSON must be a dict with key '{hostname}'")

        return json_data

    def _parse_update_json(self, hostname: str, payload: str) -> Dict[str, Any]:
        try:
            json_data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(json_data, dict) or hostname not in json_data:
            raise ValueError(f"JSON must be a dict with key '{hostname}'")

        return json_data[hostname]

    def _parse_update_kv(self, kv_args: List[str]) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for kv in kv_args:
            if "=" not in kv:
                raise ValueError(f"Invalid key=value pair: {kv}")
            path, value = kv.split("=", 1)

            # Special case: vars.* goes into nested dict
            if path.startswith("vars."):
                if "vars" not in data:
                    data["vars"] = {}
                self.set_deep(data["vars"], path[5:], value)
            else:
                data[path] = value

        return data


    # ---------------------
    # Actions
    # ---------------------

    def _action_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hosts = self.inventory.list_hosts()
        return self._ok(data={"hosts": hosts})

    def _action_add(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hosts = payload.get("hosts") or {}
        if not isinstance(hosts, dict) or not hosts:
            return self._error("Payload must contain 'hosts' dict")

        for hostname, host_data in hosts.items():
            self.inventory.add_host(hostname, host_data or {})
        self.inventory.save()

        return self._ok(message=f"Added {len(hosts)} host(s)")

    def _action_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hostname = payload.get("hostname")
        if not hostname:
            return self._error("hostname is required")

        host = self.inventory.get_host(hostname)
        if host is None:
            return self._error(f"Host {hostname} not found")

        return self._ok(data={"host": {hostname: host}})

    def _action_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hostname = payload.get("hostname")
        data = payload.get("data") or {}
        if not hostname:
            return self._error("hostname is required")
        if not isinstance(data, dict) or not data:
            return self._error("data must be a non-empty dict")

        if self.inventory.get_host(hostname) is None:
            return self._error(f"Host {hostname} not found")

        self.inventory.update_host(hostname, data)
        self.inventory.save()

        return self._ok(message=f"Host {hostname} updated")

    def _action_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hostname = payload.get("hostname")
        if not hostname:
            return self._error("hostname is required")

        if self.inventory.get_host(hostname) is None:
            return self._error(f"Host {hostname} not found")

        self.inventory.delete_host(hostname)
        self.inventory.save()

        return self._ok(message=f"Host {hostname} deleted")

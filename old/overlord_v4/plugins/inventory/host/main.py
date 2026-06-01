import json
from typing import Any, Dict, List

from common.plugin_base import BasePlugin
from common.errors import ValidationError, NotFoundError, ConflictError


class Plugin(BasePlugin):
    SUPPORTED_ACTIONS = ["list", "add", "get", "update", "delete"]

    def __init__(self, action_args, inventory, config, logger, global_args):
        super().__init__(action_args, config, logger, global_args)
        self.inventory = inventory

    # ---------------- CLI parsing ----------------

    def parse_cli_payload(self, action: str, args: List[str]) -> Dict[str, Any]:
        if action == "list":
            return {}

        if action in ("get", "delete"):
            if not args:
                raise ValidationError(f"{action} requires HOSTNAME")
            return {"hostname": args[0]}

        if action == "add":
            if not args:
                raise ValidationError("add requires JSON or HOSTNAME and optional alias")

            first = args[0]
            if first.strip().startswith("{"):
                try:
                    data = json.loads(first)
                except json.JSONDecodeError as e:
                    raise ValidationError(f"Invalid JSON: {e}") from e
                return {"hosts": data}

            hostname = first
            alias = args[1] if len(args) > 1 else None
            host_data = {}
            if alias:
                host_data["alias"] = alias
            return {"hosts": {hostname: host_data}}

        if action == "update":
            if not args:
                raise ValidationError("update requires HOSTNAME and data")
            hostname = args[0]
            if len(args) < 2:
                raise ValidationError("update requires JSON or key=value pairs")

            first = args[1]
            if first.strip().startswith("{"):
                try:
                    data = json.loads(first)
                except json.JSONDecodeError as e:
                    raise ValidationError(f"Invalid JSON: {e}") from e
            else:
                data = self._parse_update_kv(args[1:])

            return {"hostname": hostname, "data": data}

        raise ValidationError(f"Unknown action: {action}")

    def _parse_update_kv(self, kv_args: List[str]) -> Dict[str, Any]:
        data = {}
        for kv in kv_args:
            if "=" not in kv:
                raise ValidationError(f"Invalid key=value pair: {kv}")
            key, value = kv.split("=", 1)
            data[key] = value
        return data

    # ---------------- Action dispatcher ----------------

    def handle_action(self, action: str, payload: Dict[str, Any]) -> Any:
        if action == "list":
            return self._action_list()
        if action == "add":
            return self._action_add(payload)
        if action == "get":
            return self._action_get(payload)
        if action == "update":
            return self._action_update(payload)
        if action == "delete":
            return self._action_delete(payload)
        raise ValidationError(f"Unsupported action '{action}'")

    # ---------------- Actions ----------------

    def _action_list(self):
        return {"hosts": self.inventory.list_hosts()}

    def _action_add(self, payload):
        hosts = payload.get("hosts") or {}
        self.inventory.add_hosts(hosts)
        self.inventory.save()
        return f"Added {len(hosts)} host(s)"

    def _action_get(self, payload):
        hostname = payload["hostname"]
        host = self.inventory.get_host(hostname)
        if host is None:
            raise NotFoundError(f"Host {hostname} not found")
        return {"host": {hostname: host}}

    def _action_update(self, payload):
        hostname = payload["hostname"]
        data = payload["data"]
        if self.inventory.get_host(hostname) is None:
            raise NotFoundError(f"Host {hostname} not found")
        self.inventory.update_host(hostname, data)
        self.inventory.save()
        return f"Host {hostname} updated"

    def _action_delete(self, payload):
        hostname = payload["hostname"]
        if self.inventory.get_host(hostname) is None:
            raise NotFoundError(f"Host {hostname} not found")
        self.inventory.delete_host(hostname)
        self.inventory.save()
        return f"Host {hostname} deleted"

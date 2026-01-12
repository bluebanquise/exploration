# plugins/inventory/host/main.py

import json

from common.inventory import AnsibleInventory
from common.plugin_base import BasePlugin

class Plugin(BasePlugin):
    def __init__(self, action_args, config, logger, global_args):
        """
        action_args: list of tokens, e.g. ["add", "c001", '{"c001": {"alias": "compute-1"}}']
        inventory: AnsibleInventory instance
        config: plugin-specific config (unused for now)
        logger: shared logger
        global_args: dict with context (diff, check, inventory_root, etc.)
        """
        super().__init__(action_args, config, logger, global_args)
      
        # Load inventory
        self.logger.debug("Loading inventory...")
        self.inventory = AnsibleInventory(
            inventory_root=self.global_args['inventory_root'],
            working_folder=self.global_args['working_folder'],
            diff=self.global_args['diff'],
            check=self.global_args['check'],
            logger=self.logger,
        )
        # self.logger.debug("Current inventory:" + str(self.inventory.show()))

######################## CLI ENTRY POINT ########################

    def cli_execute(self):
        """
        CLI entry: parse self.action_args, build a payload, and delegate to execute().
        """

        self.logger.debug("Entering CLI host plugin")
        ##################### CHECKS

        # We define supported actions, to be filtered later
        SUPPORTED_ACTIONS = ["list", "add", "get", "update", "delete"]
        # Check there is action
        if not self.action_args:
            return self.api_error("No action specified. Use: " + str(SUPPORTED_ACTIONS))

        action = self.action_args[0]
        # Check action is allowed by plugin
        if action not in SUPPORTED_ACTIONS:
            return api_error(f"Unsupported action '{action}'. Allowed actions: '{str(SUPPORTED_ACTIONS)}'")


        ##################### FILTER ACTION AND BUILD PAYLOAD

        # Now we need to create the payload, it should be similar to something sent via HTML
        # to have execute handle both HTML and CLI :)

        if action == "list":
            payload = {}

        args = self.action_args[1:]
        if action in ("add", "get", "update", "delete"):
            if not args:
                raise ValueError(f"{action} requires at least HOSTNAME")

            hostname = args[0]

            if action == "get" or action == "delete":
                payload = {hostname}

            elif action == "add":
                if len(args) < 2:
                    # No JSON provided: minimal data
                    payload = {hostname: {}}
                else:
                    # JSON, lets read it and inculde it as data to payload
                    try:
                        data = json.loads(args[1])
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON: {e}") from e
                    payload = {hostname: data}

            elif action == "update":
                if len(args) < 2:
                    raise ValueError("Update requires JSON or key=value pairs")

                update_payload = args[1]
                # User could provide both json or foo.stuff=bar
                if update_payload.strip().startswith("{"):  # This is JSON, try to load it
                    try:
                        data = json.loads(update_payload)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON: {e}") from e
                else:  # This is foo.stuff=bar, try to load it
                    data = self.parse_update_kv(args[1:])
                payload = {hostname: data}
            else:
                raise ValueError(f"Unknown action: {action}")
                return self.api_error(str(f"Unknown action: {action}"))


        ##################### EXECUTE

        # Payload is ready, lets call main execute now
        try:
            return self.execute(action, payload)
        except Exception as e:
            self.logger.exception("Error in host plugin")
            return self.api_error(str(e))

    # Function to parse dot like dict path
    # Can be improved later
    def parse_update_kv(self, kv_args):
        data = {}
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


######################## EXECUTE AND ACTIONS ########################

    def execute(self, action, payload):
        """
        Programmatic entry: used by cli_run and REST API.
        payload structure depends on action:

        - list: {}
        - add: { "c001": { ... } }
        - get: { "c001" }
        - update: { "c001": { ... } }
        - delete: { "c001" }
        """
        
        if action == "list":
            return self.action_list(payload)
        elif action == "add":
            return self.action_add(payload)
        elif action == "get":
            return self.action_get(payload)
        elif action == "update":
            return self.action_update(payload)
        elif action == "delete":
            return self.action_delete(payload)


    def action_list(self, payload):
        hosts = self.inventory.list_hosts()
        return self.api_ok(data={"hosts": hosts})

    # Support for multiple add to be added in cli parse later
    def action_add(self, payload):
        for hostname, host_data in payload.items():
            self.inventory.add_host(hostname, host_data or {})
        self.inventory.save()

        return self.api_ok(message=f"Added {len(payload)} host(s)")

    def action_get(self, payload):
        output = {}
        for hostname in payload:
            host_data = self.inventory.get_host(hostname)
            if host_data is None:
                return self.api_error(f"Host {hostname} not found")
            output[hostname] = host_data

        return self.api_ok(data={"hosts": output})

    def action_update(self, payload):
        for hostname, host_data in payload.items():
            if not hostname:
                return self.api_error("hostname is required")
            if not isinstance(host_data, dict) or not host_data:
                return self.api_error("data must be a non-empty dict")
            if self.inventory.get_host(hostname) is None:
                return self.api_error(f"Host {hostname} not found")
            self.inventory.update_host(hostname, host_data)
        self.inventory.save()

        return self.api_ok(message=f"Host {hostname} updated")

    def action_delete(self, payload):
        for hostname in payload:
            if self.inventory.get_host(hostname) is None:
                return self.api_error(f"Host {hostname} not found")
            self.inventory.delete_host(hostname)
        self.inventory.save()

        return self.api_ok(message=f"Host {hostname} deleted")

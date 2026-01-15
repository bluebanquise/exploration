# plugins/inventory/group/main.py

from typing import Dict, Any, Optional
from common.inventory import AnsibleInventory
from common.plugin_base import BasePlugin
import json


class Plugin(BasePlugin):
    def __init__(self, action_args, config, logger, global_args):
        """
        Inventory groups management plugin.

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



######################## CLI ENTRY POINT ########################

    def cli_execute(self):
        """
        CLI entry: parse self.action_args, build a payload, and delegate to execute().
        """

        self.logger.debug("Entering CLI group plugin")
        ##################### CHECKS

        # We define supported actions, to be filtered later
        SUPPORTED_ACTIONS = ["list", "add", "get", "update", "add_hosts", "remove_hosts", "delete"]
        # Check there is action
        if not self.action_args:
            return self.api_error("No action specified. Use: " + str(SUPPORTED_ACTIONS))

        action = self.action_args[0]
        # Check action is allowed by plugin
        if action not in SUPPORTED_ACTIONS:
            return self.api_error(f"Unsupported action '{action}'. Allowed actions: '{str(SUPPORTED_ACTIONS)}'")


        ##################### FILTER ACTION AND BUILD PAYLOAD

        # Now we need to create the payload, it should be similar to something sent via HTML
        # to have execute handle both HTML and CLI :)

        if action == "list":
            payload = {}

        args = self.action_args[1:]
        if action in ("add", "get", "update", "add_hosts", "remove_hosts", "delete"):
            if not args:
                raise ValueError(f"{action} requires at least GROUPNAME")

            groupname = args[0]

            if action == "get" or action == "delete":
                payload = {groupname}

            elif action == "add":
                if len(args) < 2:
                    # No JSON provided: minimal data
                    payload = {groupname: {}}
                else:
                    # JSON, lets read it and inculde it as data to payload
                    try:
                        data = json.loads(args[1])
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON: {e}") from e
                    payload = {groupname: data}

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
                payload = {groupname: data}
            elif action in ["add_hosts", "remove_hosts"]:
                if len(args) < 2:
                    raise ValueError("Adding or removing hosts requires JSON or comma,separated,list of hosts")
                update_hosts_payload = args[1]
                if update_hosts_payload.strip().startswith("{"):  # This is JSON, try to load it
                    try:
                        data = json.loads(update_payload)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON: {e}") from e
                else:  # This is hosts=comma,separated,list. Convert to json
                    data = {"hosts": update_hosts_payload.split(",")}
                payload = {groupname: data}

            else:
                raise ValueError(f"Unknown action: {action}")
                return self.api_error(str(f"Unknown action: {action}"))


        ##################### EXECUTE

        # Payload is ready, lets call main execute now
        try:
            return self.execute(action, payload)
        except Exception as e:
            self.logger.exception("Error in group plugin")
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
        - add: { "mygroup": { ... } }
        - get: { "mygroup" }
        - update: { "mygroup": { ... } }
        - delete: { "mygroup" }
        - add_hosts: { "mygroup": { "hosts" [] } }
        - remove_hosts { "mygroup": { "hosts" [] } }
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
        elif action == "add_hosts":
            return self.action_add_hosts(payload)
        elif action == "remove_hosts":
            return self.action_remove_hosts(payload)


    # # ------------- Utility -------------
    # def _get_groups_dict(self) -> Dict[str, Any]:
    #     """
    #     Central place to access group data in the inventory structure.
    #     Adjust this to match your existing AnsibleInventory layout.
    #     """
    #     # Example: groups stored under self.inventory.data["groups"]
    #     return self.inventory.data.setdefault("groups", {})

    # ------------- Core operations -------------

    def action_list(self, payload):
        groups = self.inventory.list_groups()
        return self.api_ok(data={"groups": groups})

    def action_add(self, payload):
        for groupname, group_data in payload.items():
            self.inventory.add_group(groupname, group_data or {})
        self.inventory.save()

        return self.api_ok(message=f"Added {len(payload)} groups(s)")

    def action_get(self, payload):
        output = {}
        for groupname in payload:
            group_data = self.inventory.get_group(groupname)
            if group_data is None:
                return self.api_error(f"Group {groupname} not found")
            output[groupname] = group_data

        return self.api_ok(data={"groups": output})

    def action_update(self, payload):
        for groupname, group_data in payload.items():
            if not groupname:
                return self.api_error("groupname is required")
            if not isinstance(group_data, dict) or not group_data:
                return self.api_error("data must be a non-empty dict")
            if self.inventory.get_group(groupname) is None:
                return self.api_error(f"Group {groupname} not found")
            hosts_data = group_data.get("hosts", None)
            vars_data = group_data.get("vars", None)
            self.inventory.update_group(groupname, hosts_data, vars_data)
        self.inventory.save()

        return self.api_ok(message=f"{len(payload)} groups(s) updated")

    def action_delete(self, payload):
        for groupname in payload:
            if self.inventory.get_group(groupname) is None:
                return self.api_error(f"Group {groupname} not found")
            self.inventory.delete_group(groupname)
        self.inventory.save()

        return self.api_ok(message=f"Group {groupname} deleted")

    def action_add_hosts(self, payload):
        for groupname, group_data in payload.items():
            if not groupname:
                return self.api_error("groupname is required")
            if not isinstance(group_data, dict) or not group_data:
                return self.api_error("data must be a non-empty dict")
            if self.inventory.get_group(groupname) is None:
                return self.api_error(f"Group {groupname} not found")
            inventory_group_data = self.inventory.get_group(groupname)
            # Add new hosts and make sure no duplicates
            inventory_group_data["hosts"] = list(set(inventory_group_data["hosts"] + group_data["hosts"]))
            self.inventory.update_group(groupname, inventory_group_data["hosts"], inventory_group_data["vars"])
        self.inventory.save()

        return self.api_ok(message=f"{len(payload)} groups(s) updated")

    def action_remove_hosts(self, payload):
        for groupname, group_data in payload.items():
            if not groupname:
                return self.api_error("groupname is required")
            if not isinstance(group_data, dict) or not group_data:
                return self.api_error("data must be a non-empty dict")
            if self.inventory.get_group(groupname) is None:
                return self.api_error(f"Group {groupname} not found")
            inventory_group_data = self.inventory.get_group(groupname)
            # Remove hosts and handle if not exist (aka skip if not exist)
            inventory_group_data["hosts"] = list(set(inventory_group_data["hosts"]) - set(group_data["hosts"]))
            self.inventory.update_group(groupname, inventory_group_data["hosts"], inventory_group_data["vars"])
        self.inventory.save()

        return self.api_ok(message=f"{len(payload)} groups(s) updated")
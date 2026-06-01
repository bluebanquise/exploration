# plugins/inventory/user/main.py

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

        self.logger.debug("Entering CLI user plugin")
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

            username = args[0]

            if action == "get" or action == "delete":
                payload = {username}

            elif action == "add":
                if len(args) < 2:
                    # No JSON provided: minimal data
                    payload = {username: {}}
                else:
                    # JSON, lets read it and inculde it as data to payload
                    try:
                        data = json.loads(args[1])
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON: {e}") from e
                    payload = {username: data}

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
                payload = {username: data}
            else:
                raise ValueError(f"Unknown action: {action}")
                return self.api_error(str(f"Unknown action: {action}"))


        ##################### EXECUTE

        # Payload is ready, lets call main execute now
        try:
            return self.execute(action, payload)
        except Exception as e:
            self.logger.exception("Error in user plugin")
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
        - add: { "net-admin": { ... } }
        - get: { "net-admin" }
        - update: { "net-admin": { ... } }
        - delete: { "net-admin" }
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
        users = self.inventory.get_group('all')['vars'].get('users',{'users': []})
        return self.api_ok(data=users)

    # Support for multiple add to be added in cli parse later
    def action_add(self, payload):

        users = self.inventory.get_group('all')['vars'].get('users',{'users': []})
        for username, user_data in payload.items():
            if 'uid' not in user_data:
                return self.api_error("UID is required")
            if 'home' not in user_data:
                user_data['home'] = '/home/' + username
            users['users'].append(user_data)
        self.inventory.update_group('all', None, {'users': users})
        self.inventory.save()

        return self.api_ok(message=f"Added {len(payload)} user(s)")

    def action_get(self, payload):

        output = {}
        users = self.inventory.get_group('all')['vars'].get('users',{'users': []})
        for username in payload:
            # Look for the user in the list
            
            if username not in users['users']:
                return self.api_error(f"User {username} not found")
            output[username] = users['users'][username]

        return self.api_ok(data={"users": output})

    def action_update(self, payload):

        users = self.inventory.get_group('all')['vars'].get('users',{'users': []})
        for username, user_data in payload.items():
            if not username:
                return self.api_error("username is required")
            if not isinstance(user_data, dict) or not user_data:
                return self.api_error("data must be a non-empty dict")
            if username not in users['users']:
                return self.api_error(f"User {username} not found")
            users['users'][username] = user_data

        self.inventory.update_group('all', None, {'users': users})
        self.inventory.save()

        return self.api_ok(message=f"User {username} updated")

    def action_delete(self, payload):

        users = self.inventory.get_group('all')['vars'].get('users',{'users': []})
        for username in payload:
            if username not in users['users']:
                return self.api_error(f"User {username} not found")
            users['users'].pop(username)
        self.inventory.update_group('all', None, {'users': users})
        self.inventory.save()

        return self.api_ok(message=f"User {username} deleted")

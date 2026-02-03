
import json

from common.inventory import AnsibleInventory
from common.plugin_base import BasePlugin

class Plugin(BasePlugin):
    def __init__(self, action_args, config, logger, global_args):
        """
        action_args:
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

        if action == "get":
            return self.action_get(payload)

    def action_get(self, payload):

        inventory = self.inventory.get_inventory()
        inventory['inventory_root'] = self.global_args['inventory_root']
        
        return self.api_ok(data=inventory)

# plugins/inventory/group/main.py

from typing import Dict, Any, Optional
#from common.inventory import AnsibleInventory
from inventory import AnsibleInventory


class GroupPlugin:
    """
    Inventory group management plugin.

    Groups are stored in the inventory under something like:
      all:
        children:
          <group_name>:
            vars: { ... }
            # or however your AnsibleInventory represents groups

    This plugin focuses on a logical model:
      - group_type: one of [function, os, hardware, rack, custom]
      - data structure varies by type
    """

    def __init__(self, inventory_path: str):
        self.inventory = AnsibleInventory(inventory_path)

    # ------------- Utility -------------
    def _get_groups_dict(self) -> Dict[str, Any]:
        """
        Central place to access group data in the inventory structure.
        Adjust this to match your existing AnsibleInventory layout.
        """
        # Example: groups stored under self.inventory.data["groups"]
        return self.inventory.data.setdefault("groups", {})

    # ------------- Core operations -------------

    def list_groups(self) -> Dict[str, Any]:
        groups = self._get_groups_dict()
        return groups

    def get_group(self, name: str) -> Optional[Dict[str, Any]]:
        groups = self._get_groups_dict()
        return groups.get(name)

    def add_group(self, name: str, payload: Dict[str, Any]) -> None:
        groups = self._get_groups_dict()
        if name in groups:
            raise ValueError(f"Group {name} already exists")

        groups[name] = payload

    def update_group(self, name: str, payload: Dict[str, Any]) -> None:
        groups = self._get_groups_dict()
        if name not in groups:
            raise ValueError(f"Group {name} does not exist")

        groups[name] = payload

    def delete_group(self, name: str) -> None:
        groups = self._get_groups_dict()
        if name not in groups:
            raise ValueError(f"Group {name} does not exist")

        del groups[name]

    def save(self) -> None:
        self.inventory.save()

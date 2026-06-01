# inventory.py

import yaml
import configparser
import os
import shutil
import tempfile
import subprocess


def load_yaml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump_yaml_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_ini_file(path):
    parser = configparser.ConfigParser(allow_no_value=True, delimiters=("="))
    parser.optionxform = str  # keep case
    with open(path, "r", encoding="utf-8") as f:
        parser.read_file(f)
    return parser


def load_config(config_path):
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    return load_yaml_file(config_path)


class AnsibleInventory:
    """
    Represents an Ansible inventory rooted at: <inventory_root>

    Layout:
      inventory/cluster/hosts/<fn_group>.yml
      inventory/cluster/groups/<group>.ini
      inventory/host_vars/<host>/main.yml
      inventory/group_vars/<group>/<plugin>.yml
    """

    def __init__(
        self,
        inventory_root: str,
        working_folder: str,
        diff: bool = False,
        check: bool = False,
        logger=None,
    ):
        self.inventory_root = os.path.abspath(inventory_root)
        self.working_folder = os.path.abspath(working_folder)
        self.diff = diff
        self.check = check
        self.logger = logger

        self.hosts = {}
        self.groups = {}
        self.load_inventory()


    # ####################################################################################
    # ##### Load inventory
    # ##

    def load_inventory(self):
        #self.logger.info('Loading inventory')
        self.load_hosts()
        self.load_groups()

    def load_hosts(self):

        data = {}

        hosts_dir = os.path.join(
            self.inventory_root, "cluster", "hosts"
        )

        if not os.path.isdir(hosts_dir) or len(os.listdir(hosts_dir)) == 0:
            # No hosts yet, treat as empty
            print("No hosts folder or files found at " + hosts_dir)
            self.hosts = {}
            return

        # Now load all hosts
        for fname in os.listdir(hosts_dir):
            if not fname.endswith(".yml") and not fname.endswith(".yaml"):
                continue
            hosts_file_path = os.path.join(hosts_dir, fname)
            buffer_data = load_yaml_file(hosts_file_path) or {}
            all_section = buffer_data.get("all", {})
            hosts_section = all_section.get("hosts", {}) or {}
            data.update(hosts_section)

        print(data)

        # Check if an host posses specific hostvars
        for hostname in data:

            print("Working on host " + hostname)
            hv_path = os.path.join(
                self.inventory_root, "host_vars", hostname, "main.yml"
            )
            if os.path.isfile(hv_path):
                hostvars = load_yaml_file(hv_path) or {}
                data[hostname].update(hostvars)

        # Now save to memory
        self.hosts = data

    def load_groups(self):

        groups_dir = os.path.join(
            self.inventory_root, "cluster", "groups"
        )

        # Always init 'all' group
        self.groups = {'all':{'vars':{}, 'hosts': []}}

        if not os.path.isdir(groups_dir):
            # No groups yet, treat as empty
            return

        for fname in os.listdir(groups_dir):
            if not fname.endswith(".ini"):
                continue
            group_name = os.path.splitext(fname)[0]
            ini_path = os.path.join(groups_dir, fname)
            parser = load_ini_file(ini_path)

            hosts_list = []
            if parser.has_section(group_name):
                hosts_list = [h for h in parser.options(group_name)]

            group_vars = {}
            gv_dir = os.path.join(
                self.inventory_root, "group_vars", group_name
            )
            if os.path.isdir(gv_dir):
                for plugin_file in os.listdir(gv_dir):
                    if not plugin_file.endswith(".yml") and not plugin_file.endswith(".yaml"):
                        continue
                    plugin_name = os.path.splitext(plugin_file)[0]
                    plugin_path = os.path.join(gv_dir, plugin_file)
                    plugin_vars = load_yaml_file(plugin_path) or {}
                    group_vars[plugin_name] = plugin_vars

            self.groups[group_name] = {
                "hosts": hosts_list,
                "vars": group_vars,
            }

    # ####################################################################################
    # ##### Inventory management
    # ##

    def get_inventory(self):
        return {'hosts': self.hosts, 'groups': self.groups}

    def show(self):
        print(self.hosts)
        print(self.groups)
        return

    # #######################################
    # ##### Hosts management
    # ##

    def list_hosts(self):
        return self.hosts

    def get_host(self, name):
        return self.hosts.get(name, None)

    def add_host(self, name, data):
        if name in self.hosts:
            raise ValueError(f"Host {name} already exists")
        self.hosts[name] = {
            "alias": data.get("alias"),
            "network_interfaces": data.get("network_interfaces", []),
            "bmc": data.get("bmc", {}),
            "vars": data.get("vars", {}),
        }

    def update_host(self, name, data):
        if name not in self.hosts:
            raise ValueError(f"Host {name} does not exist")
        self.hosts[name].update(data)
 
    def delete_host(self, name):
        if name not in self.hosts:
            raise ValueError(f"Host {name} does not exist")
        del self.hosts[name]
        # When deleting an host, we need to make sure it is also purged from groups
        for group in self.groups:
            if name in self.groups[group]['hosts']:
                self.groups[group]['hosts'].remove(name)

    # # -------------------------
    # # Group operations
    # # -------------------------

    # def list_groups(self) -> Dict[str, Dict[str, Any]]:
    #     return self.groups

    # def get_group(self, name: str) -> Optional[Dict[str, Any]]:
    #     return self.groups.get(name)

    # def add_group(self, name: str, data) -> None:
    #     if name in self.groups:
    #         raise ValueError(f"Group {name} already exists")
    #     self.groups[name] = {
    #         "hosts": data.get("hosts", []),
    #         "vars": data.get("vars", {})
    #         }

    # def update_group(
    #     self,
    #     name: str,
    #     hosts: Optional[List[str]] = None,
    #     vars_update: Optional[Dict[str, Dict[str, Any]]] = None,
    # ) -> None:
    #     if name not in self.groups:
    #         raise ValueError(f"Group {name} does not exist")
    #     group = self.groups[name]
    #     if hosts is not None:
    #         group["hosts"] = hosts
    #     if vars_update:
    #         for plugin_name, plugin_vars in vars_update.items():
    #             existing = group["vars"].get(plugin_name, {})
    #             existing.update(plugin_vars or {})
    #             group["vars"][plugin_name] = existing

    # def delete_group(self, name: str) -> None:
    #     if name not in self.groups:
    #         raise ValueError(f"Group {name} does not exist")
    #     del self.groups[name]

    # # -------------------------
    # # Saving with diff/check
    # # -------------------------

    # def save(self) -> None:
    #     """
    #     Save inventory to disk.

    #     - Always writes to a temporary inventory tree under working_folder.
    #     - If diff/check: run `diff -ruN old new` and print output.
    #     - If check: do not overwrite original inventory.
    #     - If not check: overwrite original inventory and remove temp dir.
    #     """
    #     tmp_dir = tempfile.mkdtemp(
    #         prefix="overlord-inventory-new-",
    #         dir=self.working_folder,
    #     )
    #     try:
    #         # # Copy existing inventory root to tmp_dir
    #         # if os.path.isdir(self.inventory_root):
    #         #     dst_root = os.path.join(tmp_dir, os.path.basename(self.inventory_root))
    #         #     shutil.copytree(self.inventory_root, dst_root, dirs_exist_ok=True)
    #         # else:
    #         #     dst_root = os.path.join(tmp_dir, os.path.basename(self.inventory_root))
    #         #     os.makedirs(dst_root, exist_ok=True)

    #         new_root = os.path.join(tmp_dir, os.path.basename(self.inventory_root))
    #         os.makedirs(new_root, exist_ok=True)
    #         # Write current in-memory state to new_root
    #         self._write_inventory(new_root)

    #         # Diff & overwrite
    #         original_root = self.inventory_root
    #         # new_root = dst_root

    #         if self.diff or self.check:
    #             self._print_diff(original_root, new_root)
    #         if not self.check:
    #             # Overwrite original with new_root content
    #             if os.path.isdir(original_root):
    #                 shutil.rmtree(original_root)
    #             shutil.copytree(new_root, original_root)

    #     finally:
    #         # Clean temp dir if overwrite occurred, otherwise leave for debugging?
    #         if os.path.isdir(tmp_dir):
    #             shutil.rmtree(tmp_dir, ignore_errors=True)

    # def _write_inventory(self, root: str) -> None:
    #     # hosts.yml
    #     hosts_yaml_path = os.path.join(root, "inventory", "cluster", "hosts.yml")
    #     hosts_yaml = {"all": {"hosts": {}}}
    #     for hostname, host_data in self.hosts.items():
    #         entry: Dict[str, Any] = {}
    #         if host_data.get("alias") is not None:
    #             entry["alias"] = host_data["alias"]
    #         if "network_interfaces" in host_data and host_data["network_interfaces"] is not None:
    #             entry["network_interfaces"] = host_data["network_interfaces"]
    #         if "bmc" in host_data and host_data["bmc"] is not None:
    #             entry["bmc"] = host_data["bmc"]
    #         hosts_yaml["all"]["hosts"][hostname] = entry
    #     dump_yaml_file(hosts_yaml_path, hosts_yaml)

    #     # host_vars
    #     for hostname, host_data in self.hosts.items():
    #         host_vars = host_data.get("vars") or {}
    #         if host_vars:
    #             hv_path = os.path.join(
    #                 root, "inventory", "host_vars", hostname, "main.yml"
    #             )
    #             dump_yaml_file(hv_path, host_vars)
    #         else:
    #             # If no vars, we could remove existing host_vars file, but for now leave untouched
    #             pass

    #     # groups ini + group_vars
    #     groups_dir = os.path.join(root, "inventory", "cluster", "groups")
    #     os.makedirs(groups_dir, exist_ok=True)

    #     for group_name, group_data in self.groups.items():
    #         ini_path = os.path.join(groups_dir, f"{group_name}.ini")
    #         hosts_list = group_data.get("hosts", [])

    #         lines = [f"[{group_name}]"]
    #         for h in hosts_list:
    #             lines.append(h)
    #         content = "\n".join(lines) + "\n"

    #         with open(ini_path, "w", encoding="utf-8") as f:
    #             f.write(content)

    #         gv_dir = os.path.join(root, "inventory", "group_vars", group_name)
    #         vars_dict = group_data.get("vars") or {}
    #         for plugin_name, plugin_vars in vars_dict.items():
    #             if not plugin_vars:
    #                 continue
    #             plugin_path = os.path.join(gv_dir, f"{plugin_name}.yml")
    #             dump_yaml_file(plugin_path, plugin_vars)

    # def _print_diff(self, old_root: str, new_root: str) -> None:
    #     try:
    #         result = subprocess.run(
    #             ["diff", "-ruN", old_root, new_root],
    #             capture_output=True,
    #             text=True,
    #         )
    #         if result.stdout:
    #             print(result.stdout)
    #         if result.stderr and self.logger:
    #             self.logger.warning("diff stderr: %s", result.stderr.strip())
    #     except FileNotFoundError:
    #         if self.logger:
    #             self.logger.error("diff binary not found; cannot show diff")

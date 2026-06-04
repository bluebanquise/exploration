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
        inventories_root: str,
        inventory_name: str,
        working_folder: str,
        diff: bool = False,
        check: bool = False,
        logger=None,
    ):
        self.inventories_root = inventories_root
        self.inventory_name = inventory_name
        relative_path = str(os.path.join(inventories_root, inventory_name))
        self.inventory_root = os.path.abspath(relative_path)
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

        # Check if an host posses specific hostvars
        for hostname in data:

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
                    if plugin_name != "main":
                        group_vars[plugin_name] = plugin_vars
                    else:
                        group_vars.update(plugin_vars)

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
        print("############ HOSTS ############")
        print(yaml.dump(self.hosts))
        print("")
        print("############ GROUPS ############")
        print(yaml.dump(self.groups))
        return

    # #######################################
    # ##### Hosts management
    # ##

    def get_hosts(self):
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

    # #######################################
    # ##### Groups management
    # ##

    def get_groups(self):
        return self.groups

    def get_group(self, name):
        return self.groups.get(name, None)

    def add_group(self, name, data):
        if name in self.groups:
            raise ValueError(f"Group {name} already exists")
        self.groups[name] = {
            "hosts": data.get("hosts", []),
            "vars": data.get("vars", {})
            }

    def update_group(self, name, hosts, vars):
        if name not in self.groups:
            raise ValueError(f"Group {name} does not exist")
        if hosts is not None:
            self.groups[name]['hosts'] = hosts
        if vars is not None:
            self.groups[name]['vars'].update(vars)

    def delete_group(self, name: str) -> None:
        if name not in self.groups:
            raise ValueError(f"Group {name} does not exist")
        del self.groups[name]


    # ####################################################################################
    # ##### Save management
    # ##

    def save(self):
        """
        Save inventory to disk.

        - Always writes to a temporary inventory tree under working_folder.
        - If diff/check: run `diff -ruN old new` and print output.
        - If check: do not overwrite original inventory.
        - If not check: overwrite original inventory and remove temp dir.
        """
        tmp_dir = tempfile.mkdtemp(
            prefix="overlord-temporary-inventory-",
            dir=self.working_folder
        )
        try:

            self.write_inventory(tmp_dir)

            if self.diff or self.check:
                self.print_diff(self.inventory_root, tmp_dir)
            if not self.check:
                # Overwrite original with new_root content
                if os.path.isdir(self.inventory_root):
                    shutil.rmtree(self.inventory_root)
                shutil.copytree(tmp_dir, self.inventory_root)

        finally:
            # Clean temp dir if overwrite occurred, otherwise leave for debugging?
            if os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

        self.commit_change()

    def write_inventory(self, root):

        # ## hosts ##
        # Sort hosts by fn groups
        hosts_fn_dict = {}
        for hostname in self.hosts:
            host_fn_group = None
            for group in self.groups:
                if group.startswith('fn_'):
                    if hostname in self.groups[group]['hosts']:
                        host_fn_group = group
                        break
            if host_fn_group is None:
                host_fn_group = 'orphan'
            if not host_fn_group in hosts_fn_dict:
                hosts_fn_dict[host_fn_group] = []
            print(hostname)
            hosts_fn_dict[host_fn_group].append(hostname)
        print(hosts_fn_dict)
        
        # Ok now, lets write these files one by one
        for fn_group in hosts_fn_dict:
            hosts_yaml_path = os.path.join(root, "cluster", "hosts", fn_group + ".yml")
            hosts_yaml = {"all": {"hosts": {}}}
            for hostname in hosts_fn_dict[fn_group]:
                host_data = self.hosts[hostname]
                entry = {}
                if isinstance(host_data, dict):
                    if host_data.get("alias", None) is not None:
                        entry["alias"] = host_data["alias"]
                    if host_data.get("network_interfaces", None) is not None:
                        entry["network_interfaces"] = host_data["network_interfaces"]
                    if host_data.get("bmc", None) is not None:
                        entry["bmc"] = host_data["bmc"]
                hosts_yaml["all"]["hosts"][hostname] = entry
            dump_yaml_file(hosts_yaml_path, hosts_yaml)

        # host_vars
        for hostname, host_data in self.hosts.items():
            if isinstance(host_data, dict):
                host_vars = host_data.copy()
                # Filter already written values
                if "alias" in host_vars:
                    del host_vars["alias"]
                if "network_interfaces" in host_vars:
                    del host_vars["network_interfaces"]
                if "bmc" in host_vars:
                    del host_vars["bmc"]
                if len(host_vars) > 0:
                    hv_path = os.path.join(
                        root, "host_vars", hostname, "main.yml"
                    )
                    dump_yaml_file(hv_path, host_vars)

        # ## groups ##

        groups_dir = os.path.join(root, "cluster", "groups")
        os.makedirs(groups_dir, exist_ok=True)

        for group_name, group_data in self.groups.items():

            # groups ini
            ini_path = os.path.join(groups_dir, f"{group_name}.ini")
            hosts_list = group_data.get("hosts", [])

            lines = [f"[{group_name}]"]
            for h in hosts_list:
                lines.append(h)
            content = "\n".join(lines) + "\n"

            with open(ini_path, "w", encoding="utf-8") as f:
                f.write(content)

            # groups vars
            gv_dir = os.path.join(root, "group_vars", group_name)
            vars_dict = group_data.get("vars") or {}
            # Plugins should have their values behind a prefix "plugin_"
            # We write plugins into a dedicated files, everything else goes to main.yml
            vars_dict_buffer = vars_dict.copy()
            for key_name in vars_dict_buffer:
                if key_name.startswith("plugin_"):
                    plugin_path = os.path.join(gv_dir, f"{key_name}.yml")
                    dump_yaml_file(plugin_path, vars_dict[key_name])
                    del vars_dict[key_name]
            # Now that all plugins are written, lets write the remains
            if len(vars_dict) > 0:
                main_path = os.path.join(gv_dir, "main.yml")
                dump_yaml_file(main_path, vars_dict)
                

    def print_diff(self, old_root, new_root):
        try:
            result = subprocess.run(
                ["diff", "-ruN", old_root, new_root],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr and self.logger:
                self.logger.warning("diff stderr: %s", result.stderr.strip())
        except FileNotFoundError:
            if self.logger:
                self.logger.error("diff binary not found; cannot show diff")

    def commit_change(self):
        print("Now I need to git commit the changes.")
        try:
            git_command = "git --git-dir=" + os.path.abspath(self.inventories_root) + "/.git/ --work-tree=" + os.path.abspath(self.inventories_root) + "/ commit -a -m " + "'Updating inventory " + str(self.inventory_name) + "'"
            cmd_call = subprocess.Popen(git_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout, stderr = cmd_call.communicate()
            exit_code = cmd_call.returncode
            if exit_code == 0:
                print("Commit went well.")
        except Exception as e:
            print("Error I could not commit the changes.")
            print(e)

# plugins/hosts.py

import textwrap

PLUGIN_NAME = "Manage hosts"
PLUGIN_FOLDER = None


def run(wm, inventory):

    wm.w_create("Manage hosts")

    while True:

        menu_lines = [
            "Please choose action:\n",
            "1. List hosts",
            "2. Add a new host",
            "3. Update a host",
            "4. Delete a host",
            "\n9. Back\n",
        ]

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            #wm.w_destroy()
            list_hosts_by_fn_groups(wm, inventory)
            continue

        if answer == "2":
            #wm.w_destroy()
            add_host(wm, inventory)
            continue

        if answer == "3":
            #wm.w_destroy()
            update_host(wm, inventory)
            continue

        if answer == "4":
            #wm.w_destroy()
            delete_host(wm, inventory)
            continue

        wm.w_sprint("Invalid choice.")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _get_networks(inventory):
    all_group = inventory.get_group("all")
    vars_dict = all_group.setdefault("vars", {})
    return vars_dict.setdefault("networks", {})


def _manage_network_interfaces(wm, inventory, interfaces):

    wm.w_create("Manage network interfaces")

    while True:

        menu_lines = [
            "Network interfaces menu:\n",
            "1. List interfaces",
            "2. Add interface",
            "3. Update interface",
            "4. Delete interface",
            "\n9. Back\n",
        ]
        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            #wm.w_destroy()
            _list_interfaces(wm, interfaces)
            continue

        if answer == "2":
            #wm.w_destroy()
            _add_interface(wm, inventory, interfaces)
            continue

        if answer == "3":
            #wm.w_destroy()
            _update_interface(wm, inventory, interfaces)
            continue

        if answer == "4":
            #wm.w_destroy()
            _delete_interface(wm, interfaces)
            continue

        wm.w_sprint("Invalid choice.")
    wm.w_destroy()


def _list_interfaces(wm, interfaces):
    wm.w_create("List interfaces")

    if not interfaces:
        wm.w_sprint("No network interfaces defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    for iface in interfaces:
        name = iface.get("interface", "?")
        net = iface.get("network", "?")
        wm.w_sprint(f"{wm.t_blue(name)}: {wm.t_green(net)}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


def _add_interface(wm, inventory, interfaces):
    wm.w_create("Add interface")

    networks = _get_networks(inventory)
    if not networks:
        wm.w_sprint(
            "No networks defined.\n"
            "You must create at least one network before adding interfaces."
        )
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    iface_name = wm.w_input("Interface name (e.g. eth0): ").strip()
    if not iface_name:
        wm.w_sprint("Interface name is mandatory.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("Select logical network:\n")
    net_names = list(networks.keys())
    for idx, n in enumerate(net_names, start=1):
        wm.w_sprint(f"{idx}. {n}")
    wm.w_sprint("")
    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= len(net_names)):
            raise ValueError
    except Exception:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    net_name = net_names[choice - 1]

    ip4 = wm.w_input("IPv4 address: ").strip()
    if not ip4:
        wm.w_sprint("IPv4 address is mandatory.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    mac = wm.w_input("MAC address (optional): ").strip() or None

    iface = {
        "interface": iface_name,
        "ip4": ip4,
        "network": net_name,
    }
    if mac:
        iface["mac"] = mac

    interfaces.append(iface)
    wm.w_sprint("Interface added.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


def _update_interface(wm, inventory, interfaces):
    wm.w_create("Update interface")

    if not interfaces:
        wm.w_sprint("No interfaces to update.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    for idx, iface in enumerate(interfaces, start=1):
        name = iface.get("interface", "?")
        net = iface.get("network", "?")
        wm.w_sprint(f"{idx}. {name}: {net}")
    wm.w_sprint("")

    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= len(interfaces)):
            raise ValueError
    except Exception:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    iface = interfaces[choice - 1]
    networks = _get_networks(inventory)

    def ask(label, default):
        wm.w_sprint(f"{label} (current: {default})")
        val = wm.w_input(f"{label}: ").strip()
        return val if val != "" else default

    name = ask("interface", iface.get("interface"))
    ip4 = ask("ip4", iface.get("ip4"))

    wm.w_sprint("Select logical network (current: %s):" % iface.get("network"))
    net_names = list(networks.keys())
    for idx, n in enumerate(net_names, start=1):
        wm.w_sprint(f"{idx}. {n}")
    wm.w_sprint("")
    net_choice = wm.w_input("❱❱❱ ").strip()
    if net_choice.isdigit():
        idx = int(net_choice)
        if 1 <= idx <= len(net_names):
            net_name = net_names[idx - 1]
        else:
            net_name = iface.get("network")
    else:
        net_name = iface.get("network")

    mac = ask("mac", iface.get("mac"))

    iface["interface"] = name
    iface["ip4"] = ip4
    iface["network"] = net_name
    if mac:
        iface["mac"] = mac
    elif "mac" in iface:
        del iface["mac"]

    wm.w_sprint("Interface updated.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


def _delete_interface(wm, interfaces):
    wm.w_create("Delete interface")

    if not interfaces:
        wm.w_sprint("No interfaces to delete.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    for idx, iface in enumerate(interfaces, start=1):
        name = iface.get("interface", "?")
        net = iface.get("network", "?")
        wm.w_sprint(f"{idx}. {name}: {net}")
    wm.w_sprint("")

    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= len(interfaces)):
            raise ValueError
    except Exception:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    del interfaces[choice - 1]
    wm.w_sprint("Interface deleted.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 1 — LIST HOSTS
# ---------------------------------------------------------------------------

def list_hosts_by_fn_groups(wm, inventory):
    wm.w_create("List hosts")

    groups = inventory.list_groups()
    fn_groups = {g: data for g, data in groups.items() if g.startswith("fn_")}

    if not fn_groups:
        wm.w_sprint("No fn_ groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    for group_name, group_data in fn_groups.items():
        wm.w_sprint(wm.t_blue(group_name) + ":")
        hosts = group_data.get("hosts", [])
        if not hosts:
            wm.w_sprint("  (no hosts)")
        else:
            for h in hosts:
                wm.w_sprint("  - " + wm.t_green(h))
        wm.w_sprint("")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 2 — ADD HOST
# ---------------------------------------------------------------------------

def add_host(wm, inventory):
    wm.w_create("Add host")

    groups = inventory.list_groups()
    fn_groups = [g for g in groups if g.startswith("fn_")]
    hw_groups = [g for g in groups if g.startswith("hw_")]
    os_groups = [g for g in groups if g.startswith("os_")]

    if not fn_groups or not hw_groups or not os_groups:
        wm.w_sprint(
            "Cannot add host.\n"
            "You must have at least one fn_, one hw_ and one os_ group defined."
        )
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    name = wm.w_input("Host name: ").strip()
    if not name:
        wm.w_sprint("Host name is mandatory.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Select fn group
    wm.w_sprint("Select fn_ group:\n")
    for idx, g in enumerate(fn_groups, start=1):
        wm.w_sprint(f"{idx}. {g}")
    wm.w_sprint("")
    fn_choice = _select_index(wm, len(fn_groups))
    if fn_choice is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    fn_group = fn_groups[fn_choice]

    # Select hw group
    wm.w_sprint("Select hw_ group:\n")
    for idx, g in enumerate(hw_groups, start=1):
        wm.w_sprint(f"{idx}. {g}")
    wm.w_sprint("")
    hw_choice = _select_index(wm, len(hw_groups))
    if hw_choice is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    hw_group = hw_groups[hw_choice]

    # Select os group
    wm.w_sprint("Select os_ group:\n")
    for idx, g in enumerate(os_groups, start=1):
        wm.w_sprint(f"{idx}. {g}")
    wm.w_sprint("")
    os_choice = _select_index(wm, len(os_groups))
    if os_choice is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    os_group = os_groups[os_choice]

    host_data = {}

    # Alias
    wm.w_sprint("Does this host have an alias? (yes/no)")
    if wm.w_input("❱❱❱ ").strip().lower() == "yes":
        alias = wm.w_input("Alias: ").strip()
        if alias:
            host_data["alias"] = alias

    # BMC
    wm.w_sprint("Does this host have a BMC? (yes/no)")
    bmc_data = None
    if wm.w_input("❱❱❱ ").strip().lower() == "yes":
        bmc_name = wm.w_input("BMC name: ").strip()
        bmc_mac = wm.w_input("BMC MAC address: ").strip()
        bmc_ip = wm.w_input("BMC IPv4: ").strip()
        bmc_net = wm.w_input("BMC logical network: ").strip()
        bmc_data = {
            "name": bmc_name,
            "mac": bmc_mac,
            "ip4": bmc_ip,
            "network": bmc_net,
        }
        host_data["bmc"] = bmc_data

    # Network interfaces
    wm.w_sprint("Does this host have network interfaces? (yes/no)")
    interfaces = []
    if wm.w_input("❱❱❱ ").strip().lower() == "yes":
        if not _get_networks(inventory):
            wm.w_sprint(
                "No networks defined.\n"
                "You must define networks before adding interfaces."
            )
        else:
            _manage_network_interfaces(wm, inventory, interfaces)
    if interfaces:
        host_data["network_interfaces"] = interfaces

    # Create host
    try:
        inventory.add_host(name, host_data)
    except Exception as e:
        wm.w_sprint(f"Error while adding host: {e}")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Attach host to groups
    for gname in (fn_group, hw_group, os_group):
        grp = inventory.get_group(gname)
        hosts = grp.setdefault("hosts", [])
        if name not in hosts:
            hosts.append(name)

    inventory.save()
    wm.w_sprint(f"Host {wm.t_green(name)} created successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


def _select_index(wm, length):
    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= length):
            raise ValueError
        return choice - 1
    except Exception:
        wm.w_sprint("Invalid choice.")
        return None


# ---------------------------------------------------------------------------
# ACTION 3 — UPDATE HOST
# ---------------------------------------------------------------------------

def update_host(wm, inventory):
    wm.w_create("Update host")

    hosts = inventory.list_hosts()
    if not hosts:
        wm.w_sprint("No hosts defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    names = list(hosts.keys())
    wm.w_sprint("Select host to update:\n")
    for idx, h in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {h}")
    wm.w_sprint("")

    idx = _select_index(wm, len(names))
    if idx is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    name = names[idx]
    host_data = hosts[name]

    # Determine current fn/hw/os groups
    groups = inventory.list_groups()
    fn_groups = [g for g in groups if g.startswith("fn_")]
    hw_groups = [g for g in groups if g.startswith("hw_")]
    os_groups = [g for g in groups if g.startswith("os_")]

    current_fn = _find_group_for_host(groups, "fn_", name)
    current_hw = _find_group_for_host(groups, "hw_", name)
    current_os = _find_group_for_host(groups, "os_", name)

    #wm.w_destroy()
    #wm.w_create(f"Update {name}")

    # Re-select fn group
    wm.w_sprint(f"Select fn_ group (current: {current_fn}):\n")
    for i, g in enumerate(fn_groups, start=1):
        wm.w_sprint(f"{i}. {g}")
    wm.w_sprint("")
    fn_idx = _select_index(wm, len(fn_groups))
    if fn_idx is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    new_fn = fn_groups[fn_idx]

    # Re-select hw group
    wm.w_sprint(f"Select hw_ group (current: {current_hw}):\n")
    for i, g in enumerate(hw_groups, start=1):
        wm.w_sprint(f"{i}. {g}")
    wm.w_sprint("")
    hw_idx = _select_index(wm, len(hw_groups))
    if hw_idx is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    new_hw = hw_groups[hw_idx]

    # Re-select os group
    wm.w_sprint(f"Select os_ group (current: {current_os}):\n")
    for i, g in enumerate(os_groups, start=1):
        wm.w_sprint(f"{i}. {g}")
    wm.w_sprint("")
    os_idx = _select_index(wm, len(os_groups))
    if os_idx is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    new_os = os_groups[os_idx]

    # Alias
    def ask(label, default):
        wm.w_sprint(f"{label} (current: {default})")
        val = wm.w_input(f"{label}: ").strip()
        return val if val != "" else default

    alias = ask("alias", host_data.get("alias"))
    if alias:
        host_data["alias"] = alias
    elif "alias" in host_data:
        del host_data["alias"]

    # BMC
    current_bmc = host_data.get("bmc")
    has_bmc = current_bmc is not None
    wm.w_sprint(f"Does this host have a BMC? (yes/no) (current: {'yes' if has_bmc else 'no'})")
    if wm.w_input("❱❱❱ ").strip().lower() == "yes":
        bmc_name = ask("BMC name", current_bmc.get("name") if current_bmc else "")
        bmc_mac = ask("BMC MAC address", current_bmc.get("mac") if current_bmc else "")
        bmc_ip = ask("BMC IPv4", current_bmc.get("ip4") if current_bmc else "")
        bmc_net = ask("BMC logical network", current_bmc.get("network") if current_bmc else "")
        host_data["bmc"] = {
            "name": bmc_name,
            "mac": bmc_mac,
            "ip4": bmc_ip,
            "network": bmc_net,
        }
    else:
        if "bmc" in host_data:
            del host_data["bmc"]

    # Network interfaces
    interfaces = host_data.get("network_interfaces", [])
    _manage_network_interfaces(wm, inventory, interfaces)
    if interfaces:
        host_data["network_interfaces"] = interfaces
    elif "network_interfaces" in host_data:
        del host_data["network_interfaces"]

    # Update group memberships
    _update_host_groups(inventory, name, "fn_", new_fn)
    _update_host_groups(inventory, name, "hw_", new_hw)
    _update_host_groups(inventory, name, "os_", new_os)

    inventory.save()
    wm.w_sprint(f"Host {wm.t_green(name)} updated successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


def _find_group_for_host(groups, prefix, host):
    for gname, gdata in groups.items():
        if not gname.startswith(prefix):
            continue
        if host in gdata.get("hosts", []):
            return gname
    return None


def _update_host_groups(inventory, host, prefix, new_group):
    groups = inventory.list_groups()
    for gname, gdata in groups.items():
        if not gname.startswith(prefix):
            continue
        hosts = gdata.get("hosts", [])
        if host in hosts and gname != new_group:
            hosts.remove(host)
    grp = inventory.get_group(new_group)
    hosts = grp.setdefault("hosts", [])
    if host not in hosts:
        hosts.append(host)


# ---------------------------------------------------------------------------
# ACTION 4 — DELETE HOST
# ---------------------------------------------------------------------------

def delete_host(wm, inventory):
    wm.w_create("Delete host")

    hosts = inventory.list_hosts()
    if not hosts:
        wm.w_sprint("No hosts defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    names = list(hosts.keys())
    wm.w_sprint("Select host to delete:\n")
    for idx, h in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {h}")
    wm.w_sprint("")

    idx = _select_index(wm, len(names))
    if idx is None:
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    name = names[idx]

    wm.w_sprint(f"Are you sure you want to delete {wm.t_blue(name)}? (yes/no)")
    if wm.w_input("❱❱❱ ").strip().lower() != "yes":
        wm.w_sprint("Deletion cancelled.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Remove from groups
    groups = inventory.list_groups()
    for gname, gdata in groups.items():
        hosts_list = gdata.get("hosts", [])
        if name in hosts_list:
            hosts_list.remove(name)

    # Delete host from inventory
    try:
        inventory.delete_host(name)
    except Exception:
        # If delete_host is not implemented, ignore
        pass

    inventory.save()
    wm.w_sprint(f"Host {wm.t_green(name)} deleted successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()

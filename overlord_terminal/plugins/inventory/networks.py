# plugins/networks/__init__.py

import textwrap

PLUGIN_NAME = "Manage networks"
PLUGIN_FOLDER = None


def run(wm, inventory):

    wm.w_create("Manage networks")

    while True:

        menu_lines = [
            "Please choose action:\n",
            "1. List networks",
            "2. Add a new network",
            "3. Update a network",
            "4. Delete a network",
            "\n9. Back\n",
        ]

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            #wm.w_destroy()
            list_networks(wm, inventory)
            continue

        if answer == "2":
            #wm.w_destroy()
            add_network(wm, inventory)
            continue

        if answer == "3":
            #wm.w_destroy()
            update_network(wm, inventory)
            continue

        if answer == "4":
            #wm.w_destroy()
            delete_network(wm, inventory)
            continue

        wm.w_sprint("Invalid choice.")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _get_networks(inventory):
    """Return the dict of networks inside group 'all'."""
    all_group = inventory.get_group("all")
    vars_dict = all_group.setdefault("vars", {})
    return vars_dict.setdefault("networks", {})


# ---------------------------------------------------------------------------
# ACTION 1 — LIST NETWORKS
# ---------------------------------------------------------------------------

def list_networks(wm, inventory):
    wm.w_create("List networks")

    networks = _get_networks(inventory)

    if not networks:
        wm.w_sprint("No networks defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("Networks:\n")

    for name, data in networks.items():
        subnet = data.get("subnet", "?")
        prefix = data.get("prefix", "?")
        wm.w_sprint(f"{wm.t_blue(name)}: {wm.t_green(subnet)}/{prefix}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 2 — ADD NETWORK
# ---------------------------------------------------------------------------

def add_network(wm, inventory):
    wm.w_create("Add network")

    networks = _get_networks(inventory)

    # Management network?
    wm.w_sprint("Is this a management network? (yes/no)")
    is_mgmt = wm.w_input("❱❱❱ ").strip().lower() == "yes"

    # Name
    if is_mgmt:
        wm.w_sprint(
            "Enter the network name (without 'net-' prefix).\n"
            "It will be stored as 'net-<name>'."
        )
        base = wm.w_input("Network name: ").strip()
        if not base:
            wm.w_sprint("Network name cannot be empty.")
            wm.w_input("Press Enter to go back")
            wm.w_destroy()
            return
        name = f"net-{base}"
    else:
        name = wm.w_input("Network name: ").strip()
        if not name:
            wm.w_sprint("Network name cannot be empty.")
            wm.w_input("Press Enter to go back")
            wm.w_destroy()
            return

    # subnet
    wm.w_sprint("Enter subnet (mandatory). Example: 10.10.0.0")
    subnet = wm.w_input("subnet: ").strip()
    if not subnet:
        wm.w_sprint("Subnet is mandatory.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # prefix
    wm.w_sprint("Enter prefix (mandatory). Example: 16")
    prefix = wm.w_input("prefix: ").strip()
    if not prefix.isdigit():
        wm.w_sprint("Prefix must be a number.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return
    prefix = int(prefix)

    # gateway4 (optional)
    gateway4 = None
    if is_mgmt:
        wm.w_sprint("Set a gateway IPv4? (yes/no)")
        if wm.w_input("❱❱❱ ").strip().lower() == "yes":
            gateway4 = wm.w_input("gateway4: ").strip()

    # services_ip (mandatory for mgmt)
    services_ip = None
    if is_mgmt:
        wm.w_sprint("Enter services_ip (mandatory for management networks).")
        services_ip = wm.w_input("services_ip: ").strip()
        if not services_ip:
            wm.w_sprint("services_ip is mandatory.")
            wm.w_input("Press Enter to go back")
            wm.w_destroy()
            return

    # Build entry
    entry = {
        "subnet": subnet,
        "prefix": prefix,
    }
    if gateway4:
        entry["gateway4"] = gateway4
    if services_ip:
        entry["services_ip"] = services_ip

    # Store
    networks[name] = entry
    inventory.save()

    wm.w_sprint(f"Network {wm.t_green(name)} created successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 3 — UPDATE NETWORK
# ---------------------------------------------------------------------------

def update_network(wm, inventory):
    wm.w_create("Update network")

    networks = _get_networks(inventory)
    if not networks:
        wm.w_sprint("No networks defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Select network
    wm.w_sprint("Select network to update:\n")
    names = list(networks.keys())
    for idx, n in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {n}")
    wm.w_sprint("")

    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= len(names)):
            raise ValueError
    except:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    name = names[choice - 1]
    data = networks[name]

    wm.w_destroy()
    wm.w_create(f"Update {name}")

    def ask(label, default):
        wm.w_sprint(f"{label} (current: {default})")
        val = wm.w_input(f"{label}: ").strip()
        return val if val != "" else default

    subnet = ask("subnet", data.get("subnet"))
    prefix = ask("prefix", str(data.get("prefix")))
    prefix = int(prefix) if prefix.isdigit() else data.get("prefix")

    gateway4 = ask("gateway4", data.get("gateway4"))
    services_ip = ask("services_ip", data.get("services_ip"))

    new_data = {
        "subnet": subnet,
        "prefix": prefix,
    }
    if gateway4:
        new_data["gateway4"] = gateway4
    if services_ip:
        new_data["services_ip"] = services_ip

    networks[name] = new_data
    inventory.save()

    wm.w_sprint(f"Network {wm.t_green(name)} updated successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 4 — DELETE NETWORK
# ---------------------------------------------------------------------------

def delete_network(wm, inventory):
    wm.w_create("Delete network")

    networks = _get_networks(inventory)
    if not networks:
        wm.w_sprint("No networks defined.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Select network
    wm.w_sprint("Select network to delete:\n")
    names = list(networks.keys())
    for idx, n in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {n}")
    wm.w_sprint("")

    try:
        choice = int(wm.w_input("❱❱❱ "))
        if not (1 <= choice <= len(names)):
            raise ValueError
    except:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    name = names[choice - 1]

    # Safety check: ensure no host uses this network
    used_by = []
    for host, data in inventory.list_hosts().items():
        for iface in data.get("network_interfaces", []):
            if iface.get("network") == name:
                used_by.append(host)

    if used_by:
        wm.w_sprint(
            f"Cannot delete {wm.t_blue(name)} because it is still used by hosts:\n"
        )
        for h in used_by:
            wm.w_sprint("  - " + wm.t_green(h))
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Confirm deletion
    wm.w_sprint(f"Are you sure you want to delete {wm.t_blue(name)}? (yes/no)")
    if wm.w_input("❱❱❱ ").strip().lower() != "yes":
        wm.w_sprint("Deletion cancelled.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    del networks[name]
    inventory.save()

    wm.w_sprint(f"Network {wm.t_green(name)} deleted successfully.")
    wm.w_input("Press Enter to go back")
    wm.w_destroy()

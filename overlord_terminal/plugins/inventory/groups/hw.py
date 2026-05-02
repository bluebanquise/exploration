# plugins/groups/hw.py

import textwrap
from plugin_loader import load_plugins

PLUGIN_NAME = "Manage HW groups"
PLUGIN_FOLDER = None   # No nested plugins for now


def run(wm, inventory):
    """
    Main menu for HW groups management.
    """

    wm.w_create("Manage HW groups")

    while True:

        menu_lines = [
            "Please choose action:\n",
            "1. List HW groups and their hosts",
            "2. Add a new HW group",
            "3. Update an HW group",
            "4. Delete an HW group",
            "\n9. Back\n",
        ]

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            list_hw_groups(wm, inventory)
            continue

        if answer == "2":
            add_hw_group(wm, inventory)
            continue

        if answer == "3":
            update_hw_group(wm, inventory)
            continue

        if answer == "4":
            delete_hw_group(wm, inventory)
            continue

        wm.w_sprint("Invalid choice.")

    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 1 — LIST HW GROUPS
# ---------------------------------------------------------------------------

def list_hw_groups(wm, inventory):
    wm.w_create("List HW groups")

    groups = inventory.list_groups()
    hw_groups = {g: data for g, data in groups.items() if g.startswith("hw_")}

    if not hw_groups:
        wm.w_sprint("No HW groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("HW groups, their hosts, and parameters:\n")

    for group_name, group_data in hw_groups.items():
        wm.w_sprint(wm.t_blue(group_name))

        # Hosts
        hosts = group_data.get("hosts", [])
        wm.w_sprint("  " + wm.t_blue("Hosts") + ":")
        if not hosts:
            wm.w_sprint("    " + wm.t_green("(no hosts)"))
        else:
            for h in hosts:
                wm.w_sprint("    - " + wm.t_green(h))

        # Vars
        vars_dict = group_data.get("vars", {})
        wm.w_sprint("  " + wm.t_blue("Parameters") + ":")
        if not vars_dict:
            wm.w_sprint("    (no parameters)")
        else:
            for key, value in vars_dict.items():
                colored_key = wm.t_blue(key)
                if isinstance(value, str) and "\n" in value:
                    wm.w_sprint(f"    {colored_key}: |")
                    for line in value.splitlines():
                        wm.w_sprint(f"      {line}")
                else:
                    wm.w_sprint(f"    {colored_key}: {value}")

        wm.w_sprint("")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 2 — ADD HW GROUP
# ---------------------------------------------------------------------------

def add_hw_group(wm, inventory):
    wm.w_create("Add HW group")

    # Group name
    wm.w_sprint("Enter the HW group name (without 'hw_' prefix).")
    base_name = wm.w_input("Group name: ").strip()

    if not base_name:
        wm.w_sprint("Group name cannot be empty.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    group_name = f"hw_{base_name}"

    # hw_equipment_type (mandatory)
    while True:
        wm.w_sprint(
            "Hardware equipment type (MANDATORY).\n"
            "For PXE-deployed servers, use: server\n"
            "Otherwise, any descriptive value is allowed."
        )
        hw_type = wm.w_input("hw_equipment_type: ").strip()
        if hw_type:
            break
        wm.w_sprint("This value is mandatory.")

    # hw_console (optional)
    wm.w_sprint(
        "Serial console kernel parameters (optional).\n"
        "Common values:\n"
        "  console=tty0 console=ttyS0,115200n8\n"
        "  console=tty0 console=ttyS1,115200n8\n"
        "  console=tty0 console=ttyS2,115200n8\n"
        "Default: None"
    )
    hw_console = wm.w_input("hw_console: ").strip() or None

    # hw_kernel_parameters (optional)
    wm.w_sprint(
        "Hardware-specific kernel parameters (optional).\n"
        "Example: nomodeset\n"
        "Default: None"
    )
    hw_kernel = wm.w_input("hw_kernel_parameters: ").strip() or None

    # hw_specs_cpu_cores (optional)
    wm.w_sprint("Number of CPU cores (optional). Default: None")
    cpu_cores = wm.w_input("hw_specs_cpu_cores: ").strip()
    cpu_cores = int(cpu_cores) if cpu_cores.isdigit() else None

    # hw_specs_memory (optional)
    wm.w_sprint("Memory size in MB (optional). Default: None")
    mem = wm.w_input("hw_specs_memory: ").strip()
    mem = int(mem) if mem.isdigit() else None

    # hw_board_authentication_protocol (optional)
    wm.w_sprint(
        "BMC authentication protocol (optional).\n"
        "Common values: IPMI, REDFISH\n"
        "Default: None"
    )
    proto = wm.w_input("hw_board_authentication_protocol: ").strip() or None

    # hw_board_authentication_user (optional)
    wm.w_sprint("BMC authentication user (optional). Default: None")
    user = wm.w_input("hw_board_authentication_user: ").strip() or None

    # hw_board_authentication_password (optional)
    wm.w_sprint("BMC authentication password (optional). Default: None")
    pwd = wm.w_input("hw_board_authentication_password: ").strip() or None

    # Build vars
    group_vars = {
        "hw_equipment_type": hw_type,
        "hw_console": hw_console,
        "hw_kernel_parameters": hw_kernel,
        "hw_specs_cpu_cores": cpu_cores,
        "hw_specs_memory": mem,
        "hw_board_authentication_protocol": proto,
        "hw_board_authentication_user": user,
        "hw_board_authentication_password": pwd,
    }

    try:
        inventory.add_group(group_name, {"hosts": [], "vars": group_vars})
        inventory.save()
        wm.w_sprint(f"Group {wm.t_green(group_name)} created successfully.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 3 — UPDATE HW GROUP
# ---------------------------------------------------------------------------

def update_hw_group(wm, inventory):
    wm.w_create("Update HW group")

    groups = inventory.list_groups()
    hw_groups = {g: data for g, data in groups.items() if g.startswith("hw_")}

    if not hw_groups:
        wm.w_sprint("No HW groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # List groups
    wm.w_sprint("Select HW group to update:\n")
    names = list(hw_groups.keys())
    for idx, g in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {g}")
    wm.w_sprint("")

    answer = wm.w_input("❱❱❱ ")
    try:
        choice = int(answer)
        if not (1 <= choice <= len(names)):
            raise ValueError
    except:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    group_name = names[choice - 1]
    group_data = hw_groups[group_name]
    vars_current = group_data.get("vars", {})

    wm.w_destroy()
    wm.w_create(f"Update {group_name}")

    def ask(label, default):
        wm.w_sprint(f"{label} (current: {default})")
        val = wm.w_input(f"{label}: ").strip()
        return val if val != "" else default

    # Update fields
    hw_type = ask("hw_equipment_type", vars_current.get("hw_equipment_type"))
    hw_console = ask("hw_console", vars_current.get("hw_console"))
    hw_kernel = ask("hw_kernel_parameters", vars_current.get("hw_kernel_parameters"))

    cpu_cores = ask("hw_specs_cpu_cores", vars_current.get("hw_specs_cpu_cores"))
    cpu_cores = int(cpu_cores) if cpu_cores and cpu_cores.isdigit() else None

    mem = ask("hw_specs_memory", vars_current.get("hw_specs_memory"))
    mem = int(mem) if mem and mem.isdigit() else None

    proto = ask("hw_board_authentication_protocol", vars_current.get("hw_board_authentication_protocol"))
    user = ask("hw_board_authentication_user", vars_current.get("hw_board_authentication_user"))
    pwd = ask("hw_board_authentication_password", vars_current.get("hw_board_authentication_password"))

    new_vars = {
        "hw_equipment_type": hw_type,
        "hw_console": hw_console,
        "hw_kernel_parameters": hw_kernel,
        "hw_specs_cpu_cores": cpu_cores,
        "hw_specs_memory": mem,
        "hw_board_authentication_protocol": proto,
        "hw_board_authentication_user": user,
        "hw_board_authentication_password": pwd,
    }

    try:
        inventory.update_group(group_name, vars_update=new_vars)
        inventory.save()
        wm.w_sprint(f"Group {wm.t_green(group_name)} updated successfully.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 4 — DELETE HW GROUP
# ---------------------------------------------------------------------------

def delete_hw_group(wm, inventory):
    wm.w_create("Delete HW group")

    groups = inventory.list_groups()
    hw_groups = {g: data for g, data in groups.items() if g.startswith("hw_")}

    if not hw_groups:
        wm.w_sprint("No HW groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("Select HW group to delete:\n")
    names = list(hw_groups.keys())
    for idx, g in enumerate(names, start=1):
        wm.w_sprint(f"{idx}. {g}")
    wm.w_sprint("")

    answer = wm.w_input("❱❱❱ ")
    try:
        choice = int(answer)
        if not (1 <= choice <= len(names)):
            raise ValueError
    except:
        wm.w_sprint("Invalid choice.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    group_name = names[choice - 1]
    group_data = hw_groups[group_name]

    # Safety check
    if group_data.get("hosts"):
        wm.w_sprint(
            f"Cannot delete {wm.t_blue(group_name)} because it still contains hosts.\n"
            "Please remove hosts from the group first."
        )
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint(f"Are you sure you want to delete {wm.t_blue(group_name)}? (yes/no)")
    confirm = wm.w_input("❱❱❱ ").strip().lower()

    if confirm != "yes":
        wm.w_sprint("Deletion cancelled.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    try:
        inventory.delete_group(group_name)
        inventory.save()
        wm.w_sprint(f"Group {wm.t_green(group_name)} deleted successfully.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()

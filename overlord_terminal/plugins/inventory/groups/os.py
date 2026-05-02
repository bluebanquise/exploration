# plugins/groups/__init__.py

import textwrap
from plugin_loader import load_plugins

PLUGIN_NAME = "Manage OS groups"
PLUGIN_FOLDER = "plugins/groups"


def run(wm, inventory):
    """
    Main menu for OS groups management.
    """

    wm.w_create("Manage OS groups")

    while True:

        menu_lines = [
            "Please choose action:\n",
            "1. List OS groups and their hosts",
            "2. Add a new OS group",
            "3. Update an OS group",
            "4. Delete an OS group",
            "\n9. Back\n",
        ]

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            list_os_groups(wm, inventory)
            #wm.w_destroy()
            continue

        if answer == "2":
            #wm.w_destroy()
            add_os_group(wm, inventory)
            continue

        if answer == "3":
            #wm.w_destroy()
            update_os_group(wm, inventory)
            continue

        if answer == "4":
            #wm.w_destroy()
            delete_os_group(wm, inventory)
            continue

        wm.w_sprint("Invalid choice.")

    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 1 — LIST OS GROUPS
# ---------------------------------------------------------------------------

def list_os_groups(wm, inventory):
    wm.w_create("List OS groups")

    groups = inventory.list_groups()
    os_groups = {g: data for g, data in groups.items() if g.startswith("os_")}

    if not os_groups:
        wm.w_sprint("No OS groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("OS groups, their hosts, and parameters:\n")

    for group_name, group_data in os_groups.items():
        # Group name
        wm.w_sprint(wm.t_blue(group_name))

        # -------------------------
        # Hosts
        # -------------------------
        hosts = group_data.get("hosts", [])
        wm.w_sprint("  " + wm.t_blue("Hosts") + ":")

        if not hosts:
            wm.w_sprint("    " + wm.t_green("(no hosts)"))
        else:
            for h in hosts:
                wm.w_sprint("    - " + wm.t_green(h))

        # -------------------------
        # Vars
        # -------------------------
        vars_dict = group_data.get("vars", {})
        wm.w_sprint("  " + wm.t_blue("Parameters") + ":")

        if not vars_dict:
            wm.w_sprint("    (no parameters)")
        else:
            for key, value in vars_dict.items():
                colored_key = wm.t_blue(key)

                # Multiline values (like os_partitioning)
                if isinstance(value, str) and "\n" in value:
                    wm.w_sprint(f"    {colored_key}: |")
                    for line in value.splitlines():
                        wm.w_sprint(f"      {line}")
                else:
                    wm.w_sprint(f"    {colored_key}: {value}")

        wm.w_sprint("")  # blank line between groups

    wm.w_input("Press Enter to go back")
    wm.w_destroy()

# ---------------------------------------------------------------------------
# ACTION 2 — ADD OS GROUP
# ---------------------------------------------------------------------------

def add_os_group(wm, inventory):
    wm.w_create("Add OS group")

    # -------------------------
    # 1. Ask for group name
    # -------------------------
    wm.w_sprint("Enter the OS group name (without 'os_' prefix).")
    base_name = wm.w_input("Group name: ").strip()

    if not base_name:
        wm.w_sprint("Group name cannot be empty.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    group_name = f"os_{base_name}"

    # -------------------------
    # 2. distribution (mandatory)
    # -------------------------
    allowed_distros = ["ubuntu", "debian", "rhel"]

    while True:
        wm.w_sprint("Choose Linux distribution (ubuntu, debian, rhel).")
        distro = wm.w_input("distribution: ").strip().lower()
        if distro in allowed_distros:
            break
        wm.w_sprint("Invalid distribution. Please try again.")

    # -------------------------
    # 3. distribution_major_version (mandatory)
    # -------------------------
    allowed_versions = {
        "debian": ["12", "13"],
        "ubuntu": ["22.04", "24.04"],
        "rhel": ["9", "10"],
    }

    while True:
        wm.w_sprint(f"Choose version for {distro}: {', '.join(allowed_versions[distro])}")
        version = wm.w_input("distribution_major_version: ").strip()
        if version in allowed_versions[distro]:
            break
        wm.w_sprint("Invalid version. Please try again.")

    # -------------------------
    # 4. os_access_control (optional)
    # -------------------------
    wm.w_sprint(
        "OS access control (SELinux/AppArmor). Optional.\n"
        "Allowed: enforcing, permissive, disabled.\n"
        "Default: enforcing"
    )
    access_control = wm.w_input("os_access_control: ").strip().lower()
    if access_control == "":
        access_control = "enforcing"

    # -------------------------
    # 5. os_firewall (optional)
    # -------------------------
    wm.w_sprint(
        "Enable OS firewall? Optional.\n"
        "Allowed: true, false\n"
        "Default: true"
    )
    firewall = wm.w_input("os_firewall: ").strip().lower()
    if firewall == "":
        firewall = "true"
    firewall = firewall == "true"

    # -------------------------
    # 6. os_partitioning (optional, multiline)
    # -------------------------
    wm.w_sprint(
        "Enter OS partitioning configuration (Kickstart/Preseed/Curtin).\n"
        "Optional. Press Enter on an empty line to finish.\n"
        "Default: None"
    )

    partition_lines = []
    while True:
        line = wm.w_input("")
        if line.strip() == "":
            break
        partition_lines.append(line)

    os_partitioning = "\n".join(partition_lines) if partition_lines else None

    # -------------------------
    # 7. os_keyboard_layout (optional)
    # -------------------------
    wm.w_sprint("Keyboard layout (optional). Default: us")
    keyboard = wm.w_input("os_keyboard_layout: ").strip()
    if keyboard == "":
        keyboard = "us"

    # -------------------------
    # 8. os_system_language (optional)
    # -------------------------
    wm.w_sprint("System language (optional). Default: en_US.UTF-8")
    lang = wm.w_input("os_system_language: ").strip()
    if lang == "":
        lang = "en_US.UTF-8"

    # -------------------------
    # Create group
    # -------------------------
    group_vars = {
        "distribution": distro,
        "distribution_major_version": version,
        "os_access_control": access_control,
        "os_firewall": firewall,
        "os_partitioning": os_partitioning,
        "os_keyboard_layout": keyboard,
        "os_system_language": lang,
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
# ACTION 3 — UPDATE OS GROUP
# ---------------------------------------------------------------------------

def update_os_group(wm, inventory):
    wm.w_create("Update OS group")

    groups = inventory.list_groups()
    os_groups = {g: data for g, data in groups.items() if g.startswith("os_")}

    if not os_groups:
        wm.w_sprint("No OS groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # List groups
    wm.w_sprint("Select OS group to update:\n")
    names = list(os_groups.keys())
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
    group_data = os_groups[group_name]
    vars_current = group_data.get("vars", {})

    wm.w_destroy()
    wm.w_create(f"Update {group_name}")

    # Helper to ask with default
    def ask_var(label, default):
        wm.w_sprint(f"{label} (current: {default})")
        val = wm.w_input(f"{label}: ").strip()
        return val if val != "" else default

    # Update fields
    distro = ask_var("distribution", vars_current.get("distribution"))
    version = ask_var("distribution_major_version", vars_current.get("distribution_major_version"))
    access_control = ask_var("os_access_control", vars_current.get("os_access_control", "enforcing"))
    firewall = ask_var("os_firewall", str(vars_current.get("os_firewall", True))).lower() == "true"

    wm.w_sprint("Update OS partitioning (multiline). Leave empty to keep current.")
    partition_lines = []
    while True:
        line = wm.w_input("")
        if line.strip() == "":
            break
        partition_lines.append(line)
    os_partitioning = "\n".join(partition_lines) if partition_lines else vars_current.get("os_partitioning")

    keyboard = ask_var("os_keyboard_layout", vars_current.get("os_keyboard_layout", "us"))
    lang = ask_var("os_system_language", vars_current.get("os_system_language", "en_US.UTF-8"))

    # Apply update
    new_vars = {
        "distribution": distro,
        "distribution_major_version": version,
        "os_access_control": access_control,
        "os_firewall": firewall,
        "os_partitioning": os_partitioning,
        "os_keyboard_layout": keyboard,
        "os_system_language": lang,
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
# ACTION 4 — DELETE OS GROUP
# ---------------------------------------------------------------------------

def delete_os_group(wm, inventory):
    wm.w_create("Delete OS group")

    groups = inventory.list_groups()
    os_groups = {g: data for g, data in groups.items() if g.startswith("os_")}

    if not os_groups:
        wm.w_sprint("No OS groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # List groups
    wm.w_sprint("Select OS group to delete:\n")
    names = list(os_groups.keys())
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
    group_data = os_groups[group_name]

    # Safety check: refuse deletion if hosts exist
    if group_data.get("hosts"):
        wm.w_sprint(
            f"Cannot delete {wm.t_blue(group_name)} because it still contains hosts.\n"
            "Please remove hosts from the group first."
        )
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Confirm deletion
    wm.w_sprint(f"Are you sure you want to delete {wm.t_blue(group_name)}? (yes/no)")
    confirm = wm.w_input("❱❱❱ ").strip().lower()

    if confirm != "yes":
        wm.w_sprint("Deletion cancelled.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    # Delete
    try:
        inventory.delete_group(group_name)
        inventory.save()
        wm.w_sprint(f"Group {wm.t_green(group_name)} deleted successfully.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()

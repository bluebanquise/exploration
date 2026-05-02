# plugins/groups/fn.py

import textwrap

PLUGIN_NAME = "Manage FN groups"
PLUGIN_FOLDER = None   # No nested plugins


def run(wm, inventory):
    """
    Main menu for FN groups management.
    """

    wm.w_create("Manage FN groups")

    while True:

        menu_lines = [
            "Please choose action:\n",
            "1. List FN groups and their hosts",
            "2. Add a new FN group",
            "3. Rename an FN group",
            "4. Delete an FN group",
            "\n9. Back\n",
        ]

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        if answer == "1":
            #wm.w_destroy()
            list_fn_groups(wm, inventory)
            continue

        if answer == "2":
            #wm.w_destroy()
            add_fn_group(wm, inventory)
            continue

        if answer == "3":
            #wm.w_destroy()
            rename_fn_group(wm, inventory)
            continue

        if answer == "4":
            #wm.w_destroy()
            delete_fn_group(wm, inventory)
            continue

        wm.w_sprint("Invalid choice.")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 1 — LIST FN GROUPS
# ---------------------------------------------------------------------------

def list_fn_groups(wm, inventory):
    wm.w_create("List FN groups")

    groups = inventory.list_groups()
    fn_groups = {g: data for g, data in groups.items() if g.startswith("fn_")}

    if not fn_groups:
        wm.w_sprint("No FN groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("FN groups and their hosts:\n")

    for group_name, group_data in fn_groups.items():
        wm.w_sprint(wm.t_blue(group_name))

        hosts = group_data.get("hosts", [])
        wm.w_sprint("  " + wm.t_blue("Hosts") + ":")

        if not hosts:
            wm.w_sprint("    " + wm.t_green("(no hosts)"))
        else:
            for h in hosts:
                wm.w_sprint("    - " + wm.t_green(h))

        wm.w_sprint("")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 2 — ADD FN GROUP
# ---------------------------------------------------------------------------

def add_fn_group(wm, inventory):
    wm.w_create("Add FN group")

    wm.w_sprint("Enter the FN group name (without 'fn_' prefix).")
    base_name = wm.w_input("Group name: ").strip()

    if not base_name:
        wm.w_sprint("Group name cannot be empty.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    group_name = f"fn_{base_name}"

    try:
        inventory.add_group(group_name, {"hosts": [], "vars": {}})
        inventory.save()
        wm.w_sprint(f"Group {wm.t_green(group_name)} created successfully.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 3 — RENAME FN GROUP
# ---------------------------------------------------------------------------

def rename_fn_group(wm, inventory):
    wm.w_create("Rename FN group")

    groups = inventory.list_groups()
    fn_groups = {g: data for g, data in groups.items() if g.startswith("fn_")}

    if not fn_groups:
        wm.w_sprint("No FN groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("Select FN group to rename:\n")
    names = list(fn_groups.keys())
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

    old_name = names[choice - 1]

    wm.w_sprint(f"Enter new name for {wm.t_blue(old_name)} (without 'fn_' prefix).")
    new_base = wm.w_input("New name: ").strip()

    if not new_base:
        wm.w_sprint("New name cannot be empty.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    new_name = f"fn_{new_base}"

    try:
        inventory.rename_group(old_name, new_name)
        inventory.save()
        wm.w_sprint(f"Group renamed to {wm.t_green(new_name)}.")
    except Exception as e:
        wm.w_sprint(f"Error: {e}")

    wm.w_input("Press Enter to go back")
    wm.w_destroy()


# ---------------------------------------------------------------------------
# ACTION 4 — DELETE FN GROUP
# ---------------------------------------------------------------------------

def delete_fn_group(wm, inventory):
    wm.w_create("Delete FN group")

    groups = inventory.list_groups()
    fn_groups = {g: data for g, data in groups.items() if g.startswith("fn_")}

    if not fn_groups:
        wm.w_sprint("No FN groups found.")
        wm.w_input("Press Enter to go back")
        wm.w_destroy()
        return

    wm.w_sprint("Select FN group to delete:\n")
    names = list(fn_groups.keys())
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
    group_data = fn_groups[group_name]

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

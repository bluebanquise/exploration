import textwrap
from windows_manager import windows_manager
from inventory import AnsibleInventory
from plugin_loader import load_plugins


def main():
    wm = windows_manager()

    inventory = AnsibleInventory(
        inventory_root="/var/lib/bluebanquise/inventories/default/",
        working_folder="/tmp",
    )

    # Only load top-level plugins
    plugins = load_plugins("plugins")

    wm.w_create("BlueBanquise manager")

    while True:

        menu_lines = ["Please choose action:\n"]
        for idx, plugin in enumerate(plugins, start=1):
            menu_lines.append(f"{idx}. {plugin.name}")
        menu_lines.append("\n9. Exit\n")

        wm.w_sprint(textwrap.dedent("\n".join(menu_lines)))
        answer = wm.w_input("❱❱❱ ")

        if answer == "9":
            #wm.w_destroy()
            break

        try:
            choice = int(answer)
            if 1 <= choice <= len(plugins):
                selected = plugins[choice - 1]
                #wm.w_destroy()
                selected.run(wm, inventory)
                continue
        except ValueError:
            pass

        wm.w_sprint("Invalid choice.")

    wm.w_destroy()


if __name__ == "__main__":
    main()

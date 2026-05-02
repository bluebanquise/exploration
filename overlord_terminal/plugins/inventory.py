# plugins/inventory/__init__.py

import textwrap
from plugin_loader import load_plugins

PLUGIN_NAME = "Manage inventory"
PLUGIN_FOLDER = "plugins/inventory"


def run(wm, inventory):
    # Load sub-plugins lazily
    plugins = load_plugins(PLUGIN_FOLDER)

    wm.w_create("Manage inventory")

    while True:

        menu_lines = ["Please choose action:\n"]
        for idx, plugin in enumerate(plugins, start=1):
            menu_lines.append(f"{idx}. {plugin.name}")
        menu_lines.append("\n9. Back\n")

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

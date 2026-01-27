#!/usr/bin/env python3

import os
import sys

from flask import Flask, send_from_directory

from common.inventory import AnsibleInventory
from common.files import load_config, load_yaml_file
from common.logging import configure_logging
from common.plugins import load_plugin_module, load_plugin_metadata
from common.ui import deep_merge_ui_skeleton


def create_app(config_path: str = "bluebanquise-overlord.yml") -> Flask:
    config = load_config(config_path)
    log_level = config.get("log_level", "INFO")
    logger = configure_logging(config.get("log_file"), log_level)
    logger.debug("Starting Overlord UI")

    app = Flask(__name__)
    app.config["OVERLORD_CONFIG"] = config

    # UI Skeleton
    #
    # - name: inventory
    #   url: /inventory
    #   title: "Inventory"
    #   sub_elements:
    #     - name: host
    #       url: /inventory/host
    #       title: "Hosts"
    #       sub_elements:
    #         ...


    app.config["UI_SKELETON"] = [
        {
            "name": "inventory",
            "url": "/inventory",
            "title": '<i class="fa-solid fa-boxes-stacked"></i> Inventory',
            "sub_elements": []
        },
        {
            "name": "production",
            "url": "/production",
            "title": '<i class="fa-solid fa-gears"></i> Production',
            "sub_elements": []
        }
    ]


    def deep_merge_ui_skeleton(base_list: list, other_list: list) -> list:
        """
        Recursively merge two lists of menu elements.
        Elements are matched by 'name'.
        Ordering from base_list is preserved.
        New elements from other_list are appended.
        """

        # Index base elements by name for quick lookup
        base_index = {item["name"]: item for item in base_list if isinstance(item, dict)}

        for other_item in other_list:
            # Skip malformed entries
            if not isinstance(other_item, dict):
                continue

            name = other_item.get("name")
            if name is None:
                continue

            if name not in base_index:
                # New element → append at the end
                base_list.append(other_item)
                base_index[name] = other_item
                continue

            # Merge into existing element
            base_item = base_index[name]

            for key, value in other_item.items():
                if key == "sub_elements":
                    base_item.setdefault("sub_elements", [])
                    base_item["sub_elements"] = deep_merge_ui_skeleton(
                        base_item["sub_elements"],
                        value
                    )
                else:
                    # Overwrite scalar fields
                    base_item[key] = value

        return base_list



    # def deep_merge_ui_skeleton(base: dict, other: dict) -> dict:
    #     """
    #     Merge two dicts of the format:
    #     { "data": [ { name, url, title, sub_elements: [...] }, ... ] }
    #     """
    #     # base.setdefault("data", [])
    #     # other.setdefault("data", [])

    #     base["data"] = merge_elements(base["data"], other["data"])
    #     return base


    # def deep_merge_ui_skeleton(base, addition):
    #     """
    #     Deep-merge ui_skeleton-like dicts:
    #     level 0: navbar sections (inventory, production, ...)
    #     level 1: titles (host, slurm, ...)
    #     level 2: list of {name, url} entries

    #     This function mutates base and also returns it.
    #     """
    #     for new_section in addition:
    #         section_exists = False
    #         if 'name' in new_section:
    #             for existing_section in base:
    #                 if new_section['name'] == existing_section['name']:
    #                     section_exists = True
    #         if section_exists = False: # Need to create it, so we just slurp it entirely
    #             base.append(new_section)
    #         else: # It exists, so we need to go deeper to update it
    #             for new_title in new_section.get('sub_elements', []):
    #                 title_exists = False
    #                 if 'name' in new_title:
    #                     for existing_title in base[new_section['name']]['sub_elements']:
    #                         if new_section['name'] == existing_section['name']:
    #                             section_exists = True



            

    #     for section, content in addition.items():
    #         if section not in base:
    #             base[section] = {}
    #         for title, items in content.items():
    #             if title not in base[section]:
    #                 base[section][title] = []
    #             base[section][title].extend(items)
    #     return base


    inventory_root = config.get("inventory_path")
    working_folder = config.get("working_folder")
    if not inventory_root or not working_folder:
        logger.error("inventory_path or working_folder not defined in configuration")

    # Register plugins path to allow relative load
    plugins_path = config.get("plugins_path", "./plugins")
    sys.path.insert(0, os.path.abspath(plugins_path))

    # Add plugin template folders to Jinja search path
    for root, dirs, files in os.walk(plugins_path):
        if "templates" in dirs:
            template_dir = os.path.join(root, "templates")
            app.jinja_loader.searchpath.append(os.path.abspath(template_dir))

    # Discover plugin UI and API blueprints
    for root, dirs, files in os.walk(plugins_path):

        # Load plugin config first
        plugin_config = {}
        if "config.yml" in files:
            plugin_config_path = os.path.join(root, "config.yml")
            plugin_config = load_yaml_file(plugin_config_path) or {}
        if "main_ui.py" in files:
            main_ui_path = os.path.join(root, "main_ui.py")

            # Build a unique module name from path
            rel = os.path.relpath(main_ui_path, plugins_path)
            mod_name = "plugins_ui_" + rel.replace(os.sep, "_").replace(".py", "")

            try:
                module = load_plugin_module(main_ui_path, mod_name)
            except Exception as e:
                logger.error("Failed to load UI module %s: %s", main_ui_path, e)
                continue

            # Expect: module.blueprint and module.ui_integration
            blueprint = getattr(module, "blueprint", None)

            ui_integration = plugin_config.get("ui_integration", None)

            if blueprint is None or ui_integration is None:
                logger.warning(
                    "UI module %s does not expose both blueprint and ui_integration",
                    main_ui_path,
                )
                continue

            # Register blueprint with no prefix; routes must be absolute in plugin
            app.register_blueprint(blueprint)

            # Merge ui_integration into global skeleton
            skeleton = app.config["UI_SKELETON"]
            deep_merge_ui_skeleton(skeleton, ui_integration)

            logger.debug("Loaded UI plugin from %s", main_ui_path)

        if "main_api.py" in files:
            main_api_path = os.path.join(root, "main_api.py")

            # Build a unique module name from path
            rel = os.path.relpath(main_api_path, plugins_path)
            mod_name = "plugins_api_" + rel.replace(os.sep, "_").replace(".py", "")

            try:
                module = load_plugin_module(main_api_path, mod_name)
            except Exception as e:
                logger.error("Failed to load API module %s: %s", main_api_path, e)
                continue

            # Expect: module.blueprint and module.api_integration
            blueprint = getattr(module, "blueprint", None)

            if blueprint is None:
                logger.warning(
                    "API module %s does not expose both blueprint",
                    main_api_path,
                )
                continue

            # Register blueprint with no prefix; routes must be absolute in plugin
            app.register_blueprint(blueprint)

            logger.debug("Loaded API plugin from %s", main_api_path)


    # This is a special move
    # We can inject a dict into templates rendering context, this avoids to pass it all the time
    # Super useful for us here
    @app.context_processor
    def inject_overlord_context():
        return {
            "ui_skeleton": app.config.get("UI_SKELETON", {}),
        }

    @app.route('/webfonts/<path:filename>')
    def cover_webfonts(filename):
        return send_from_directory(app.root_path + '/static/webfonts/', filename)

    return app


if __name__ == "__main__":
    config_path = os.environ.get("OVERLORD_CONFIG", "bluebanquise-overlord.yml")
    app = create_app(config_path)
    cfg = app.config["OVERLORD_CONFIG"]
    host = cfg.get("ui", {}).get("host", "127.0.0.1")
    port = int(cfg.get("ui", {}).get("port", 5000))
    
    print("URLs map:")
    print(app.url_map)
    app.run(host=host, port=port, debug=False)

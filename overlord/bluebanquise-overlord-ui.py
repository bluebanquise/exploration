#!/usr/bin/env python3

import os
import sys

from flask import Flask
from common import (
    load_config,
    configure_logging,
    load_plugin_module,
    deep_merge_ui_skeleton,
)
from inventory import AnsibleInventory


def create_app(config_path: str = "bluebanquise-overlord.yml") -> Flask:
    config = load_config(config_path)
    log_level = config.get("log_level", "INFO")
    logger = configure_logging(config.get("log_file"), log_level)
    logger.debug("Starting Overlord UI")

    app = Flask(__name__)
    app.config["OVERLORD_CONFIG"] = config
    app.config["UI_SKELETON"] = {}

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

    # Discover plugin UI blueprints
    plugins_path = config.get("plugins_path", "./plugins")

    for root, dirs, files in os.walk(plugins_path):
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
            ui_integration = getattr(module, "ui_integration", None)

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

    @app.context_processor
    def inject_overlord_context():
        return {
            "ui_skeleton": app.config.get("UI_SKELETON", {}),
        }

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

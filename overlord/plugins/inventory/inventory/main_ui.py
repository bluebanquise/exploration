# plugins/inventory/network/main_ui.py

from typing import Any, Dict

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    render_template,
)
from flask_restful import Api, Resource

# from common.ui import overlord_page_render
from common.files import load_yaml_file
from common.logging import configure_logging
from common.inventory import AnsibleInventory

# Import plugin logic
from plugins.inventory.inventory.main import Plugin as InventoryPlugin

blueprint = Blueprint(
    "inventory_inventory",
    __name__,
    template_folder="templates",
)

def call_plugin(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate plugin and execute a specific action with payload.
    """
    cfg = current_app.config.get("OVERLORD_CONFIG", {})

    # Get logger
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    logger = configure_logging(log_file, log_level)

    # Get plugin config
    plugins_path = cfg.get("plugins_path", "./plugins")
    config_path = f"{plugins_path}/inventory/inventory/config.yml"
    try:
        plugin_config = load_yaml_file(config_path) or {}
    except FileNotFoundError:
        plugin_config = {}

    # Build global context to pass to plugin
    global_ctx = {
        "diff": False,
        "check": False,
        "debug": cfg.get("log_level", "INFO").upper() == "DEBUG",
        "inventory_root": cfg.get("inventory_path"),
        "working_folder": cfg.get("working_folder"),
        "section": "inventory",
        "plugin": "inventory",
        "config": cfg,
    }

    # Ok ready to call plugin, init it
    plugin = InventoryPlugin(
        action_args=[action],
        config=plugin_config,
        logger=logger,
        global_args=global_ctx,
    )

    # All went well, execute with payload and action
    return plugin.execute(action, payload)


####################### HTML ENDPOINT #######################

# NO REST API for now, its not needed here, would be overkill
# Can be added later.

@blueprint.route("/inventory")
def inventory_root():

    inventory = call_plugin("get", {})

    return render_template(
        "inventory/index.j2",
        current_section="inventory",
        inventory=inventory['data']
    )

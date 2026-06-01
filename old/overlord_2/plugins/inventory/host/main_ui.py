# plugins/inventory/host/main_ui.py

import os
from flask import Blueprint, current_app, render_template

from common.metadata import load_plugin_metadata
from common import overlord_page_render  # assuming you have this helper already

blueprint = Blueprint(
    "inventory_host",
    __name__,
    template_folder="templates",
)

PLUGIN_DIR = os.path.dirname(__file__)
METADATA = load_plugin_metadata(PLUGIN_DIR)

# UI integration structure consumed by the core UI
ui_integration = {
    METADATA.get("ui", {}).get("menu", {}).get("section", "inventory"): {
        METADATA.get("name", "inventory_host"): METADATA.get("ui", {}).get("menu", {}).get("entries", [])
    }
}


@blueprint.route("/inventory/host/list")
def host_list_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="host/list.j2",
    )


@blueprint.route("/inventory/host/add")
def host_add_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="host/add.j2",
    )

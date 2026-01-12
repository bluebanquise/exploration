# plugins/inventory/host/main_ui.py

from typing import Any, Dict

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    render_template,
)
from flask_restful import Api, Resource

from common.ui import overlord_page_render
from common.files import load_yaml_file
from common.logging import configure_logging
from common.inventory import AnsibleInventory

# Import plugin logic
from plugins.inventory.host.main import Plugin as HostPlugin

blueprint = Blueprint(
    "inventory_host",
    __name__,
    template_folder="templates",
)

# --------------------------
# HTML endpoints (thin)
# --------------------------

@blueprint.route("/inventory/host/list")
def host_list_page():
    """
    Just render the page; JS will fetch the hosts from the REST API.
    """
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


@blueprint.route("/inventory/host/delete")
def host_delete_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="host/delete.j2",
    )


@blueprint.route("/inventory/host/<string:hostname>")
def host_details_page(hostname: str):
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="host/details.j2",
        hostname=hostname,
    )

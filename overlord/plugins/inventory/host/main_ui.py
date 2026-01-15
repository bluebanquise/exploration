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

# from common.ui import overlord_page_render
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

####################### HTML ENDPOINT #######################

@blueprint.route("/inventory/host/list")
def host_list_page():
    return render_template(
        "host/list.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/host/add")
def host_add_page():
    return render_template(
        "host/add.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/host/delete")
def host_delete_page():
    return render_template(
        "host/delete.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/host/<string:hostname>")
def host_details_page(hostname: str):
    return render_template(
        "host/details.j2",
        current_section="inventory",
    )

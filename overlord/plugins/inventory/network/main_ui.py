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
from plugins.inventory.network.main import Plugin as NetworkPlugin

blueprint = Blueprint(
    "inventory_network",
    __name__,
    template_folder="templates",
)

####################### HTML ENDPOINT #######################

@blueprint.route("/inventory/network/list")
def network_list_page():
    return render_template(
        "network/list.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/network/add")
def network_add_page():
    return render_template(
        "network/add.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/network/delete/<string:networkname>")
def network_delete_page(networkname: str):
    return render_template(
        "network/delete.j2",
        current_section="inventory",
        name=networkname
    )

@blueprint.route("/inventory/network/<string:networkname>")
def network_details_page(networkname: str):
    return render_template(
        "network/details.j2",
        current_section="inventory",
        name=networkname
    )

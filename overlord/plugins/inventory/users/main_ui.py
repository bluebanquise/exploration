# plugins/inventory/user/main_ui.py

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
from plugins.inventory.user.main import Plugin as UserPlugin

blueprint = Blueprint(
    "inventory_user",
    __name__,
    template_folder="templates",
)

####################### HTML ENDPOINT #######################

@blueprint.route("/inventory/user/list")
def user_list_page():
    return render_template(
        "user/list.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/user/add")
def user_add_page():
    return render_template(
        "user/add.j2",
        current_section="inventory",
    )

@blueprint.route("/inventory/user/delete/<string:username>")
def user_delete_page(username: str):
    return render_template(
        "user/delete.j2",
        current_section="inventory",
        name=username
    )

@blueprint.route("/inventory/user/<string:username>")
def user_details_page(username: str):
    return render_template(
        "user/details.j2",
        current_section="inventory",
        name=username
    )

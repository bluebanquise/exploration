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
from plugins.inventory.group.main import Plugin as GroupPlugin

blueprint = Blueprint(
    "inventory_group",
    __name__,
    template_folder="templates",
)

####################### HTML ENDPOINT #######################

@blueprint.route("/inventory/group/list")
def group_list_page():
    return render_template(
        "group/list.j2",
        current_section="inventory",
    )

# STEP 1 — Select group type
@blueprint.route("/inventory/group/add")
def group_add_select_page():
    return render_template(
        "group/add_select.j2",
        current_section="inventory",
    )

# STEP 2 — Dedicated pages
@blueprint.route("/inventory/group/add/<group_type>")
def group_add_specific_page(group_type):
    template_map = {
        "function": "group/add_function.j2",
        "os": "group/add_os.j2",
        "hardware": "group/add_hardware.j2",
        "rack": "group/add_function.j2",
        "custom": "group/add_custom.j2",
    }

    if group_type not in template_map:
        return "Unknown group type", 404

    return render_template(
        template_map[group_type],
        group_type=group_type,
        current_section="inventory",
    )

# NEW: dedicated details pages
@blueprint.route("/inventory/group/details/<group_type>/<name>")
def group_details_specific_page(group_type, name):
    template_map = {
        "function": "group/details_function.j2",
        "os": "group/details_os.j2",
        "hardware": "group/details_hardware.j2",
        "rack": "group/details_function.j2",
        "custom": "group/details_custom.j2",
    }

    if group_type not in template_map:
        return "Unknown group type", 404

    return render_template(
        template_map[group_type],
        current_section="inventory",
        group_type=group_type,
        name=name
    )

@blueprint.route("/inventory/group/details/<name>")
def group_details_page(name):
    return render_template(
        "group/details.j2",
        current_section="inventory",
        name=name
    )

@blueprint.route("/inventory/group/delete/<name>")
def group_delete_page(name):
    return render_template(
        "group/delete.j2",
        current_section="inventory",
        name=name
    )

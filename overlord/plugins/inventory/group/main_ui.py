# plugins/inventory/group/main_ui.py

from flask import Blueprint, current_app
from common.overlord_page_render import overlord_page_render

blueprint = Blueprint(
    "inventory_group",
    __name__,
    template_folder="templates",
)


@blueprint.route("/inventory/group/list")
def group_list_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/list.j2",
    )


@blueprint.route("/inventory/group/add")
def group_add_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/add.j2",
    )


@blueprint.route("/inventory/group/details/<name>")
def group_details_page(name):
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/details.j2",
        name=name,
    )


@blueprint.route("/inventory/group/delete/<name>")
def group_delete_page(name):
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/delete.j2",
        name=name,
    )

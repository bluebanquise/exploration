# plugins/production/playbook/main_ui.py

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
from plugins.production.playbook.main import Plugin as playbookPlugin

blueprint = Blueprint(
    "production_playbook",
    __name__,
    template_folder="templates",
)

####################### HTML ENDPOINT #######################

@blueprint.route("/production/playbook/list")
def playbook_list_page():
    return render_template(
        "playbook/list.j2",
        current_section="production",
    )

@blueprint.route("/production/playbook/add")
def playbook_add_page():
    return render_template(
        "playbook/add.j2",
        current_section="production",
    )

@blueprint.route("/production/playbook/delete/<string:playbookname>")
def playbook_delete_page(playbookname: str):
    return render_template(
        "playbook/delete.j2",
        current_section="production",
        name=playbookname
    )

@blueprint.route("/production/playbook/<string:playbookname>")
def playbook_details_page(playbookname: str):
    return render_template(
        "playbook/details.j2",
        current_section="production",
        name=playbookname
    )

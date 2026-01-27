# plugins/production/health/main_ui.py

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

blueprint = Blueprint(
    "production_health",
    __name__,
    template_folder="templates",
)

####################### HTML ENDPOINT #######################

@blueprint.route("/production/health/cluster_view")
def health_list_page():
    return render_template(
        "health/cluster_view.j2",
        current_section="production",
    )

@blueprint.route("/api/v1/production/health")
def health_api():

    health_results = load_yaml_file("resulsts.yam")

    return health_results, 200
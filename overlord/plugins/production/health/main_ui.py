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

    results = load_yaml_file("results.yaml")

    return render_template(
        "health/cluster_view.j2",
        current_section="production",
        results=results
    )

@blueprint.route("/api/v1/production/health")
def health_api():

    results = load_yaml_file("results.yaml")
    print(results)

    toto = render_template(
        "health/cluster_view.j2",
        current_section="production",
        results=results
    )
    print(toto)
    return "OK"
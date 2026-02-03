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
def health_cluster_view():

    results = load_yaml_file("results.yaml")

    return render_template(
        "health/cluster_view.j2",
        current_section="production",
        results=results
    )

@blueprint.route("/production/health/cluster_view/<string:hostname>")
def health_hostpage(hostname):

    results = load_yaml_file("results.yaml")
    host_result = {}
    for rack in results:
        for host in results[rack]:
            if hostname == host:
                host_result = results[rack][host]
                break
        if len(host_result) > 0:
            break

    return render_template(
        "health/host_view.j2",
        current_section="production",
        data=host_result,
        host=hostname
    )

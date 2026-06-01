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

from common import overlord_page_render, load_yaml_file, configure_logging
from inventory import AnsibleInventory

# Import plugin logic
from plugins.inventory.host.main import Plugin as HostPlugin

blueprint = Blueprint(
    "inventory_host",
    __name__,
    template_folder="templates",
)

ui_integration = {
    "inventory": {
        "host": [
            {"name": "List hosts", "url": "inventory/host/list"},
            {"name": "Add new host", "url": "inventory/host/add"},
            {"name": "Delete an host", "url": "inventory/host/delete"},
        ]
    }
}

# --------------------------
# Helpers
# --------------------------


def get_logger():
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    return configure_logging(log_file, log_level)


def get_inventory(diff: bool = False, check: bool = False) -> AnsibleInventory:
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    inventory_root = cfg.get("inventory_path")
    working_folder = cfg.get("working_folder")
    logger = get_logger()
    return AnsibleInventory(
        inventory_root=inventory_root,
        working_folder=working_folder,
        diff=diff,
        check=check,
        logger=logger,
    )


def get_plugin_config() -> Dict[str, Any]:
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    plugins_path = cfg.get("plugins_path", "./plugins")
    config_path = f"{plugins_path}/inventory/host/config.yml"
    try:
        return load_yaml_file(config_path) or {}
    except FileNotFoundError:
        return {}


def build_global_context() -> Dict[str, Any]:
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    return {
        "diff": False,
        "check": False,
        "debug": cfg.get("log_level", "INFO").upper() == "DEBUG",
        "inventory_root": cfg.get("inventory_path"),
        "working_folder": cfg.get("working_folder"),
        "section": "inventory",
        "plugin": "host",
        "config": cfg,
    }


def call_plugin(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate HostPlugin and execute a specific action with payload.
    """
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    logger = get_logger()
    inv = get_inventory(diff=False, check=False)
    plugin_config = get_plugin_config()
    global_ctx = build_global_context()

    plugin = HostPlugin(
        action_args=[action],  # CLI args not used here; we pass payload directly
        inventory=inv,
        config=plugin_config,
        logger=logger,
        global_args=global_ctx,
    )

    return plugin.execute(action, payload)


# --------------------------
# REST API
# --------------------------

api = Api(blueprint)


class HostListResource(Resource):
    def get(self):
        result = call_plugin("list", {})
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def post(self):
        """
        Payload expected:
        {
          "c003": {
            "alias": "compute-3",
            ...
          }
        }
        """
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict) or not data:
            return {
                "status": "error",
                "message": "JSON payload must be a non-empty object",
            }, 400

        payload = {"hosts": data}
        result = call_plugin("add", payload)
        status_code = 201 if result.get("status") == "ok" else 400
        return result, status_code


class HostResource(Resource):
    def get(self, hostname: str):
        payload = {"hostname": hostname}
        result = call_plugin("get", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code

    def put(self, hostname: str):
        """
        Update host.
        Body is a dict of fields to update, e.g.:

        {
          "alias": "new-alias",
          "network_interfaces": {...},
          "bmc": {...},
          "vars": {...}
        }
        """
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return {
                "status": "error",
                "message": "JSON payload must be an object",
            }, 400

        payload = {"hostname": hostname, "data": data}
        result = call_plugin("update", payload)
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def delete(self, hostname: str):
        payload = {"hostname": hostname}
        result = call_plugin("delete", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code


api.add_resource(HostListResource, "/api/v1/inventory/host")
api.add_resource(HostResource, "/api/v1/inventory/host/<string:hostname>")


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

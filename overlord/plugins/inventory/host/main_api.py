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

from common.ui import overlord_page_render
from common.files import load_yaml_file
from common.logging import configure_logging
# from common.inventory import AnsibleInventory

# Import plugin logic
from plugins.inventory.host.main import Plugin as HostPlugin

blueprint = Blueprint(
    "inventory_host_api",
    __name__,
    template_folder="templates",
)

# --------------------------
# Helpers
# --------------------------


def get_logger():
    cfg = current_app.config.get("OVERLORD_CONFIG", {})
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    return configure_logging(log_file, log_level)


# def get_inventory(diff: bool = False, check: bool = False) -> AnsibleInventory:
#     cfg = current_app.config.get("OVERLORD_CONFIG", {})
#     inventory_root = cfg.get("inventory_path")
#     working_folder = cfg.get("working_folder")
#     logger = get_logger()
#     return AnsibleInventory(
#         inventory_root=inventory_root,
#         working_folder=working_folder,
#         diff=diff,
#         check=check,
#         logger=logger,
#     )


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
    #inv = get_inventory(diff=False, check=False)
    plugin_config = get_plugin_config()
    global_ctx = build_global_context()

    plugin = HostPlugin(
        action_args=[action],  # CLI args not used here; we pass payload directly
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
        payload = {hostname}
        print('coucou')
        print(payload)
        result = call_plugin("get", payload)
        print('result')
        print(result)
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

        payload = {hostname: data}
        result = call_plugin("update", payload)
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def delete(self, hostname: str):
        payload = {hostname}
        result = call_plugin("delete", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code


api.add_resource(HostListResource, "/api/v1/inventory/host")
api.add_resource(HostResource, "/api/v1/inventory/host/<string:hostname>")


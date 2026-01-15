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

from common.files import load_yaml_file
from common.logging import configure_logging

# Import plugin logic
from plugins.inventory.host.main import Plugin as HostPlugin

blueprint = Blueprint(
    "inventory_host_api",
    __name__,
    template_folder="templates",
)
api = Api(blueprint)


def call_plugin(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate HostPlugin and execute a specific action with payload.
    """
    cfg = current_app.config.get("OVERLORD_CONFIG", {})

    # Get logger
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    logger = configure_logging(log_file, log_level)

    # Get plugin config
    plugins_path = cfg.get("plugins_path", "./plugins")
    config_path = f"{plugins_path}/inventory/host/config.yml"
    try:
        plugin_config = load_yaml_file(config_path) or {}
    except FileNotFoundError:
        plugin_config = {}

    # Build global context to pass to plugin
    global_ctx = {
        "diff": False,
        "check": False,
        "debug": cfg.get("log_level", "INFO").upper() == "DEBUG",
        "inventory_root": cfg.get("inventory_path"),
        "working_folder": cfg.get("working_folder"),
        "section": "inventory",
        "plugin": "host",
        "config": cfg,
    }

    # Ok ready to call plugin, init it
    plugin = HostPlugin(
        action_args=[action],
        config=plugin_config,
        logger=logger,
        global_args=global_ctx,
    )

    # All went well, execute with payload and action
    return plugin.execute(action, payload)


################## REST API ##################



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

        payload = data
        result = call_plugin("add", payload)
        status_code = 201 if result.get("status") == "ok" else 400
        return result, status_code


class HostResource(Resource):
    def get(self, hostname: str):
        payload = {hostname}
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


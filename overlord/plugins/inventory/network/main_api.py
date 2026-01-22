# plugins/inventory/network/main_ui.py

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
from plugins.inventory.network.main import Plugin as NetworkPlugin

blueprint = Blueprint(
    "inventory_network_api",
    __name__,
    template_folder="templates",
)
api = Api(blueprint)


def call_plugin(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate NetworkPlugin and execute a specific action with payload.
    """
    cfg = current_app.config.get("OVERLORD_CONFIG", {})

    # Get logger
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    logger = configure_logging(log_file, log_level)

    # Get plugin config
    plugins_path = cfg.get("plugins_path", "./plugins")
    config_path = f"{plugins_path}/inventory/network/config.yml"
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
        "plugin": "network",
        "config": cfg,
    }

    # Ok ready to call plugin, init it
    plugin = NetworkPlugin(
        action_args=[action],
        config=plugin_config,
        logger=logger,
        global_args=global_ctx,
    )

    # All went well, execute with payload and action
    return plugin.execute(action, payload)


################## REST API ##################



class NetworkListResource(Resource):
    def get(self):
        result = call_plugin("list", {})
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def post(self):
        """
        Payload expected:
        {
          "net-admin": {
            "subnet": "10.10.0.0",
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


class NetworkResource(Resource):
    def get(self, networkname: str):
        payload = {networkname}
        result = call_plugin("get", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code

    def put(self, networkname: str):
        """
        Update network.
        Body is a dict of fields to update
        """
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return {
                "status": "error",
                "message": "JSON payload must be an object",
            }, 400

        payload = {networkname: data}
        result = call_plugin("update", payload)
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def delete(self, networkname: str):
        payload = {networkname}
        result = call_plugin("delete", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code


api.add_resource(NetworkListResource, "/api/v1/inventory/network")
api.add_resource(NetworkResource, "/api/v1/inventory/network/<string:networkname>")


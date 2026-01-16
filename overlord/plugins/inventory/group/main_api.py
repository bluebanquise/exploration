# plugins/inventory/group/main_api.py

from flask import Blueprint, request, current_app
from flask_restful import Api, Resource



from common.files import load_yaml_file
from common.logging import configure_logging
from typing import Any, Dict

# Import plugin logic
from plugins.inventory.group.main import Plugin as GroupPlugin


blueprint = Blueprint(
    "inventory_group_api",
    __name__
)
api = Api(blueprint)



def call_plugin(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiate GroupPlugin and execute a specific action with payload.
    """
    cfg = current_app.config.get("OVERLORD_CONFIG", {})

    # Get logger
    log_level = cfg.get("log_level", "INFO")
    log_file = cfg.get("log_file")
    logger = configure_logging(log_file, log_level)

    # Get plugin config
    plugins_path = cfg.get("plugins_path", "./plugins")
    config_path = f"{plugins_path}/inventory/group/config.yml"
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
        "plugin": "group",
        "config": cfg,
    }

    # Ok ready to call plugin, init it
    plugin = GroupPlugin(
        action_args=[action],
        config=plugin_config,
        logger=logger,
        global_args=global_ctx,
    )

    # All went well, execute with payload and action
    return plugin.execute(action, payload)

# ------------------------------------------------------------
# /api/v1/inventory/group
# ------------------------------------------------------------
class GroupListResource(Resource):
    def get(self):
        """
        GET /api/v1/inventory/group
        List all groups.
        """
        result = call_plugin("list", {})
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code
        # plugin = get_group_plugin()
        # groups = plugin.list_groups()
        # return api_ok(data={"groups": groups})

    def post(self):
        """
        POST /api/v1/inventory/group
        Create a new group.

        Expected JSON:
        {
            "mygroup":
              "group_type": "os" | "hardware" | "function" | "rack" | "custom",
              "vars": {}
              "hosts": []
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

# ------------------------------------------------------------
# /api/v1/inventory/group/<groupname>
# ------------------------------------------------------------
class GroupResource(Resource):
    def get(self, groupname):
        payload = {groupname}
        result = call_plugin("get", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code

    def put(self, groupname):
        """
        Update group.
        Body is a dict of fields to update, e.g.:

        {
          "hosts": [],
          "vars": {...}
        }
        """
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return {
                "status": "error",
                "message": "JSON payload must be an object",
            }, 400

        payload = {groupname: data}
        result = call_plugin("update", payload)
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def delete(self, groupname: str):
        payload = {groupname}
        result = call_plugin("delete", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code


# ------------------------------------------------------------
# /api/v1/inventory/group/<groupname>/hosts/
# ------------------------------------------------------------
class GroupHostsResource(Resource):
    def get(self, groupname):
        payload = {groupname}
        result = call_plugin("get_hosts", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code

    def post(self, groupname):
        """
        Add new host to group
        {
            host: c001
        }
        """
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return {
                "status": "error",
                "message": "JSON payload must be an object",
            }, 400

        payload = {groupname: {"hosts": [data["host"]]}}
        result = call_plugin("add_hosts", payload)
        status_code = 200 if result.get("status") == "ok" else 400
        return result, status_code

    def delete(self, groupname: str):
        data = request.get_json(force=True, silent=True)
        payload = {groupname: {"hosts": [data["host"]]}}
        result = call_plugin("delete_hosts", payload)
        status_code = 200 if result.get("status") == "ok" else 404
        return result, status_code


# ------------------------------------------------------------
# Resource registration
# ------------------------------------------------------------
api.add_resource(GroupListResource, "/api/v1/inventory/group")
api.add_resource(GroupResource, "/api/v1/inventory/group/<string:groupname>")
api.add_resource(GroupHostsResource, "/api/v1/inventory/group/<string:groupname>/hosts")

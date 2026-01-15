# plugins/inventory/group/main_api.py

from flask import Blueprint, request, current_app
from flask_restful import Api, Resource



from common.files import load_yaml_file
from common.logging import configure_logging

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
            "name": "mygroup",
            "group_type": "os" | "hardware" | "function" | "rack" | "custom",
            ... type-specific fields ...
        }
        """
        payload = request.get_json() or {}
        name = payload.get("name")

        if not name:
            return api_error("Missing 'name'")

        try:
            plugin = get_group_plugin()
            plugin.add_group(name, payload)
            plugin.save()
            return api_ok(message=f"Group {name} created")
        except Exception as e:
            return api_error(str(e))


# ------------------------------------------------------------
# /api/v1/inventory/group/<name>
# ------------------------------------------------------------
class GroupResource(Resource):
    def get(self, name):
        """
        GET /api/v1/inventory/group/<name>
        Retrieve a single group.
        """
        plugin = get_group_plugin()
        group = plugin.get_group(name)

        if group is None:
            return api_error(f"Group {name} not found")

        return api_ok(data={"group": {name: group}})

    def put(self, name):
        """
        PUT /api/v1/inventory/group/<name>
        Update a group.
        """
        payload = request.get_json() or {}

        try:
            plugin = get_group_plugin()
            plugin.update_group(name, payload)
            plugin.save()
            return api_ok(message=f"Group {name} updated")
        except Exception as e:
            return api_error(str(e))

    def delete(self, name):
        """
        DELETE /api/v1/inventory/group/<name>
        Delete a group.
        """
        try:
            plugin = get_group_plugin()
            plugin.delete_group(name)
            plugin.save()
            return api_ok(message=f"Group {name} deleted")
        except Exception as e:
            return api_error(str(e))


# ------------------------------------------------------------
# Resource registration
# ------------------------------------------------------------
api.add_resource(GroupListResource, "/api/v1/inventory/group")
api.add_resource(GroupResource, "/api/v1/inventory/group/<string:name>")

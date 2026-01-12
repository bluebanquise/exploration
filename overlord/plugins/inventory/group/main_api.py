# plugins/inventory/group/main_api.py

from flask import Blueprint, request, current_app
from flask_restful import Api, Resource
from common.responses import api_ok, api_error
from plugins.inventory.group.main import GroupPlugin

blueprint = Blueprint("inventory_group_api", __name__)
api = Api(blueprint)


def get_group_plugin() -> GroupPlugin:
    inventory_path = current_app.config["INVENTORY_PATH"]
    return GroupPlugin(inventory_path)


class GroupListResource(Resource):
    def get(self):
        plugin = get_group_plugin()
        groups = plugin.list_groups()
        return api_ok(data={"groups": groups})

    def post(self):
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


class GroupResource(Resource):
    def get(self, name):
        plugin = get_group_plugin()
        group = plugin.get_group(name)
        if group is None:
            return api_error(f"Group {name} not found")
        return api_ok(data={"group": {name: group}})

    def put(self, name):
        payload = request.get_json() or {}
        try:
            plugin = get_group_plugin()
            plugin.update_group(name, payload)
            plugin.save()
            return api_ok(message=f"Group {name} updated")
        except Exception as e:
            return api_error(str(e))

    def delete(self, name):
        try:
            plugin = get_group_plugin()
            plugin.delete_group(name)
            plugin.save()
            return api_ok(message=f"Group {name} deleted")
        except Exception as e:
            return api_error(str(e))


api.add_resource(GroupListResource, "/api/v1/inventory/group")
api.add_resource(GroupResource, "/api/v1/inventory/group/<string:name>")

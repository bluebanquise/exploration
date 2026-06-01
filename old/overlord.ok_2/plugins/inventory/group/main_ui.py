# plugins/inventory/group/main_ui.py

from flask import Blueprint, current_app
from common.overlord_page_render import overlord_page_render


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


blueprint = Blueprint(
    "inventory_group",
    __name__,
    template_folder="templates",
)


@blueprint.route("/inventory/group/list")
def group_list_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/list.j2",
    )


@blueprint.route("/inventory/group/add")
def group_add_page():
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/add.j2",
    )


@blueprint.route("/inventory/group/delete/<name>")
def group_delete_page(name):
    return overlord_page_render(
        current_app.config["UI_SKELETON"],
        current_section="inventory",
        template_name="group/delete.j2",
        name=name,
    )




class GroupListResource(Resource):
    def get(self):
        """
        GET /api/v1/inventory/group
        List all groups.
        """
        plugin = get_group_plugin()
        groups = plugin.list_groups()
        return api_ok(data={"groups": groups})

    def post(self):
        """
        POST /api/v1/inventory/group
        Body:
          {
            "name": "group_name",
            "group_type": "function" | "os" | "hardware" | "rack" | "custom",
            ... type-specific data ...
          }
        """
        payload = request.get_json() or {}
        name = payload.get("name")
        if not name:
            return api_error("Missing 'name'")

        try:
            plugin = get_group_plugin()
            # Store the full payload under the group name
            plugin.add_group(name, payload)
            plugin.save()
            return api_ok(message=f"Group {name} created")
        except Exception as e:
            return api_error(str(e))


class GroupResource(Resource):
    def get(self, name):
        """
        GET /api/v1/inventory/group/<name>
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
        """
        try:
            plugin = get_group_plugin()
            plugin.delete_group(name)
            plugin.save()
            return api_ok(message=f"Group {name} deleted")
        except Exception as e:
            return api_error(str(e))


api.add_resource(GroupListResource, "/api/v1/inventory/group")
api.add_resource(GroupResource, "/api/v1/inventory/group/<string:name>")

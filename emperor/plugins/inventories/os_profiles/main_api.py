from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    render_template,
)
from flask_restful import Api, Resource
from common.inventory import AnsibleInventory

blueprint = Blueprint(
    "inventory_os_profiles_api",
    __name__,
    template_folder="templates",
)
api = Api(blueprint)


# If needed, an init is always called when plugin is loaded first time
def init_plugin():
    return True


def load_inventory() -> AnsibleInventory:
    cfg = current_app.config.get("MAIN_CONFIG", {})
    inventory = AnsibleInventory(
        inventories_root=cfg.get("inventories_root"),
        inventory_name=cfg.get("inventory_name"),
        working_folder=cfg.get("working_folder"),
        diff=True,
        check=False,
        logger=current_app.logger)

    return inventory


class OsProfilesRootResource(Resource):
    def get(self):
        inventory = load_inventory()
        os_profiles = {}
        for group, group_data in inventory.get_groups():
            if group.startswith('os_'):
                os_profiles[group] = group_data

        return os_profiles, 200

    def post(self):
        """
        Payload expected:
        {
          "os_ubuntu_24.04_A": {
            "os_operating_system...
            ...
          }
        }
        """
        data = request.get_json(force=True, silent=True)

        inventory = load_inventory()
        all_vars = inventory.get_group('all')['vars']
        all_vars['plugin_networks']['networks'].update(data)
        inventory.update_group('all', None, all_vars)
        inventory.save()

        return {"status": "OK", "message": "Network added"}, 200


class OsProfileResource(Resource):
    def get(self, network_name):

        inventory = load_inventory()
        networks = inventory.get_group('all')['vars']['plugin_networks']['networks']

        if network_name in networks:
            return networks[network_name], 200
        else:
            return {"status": "Error", "message": "Network not found"}, 400

    def put(self, network_name):
        """
        Payload expected:
          {
            "subnet": "10.10.0.0",
            ...
          }
        """

        data = request.get_json(force=True, silent=True)

        inventory = load_inventory()
        all_vars = inventory.get_group('all')['vars']
        all_vars['plugin_networks']['networks'][network_name].update(data)
        inventory.update_group('all', None, all_vars)
        inventory.save()

        return {"status": "OK", "message": "Network updated"}, 200

    def delete(self, network_name: str):

        inventory = load_inventory()
        all_vars = inventory.get_group('all')['vars']
        del all_vars['plugin_networks']['networks'][network_name]
        inventory.update_group('all', None, all_vars)
        inventory.save()

        return {"status": "OK", "message": "Network deleted"}, 200


api.add_resource(OsProfilesRootResource, "/api/v1/inventory/os_profiles")
api.add_resource(OsProfileResource, "/api/v1/inventory/os_profile/<string:network_name>")

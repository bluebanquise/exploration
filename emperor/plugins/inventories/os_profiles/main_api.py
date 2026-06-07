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


class OSProfilesRootResource(Resource):

    def get(self):
        inventory = load_inventory()
        os_profiles = {}
        for group, group_data in inventory.get_groups().items():
            if group.startswith('os_'):
                os_profiles[group] = group_data

        return os_profiles, 200


    def post(self):
        """
        Payload expected:
        {
          "os_ubuntu_24.04_A":
            hosts: [],
            vars: {
                {
                    "os_operating_system...
                    ...
                }
            }
        }
        """
        data = request.get_json(force=True, silent=True)
        inventory = load_inventory()

        os_profile_skeleton = {
            "os_operating_system": {
                "distribution": "ubuntu",
                "distribution_version": "24.04",
                "distribution_major_version": "24"
            },
            "os_keyboard_layout": "us",
            "os_system_language": "en_US.UTF-8",
            "os_firewall": True,
            "os_access_control": "enforcing",
            "os_admin_password_sha512": "",
            "os_admin_ssh_keys": [],
            "os_partitioning": "",
            "os_kernel_parameters": "nomodeset"
            }

        for os_profile, os_profile_data in data.items():
            if not os_profile.startswith('os_'):
                return {"status": "Error", "message": "The emperor says: OS profile names must start with os_ prefix"}, 200
            os_profile_data_buffer = {}
            if 'hosts' not in os_profile_data:
                os_profile_data_buffer['hosts'] = []
            else:
                os_profile_data_buffer['hosts'] = os_profile_data['hosts']
            if 'vars' not in os_profile_data:
                os_profile_data_buffer['vars'] = os_profile_skeleton
            else:
                os_profile_data_buffer['vars'] = os_profile_skeleton | os_profile_data['vars']
            inventory.add_group(os_profile, os_profile_data_buffer)

        inventory.save()
        return {"status": "OK", "message": "The emperor says: OS profile added"}, 200


class OSProfileResource(Resource):


    def get(self, os_profile_name):

        inventory = load_inventory()
        os_profiles = {}
        for group, group_data in inventory.get_groups().items():
            if group.startswith('os_'):
                os_profiles[group] = group_data
        if os_profile_name not in os_profiles:
            return {"status": "Error", "message": "The emperor says: OS profile not found"}, 400

        return os_profiles[os_profile_name], 200


    def put(self, os_profile_name):
        """
        Payload expected:
          {
            hosts: [],
            vars: {
                {
                    "os_operating_system...
                    ...
                }
            }
          }
        """

        data = request.get_json(force=True, silent=True)

        inventory = load_inventory()
        os_profiles = {}
        for group, group_data in inventory.get_groups().items():
            if group.startswith('os_'):
                os_profiles[group] = group_data
        if os_profile_name not in os_profiles:
            return {"status": "Error", "message": "The emperor says: OS profile not found"}, 400

        inventory.update_group(os_profile_name, data.get('hosts', []), data.get('vars', {}))
        inventory.save()

        return {"status": "OK", "message": "The emperor says: Group updated"}, 200


    def delete(self, os_profile_name: str):

        inventory = load_inventory()
        os_profiles = {}
        for group, group_data in inventory.get_groups().items():
            if group.startswith('os_'):
                os_profiles[group] = group_data
        if os_profile_name not in os_profiles:
            return {"status": "Error", "message": "The emperor says: OS profile not found"}, 400

        inventory.delete_group(os_profile_name)
        inventory.save()

        return {"status": "OK", "message": "The emperor says: Group delete"}, 200


api.add_resource(OSProfilesRootResource, "/api/v1/inventory/os_profiles")
api.add_resource(OSProfileResource, "/api/v1/inventory/os_profile/<string:os_profile_name>")

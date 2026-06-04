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
    "inventory_network_api",
    __name__,
    template_folder="templates",
)
api = Api(blueprint)

def load_inventory() -> AnsibleInventory:
    cfg = current_app.config.get("MAIN_CONFIG", {})
    inventory = AnsibleInventory(
        inventories_root=cfg.get("inventories_root"),
        inventory_name=cfg.get("inventory_name"),
        working_folder=cfg.get("working_folder"),
        diff=True,
        check=False,
        logger=current_app.logger)
    # inventory.show()
    return inventory

def init_plugin():
    print("COUCOU")
    return True


class NetworkListResource(Resource):
    def get(self):
        inventory = load_inventory()
        networks = inventory.get_group('all', {}).get('vars', {}).get('plugin_networks', {}).get('networks', {})
        return networks

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
                "message": "The emperor says: payload must be a non-empty object",
            }, 400
        if not 'subnet' in data or not 'prefix' in data:
            return {
                "status": "error",
                "message": "The emperor says: networks must contains at least a prefix and a subnet",
            }, 400

        inventory = load_inventory()

        # Make sure networks entry exists
        all_group_vars = inventory.get_group('all', {}).get('vars', {})
        if not 'plugin_networks' in all_group_vars:
            all_group_vars['plugin_networks'] = {}
        if not 'networks' in all_group_vars['plugin_networks']:
            all_group_vars['plugin_networks']['networks'] = {}
        

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


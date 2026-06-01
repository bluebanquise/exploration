from flask import Blueprint, request
from flask_restful import Api, Resource
from common.plugin_loader import load_plugin

blueprint = Blueprint("inventory_host_api", __name__)
api = Api(blueprint)


# -------------------------
# /api/v1/inventory/host
# -------------------------

class HostList(Resource):
    def get(self):
        plugin = load_plugin("inventory", "host")
        return plugin.execute("list", {})

    def post(self):
        payload = request.get_json() or {}
        plugin = load_plugin("inventory", "host")
        return plugin.execute("add", {"hosts": payload})


# -------------------------
# /api/v1/inventory/host/<hostname>
# -------------------------

class HostItem(Resource):
    def get(self, hostname):
        plugin = load_plugin("inventory", "host")
        return plugin.execute("get", {"hostname": hostname})

    def put(self, hostname):
        payload = request.get_json() or {}
        plugin = load_plugin("inventory", "host")
        return plugin.execute("update", {"hostname": hostname, "data": payload})

    def delete(self, hostname):
        plugin = load_plugin("inventory", "host")
        return plugin.execute("delete", {"hostname": hostname})


# -------------------------
# Resource registration
# -------------------------

api.add_resource(HostList, "/api/v1/inventory/host")
api.add_resource(HostItem, "/api/v1/inventory/host/<string:hostname>")

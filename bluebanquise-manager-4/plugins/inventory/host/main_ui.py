# from flask import Blueprint, jsonify
# from . import logic

# from core.utils import say_hello

# bp = Blueprint("inventory_hosts", __name__, url_prefix="/inventory/hosts")

# @bp.get("/list")
# def list_hosts():
#     logic.node_add("foo")
#     say_hello()
#     return jsonify({"hosts": ["c001", "c002", "c003"]})

from flask import Blueprint, request, jsonify, current_app
from flask_restful import Resource, Api, reqparse, abort
from . import logic

# Flask setup
bp = Blueprint('hosts', __name__)
api = Api(bp)


@bp.get("/inventory/hosts/index")
def list_hosts():
    return jsonify({"hosts": ["c001", "c002", "c003"]})

class NodeListResource(Resource):
    def get(self):
        print(current_app.config["PLUGIN_METADATA"])
        return logic.get_hosts()

    def post(self):
        new_node = request.get_json(force=True)
        hosts_list = load_yaml()
        node_name = new_node.pop('name')
        if node_name in hosts_list:
            return {'message': 'Node already in the inventory', 'node': node_name}, 409
        if 'fn_group' in new_node or 'hw_group' in new_node or 'os_group' in new_node:
            groups_list_hosts = read_INI(INI_hosts_GROUPS)
            for group_prefix in ['fn_', 'os_', 'hw_']:
                if str(group_prefix + 'group') in new_node:
                    group = new_node.pop(str(group_prefix + 'group'))
                    if group not in groups_list_hosts:
                        return {'message': 'Node group doesnt exist', 'group': group, 'node': node_name}, 404
                    groups_list_hosts[group].append(node_name)
            write_INI(groups_list_hosts, INI_hosts_GROUPS)
        hosts_list[node_name] = new_node
        save_yaml(hosts_list)
        return {'message': 'Node added', 'node': node_name}, 201

class NodeResource(Resource):

    def get(self, node_name):
        # Get node from main list with its parameters
        hosts_list = load_yaml()
        if node_name not in hosts_list:
            abort(404, message="Node not found")
        node = hosts_list[node_name]
        # Now check if node belongs to any group
        groups_list_hosts = read_INI(INI_hosts_GROUPS)
        node_groups = {'fn_group':"", 'os_group':"", 'hw_group':""}
        for group in groups_list_hosts:
            if node_name in groups_list_hosts[group]:
                for group_prefix in ['fn_', 'os_', 'hw_']:
                    if group.startswith(group_prefix):
                        node_groups[str(group_prefix + 'group')] = group
        # Add groups to node returned
        node.update(node_groups)
        return node, 200

    def put(self, node_name):
        updated_node = request.get_json(force=True)
        if 'name' in updated_node:
            del updated_node['name']
        # Get node from main list with its parameters
        hosts_list = load_yaml()
        if node_name not in hosts_list:
            abort(404, message="Node not found")
        # Check if we need to update groups
        # Remember to check for conflicts, so we purge the node from groups when needed
        if 'fn_group' in updated_node or 'hw_group' in updated_node or 'os_group' in updated_node:
            groups_list_hosts = read_INI(INI_hosts_GROUPS)
            for group_prefix in ['fn_', 'os_', 'hw_']:
                if str(group_prefix + 'group') in updated_node:
                    # Purge first from all groups related
                    for group in groups_list_hosts:
                        if group.startswith(group_prefix) and node_name in groups_list_hosts[group]:
                            groups_list_hosts[group].remove(node_name)
                    # Now add to group
                    groups_list_hosts[updated_node.pop(str(group_prefix + 'group'))].append(node_name)
            write_INI(groups_list_hosts, INI_hosts_GROUPS)
        hosts_list[node_name] = updated_node
        save_yaml(hosts_list)
        return {'message': 'Node updated', 'node': node_name}, 200

    def delete(self, node_name):
        hosts_list = load_yaml()
        if node_name not in hosts_list:
            abort(404, message="Node not found")
        # Check if we need to purge groups
        groups_list_hosts = read_INI(INI_hosts_GROUPS)
        for group in groups_list_hosts:
            if node_name in group:
                groups_list_hosts[group].remove(node_name)
        write_INI(groups_list_hosts, INI_hosts_GROUPS)
        # Now delete node from main list and return
        del hosts_list[node_name]
        save_yaml(hosts_list)
        return {'message': 'Node deleted', 'node': node_name}, 200

# Routes
api.add_resource(NodeListResource, '/api/v1/inventory/hosts/')
api.add_resource(NodeResource, '/api/v1/inventory/hosts/<string:node_name>')

# plugins/inventory/host/schema_def.py

from common.schema import schema_registry, Schema

HOST_SCHEMA: Schema = {
    "alias": str,
    "vars": dict,
    "network_interfaces": dict,
    "bmc": {
        "ip": str,
        "user": str,
        "password": str,
    },
}

schema_registry.register("inventory.host", HOST_SCHEMA)

# Import inventory
from core.inventory import Inventory, Host, Group
import json
from . import logic

def init(args, context):
    log = context["logger"]
    dry = context["dry_run"]

    log.debug("Inventory → host plugin started")

    # Load inventory
    inventory = Inventory()

    if len(args) < 2:
        logger.exception(f"This plugin needs at least 2 arguments.")
        sys.exit(1)


    # inventory host add c002
    # inventory host add c002 '{"alias": "foobar"}'
    # inventory host add c002 network_interface eth0
    # inventory host add c002 network_interface eth0 '{"ip4": "10.10.3.2"}'

    # Split args into chuncks
    action = args[0]
    host = args[1]

    # ADD
    if action == "add":

        nested_key = args[2:]
        json_parameter = "{}"
        if len(nested_key) > 0:
            if nested_key[-1].startswith("{"):  # This is a JSON parameter, extract it
                json_parameter = nested_key.pop()

        # Do we work on a host or a key of a host?
        if len(nested_key) == 0:  # We work on a host
            inventory.update_host(host, json.loads(json_parameter), create_host = True)

    print(inventory)


    # path_to_key = None
    # if len(args) > 3:
    #     path_to_key = args[2]

    # if path_to_key is None:
    #     # Means we only create or update a host


    



    # if len(args) < 2:
    #     if args[0] == "get":

    # # Root get
    # print(inventory)
    # if len(args) == 1:
    #     if args[0] == "get":

    # if len(args) >= 2 and args[0] == "get":
    #     host = args[1]
    #     if dry:
    #         log.info(f"[DRY] Would add host: {host}")
    #     else:
    #         log.info(f"Adding host: {host}")
    #         logic.
    #         print(f"host '{host}' added successfully.")
#!/usr/bin/env python3

import os
import sys
import json
import yaml
import argparse

from common import (
    load_config,
    configure_logging,
    load_plugin_module,
)
from inventory import AnsibleInventory


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="BlueBanquise Overlord CLI",
        add_help=False,
    )

    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--yaml", action="store_true", help="Output YAML")
    parser.add_argument("-D", "--diff", action="store_true", help="Show diff when saving")
    parser.add_argument("-c", "--check", action="store_true", help="Dry run, no changes on disk")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "-i",
        "--inventory",
        metavar="INVENTORY_PATH",
        help="Use this inventory root path instead of the one defined in the configuration",
    )
    parser.add_argument(
        "-w",
        "--working-folder",
        metavar="WORKING_FOLDER",
        help="Use this working folder instead of the one defined in the configuration",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Show help relative to the remaining command",
    )

    # Everything after the known options: section plugin action...
    known, remaining = parser.parse_known_args(argv)

    return parser, known, remaining


def print_main_help():
    print(
        """Usage:
  bluebanquise-overlord.py [GLOBAL_OPTIONS] SECTION PLUGIN [ACTION ...]

Global options:
  -D, --diff              Show a diff when something is saved on disk (unix patch format)
  -c, --check             Dry run, do not save anything on disk
  -d, --debug             Enable debug logging
  -h, --help              Show this help or plugin-specific help
  -i, --inventory PATH    Override inventory root path from configuration
  -w, --working-folder P  Override working folder path from configuration

Example:
  bluebanquise-overlord.py inventory host list
  bluebanquise-overlord.py inventory host add c001 '{"alias": "compute-1"}'
"""
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser, global_args, remaining = parse_args(argv)

    # Load configuration
    config_path = os.environ.get("OVERLORD_CONFIG", "bluebanquise-overlord.yml")
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    log_level = "DEBUG" if global_args.debug else config.get("log_level", "INFO")
    logger = configure_logging(config.get("log_file"), log_level)
    logger.debug("Starting Overlord CLI")

    inventory_root = global_args.inventory or config.get("inventory_path")
    working_folder = global_args.working_folder or config.get("working_folder")

    if not inventory_root:
        print("No inventory_path defined (config or CLI)", file=sys.stderr)
        return 1
    if not working_folder:
        print("No working_folder defined (config or CLI)", file=sys.stderr)
        return 1

    if len(remaining) < 2:
        if global_args.help:
            print_main_help()
            return 0
        print("Missing SECTION and PLUGIN. Use --help for usage.", file=sys.stderr)
        return 1

    section = remaining[0]
    plugin_name = remaining[1]
    action_args = remaining[2:]

    if global_args.help and not action_args:
        # Show basic plugin invocation usage
        print(
            f"Plugin usage:\n  bluebanquise-overlord.py {section} {plugin_name} [ACTION ...]\n"
        )
        return 0

    # Load inventory
    inventory = AnsibleInventory(
        inventory_root=inventory_root,
        working_folder=working_folder,
        diff=global_args.diff,
        check=global_args.check,
        logger=logger,
    )

    # inventory.show()

    # Load plugin
    plugins_path = config.get("plugins_path", "./plugins")
    plugin_main_path = os.path.join(plugins_path, section, plugin_name, "main.py")
    if not os.path.isfile(plugin_main_path):
        print(
            f"Plugin not found: section={section}, plugin={plugin_name}, path={plugin_main_path}",
            file=sys.stderr,
        )
        return 1

    module_name = f"plugins.{section}.{plugin_name}.main"
    plugin_module = load_plugin_module(plugin_main_path, module_name)

    if not hasattr(plugin_module, "Plugin"):
        print(f"Plugin module {module_name} does not define class Plugin", file=sys.stderr)
        return 1

    PluginClass = plugin_module.Plugin

    global_context = {
        "diff": global_args.diff,
        "check": global_args.check,
        "debug": global_args.debug,
        "inventory_root": inventory_root,
        "working_folder": working_folder,
        "section": section,
        "plugin": plugin_name,
        "config": config,
    }

    # Load plugin config.yml if present
    plugin_config_path = os.path.join(
        plugins_path, section, plugin_name, "config.yml"
    )
    plugin_config = {}
    if os.path.isfile(plugin_config_path):
        plugin_config = load_yaml_file(plugin_config_path) or {}

    plugin_instance = PluginClass(
        action_args=action_args,
        inventory=inventory,
        config=plugin_config,
        logger=logger,
        global_args=global_context,
    )

    result = plugin_instance.run()

    if isinstance(result, dict):
        status = result.get("status", "ok")
        message = result.get("message")
        data = result.get("data")

        if status != "ok":
            print(f"ERROR: {message or 'Unknown error'}", file=sys.stderr)
            return 1

        # If user requested JSON
        if global_args.json:
            print(json.dumps(result, indent=2))
            return 0

        # If user requested YAML
        if global_args.yaml:
            print(yaml.safe_dump(result, sort_keys=False))
            return 0

        # Default behavior
        if message:
            print(message)
        if data is not None:
            print(json.dumps(data, indent=2))
        return 0

    # Fallback for non-dict results
    print(json.dumps(result, indent=2))
    return 0



if __name__ == "__main__":
    sys.exit(main())

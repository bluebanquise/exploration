#!/usr/bin/env python3
import sys
import importlib
import logging
import argparse
import yaml
from pathlib import Path
from flask import Flask

PLUGIN_ROOT = Path(__file__).parent / "plugins"


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def configure_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("bluebanquise-manager-ui")


# ---------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------
def load_yaml_config(path: str | None):
    if not path:
        return {}

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------
# Plugin discovery
# ---------------------------------------------------------
def discover_plugins():
    """
    Returns a list of plugin paths like:
    [("inventory", "nodes"), ("monitoring", "healthcheck")]
    """
    plugins = []

    for category in PLUGIN_ROOT.iterdir():
        if not category.is_dir():
            continue

        for plugin in category.iterdir():
            if not plugin.is_dir():
                continue

            plugins.append((category.name, plugin.name))

    return plugins


def discover_plugin_ui_files():
    """
    Returns dotted module paths for all main_ui.py files.
    """
    ui_modules = []

    for category, plugin in discover_plugins():
        ui_file = PLUGIN_ROOT / category / plugin / "main_ui.py"
        if ui_file.exists():
            module_path = ".".join(["plugins", category, plugin, "main_ui"])
            ui_modules.append(module_path)

    return ui_modules


# ---------------------------------------------------------
# Metadata loader
# ---------------------------------------------------------
def load_plugin_metadata(category, plugin):
    """
    Load metadata.yaml for a specific plugin.
    """
    metadata_file = PLUGIN_ROOT / category / plugin / "metadata.yaml"

    if not metadata_file.exists():
        return {}

    try:
        with open(metadata_file, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise RuntimeError(
            f"Failed to load metadata.yaml for plugin {category}/{plugin}: {e}"
        )


def load_all_metadata(logger):
    """
    Load metadata.yaml for all plugins and return a dict:
    {
        "inventory/nodes": {...},
        "monitoring/healthcheck": {...}
    }
    """
    metadata_registry = {}

    for category, plugin in discover_plugins():
        try:
            metadata = load_plugin_metadata(category, plugin)
            key = f"{category}/{plugin}"
            metadata_registry[key] = metadata
            logger.info(f"Loaded metadata for {key}: {metadata}")
        except Exception as e:
            logger.error(e)

    return metadata_registry


# ---------------------------------------------------------
# Blueprint loader
# ---------------------------------------------------------
def load_blueprint(module_path, logger):
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        logger.error(f"Failed to import {module_path}: {e}")
        return None

    if not hasattr(module, "bp"):
        logger.error(f"Module {module_path} has no 'bp' Blueprint")
        return None

    return getattr(module, "bp")


# ---------------------------------------------------------
# Main server
# ---------------------------------------------------------
def create_app(config, logger):
    app = Flask(__name__)

    # Load all plugin metadata and store globally
    metadata_registry = load_all_metadata(logger)
    app.config["PLUGIN_METADATA"] = metadata_registry
    app.config["MANAGER_CONFIG"] = {
        "YAML_NODES_DB": 'inventory/cluster/nodes.yml',
        "INI_NODES_GROUPS": 'inventory/cluster/groups'
    }

    # Load UI modules
    ui_modules = discover_plugin_ui_files()
    logger.info(f"Discovered UI modules: {ui_modules}")

    for module_path in ui_modules:
        bp = load_blueprint(module_path, logger)
        if bp:
            app.register_blueprint(bp)
            logger.info(f"Registered blueprint from {module_path}")

    @app.get("/")
    def index():
        return {
            "service": "bluebanquise-manager-ui",
            "plugins_loaded": ui_modules,
            "metadata": metadata_registry,
        }

    return app


# ---------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="BlueBanquise Manager UI — REST API for plugins"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, help="Path to YAML configuration file")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")

    args = parser.parse_args()

    logger = configure_logging(args.debug)
    logger.debug("Debug mode enabled")

    try:
        config = load_yaml_config(args.config)
        logger.debug(f"Loaded configuration: {config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    app = create_app(config, logger)

    logger.info(f"Starting BlueBanquise Manager UI on {args.host}:{args.port}")
    logger.info("URLs map:")
    logger.info(app.url_map)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

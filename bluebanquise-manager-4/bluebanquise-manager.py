#!/usr/bin/env python3
import sys
import importlib
import logging
import argparse
import yaml
from pathlib import Path

# Root directory for plugins, relative to this script, for now
PLUGIN_ROOT = Path(__file__).parent / "plugins"


# #########################################################
# Logging configuration
# ###############

def configure_logging(debug: bool):
    """
    Configure global logging. Debug mode enables verbose logging.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("bluebanquise-manager")


# #########################################################
# Main CLI
# ###############

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="BlueBanquise Manager — Modular CLI")

    # Global flags
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to YAML configuration file")

    # Plugin path
    parser.add_argument("category", help="Plugin category (e.g., inventory, monitoring)")
    parser.add_argument("plugin", help="Plugin name (e.g., nodes, healthcheck)")
    parser.add_argument("plugin_args", nargs=argparse.REMAINDER, help="Arguments for the plugin")

    args = parser.parse_args()

    # Configure logging
    logger = configure_logging(args.debug)
    logger.debug("Debug mode enabled")

    # Load global YAML config
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {args.config}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        if config:
            logger.debug(f"Loaded configuration: {config}")
        else:
            logger.debug("No configuration loaded or configuration file empty")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Check plugin existence
    logger.debug("Check plugin existence")
    plugin_path = PLUGIN_ROOT.joinpath(args.category, args.plugin)
    if not Path(plugin_path, "main.py").exists():
        logger.error(f"Plugin '{args.category}/{args.plugin}' not found.")
        sys.exit(1)

    # Import plugin module
    logger.debug("Import plugin module")
    module_path = ".".join(["plugins"] + [args.category, args.plugin] + ["main"])
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        logger.exception(f"Failed to load plugin module '{module_path}': {e}")
        sys.exit(1)

    # Load plugin metadata from metadata.yaml from the plugin directory if present.
    logger.debug("Load plugin metadata")
    plugin_path = PLUGIN_ROOT.joinpath(args.category, args.plugin)
    metadata_file = Path(plugin_path, "metadata.yaml")
    try:
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)
        if metadata:
            logger.info(f"Loaded plugin metadata: {metadata}")
        else:
            logger.debug(
                f"No metadata.yaml found for plugin '{args.category}/{args.plugin}'"
            )
    except Exception as e:
        raise RuntimeError(f"Failed to load metadata.yaml for plugin")
        logger.error(e)
        sys.exit(1)

    # Ensure plugin has an init() function
    logger.debug("Ensure plugin has an init() function")
    if not hasattr(module, "init"):
        logger.error(
            f"Plugin '{args.category}/{args.plugin}' has no init(args, context) function."
        )
        sys.exit(1)

    # Build context dictionary passed to plugin
    logger.debug("Build context dictionary passed to plugin")
    plugin_logger = logging.getLogger(f"plugin.{args.category}.{args.plugin}")
    context = {
        "debug": args.debug,
        "dry_run": args.dry_run,
        "config": config,
        "metadata": metadata,
        "logger": plugin_logger,
    }

    # Execute plugin
    try:
        logger.info(
            f"Executing plugin '{args.category}/{args.plugin}' "
            f"with args: {args.plugin_args}"
        )
        module.init(args.plugin_args, context)
    except Exception as e:
        logger.exception(f"Plugin execution failed: {e}")
        sys.exit(1)


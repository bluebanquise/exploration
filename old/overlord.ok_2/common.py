# common.py

import os
import sys
import yaml
import logging
import configparser
import importlib.util
from typing import Any, Dict, List, Tuple

from flask import render_template


def load_yaml_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump_yaml_file(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_ini_file(path: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(allow_no_value=True, delimiters=("="))
    parser.optionxform = str  # keep case
    with open(path, "r", encoding="utf-8") as f:
        parser.read_file(f)
    return parser


def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    return load_yaml_file(config_path)


def configure_logging(log_file: str = None, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("overlord")
    if logger.handlers:
        # Already configured
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def discover_plugins(plugins_path: str) -> List[Tuple[str, str, str]]:
    """
    Discover plugins.

    Returns a list of tuples: (section, plugin_name, main_path)

    For CLI: we’ll later look for main.py under plugins/<section>/<plugin>/main.py
    """
    found = []
    if not os.path.isdir(plugins_path):
        return found

    for section in os.listdir(plugins_path):
        section_path = os.path.join(plugins_path, section)
        if not os.path.isdir(section_path):
            continue
        for plugin_name in os.listdir(section_path):
            plugin_path = os.path.join(section_path, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            main_path = os.path.join(plugin_path, "main.py")
            if os.path.isfile(main_path):
                found.append((section, plugin_name, main_path))
    return found


def load_plugin_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_merge_ui_skeleton(base: Dict[str, Any], addition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-merge ui_skeleton-like dicts:
    level 0: navbar sections (inventory, production, ...)
    level 1: titles (host, slurm, ...)
    level 2: list of {name, url} entries

    This function mutates base and also returns it.
    """
    for section, content in addition.items():
        if section not in base:
            base[section] = {}
        for title, items in content.items():
            if title not in base[section]:
                base[section][title] = []
            base[section][title].extend(items)
    return base


def overlord_page_render(ui_skeleton, current_section, template_name, **kwargs):
    """
    Render a plugin page that itself extends main.j2.
    ui_skeleton is kept for compatibility if other code still passes it,
    but we no longer render it directly here.
    """
    return render_template(
        template_name,
        current_section=current_section,
        **kwargs,
    )


def load_plugin_metadata(plugin_dir: str) -> Dict[str, Any]:
    """
    Load metadata.yml from a plugin directory.
    Returns {} if the file does not exist.
    """
    path = os.path.join(plugin_dir, "metadata.yml")
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data

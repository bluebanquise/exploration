import os
import importlib.util
import yaml
from typing import Any, Dict, List, Tuple

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

# common/metadata.py

import os
from typing import Any, Dict

import yaml  # you already depend on PyYAML for inventory

def load_yaml_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_plugin_metadata(plugin_path: str) -> Dict[str, Any]:
    """
    plugin_path: directory where main.py lives.
    """
    meta_file = os.path.join(plugin_path, "metadata.yml")
    if not os.path.exists(meta_file):
        return {}
    return load_yaml_file(meta_file)

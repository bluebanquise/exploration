# plugin_loader.py

import importlib.util
import os


class PluginNode:
    def __init__(self, name, run, folder):
        self.name = name
        self.run = run
        self.folder = folder  # None for leaf plugins


def load_plugin_file(path):
    module_name = "plugin_" + path.replace("/", "_").replace("\\", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    name = getattr(module, "PLUGIN_NAME", None)
    folder = getattr(module, "PLUGIN_FOLDER", None)
    run = getattr(module, "run", None)

    return name, folder, run


def load_plugins(folder):
    """Load all plugins inside a single folder (non-recursive)."""
    nodes = []

    for fname in os.listdir(folder):
        if not fname.endswith(".py"):
            continue

        path = os.path.join(folder, fname)
        name, subfolder, run = load_plugin_file(path)

        if name is None:
            continue

        # Normalize subfolder path if defined
        if subfolder:
            subfolder = os.path.join(folder, subfolder)

        nodes.append(PluginNode(name, run, subfolder))

    return nodes

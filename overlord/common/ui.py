from flask import render_template
from typing import Any, Dict, List, Tuple

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

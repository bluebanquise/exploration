# common/utils.py

from typing import Any, Dict, List, Union


def set_deep_path(root: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set a value in a nested dict using dot-separated path.
    Example: set_deep_path(data, "vars.networks.net-admin.subnet", "10.10.0.0")
    """
    keys: List[str] = path.split(".")
    d: Dict[str, Any] = root
    for key in keys[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge b into a (shallow copy), recursively for nested dicts.
    Values in b override values in a.
    """
    result: Dict[str, Any] = dict(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def deep_diff(a: Any, b: Any) -> Any:
    """
    Return a structure describing differences between a and b.

    For dicts:
      - keys only in b → {"added": value}
      - keys only in a → {"removed": value}
      - keys in both → recurse, only include if different

    For scalars:
      - if different → {"from": a, "to": b}
      - if equal → None
    """
    if isinstance(a, dict) and isinstance(b, dict):
        diff: Dict[str, Any] = {}
        keys = set(a.keys()) | set(b.keys())
        for k in keys:
            if k not in a:
                diff[k] = {"added": b[k]}
            elif k not in b:
                diff[k] = {"removed": a[k]}
            else:
                sub = deep_diff(a[k], b[k])
                if sub not in (None, {}):
                    diff[k] = sub
        return diff
    else:
        if a != b:
            return {"from": a, "to": b}
        return None

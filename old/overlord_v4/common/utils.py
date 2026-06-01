# common/utils.py

from typing import Any, Dict, List


# ------------------------------------------------------------
# Deep path setter (already used in your host plugin)
# ------------------------------------------------------------

def set_deep_path(root: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set a value in a nested dict using a dot-separated path.
    Example:
        set_deep_path(data, "vars.networks.admin.ip", "10.0.0.1")
    """
    keys = path.split(".")
    d = root
    for key in keys[:-1]:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value


# ------------------------------------------------------------
# Deep merge
# ------------------------------------------------------------

def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge dict b into dict a.
    Values in b override values in a.
    Returns a new dict (does not mutate inputs).
    """
    result = dict(a)
    for key, value in b.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ------------------------------------------------------------
# Deep diff
# ------------------------------------------------------------

def deep_diff(a: Any, b: Any) -> Any:
    """
    Compute a recursive diff between a and b.

    Returns a structure describing:
      - added keys
      - removed keys
      - changed values

    Examples:
      deep_diff({"x":1}, {"x":2})
        -> {"x": {"from":1, "to":2}}

      deep_diff({"a":1}, {"a":1})
        -> None

      deep_diff({"a":1}, {"a":1, "b":2})
        -> {"b": {"added":2}}
    """
    # Both dicts → recurse
    if isinstance(a, dict) and isinstance(b, dict):
        diff: Dict[str, Any] = {}
        keys = set(a.keys()) | set(b.keys())

        for key in keys:
            if key not in a:
                diff[key] = {"added": b[key]}
            elif key not in b:
                diff[key] = {"removed": a[key]}
            else:
                sub = deep_diff(a[key], b[key])
                if sub not in (None, {}):
                    diff[key] = sub

        return diff or None

    # Scalars → compare directly
    if a != b:
        return {"from": a, "to": b}

    return None

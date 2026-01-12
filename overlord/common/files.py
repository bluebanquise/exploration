import yaml
import configparser
import os
from typing import Any, Dict, List, Tuple

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
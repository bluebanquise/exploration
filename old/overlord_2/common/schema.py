# common/schema.py

from typing import Any, Dict
from .errors import ValidationError

Schema = Dict[str, Any]


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: Dict[str, Schema] = {}

    def register(self, name: str, schema: Schema) -> None:
        self._schemas[name] = schema

    def get(self, name: str) -> Schema:
        return self._schemas[name]


schema_registry = SchemaRegistry()


def validate_schema(data: Any, schema: Schema, path: str = "") -> None:
    """
    Very simple schema validator.

    - schema is a dict mapping keys -> type or nested schema
    - supported types: str, int, dict, nested dict
    - currently treats all keys as optional (no required enforcement yet)
    """
    if not isinstance(data, dict):
        raise ValidationError(f"{path or 'root'} must be a mapping")

    for key, rule in schema.items():
        full_path = f"{path}.{key}" if path else key
        if key not in data:
            # Optional for now
            continue
        value = data[key]

        if rule is str:
            if not isinstance(value, str):
                raise ValidationError(f"{full_path} must be a string")
        elif rule is int:
            if not isinstance(value, int):
                raise ValidationError(f"{full_path} must be an integer")
        elif rule is dict:
            if not isinstance(value, dict):
                raise ValidationError(f"{full_path} must be a dict")
        elif isinstance(rule, dict):
            if not isinstance(value, dict):
                raise ValidationError(f"{full_path} must be a dict")
            validate_schema(value, rule, full_path)
        # You can extend with more types later if needed.

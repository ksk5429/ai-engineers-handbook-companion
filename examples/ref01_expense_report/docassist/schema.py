"""A small JSON Schema validator for the subset of keywords this example uses.

Supported keywords: type, required, properties, additionalProperties (false only),
enum, items, minItems, minimum, minLength, pattern. Anything else in a schema is
reported as unsupported rather than silently ignored, so the validator can never
pass a document because it did not understand a rule.

For full JSON Schema 2020-12 support, use the third-party `jsonschema` package.
"""

from __future__ import annotations

import re
from typing import Any

SUPPORTED = {
    "$schema", "title", "description", "type", "required", "properties",
    "additionalProperties", "enum", "items", "minItems", "minimum",
    "minLength", "pattern",
}

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}


def _type_ok(value: Any, expected: str) -> bool:
    # bool is a subclass of int in Python, so exclude it from number types.
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[expected])


# --8<-- [start:validate]
def validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Return a list of error messages; an empty list means the value is valid."""
    errors: list[str] = []
    unknown = set(schema) - SUPPORTED
    if unknown:
        return [f"{path}: unsupported schema keyword(s) {sorted(unknown)}"]

    expected = schema.get("type")
    if expected and not _type_ok(value, expected):
        return [f"{path}: expected {expected}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than {schema['minLength']} characters")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if _type_ok(value, "number") and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: {value} is below the minimum {schema['minimum']}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field '{key}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unexpected field '{key}'")
        for key, sub in props.items():
            if key in value:
                errors.extend(validate(value[key], sub, f"{path}.{key}"))

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
    return errors
# --8<-- [end:validate]

#!/usr/bin/env python3

import json
import re
import sys

import jsonschema

_IDENTIFIER_PATTERN = "^[a-z_A-Z][0-9a-z_A-Z]*$"

_OPTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "go_package": {"type": "string"},
    },
    "required": ["go_package"],
    "additionalProperties": False,
}

_RPC_SCHEMA = {
    "type": "object",
    "properties": {
        "requestType": {"type": "string", "pattern": _IDENTIFIER_PATTERN},
        "responseType": {"type": "string", "pattern": _IDENTIFIER_PATTERN},
    },
    "required": ["requestType", "responseType"],
    "additionalProperties": False,
}

_SERVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "methods": {
            "type": "object",
            "patternProperties": {_IDENTIFIER_PATTERN: _RPC_SCHEMA},
            "additionalProperties": False,
        },
    },
    "required": ["methods"],
    "additionalProperties": False,
}

_FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "rule": {"constant": "repeated"},
        "type": {
            "anyOf": [
                {"enum": ["uint32", "bool", "string"]},
                {
                    "type": "string",
                    "pattern": "^(lq\\.)?[a-z_A-Z][0-9a-z_A-Z]*$",
                },
            ],
        },
        "id": {"type": "integer", "minimum": 1},
    },
    "required": ["type", "id"],
    "additionalProperties": False,
}

_MESSAGE_SCHEMA = {
    "$dynamicAnchor": "message",
    "type": "object",
    "properties": {
        "fields": {
            "type": "object",
            "patternProperties": {_IDENTIFIER_PATTERN: _FIELD_SCHEMA},
            "additionalProperties": False,
        },
        "nested": {
            "type": "object",
            "patternProperties": {
                _IDENTIFIER_PATTERN: {"$dynamicRef": "#message"},
            },
            "additionalProperties": False,
        },
    },
    "required": ["fields"],
    "additionalProperties": False,
}

_ENUM_SCHEMA = {
    "type": "object",
    "properties": {
        "values": {
            "type": "object",
            "patternProperties": {_IDENTIFIER_PATTERN: {"type": "integer"}},
            "additionalPattern": False,
        },
    },
    "required": ["values"],
    "additionalProperties": False,
}

_LQ_SCHEMA = {
    "type": "object",
    "patternProperties": {
        _IDENTIFIER_PATTERN: {
            "oneOf": [_SERVICE_SCHEMA, _MESSAGE_SCHEMA, _ENUM_SCHEMA],
        },
    },
    "additionalProperties": False,
}

_SCHEMA = {
    "type": "object",
    "properties": {
        "nested": {
            "type": "object",
            "properties": {
                "lq": {
                    "type": "object",
                    "properties": {
                        "options": _OPTIONS_SCHEMA,
                        "nested": _LQ_SCHEMA,
                    },
                    "required": ["nested"],
                    "additionalProperties": False,
                },
            },
            "required": ["lq"],
            "additionalProperties": False,
        },
    },
    "required": ["nested"],
    "additionalProperties": False,
}


def _parse_service(service_name: str, service_spec: dict[str, dict]) -> str:
    result = "service " + service_name + " {\n"
    lines: list[tuple[str, str]] = []
    for method_name, method_spec in service_spec["methods"].items():
        request_type = method_spec["requestType"]
        response_type = method_spec["responseType"]
        lines.append(
            (
                method_name,
                f"  rpc {method_name} ({request_type}) returns ({response_type});",  # noqa: E501
            ),
        )
    lines.sort(key=lambda e: e[0])
    for _, line in lines:
        result += line + "\n"
    result += "}\n"
    return result


def _parse_message(
    indent: int, message_name: str, message_spec: dict[str, dict],
) -> str:
    result = (" " * indent) + "message " + message_name + " {\n"
    lines = []
    for field_name, field_spec in message_spec["fields"].items():
        line = " " * (indent + 2)
        if "rule" in field_spec:
            assert field_spec["rule"] == "repeated"
            line += "repeated "
        _type = field_spec["type"]
        _type = re.sub("^lq\\.", "", _type)
        _id = field_spec["id"]
        line += f"{_type} {field_name} = {_id};"
        lines.append((_id, line))
    lines.sort(key=lambda e: e[0])
    for _, line in lines:
        result += line + "\n"
    if "nested" in message_spec:
        for _message_name, _message_spec in message_spec["nested"].items():
            result += _parse_message(indent + 2, _message_name, _message_spec)
    result += (" " * indent) + "}\n"
    return result


def _parse_enum(enum_name: str, enum_spec: dict[str, dict]) -> str:
    result = "enum " + enum_name + " {\n"
    lines = []
    for name, value in enum_spec["values"].items():
        line = f"  {name} = {value};"
        lines.append((value, line))
    lines.sort(key=lambda e: e[0])
    for _, line in lines:
        result += line + "\n"
    result += "}\n"
    return result


def _parse() -> None:
    input_text = sys.stdin.read()
    liqi_json = json.loads(input_text)

    jsonschema.validate(instance=liqi_json, schema=_SCHEMA)

    print('syntax = "proto3";\n\npackage lq;\n')

    liqi_json = liqi_json["nested"]["lq"]["nested"]

    services = []
    for key, value in liqi_json.items():
        if "methods" in value:
            service = _parse_service(key, value)
            services.append((key, service))
    services.sort(key=lambda e: e[0])
    for _, service in services:
        print(service, end="")

    messages = []
    for key, value in liqi_json.items():
        if "fields" in value:
            message = _parse_message(0, key, value)
            messages.append((key, message))
    messages.sort(key=lambda e: e[0])
    for _, message in messages:
        print(message, end="")

    enums = []
    for key, value in liqi_json.items():
        if "values" in value:
            enum = _parse_enum(key, value)
            enums.append((key, enum))
    enums.sort(key=lambda e: e[0])
    for _, enum in enums:
        print(enum, end="")


if __name__ == "__main__":
    _parse()
    sys.exit(0)

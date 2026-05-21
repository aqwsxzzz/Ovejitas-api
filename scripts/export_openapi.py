"""Export the FastAPI OpenAPI schema + per-tag YAML for agents and codegen.

Source of truth is the running FastAPI app; this script imports it and calls
`app.openapi()`. Re-run whenever routes or schemas change — the pre-commit hook
handles this automatically. Outputs:

- openapi.json                full spec (used by @hey-api/openapi-ts)
- docs/api/INDEX.yaml         resource index
- docs/api/{tag}.yaml         per-resource agent-readable spec, with enum
                              values inlined and referenced types expanded
                              under a `types:` section.

YAML is used over markdown for ~40% lower token cost while keeping the
structure parseable by both humans and LLM agents.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ovejitas.main import app  # noqa: E402

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


class _Flow(dict[str, Any]):
    """Dict rendered in YAML flow style (one line)."""


class _FlowList(list[Any]):
    """List rendered in YAML flow style (one line)."""


def _flow_dict_rep(dumper: yaml.Dumper, data: _Flow) -> yaml.MappingNode:
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)


def _flow_list_rep(dumper: yaml.Dumper, data: _FlowList) -> yaml.SequenceNode:
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


yaml.add_representer(_Flow, _flow_dict_rep)
yaml.add_representer(_FlowList, _flow_list_rep)


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _describe(schema: dict[str, Any], components: dict[str, Any]) -> str:
    """One-line type description. Enum refs inline values; object refs keep their name."""
    if "$ref" in schema:
        name = _ref_name(schema["$ref"])
        ref_schema = components.get("schemas", {}).get(name, {})
        if "enum" in ref_schema:
            return " | ".join(str(v) for v in ref_schema["enum"])
        return name
    type_ = schema.get("type")
    if type_ == "array":
        return f"{_describe(schema.get('items', {}), components)}[]"
    if "anyOf" in schema:
        return " | ".join(_describe(s, components) for s in schema["anyOf"])
    if type_ == "string" and "format" in schema:
        return f"string ({schema['format']})"
    return type_ or "any"


def _fields_to_dict(schema: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    """Map of property name → type string, or flow-dict if a description exists."""
    if "$ref" in schema:
        schema = components.get("schemas", {}).get(_ref_name(schema["$ref"]), {})
    fields: dict[str, Any] = {}
    for name, spec in schema.get("properties", {}).items():
        type_str = _describe(spec, components)
        if desc := spec.get("description"):
            fields[name] = _Flow({"type": type_str, "desc": desc})
        else:
            fields[name] = type_str
    return fields


def _collect_refs(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        if "$ref" in node:
            out.add(_ref_name(node["$ref"]))
        for v in node.values():
            _collect_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_refs(v, out)


def _transitive_refs(seed: set[str], components: dict[str, Any]) -> set[str]:
    found = set(seed)
    queue = list(seed)
    while queue:
        name = queue.pop()
        schema = components.get("schemas", {}).get(name, {})
        sub: set[str] = set()
        _collect_refs(schema, sub)
        for dep in sub:
            if dep not in found:
                found.add(dep)
                queue.append(dep)
    return found


def _op_to_dict(
    path: str, method: str, op: dict[str, Any], components: dict[str, Any]
) -> dict[str, Any]:
    entry: dict[str, Any] = {"method": method.upper(), "path": path}
    if summary := op.get("summary"):
        entry["summary"] = summary
    if desc := op.get("description"):
        entry["description"] = desc

    body_schema = (
        op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    )
    if body_schema:
        name = _ref_name(body_schema.get("$ref", ""))
        entry["body"] = name or _describe(body_schema, components)

    responses: dict[str, str] = {}
    for code, resp in sorted((op.get("responses") or {}).items()):
        rschema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        responses[code] = _ref_name(rschema.get("$ref", "")) or _describe(rschema, components)
    if responses:
        entry["responses"] = _Flow(responses)
    return entry


def _type_to_dict(schema: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    if "enum" in schema:
        return {"kind": "enum", "values": _FlowList(schema["enum"])}
    entry: dict[str, Any] = {"kind": "object"}
    required = schema.get("required") or []
    if required:
        entry["required"] = _FlowList(required)
    fields = _fields_to_dict(schema, components)
    if fields:
        entry["fields"] = fields
    return entry


def _group_by_tag(
    schema: dict[str, Any],
) -> dict[str, list[tuple[str, str, dict[str, Any]]]]:
    grouped: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for path, methods in schema.get("paths", {}).items():
        for method, op in methods.items():
            if method not in HTTP_METHODS:
                continue
            for tag in op.get("tags") or ["untagged"]:
                grouped.setdefault(tag, []).append((path, method, op))
    return grouped


def _dump(data: Any) -> str:
    result: str = yaml.dump(data, sort_keys=False, allow_unicode=True, width=120)
    return result


def main() -> None:
    schema = app.openapi()
    repo_root = Path(__file__).resolve().parent.parent

    full = repo_root / "openapi.json"
    full.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {full.relative_to(repo_root)}")

    api_dir = repo_root / "docs" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    for stale in [*api_dir.glob("*.md"), *api_dir.glob("*.yaml")]:
        stale.unlink()

    grouped = _group_by_tag(schema)
    components = schema.get("components", {})

    index = {
        "title": "Ovejitas API",
        "generated_from": "openapi.json",
        "note": "Auto-generated. Do not edit by hand.",
        "resources": [
            {"tag": tag, "file": f"{tag}.yaml", "operations": len(grouped[tag])}
            for tag in sorted(grouped)
        ],
    }
    (api_dir / "INDEX.yaml").write_text(_dump(index))
    print(f"wrote {(api_dir / 'INDEX.yaml').relative_to(repo_root)}")

    for tag, ops in grouped.items():
        operations = [_op_to_dict(path, method, op, components) for path, method, op in ops]
        direct_refs: set[str] = set()
        for _, _, op in ops:
            _collect_refs(op, direct_refs)
        all_refs = _transitive_refs(direct_refs, components)
        # Enums are inlined into _describe wherever referenced, so skip them here.
        types = {
            name: _type_to_dict(components["schemas"][name], components)
            for name in sorted(all_refs)
            if name in components.get("schemas", {}) and "enum" not in components["schemas"][name]
        }

        doc: dict[str, Any] = {"tag": tag, "operations": operations}
        if types:
            doc["types"] = types
        (api_dir / f"{tag}.yaml").write_text(_dump(doc))
        print(f"wrote docs/api/{tag}.yaml")


if __name__ == "__main__":
    main()

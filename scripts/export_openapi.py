"""Export the FastAPI OpenAPI schema + per-tag markdown for agents and codegen.

Source of truth is the running FastAPI app; this script imports it and calls
`app.openapi()`. Re-run whenever routes or schemas change — the pre-commit hook
handles this automatically. Outputs:

- openapi.json                full spec (used by @hey-api/openapi-ts)
- docs/api/INDEX.md           one-line table of resources
- docs/api/{tag}.md           per-resource human/agent-readable markdown
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Make `src/` importable when run directly (no `uv run` needed).
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ovejitas.main import app  # noqa: E402

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _describe(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return _ref_name(schema["$ref"])
    type_ = schema.get("type")
    if type_ == "array":
        return f"{_describe(schema.get('items', {}))}[]"
    if "anyOf" in schema:
        return " | ".join(_describe(s) for s in schema["anyOf"])
    if type_ == "string" and "format" in schema:
        return f"string ({schema['format']})"
    return type_ or "any"


def _fields(schema: dict[str, Any], components: dict[str, Any]) -> list[str]:
    if "$ref" in schema:
        schema = components.get("schemas", {}).get(_ref_name(schema["$ref"]), {})
    required = set(schema.get("required", []))
    lines: list[str] = []
    for name, spec in schema.get("properties", {}).items():
        flag = "required" if name in required else "optional"
        line = f"- `{name}` ({_describe(spec)}, {flag})"
        if desc := spec.get("description"):
            line += f" — {desc}"
        lines.append(line)
    return lines


def _render_op(path: str, method: str, op: dict[str, Any], components: dict[str, Any]) -> str:
    out: list[str] = [f"## {method.upper()} {path}", ""]
    if summary := op.get("summary"):
        out.extend([f"_{summary}_", ""])
    if desc := op.get("description"):
        out.extend([desc, ""])

    body_schema = (
        op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    )
    if body_schema:
        out.append("**Request body:**")
        out.extend(_fields(body_schema, components))
        out.append("")

    if responses := op.get("responses"):
        out.append("**Responses:**")
        for code, resp in sorted(responses.items()):
            rschema = resp.get("content", {}).get("application/json", {}).get("schema", {})
            name = _ref_name(rschema.get("$ref", "")) or _describe(rschema)
            rdesc = resp.get("description", "")
            suffix = f" — {rdesc}" if rdesc and rdesc != name else ""
            out.append(f"- `{code}` → {name}{suffix}")
        out.append("")
    return "\n".join(out)


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


def main() -> None:
    schema = app.openapi()
    repo_root = Path(__file__).resolve().parent.parent

    full = repo_root / "openapi.json"
    full.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {full.relative_to(repo_root)}")

    api_dir = repo_root / "docs" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    for stale in api_dir.glob("*.md"):
        stale.unlink()

    grouped = _group_by_tag(schema)
    components = schema.get("components", {})

    index = [
        "# API Reference",
        "",
        "_Auto-generated from FastAPI. Do not edit by hand._",
        "",
        "Source of truth: [`openapi.json`](../../openapi.json)",
        "",
        "| Resource | Endpoints |",
        "|---|---|",
    ]
    for tag in sorted(grouped):
        index.append(f"| [{tag}](./{tag}.md) | {len(grouped[tag])} |")
    (api_dir / "INDEX.md").write_text("\n".join(index) + "\n")
    print(f"wrote {(api_dir / 'INDEX.md').relative_to(repo_root)}")

    for tag, ops in grouped.items():
        body = [f"# {tag}", "", "_Auto-generated. Do not edit by hand._", ""]
        for path, method, op in ops:
            body.append(_render_op(path, method, op, components))
        (api_dir / f"{tag}.md").write_text("\n".join(body) + "\n")
        print(f"wrote docs/api/{tag}.md")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Leon API — GraphQL Query Validator

Downloads the Leon GraphQL API schema and validates queries against it.

Usage:
  python validate_query.py --dump-schema
  python validate_query.py --query 'query { operator { name subdomain } }'
  python validate_query.py --file my_query.graphql
  echo 'query { operator { name } }' | python validate_query.py

Requirements (auto-installed if missing):
  graphql-core, requests

Environment variables:
  LEON_SCHEMA_URL    — optional schema URL override
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Silent auto-install of missing packages (no user prompts)
# ---------------------------------------------------------------------------

def _ensure_package(import_name: str, pip_name: str) -> None:
    """Installs a package silently if not present."""
    import importlib.util
    if importlib.util.find_spec(import_name) is not None:
        return
    print(f"  [setup] Installing '{pip_name}'...", file=sys.stderr)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_name, "-q", "--disable-pip-version-check"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.exit(
            f"Failed to install '{pip_name}'.\n"
            f"    Install manually: pip install {pip_name}\n"
            f"    {result.stderr.decode().strip()}"
        )
    print(f"  [setup] Installed '{pip_name}'.", file=sys.stderr)


_ensure_package("requests", "requests")
_ensure_package("graphql", "graphql-core")


import requests  # noqa: E402
from graphql import GraphQLSchema, build_client_schema, parse, validate  # noqa: E402
from graphql.error import GraphQLError  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_URL: str = os.getenv(
    "LEON_SCHEMA_URL",
    "http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/schema-beta.json",
)
CACHE_FILE: Path = Path(__file__).parent / ".schema_cache.json"
# ANSI colors — only when stderr is a TTY (does not interfere with --dump-schema on stdout)
_USE_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def GREEN(t: str) -> str:  return _c("32", t)
def RED(t: str) -> str:    return _c("31", t)
def YELLOW(t: str) -> str: return _c("33", t)
def BOLD(t: str) -> str:   return _c("1",  t)
def DIM(t: str) -> str:    return _c("2",  t)


def _err(*args: object) -> None:
    """Prints to stderr (never mixes with --dump-schema on stdout)."""
    print(*args, file=sys.stderr)


# ---------------------------------------------------------------------------
# Schema fetching and parsing
# ---------------------------------------------------------------------------

class SchemaFetchError(RuntimeError):
    pass


def _fetch_raw(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise SchemaFetchError(f"Cannot fetch schema from {url}: {exc}") from exc


def load_schema(*, force_refresh: bool = False) -> tuple[GraphQLSchema, dict]:
    """Returns (parsed GQL schema, raw introspection dict)."""
    if not force_refresh and CACHE_FILE.exists():
        _err(DIM(f"  [schema] Using cache: {CACHE_FILE}"))
        raw = json.loads(CACHE_FILE.read_text())
    else:
        _err(DIM(f"  [schema] Fetching from {SCHEMA_URL} ..."))
        raw = _fetch_raw(SCHEMA_URL)
        CACHE_FILE.write_text(json.dumps(raw))
        _err(DIM(f"  [schema] Saved cache: {CACHE_FILE}"))

    try:
        schema = build_client_schema(raw["data"])
        return schema, raw
    except (KeyError, Exception) as exc:
        if not force_refresh:
            _err(YELLOW("  [schema] Cache corrupted, re-fetching..."))
            CACHE_FILE.unlink(missing_ok=True)
            return load_schema(force_refresh=True)
        raise SchemaFetchError(f"Cannot build schema: {exc}") from exc


# ---------------------------------------------------------------------------
# Schema dump — --dump-schema mode
# ---------------------------------------------------------------------------

def _type_ref_str(type_ref: dict) -> str:
    """Recursively converts typeRef dict to string, e.g. 'String!', '[Flight!]!'."""
    kind = type_ref.get("kind", "")
    name = type_ref.get("name")
    of_type = type_ref.get("ofType")
    if kind == "NON_NULL":
        return f"{_type_ref_str(of_type)}!"
    if kind == "LIST":
        return f"[{_type_ref_str(of_type)}]"
    return name or "?"


def lookup_types(schema_raw: dict, names: list[str]) -> None:
    """Prints type/field definitions from the schema to stdout.

    Supports:
    - type names (e.g. Flight, FlightFilter, CrewMemberOnLeg)
    - root query/mutation field names (e.g. flightList, operator)
    - case-insensitive partial matching when no exact match found
    """
    schema_def = schema_raw.get("data", {}).get("__schema", {})
    types: list[dict] = schema_def.get("types", [])
    query_type_name = (schema_def.get("queryType") or {}).get("name", "Query")
    mutation_type_name = (schema_def.get("mutationType") or {}).get("name", "Mutation")
    types_by_name = {t["name"]: t for t in types}

    root_query = types_by_name.get(query_type_name, {})
    root_mutation = types_by_name.get(mutation_type_name, {})
    root_fields = {f["name"]: ("QUERY", f) for f in (root_query.get("fields") or [])}
    root_fields.update({f["name"]: ("MUTATION", f) for f in (root_mutation.get("fields") or [])})

    output: list[str] = []

    for name in names:
        # 1. Exact match on type name
        if name in types_by_name:
            t = types_by_name[name]
            output.extend(_format_type(t))
            output.append("")
            continue

        # 2. Exact match on root query/mutation field
        if name in root_fields:
            kind, f = root_fields[name]
            args_str = ""
            if f.get("args"):
                args_parts = [f"{a['name']}: {_type_ref_str(a['type'])}" for a in f["args"]]
                args_str = f"({', '.join(args_parts)})"
            ret = _type_ref_str(f["type"])
            desc = f"  # {f['description']}" if f.get("description") else ""
            output.append(f"{kind} FIELD  {f['name']}{args_str}: {ret}{desc}")
            output.append("")
            continue

        # 3. Case-insensitive partial matching
        name_lower = name.lower()
        matched_types = [n for n in types_by_name if name_lower in n.lower() and not n.startswith("__")]
        matched_fields = [n for n in root_fields if name_lower in n.lower()]

        if matched_types or matched_fields:
            output.append(f"# No exact match for '{name}' — showing partial matches:")
            for n in matched_types[:10]:
                t = types_by_name[n]
                output.extend(_format_type(t))
                output.append("")
            for n in matched_fields[:5]:
                kind, f = root_fields[n]
                args_str = ""
                if f.get("args"):
                    args_parts = [f"{a['name']}: {_type_ref_str(a['type'])}" for a in f["args"]]
                    args_str = f"({', '.join(args_parts)})"
                ret = _type_ref_str(f["type"])
                desc = f"  # {f['description']}" if f.get("description") else ""
                output.append(f"{kind} FIELD  {f['name']}{args_str}: {ret}{desc}")
                output.append("")
        else:
            output.append(f"# '{name}' — not found in schema (no type, query, or mutation matches)")
            output.append("")

    print("\n".join(output))


def _format_type(t: dict) -> list[str]:
    """Formats a single type to readable text."""
    lines: list[str] = []
    desc = f"  # {t['description']}" if t.get("description") else ""
    lines.append(f"{t['kind']} {t['name']}{desc} {{")

    if t["kind"] == "ENUM":
        for v in t.get("enumValues") or []:
            vdesc = f"  # {v['description']}" if v.get("description") else ""
            lines.append(f"  {v['name']}{vdesc}")
    elif t["kind"] == "UNION":
        possible = [p["name"] for p in (t.get("possibleTypes") or [])]
        lines.append(f"  = {' | '.join(possible)}")
    else:
        fields = t.get("fields") or t.get("inputFields") or []
        for f in fields:
            fdesc = f"  # {f['description']}" if f.get("description") else ""
            args_str = ""
            if f.get("args"):
                args_parts = [f"{a['name']}: {_type_ref_str(a['type'])}" for a in f["args"]]
                args_str = f"({', '.join(args_parts)})"
            ret = _type_ref_str(f["type"])
            deprecated = "  DEPRECATED" if f.get("isDeprecated") else ""
            lines.append(f"  {f['name']}{args_str}: {ret}{deprecated}{fdesc}")

    lines.append("}")
    return lines


def dump_schema(schema_raw: dict) -> None:
    """Prints a condensed schema summary to stdout for analysis by Claude."""
    schema_def = schema_raw.get("data", {}).get("__schema", {})
    types: list[dict] = schema_def.get("types", [])

    query_type_name = (schema_def.get("queryType") or {}).get("name", "Query")
    mutation_type_name = (schema_def.get("mutationType") or {}).get("name", "Mutation")

    types_by_name = {t["name"]: t for t in types}

    output: list[str] = []

    # --- Root queries ---
    output.append("=== ROOT QUERIES ===")
    root_query = types_by_name.get(query_type_name, {})
    for field in root_query.get("fields") or []:
        args_str = ""
        if field.get("args"):
            args_parts = [
                f"{a['name']}: {_type_ref_str(a['type'])}"
                for a in field["args"]
            ]
            args_str = f"({', '.join(args_parts)})"
        ret = _type_ref_str(field["type"])
        desc = f"  # {field['description']}" if field.get("description") else ""
        output.append(f"  {field['name']}{args_str}: {ret}{desc}")

    # --- Root mutations ---
    output.append("")
    output.append("=== ROOT MUTATIONS ===")
    root_mutation = types_by_name.get(mutation_type_name, {})
    for field in root_mutation.get("fields") or []:
        args_str = ""
        if field.get("args"):
            args_parts = [
                f"{a['name']}: {_type_ref_str(a['type'])}"
                for a in field["args"]
            ]
            args_str = f"({', '.join(args_parts)})"
        ret = _type_ref_str(field["type"])
        desc = f"  # {field['description']}" if field.get("description") else ""
        output.append(f"  {field['name']}{args_str}: {ret}{desc}")

    # --- All non-internal types ---
    output.append("")
    output.append("=== TYPES ===")
    for t in types:
        if t["name"].startswith("__"):
            continue
        if t["kind"] not in ("OBJECT", "INTERFACE", "INPUT_OBJECT", "ENUM", "UNION"):
            continue
        if t["name"] in (query_type_name, mutation_type_name):
            continue
        output.extend(_format_type(t))
        output.append("")

    print("\n".join(output))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationResult(NamedTuple):
    valid: bool
    errors: list[str]


def validate_query_str(schema: GraphQLSchema, query_string: str) -> ValidationResult:
    """Parses and validates a GQL query."""
    try:
        document = parse(query_string)
    except GraphQLError as exc:
        return ValidationResult(valid=False, errors=[f"Parse error: {exc.message}"])

    errors = validate(schema, document)
    if errors:
        return ValidationResult(valid=False, errors=[e.message for e in errors])
    return ValidationResult(valid=True, errors=[])


# ---------------------------------------------------------------------------
# Main validation logic
# ---------------------------------------------------------------------------

def _print_errors(errors: list[str], indent: int = 2) -> None:
    pad = " " * indent
    for err in errors:
        _err(f"{pad}{RED('x')} {err}")


def run(query_string: str, *, force_refresh: bool = False) -> bool:
    """Validates a query. Returns True if query is valid."""
    _err()
    _err(BOLD("--- Leon GQL Validator ---"))
    _err()

    try:
        schema, schema_raw = load_schema(force_refresh=force_refresh)
    except SchemaFetchError as exc:
        _err(RED(f"  {exc}"))
        return False

    _err()
    _err(BOLD("> Validating query..."))
    result = validate_query_str(schema, query_string)

    if result.valid:
        _err(GREEN("  Query is valid."))
        _err()
        print(query_string)
        return True

    _err(RED(f"  Found {len(result.errors)} error(s):"))
    _print_errors(result.errors)
    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validates a GraphQL query against the Leon API schema.",
        epilog=(
            "Examples:\n"
            "  python validate_query.py --dump-schema\n"
            "  python validate_query.py --query 'query { operator { name subdomain } }'\n"
            "  python validate_query.py --file flights.graphql\n"
            "  cat query.graphql | python validate_query.py\n"
            "  python validate_query.py --refresh --query 'query { operator { name } }'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--query",       "-q", metavar="GQL",  help="GraphQL query as a string")
    parser.add_argument("--file",        "-f", metavar="PATH", help="Path to .graphql file")
    parser.add_argument("--dump-schema", "-d", action="store_true",
                        help="Print schema summary to stdout and exit")
    parser.add_argument("--lookup", "-l", metavar="TYPE", nargs="+",
                        help="Print definitions of specific types/fields (e.g. --lookup Flight CrewMemberOnLeg)")
    parser.add_argument("--no-fix",      action="store_true",
                        help="(ignored, kept for backwards compatibility)")
    parser.add_argument("--refresh",     action="store_true",
                        help="Force fresh schema fetch (bypass cache)")

    args = parser.parse_args()

    try:
        schema, schema_raw = load_schema(force_refresh=args.refresh)
    except SchemaFetchError as exc:
        sys.exit(f"  {exc}")

    if args.dump_schema:
        dump_schema(schema_raw)
        return

    if args.lookup:
        lookup_types(schema_raw, args.lookup)
        return

    # Read query
    if args.query:
        query_string = args.query
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            sys.exit(f"  File not found: {path}")
        query_string = path.read_text()
    elif not sys.stdin.isatty():
        query_string = sys.stdin.read()
    else:
        sys.exit(
            "  No query provided. Use --query, --file, --dump-schema, or pipe via stdin.\n"
            "    Example: python validate_query.py --query 'query { operator { name } }'"
        )

    success = run(query_string, force_refresh=False)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

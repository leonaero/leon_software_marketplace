#!/usr/bin/env python3
"""
Leon API — GraphQL Query Validator

Pobiera schemat Leon GraphQL API i waliduje zapytanie.

Użycie:
  python validate_query.py --dump-schema
  python validate_query.py --query 'query { operator { name subdomain } }'
  python validate_query.py --file my_query.graphql
  echo 'query { operator { name } }' | python validate_query.py

Wymagania (instalowane automatycznie):
  graphql-core, requests

Zmienne środowiskowe:
  LEON_SCHEMA_URL    — opcjonalne nadpisanie URL schematu
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Ciche auto-instalowanie brakujących paczek (bez pytania użytkownika)
# ---------------------------------------------------------------------------

def _ensure_package(import_name: str, pip_name: str) -> None:
    """Instaluje pakiet cicho jeśli go nie ma. Nie pyta użytkownika."""
    import importlib.util
    if importlib.util.find_spec(import_name) is not None:
        return
    print(f"  [setup] Instaluję '{pip_name}'...", file=sys.stderr)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_name, "-q", "--disable-pip-version-check"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.exit(
            f"❌  Nie udało się zainstalować '{pip_name}'.\n"
            f"    Zainstaluj ręcznie: pip install {pip_name}\n"
            f"    {result.stderr.decode().strip()}"
        )
    print(f"  [setup] Zainstalowano '{pip_name}'.", file=sys.stderr)


_ensure_package("requests", "requests")
_ensure_package("graphql", "graphql-core")


import requests  # noqa: E402
from graphql import GraphQLSchema, build_client_schema, parse, validate  # noqa: E402
from graphql.error import GraphQLError  # noqa: E402


# ---------------------------------------------------------------------------
# Stałe
# ---------------------------------------------------------------------------

SCHEMA_URL: str = os.getenv(
    "LEON_SCHEMA_URL",
    "http://api-schema-doc.s3-website-eu-west-1.amazonaws.com/schema-beta.json",
)
CACHE_FILE: Path = Path(__file__).parent / ".schema_cache.json"
# Kolory ANSI — tylko gdy stderr jest TTY (nie blokują --dump-schema na stdout)
_USE_COLOR = sys.stderr.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def GREEN(t: str) -> str:  return _c("32", t)
def RED(t: str) -> str:    return _c("31", t)
def YELLOW(t: str) -> str: return _c("33", t)
def BOLD(t: str) -> str:   return _c("1",  t)
def DIM(t: str) -> str:    return _c("2",  t)


def _err(*args: object) -> None:
    """Wypisuje na stderr (nigdy nie miesza się z --dump-schema na stdout)."""
    print(*args, file=sys.stderr)


# ---------------------------------------------------------------------------
# Pobieranie i parsowanie schematu
# ---------------------------------------------------------------------------

class SchemaFetchError(RuntimeError):
    pass


def _fetch_raw(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise SchemaFetchError(f"Nie można pobrać schematu z {url}: {exc}") from exc


def load_schema(*, force_refresh: bool = False) -> tuple[GraphQLSchema, dict]:
    """Zwraca (sparsowany schemat GQL, surowy introspection dict)."""
    if not force_refresh and CACHE_FILE.exists():
        _err(DIM(f"  [schema] Używam cache: {CACHE_FILE}"))
        raw = json.loads(CACHE_FILE.read_text())
    else:
        _err(DIM(f"  [schema] Pobieram z {SCHEMA_URL} …"))
        raw = _fetch_raw(SCHEMA_URL)
        CACHE_FILE.write_text(json.dumps(raw))
        _err(DIM(f"  [schema] Zapisano cache: {CACHE_FILE}"))

    try:
        schema = build_client_schema(raw["data"])
        return schema, raw
    except (KeyError, Exception) as exc:
        if not force_refresh:
            _err(YELLOW("  [schema] Cache uszkodzony, pobieram ponownie…"))
            CACHE_FILE.unlink(missing_ok=True)
            return load_schema(force_refresh=True)
        raise SchemaFetchError(f"Nie można zbudować schematu: {exc}") from exc


# ---------------------------------------------------------------------------
# Dump schematu — tryb --dump-schema
# ---------------------------------------------------------------------------

def _type_ref_str(type_ref: dict) -> str:
    """Rekurencyjnie zamienia typeRef dict na string, np. 'String!', '[Flight!]!'."""
    kind = type_ref.get("kind", "")
    name = type_ref.get("name")
    of_type = type_ref.get("ofType")
    if kind == "NON_NULL":
        return f"{_type_ref_str(of_type)}!"
    if kind == "LIST":
        return f"[{_type_ref_str(of_type)}]"
    return name or "?"


def lookup_types(schema_raw: dict, names: list[str]) -> None:
    """Drukuje na stdout definicje konkretnych typów/pól z schematu.

    Obsługuje:
    - nazwy typów (np. Flight, FlightFilter, CrewMemberOnLeg)
    - nazwy root queries/mutations (np. flightList, operator)
    - wyszukiwanie case-insensitive z częściowym dopasowaniem gdy brak dokładnego trafu
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
        # 1. Dokładne dopasowanie do nazwy typu
        if name in types_by_name:
            t = types_by_name[name]
            output.extend(_format_type(t))
            output.append("")
            continue

        # 2. Dokładne dopasowanie do root query/mutation field
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

        # 3. Case-insensitive częściowe dopasowanie
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
    """Formatuje pojedynczy typ do czytelnej postaci tekstowej."""
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
            deprecated = "  ⚠️ DEPRECATED" if f.get("isDeprecated") else ""
            lines.append(f"  {f['name']}{args_str}: {ret}{deprecated}{fdesc}")

    lines.append("}")
    return lines


def dump_schema(schema_raw: dict) -> None:
    """Drukuje na stdout skondensowane podsumowanie schematu do analizy przez Claude."""
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
# Walidacja
# ---------------------------------------------------------------------------

class ValidationResult(NamedTuple):
    valid: bool
    errors: list[str]


def validate_query_str(schema: GraphQLSchema, query_string: str) -> ValidationResult:
    """Parsuje i waliduje zapytanie GQL."""
    try:
        document = parse(query_string)
    except GraphQLError as exc:
        return ValidationResult(valid=False, errors=[f"Błąd parsowania: {exc.message}"])

    errors = validate(schema, document)
    if errors:
        return ValidationResult(valid=False, errors=[e.message for e in errors])
    return ValidationResult(valid=True, errors=[])


# ---------------------------------------------------------------------------
# Główna logika walidacji
# ---------------------------------------------------------------------------

def _print_errors(errors: list[str], indent: int = 2) -> None:
    pad = " " * indent
    for err in errors:
        _err(f"{pad}{RED('✗')} {err}")


def run(query_string: str, *, force_refresh: bool = False) -> bool:
    """Waliduje zapytanie. Zwraca True jeśli zapytanie jest poprawne."""
    _err()
    _err(BOLD("━━━ Leon GQL Validator ━━━"))
    _err()

    try:
        schema, schema_raw = load_schema(force_refresh=force_refresh)
    except SchemaFetchError as exc:
        _err(RED(f"❌  {exc}"))
        return False

    _err()
    _err(BOLD("▶ Walidacja zapytania…"))
    result = validate_query_str(schema, query_string)

    if result.valid:
        _err(GREEN("✅  Zapytanie jest poprawne."))
        _err()
        print(query_string)
        return True

    _err(RED(f"❌  Znaleziono {len(result.errors)} błąd(ów):"))
    _print_errors(result.errors)
    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Waliduje zapytanie GraphQL względem schematu Leon API.",
        epilog=(
            "Przykłady:\n"
            "  python validate_query.py --dump-schema\n"
            "  python validate_query.py --query 'query { operator { name subdomain } }'\n"
            "  python validate_query.py --file flights.graphql\n"
            "  cat query.graphql | python validate_query.py\n"
            "  python validate_query.py --refresh --query 'query { operator { name } }'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--query",       "-q", metavar="GQL",  help="Zapytanie GraphQL jako string")
    parser.add_argument("--file",        "-f", metavar="PATH", help="Ścieżka do pliku .graphql")
    parser.add_argument("--dump-schema", "-d", action="store_true",
                        help="Wydrukuj podsumowanie schematu na stdout i zakończ")
    parser.add_argument("--lookup", "-l", metavar="TYPE", nargs="+",
                        help="Wydrukuj definicję konkretnych typów/pól (np. --lookup Flight CrewMemberOnLeg)")
    parser.add_argument("--no-fix",      action="store_true",
                        help="(ignorowany, pozostawiony dla kompatybilności wstecznej)")
    parser.add_argument("--refresh",     action="store_true",
                        help="Wymuś pobranie świeżego schematu (ignoruj cache)")

    args = parser.parse_args()

    try:
        schema, schema_raw = load_schema(force_refresh=args.refresh)
    except SchemaFetchError as exc:
        sys.exit(f"❌  {exc}")

    if args.dump_schema:
        dump_schema(schema_raw)
        return

    if args.lookup:
        lookup_types(schema_raw, args.lookup)
        return

    # Odczyt zapytania
    if args.query:
        query_string = args.query
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            sys.exit(f"❌  Plik nie istnieje: {path}")
        query_string = path.read_text()
    elif not sys.stdin.isatty():
        query_string = sys.stdin.read()
    else:
        sys.exit(
            "❌  Brak zapytania. Podaj --query, --file, --dump-schema lub przekaż przez stdin.\n"
            "    Przykład: python validate_query.py --query 'query { operator { name } }'"
        )

    success = run(query_string, force_refresh=False)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
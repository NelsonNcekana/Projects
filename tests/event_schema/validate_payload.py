#!/usr/bin/env python3
"""Validate one JSON payload against event-schema.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    print(
        "Dependency error: 'jsonschema' is not installed.\n"
        "Install it with: pip install jsonschema",
        file=sys.stderr,
    )
    raise SystemExit(3) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a single payload against JSON schema."
    )
    parser.add_argument(
        "--schema",
        default="event-schema.json",
        help="Path to JSON schema file (default: event-schema.json).",
    )
    parser.add_argument(
        "--payload",
        required=True,
        help="Path to payload JSON file to validate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    schema_path = Path(args.schema)
    payload_path = Path(args.payload)

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - script-level failure
        print(f"SCHEMA_LOAD_ERROR: {exc}")
        return 2

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - script-level failure
        print(f"PAYLOAD_LOAD_ERROR: {exc}")
        return 2

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    if errors:
        print("INVALID")
        for idx, err in enumerate(errors, start=1):
            location = ".".join(str(part) for part in err.path) or "$"
            print(f"{idx}. {location}: {err.message}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())

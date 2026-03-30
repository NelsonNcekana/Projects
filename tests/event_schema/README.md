# Event Schema Tests

This folder provides a ready-made validation suite for `event-schema.json`.

## Contents

- `payloads/valid-inquiry.json`: known-good sample payload
- `payloads/invalid-inquiry-missing-response-time.json`: known-bad sample payload
- `validate_event.py`: validate a single JSON payload file against the schema
- `run_event_schema_tests.py`: automated matrix test for all supported event types
- `run_event_schema_tests.sh`: one-command runner for sample + matrix tests

## Quick start

From repo root:

```bash
bash tests/event_schema/run_event_schema_tests.sh
```

## Single payload validation

```bash
python3 tests/event_schema/validate_event.py \
  --schema event-schema.json \
  tests/event_schema/payloads/valid-inquiry.json
```

If invalid, the script prints schema errors and exits with code `1`.

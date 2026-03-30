#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_PATH="${ROOT_DIR}/../../event-schema.json"
VALIDATOR="${ROOT_DIR}/validate_payload.py"
PAYLOADS_DIR="${ROOT_DIR}/payloads"

if [[ ! -f "${SCHEMA_PATH}" ]]; then
  echo "Schema not found at ${SCHEMA_PATH}" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if ! python3 -c "import jsonschema" >/dev/null 2>&1; then
  echo "Installing jsonschema dependency..."
  python3 -m pip install --user jsonschema >/dev/null
fi

run_case() {
  local payload_file="$1"
  local expected="$2"
  local output
  set +e
  output="$(python3 "${VALIDATOR}" --schema "${SCHEMA_PATH}" --payload "${payload_file}" 2>&1)"
  local status=$?
  set -e

  if [[ "${expected}" == "pass" && ${status} -eq 0 ]]; then
    echo "PASS: $(basename "${payload_file}")"
    return 0
  fi

  if [[ "${expected}" == "fail" && ${status} -ne 0 ]]; then
    echo "PASS (expected fail): $(basename "${payload_file}")"
    return 0
  fi

  echo "FAIL: $(basename "${payload_file}") (expected ${expected}, got exit ${status})"
  echo "${output}"
  return 1
}

echo "Running event schema test matrix..."
echo

failures=0

while IFS= read -r -d '' file; do
  if ! run_case "${file}" "pass"; then
    failures=$((failures + 1))
  fi
done < <(find "${PAYLOADS_DIR}/valid" -type f -name "*.json" -print0 | sort -z)

while IFS= read -r -d '' file; do
  if ! run_case "${file}" "fail"; then
    failures=$((failures + 1))
  fi
done < <(find "${PAYLOADS_DIR}/invalid" -type f -name "*.json" -print0 | sort -z)

echo
if [[ ${failures} -eq 0 ]]; then
  echo "All event schema tests passed."
  exit 0
fi

echo "${failures} test(s) failed."
exit 1

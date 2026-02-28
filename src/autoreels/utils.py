from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib import error, parse, request


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-") or "reel"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def check_binary(name: str) -> bool:
    result = subprocess.run(
        ["bash", "-lc", f"command -v {name}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 60,
    retries: int = 2,
    backoff_seconds: float = 1.5,
) -> dict[str, Any]:
    raw = None
    if payload is not None:
        raw = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, method=method, headers=headers or {}, data=raw)
    if raw is not None and "Content-Type" not in (headers or {}):
        req.add_header("Content-Type", "application/json")

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8") or "{}"
                return json.loads(body)
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(backoff_seconds * (2**attempt))
                continue
            break
    raise RuntimeError(f"HTTP request failed: {url}: {last_error}")


def http_form(
    url: str,
    *,
    method: str = "POST",
    headers: dict[str, str] | None = None,
    payload: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    encoded = parse.urlencode(payload or {}).encode("utf-8")
    req = request.Request(url=url, method=method, data=encoded, headers=headers or {})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def probe_duration_seconds(input_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    value = result.stdout.strip() or "0"
    return float(value)


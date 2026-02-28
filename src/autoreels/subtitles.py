from __future__ import annotations

from pathlib import Path


def _to_srt_timestamp(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    secs = total_seconds % 60
    total_minutes = total_seconds // 60
    mins = total_minutes % 60
    hours = total_minutes // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def build_srt(lines: list[str], total_duration: float) -> str:
    if not lines:
        return ""
    min_duration = 1.4
    count = len(lines)
    chunk = max(total_duration / count, min_duration)
    cursor = 0.0
    blocks: list[str] = []
    for index, line in enumerate(lines, start=1):
        start = cursor
        end = cursor + chunk
        blocks.append(
            f"{index}\n{_to_srt_timestamp(start)} --> {_to_srt_timestamp(end)}\n{line.strip()}\n"
        )
        cursor = end
    return "\n".join(blocks).strip() + "\n"


def write_srt(path: Path, lines: list[str], total_duration: float) -> None:
    path.write_text(build_srt(lines, total_duration), encoding="utf-8")


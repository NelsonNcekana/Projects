from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from urllib import parse, request

from .config import RuntimeConfig
from .models import ScriptDraft
from .utils import check_binary, http_json, probe_duration_seconds


def _escape_drawtext(value: str) -> str:
    value = value.replace("\\", "\\\\")
    value = value.replace(":", r"\:")
    value = value.replace("'", r"\'")
    value = value.replace("%", r"\%")
    return value


def _run(command: list[str]) -> None:
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(command)}): {result.stderr.strip()}")


def ensure_ffmpeg() -> None:
    if not check_binary("ffmpeg") or not check_binary("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required in PATH.")


def build_voiceover(runtime: RuntimeConfig, script: ScriptDraft, out_mp3: Path, voice: str) -> float:
    full_text = script.as_text()
    if runtime.openai_api_key:
        req = request.Request(
            "https://api.openai.com/v1/audio/speech",
            method="POST",
            data=json.dumps(
                {
                    "model": runtime.openai_tts_model,
                    "voice": voice or "alloy",
                    "input": full_text,
                    "format": "mp3",
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {runtime.openai_api_key}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=120) as response:
            out_mp3.write_bytes(response.read())
        return probe_duration_seconds(out_mp3)

    estimated = max(8.0, min(45.0, len(full_text.split()) / 2.6))
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t",
            f"{estimated:.2f}",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(out_mp3),
        ]
    )
    return estimated


def build_background(runtime: RuntimeConfig, topic: str, duration: float, out_video: Path) -> None:
    if runtime.pexels_api_key:
        try:
            source = _download_pexels_video(runtime.pexels_api_key, topic, out_video.parent)
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    str(source),
                    "-t",
                    f"{duration:.2f}",
                    "-an",
                    "-vf",
                    "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
                    "-r",
                    "30",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "22",
                    str(out_video),
                ]
            )
            return
        except Exception:
            pass

    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=#111827:s=1080x1920:r=30",
            "-t",
            f"{duration:.2f}",
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
            str(out_video),
        ]
    )


def render_reel(
    hook: str,
    background_path: Path,
    voiceover_path: Path,
    subtitles_path: Path,
    out_path: Path,
) -> None:
    title = _escape_drawtext(hook[:84])
    subtitles = str(subtitles_path).replace("\\", "\\\\").replace(":", r"\:")
    filter_graph = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,format=yuv420p,"
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{title}':fontcolor=white:fontsize=52:"
        "box=1:boxcolor=black@0.45:boxborderw=18:x=(w-text_w)/2:y=110,"
        f"subtitles='{subtitles}':force_style='FontName=DejaVu Sans,FontSize=11,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,"
        "Shadow=0,MarginV=82'[vout]"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(background_path),
            "-i",
            str(voiceover_path),
            "-filter_complex",
            filter_graph,
            "-map",
            "[vout]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_path),
        ]
    )


def _download_pexels_video(api_key: str, topic: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": api_key}
    query = topic or "cinematic abstract background"
    url = f"https://api.pexels.com/videos/search?query={parse.quote(query)}&per_page=1"
    response = http_json(url, headers=headers, method="GET")
    videos = response.get("videos", [])
    if not videos:
        raise RuntimeError("No Pexels videos found.")
    files = videos[0].get("video_files") or []
    mp4_choices = [item for item in files if item.get("file_type") == "video/mp4"]
    if not mp4_choices:
        raise RuntimeError("No mp4 sources in Pexels response.")
    best = sorted(mp4_choices, key=lambda x: x.get("width", 0), reverse=True)[0]
    source_url = best["link"]
    target_path = out_dir / "pexels_source.mp4"
    with request.urlopen(source_url, timeout=120) as source, target_path.open("wb") as out_file:
        shutil.copyfileobj(source, out_file)
    return target_path


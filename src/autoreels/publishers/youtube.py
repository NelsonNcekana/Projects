from __future__ import annotations

import json
import uuid
from pathlib import Path
from urllib import error, request

from ..models import PublishResult


def publish_youtube_short(
    access_token: str,
    video_path: Path,
    *,
    title: str,
    description: str,
    dry_run: bool,
) -> PublishResult:
    if dry_run:
        return PublishResult(platform="youtube", ok=True, message="Dry-run: skipped upload")
    if not access_token:
        return PublishResult(platform="youtube", ok=False, message="Missing YOUTUBE_ACCESS_TOKEN")
    if not video_path.exists():
        return PublishResult(platform="youtube", ok=False, message=f"Video not found: {video_path}")

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    boundary = f"autoreels-{uuid.uuid4().hex}"
    json_part = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
    ).encode("utf-8")
    video_header = (
        f"--{boundary}\r\n"
        "Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8")
    end_part = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = json_part + video_header + video_path.read_bytes() + end_part

    endpoint = "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=multipart"
    req = request.Request(
        endpoint,
        method="POST",
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
    )
    try:
        with request.urlopen(req, timeout=300) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        return PublishResult(platform="youtube", ok=False, message=f"YouTube error: {details[:500]}")
    except Exception as exc:
        return PublishResult(platform="youtube", ok=False, message=f"YouTube upload failed: {exc}")

    video_id = str(payload.get("id", ""))
    if not video_id:
        return PublishResult(platform="youtube", ok=False, message=f"Unexpected response: {payload}")
    url = f"https://www.youtube.com/shorts/{video_id}"
    return PublishResult(
        platform="youtube",
        ok=True,
        message="Uploaded",
        remote_id=video_id,
        remote_url=url,
    )


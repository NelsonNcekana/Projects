from __future__ import annotations

from ..models import PublishResult
from ..utils import http_json


def publish_tiktok_video(
    access_token: str,
    *,
    video_url: str,
    title: str,
    dry_run: bool,
) -> PublishResult:
    if dry_run:
        return PublishResult(platform="tiktok", ok=True, message="Dry-run: skipped publish")
    if not access_token:
        return PublishResult(platform="tiktok", ok=False, message="Missing TIKTOK_ACCESS_TOKEN")
    if not video_url:
        return PublishResult(platform="tiktok", ok=False, message="Missing public video URL")

    payload = {
        "post_info": {
            "title": title[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": video_url,
        },
    }
    try:
        response = http_json(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            method="POST",
            headers={"Authorization": f"Bearer {access_token}"},
            payload=payload,
        )
    except Exception as exc:
        return PublishResult(platform="tiktok", ok=False, message=f"TikTok error: {exc}")

    data = response.get("data") or {}
    publish_id = str(data.get("publish_id", ""))
    if not publish_id:
        return PublishResult(platform="tiktok", ok=False, message=f"Unexpected response: {response}")
    return PublishResult(
        platform="tiktok",
        ok=True,
        message="Publish requested",
        remote_id=publish_id,
    )


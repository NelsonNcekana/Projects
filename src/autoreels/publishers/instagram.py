from __future__ import annotations

import time
from urllib import parse

from ..models import PublishResult
from ..utils import http_form, http_json


GRAPH_VERSION = "v22.0"


def publish_instagram_reel(
    access_token: str,
    ig_user_id: str,
    *,
    video_url: str,
    caption: str,
    dry_run: bool,
) -> PublishResult:
    if dry_run:
        return PublishResult(platform="instagram", ok=True, message="Dry-run: skipped publish")
    if not access_token:
        return PublishResult(platform="instagram", ok=False, message="Missing INSTAGRAM_ACCESS_TOKEN")
    if not ig_user_id:
        return PublishResult(platform="instagram", ok=False, message="Missing INSTAGRAM_IG_USER_ID")
    if not video_url:
        return PublishResult(platform="instagram", ok=False, message="Missing public video URL")

    base = f"https://graph.facebook.com/{GRAPH_VERSION}"
    container_url = f"{base}/{ig_user_id}/media"
    try:
        container = http_form(
            container_url,
            payload={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": access_token,
            },
        )
    except Exception as exc:
        return PublishResult(platform="instagram", ok=False, message=f"Container request failed: {exc}")
    creation_id = str(container.get("id", ""))
    if not creation_id:
        return PublishResult(platform="instagram", ok=False, message=f"Container failed: {container}")

    # Reels containers are asynchronous; poll until processing completes.
    for _ in range(12):
        params = parse.urlencode(
            {"fields": "status_code,status", "access_token": access_token}
        )
        try:
            status_payload = http_json(f"{base}/{creation_id}?{params}")
        except Exception as exc:
            return PublishResult(platform="instagram", ok=False, message=f"Status check failed: {exc}")
        status = str(status_payload.get("status_code", "")).upper()
        if status in {"FINISHED", "PUBLISHED"}:
            break
        if status in {"ERROR", "EXPIRED"}:
            return PublishResult(
                platform="instagram",
                ok=False,
                message=f"Container processing failed: {status_payload}",
            )
        time.sleep(5)

    try:
        publish_payload = http_form(
            f"{base}/{ig_user_id}/media_publish",
            payload={
                "creation_id": creation_id,
                "access_token": access_token,
            },
        )
    except Exception as exc:
        return PublishResult(platform="instagram", ok=False, message=f"Publish request failed: {exc}")
    post_id = str(publish_payload.get("id", ""))
    if not post_id:
        return PublishResult(platform="instagram", ok=False, message=f"Publish failed: {publish_payload}")
    return PublishResult(
        platform="instagram",
        ok=True,
        message="Published",
        remote_id=post_id,
    )


from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import RuntimeConfig
from .content import ContentEngine, build_caption
from .media import build_background, build_voiceover, ensure_ffmpeg, render_reel
from .models import CampaignConfig, ReelPaths, TopicConfig
from .publishers import publish_instagram_reel, publish_tiktok_video, publish_youtube_short
from .subtitles import write_srt
from .utils import ensure_dir, slugify, write_json


def load_campaign(path: Path) -> CampaignConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return CampaignConfig.from_dict(raw)


class AutoReelsPipeline:
    def __init__(self, runtime: RuntimeConfig, campaign: CampaignConfig) -> None:
        self.runtime = runtime
        self.campaign = campaign
        self.content_engine = ContentEngine(runtime, campaign)

    def run(self, max_items: int = 0) -> Path:
        ensure_ffmpeg()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_dir = ensure_dir(self.runtime.output_dir / timestamp)
        selected_topics = self.campaign.topics[: max_items or None]
        report: dict[str, object] = {
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.runtime.dry_run,
            "brand": self.campaign.brand_name,
            "results": [],
        }

        for index, topic_cfg in enumerate(selected_topics, start=1):
            artifact = self._build_reel(run_dir, topic_cfg, index)
            caption = build_caption(self.campaign, artifact["script"])
            public_url = ""
            if self.runtime.public_base_url:
                relative_path = artifact["paths"].final_video.relative_to(self.runtime.output_dir).as_posix()
                public_url = f"{self.runtime.public_base_url}/{relative_path}"

            publish_results = [
                publish_youtube_short(
                    self.runtime.youtube_access_token,
                    artifact["paths"].final_video,
                    title=artifact["script"].hook,
                    description=caption,
                    dry_run=self.runtime.dry_run,
                ),
                publish_instagram_reel(
                    self.runtime.instagram_access_token,
                    self.runtime.instagram_user_id,
                    video_url=public_url,
                    caption=caption,
                    dry_run=self.runtime.dry_run,
                ),
                publish_tiktok_video(
                    self.runtime.tiktok_access_token,
                    video_url=public_url,
                    title=artifact["script"].hook,
                    dry_run=self.runtime.dry_run,
                ),
            ]
            report_item = {
                "topic": topic_cfg.topic,
                "slug": artifact["paths"].slug,
                "files": {
                    "script_json": str(artifact["paths"].script_json),
                    "subtitles_srt": str(artifact["paths"].subtitles_srt),
                    "voiceover_audio": str(artifact["paths"].voiceover_audio),
                    "background_video": str(artifact["paths"].background_video),
                    "final_video": str(artifact["paths"].final_video),
                },
                "public_video_url": public_url,
                "publish": [asdict(result) for result in publish_results],
            }
            report["results"].append(report_item)  # type: ignore[index]

        report_path = run_dir / "run_report.json"
        write_json(report_path, report)
        return report_path

    def _build_reel(self, run_dir: Path, topic_cfg: TopicConfig, index: int) -> dict[str, object]:
        slug = f"{index:02d}-{slugify(topic_cfg.topic)}"
        item_dir = ensure_dir(run_dir / slug)
        paths = ReelPaths(
            slug=slug,
            work_dir=item_dir,
            script_json=item_dir / "script.json",
            subtitles_srt=item_dir / "subtitles.srt",
            voiceover_audio=item_dir / "voiceover.mp3",
            background_video=item_dir / "background.mp4",
            final_video=item_dir / f"{slug}.mp4",
        )
        script = self.content_engine.build_script(topic_cfg)
        self.content_engine.write_script_json(paths.script_json, script, topic_cfg)
        duration = build_voiceover(self.runtime, script, paths.voiceover_audio, self.campaign.voice)
        write_srt(paths.subtitles_srt, script.as_lines(), total_duration=duration)
        build_background(self.runtime, topic_cfg.topic, duration, paths.background_video)
        render_reel(script.hook, paths.background_video, paths.voiceover_audio, paths.subtitles_srt, paths.final_video)
        return {"script": script, "paths": paths}


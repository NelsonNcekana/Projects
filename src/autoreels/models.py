from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TopicConfig:
    topic: str
    angle: str = ""
    cta: str = ""


@dataclass(slots=True)
class CampaignConfig:
    brand_name: str
    niche: str
    default_cta: str
    topics: list[TopicConfig]
    hashtags: list[str] = field(default_factory=list)
    voice: str = "alloy"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CampaignConfig":
        raw_topics = data.get("topics") or []
        topics = [TopicConfig(**topic) for topic in raw_topics]
        if not topics:
            raise ValueError("Campaign config must include at least one topic.")
        return cls(
            brand_name=str(data.get("brand_name", "Faceless Channel")).strip(),
            niche=str(data.get("niche", "general")).strip(),
            default_cta=str(data.get("default_cta", "Follow for more tips.")).strip(),
            hashtags=[str(tag).strip() for tag in data.get("hashtags", []) if str(tag).strip()],
            voice=str(data.get("voice", "alloy")).strip() or "alloy",
            topics=topics,
        )


@dataclass(slots=True)
class ScriptDraft:
    hook: str
    beats: list[str]
    cta: str

    def as_lines(self) -> list[str]:
        lines = [self.hook]
        lines.extend(self.beats)
        lines.append(self.cta)
        return lines

    def as_text(self) -> str:
        return " ".join(self.as_lines())


@dataclass(slots=True)
class ReelPaths:
    slug: str
    work_dir: Path
    script_json: Path
    subtitles_srt: Path
    voiceover_audio: Path
    background_video: Path
    final_video: Path


@dataclass(slots=True)
class PublishResult:
    platform: str
    ok: bool
    message: str
    remote_id: str = ""
    remote_url: str = ""


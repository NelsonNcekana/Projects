from __future__ import annotations

import json
from pathlib import Path

from .config import RuntimeConfig
from .models import CampaignConfig, ScriptDraft, TopicConfig
from .utils import http_json, write_json


class ContentEngine:
    def __init__(self, runtime: RuntimeConfig, campaign: CampaignConfig) -> None:
        self.runtime = runtime
        self.campaign = campaign

    def build_script(self, topic_cfg: TopicConfig) -> ScriptDraft:
        if self.runtime.openai_api_key:
            try:
                return self._build_script_openai(topic_cfg)
            except Exception:
                # Fall back to deterministic templates so the pipeline can continue.
                return self._build_script_template(topic_cfg)
        return self._build_script_template(topic_cfg)

    def write_script_json(self, output_path: Path, script: ScriptDraft, topic_cfg: TopicConfig) -> None:
        payload = {
            "topic": topic_cfg.topic,
            "angle": topic_cfg.angle,
            "hook": script.hook,
            "beats": script.beats,
            "cta": script.cta,
            "text": script.as_text(),
        }
        write_json(output_path, payload)

    def _build_script_openai(self, topic_cfg: TopicConfig) -> ScriptDraft:
        system_prompt = (
            "You are a short-form content writer. Return strict JSON only with keys: "
            "hook (string), beats (array of 3-5 short lines), cta (string)."
        )
        user_prompt = {
            "brand_name": self.campaign.brand_name,
            "niche": self.campaign.niche,
            "topic": topic_cfg.topic,
            "angle": topic_cfg.angle or "practical and actionable",
            "default_cta": topic_cfg.cta or self.campaign.default_cta,
            "constraints": [
                "Faceless reel style",
                "Max 35 seconds speaking time",
                "Punchy and clear language",
            ],
        }

        payload = {
            "model": self.runtime.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)},
            ],
            "temperature": 0.8,
        }
        response = http_json(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={"Authorization": f"Bearer {self.runtime.openai_api_key}"},
            payload=payload,
        )
        message = response["choices"][0]["message"]["content"]
        parsed = json.loads(message)
        beats = [str(item).strip() for item in parsed.get("beats", []) if str(item).strip()]
        if not beats:
            raise ValueError("OpenAI returned empty beats.")
        return ScriptDraft(
            hook=str(parsed.get("hook", "")).strip(),
            beats=beats[:5],
            cta=str(parsed.get("cta", topic_cfg.cta or self.campaign.default_cta)).strip(),
        )

    def _build_script_template(self, topic_cfg: TopicConfig) -> ScriptDraft:
        topic = topic_cfg.topic.strip()
        angle = topic_cfg.angle.strip() or "practical, no-fluff"
        cta = (topic_cfg.cta or self.campaign.default_cta).strip()

        hook = f"{topic}: 3 fast wins most people miss."
        beats = [
            f"Step 1 ({angle}): start with the highest-impact action in the first 10 minutes.",
            "Step 2: remove one friction point so this is easier to repeat tomorrow.",
            "Step 3: use a tiny checkpoint to track progress and prevent burnout.",
        ]
        return ScriptDraft(hook=hook, beats=beats, cta=cta)


def build_caption(campaign: CampaignConfig, script: ScriptDraft) -> str:
    tags = " ".join(campaign.hashtags)
    base = f"{script.hook}\n\n{script.cta}"
    if tags:
        base = f"{base}\n\n{tags}"
    return base[:2200]


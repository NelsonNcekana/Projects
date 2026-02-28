# AutoReels: Faceless Reels on Autopilot

Create, render, and publish faceless short-form videos automatically to:

- TikTok
- Instagram Reels
- YouTube Shorts

This project generates scripts, optional AI voiceovers, subtitles, and vertical videos, then pushes them to platform APIs from a single CLI command.

## What this gives you

- Campaign-based content generation (`campaign.json`)
- Optional OpenAI script + TTS voice generation
- Optional Pexels stock footage
- FFmpeg-based 9:16 rendering with caption burn-in
- Cross-platform publishing workflow
- Dry-run mode for safe testing
- JSON run report with generated files + publish outcomes

## Quick start

### 1) Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` available in PATH
- API credentials for the platforms you want to publish to

### 2) Initialize starter files

```bash
python -m autoreels.cli init --dir .
```

This creates:

- `.env.example`
- `campaign.json`
- `AUTOREELS.md`

Copy `.env.example` to `.env` and fill in your keys/tokens.

### 3) Dry-run (generate videos, skip live posting)

```bash
python -m autoreels.cli run --campaign campaign.json
```

### 4) Live publish mode

```bash
python -m autoreels.cli run --campaign campaign.json --publish
```

> By default, `AUTOREELS_DRY_RUN=true`. `--publish` overrides that for the current run.

## Auth and platform notes

### YouTube Shorts

- Uses YouTube Data API upload endpoint.
- Requires `YOUTUBE_ACCESS_TOKEN` with upload scope.
- Uploads directly from the local `.mp4`.

### Instagram Reels

- Uses Meta Graph API.
- Requires:
  - `INSTAGRAM_ACCESS_TOKEN`
  - `INSTAGRAM_IG_USER_ID`
  - `AUTOREELS_PUBLIC_BASE_URL`
- Instagram publishing requires a **publicly accessible** video URL.

### TikTok

- Uses TikTok Content Posting API.
- Requires:
  - `TIKTOK_ACCESS_TOKEN`
  - `AUTOREELS_PUBLIC_BASE_URL`
- TikTok publish flow in this project uses pull-from-URL mode.

## Output structure

Each run creates a timestamped directory:

```
output/YYYYMMDD-HHMMSS/
  01-topic-slug/
    script.json
    subtitles.srt
    voiceover.mp3
    background.mp4
    01-topic-slug.mp4
  02-topic-slug/
    ...
  run_report.json
```

## Campaign schema (`campaign.json`)

```json
{
  "brand_name": "Growth Lab",
  "niche": "productivity",
  "default_cta": "Follow for practical growth tactics.",
  "voice": "alloy",
  "hashtags": ["#productivity", "#shorts"],
  "topics": [
    {
      "topic": "How to stop procrastinating in 10 minutes",
      "angle": "simple mental model",
      "cta": "Follow for daily no-fluff habits."
    }
  ]
}
```

## Recommended production setup

For true autopilot publishing every day:

1. Run this CLI on a schedule (cron/GitHub Actions/CI).
2. Host output videos on a public URL path used by Instagram/TikTok ingestion.
3. Refresh OAuth tokens automatically.
4. Keep `AUTOREELS_DRY_RUN=false` in production runs.

## Responsible use

Follow each platform's API and automation policies. Ensure your content and posting behavior comply with local law and platform rules.
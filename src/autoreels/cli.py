from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import RuntimeConfig, load_dotenv
from .pipeline import AutoReelsPipeline, load_campaign


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def cmd_init(target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)
    env_example = """# Core behavior
AUTOREELS_DRY_RUN=true
AUTOREELS_OUTPUT_DIR=output

# Optional LLM/TTS generation
OPENAI_API_KEY=
AUTOREELS_OPENAI_MODEL=gpt-4o-mini
AUTOREELS_OPENAI_TTS_MODEL=gpt-4o-mini-tts

# Optional stock clips
PEXELS_API_KEY=

# Needed for Instagram/TikTok publish (URL where final videos are publicly hosted)
AUTOREELS_PUBLIC_BASE_URL=

# Platform auth tokens
YOUTUBE_ACCESS_TOKEN=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_IG_USER_ID=
TIKTOK_ACCESS_TOKEN=
"""
    campaign_example = {
        "brand_name": "Growth Lab",
        "niche": "productivity",
        "default_cta": "Follow for practical growth tactics.",
        "voice": "alloy",
        "hashtags": ["#productivity", "#selfimprovement", "#mindset", "#shorts"],
        "topics": [
            {
                "topic": "How to stop procrastinating in 10 minutes",
                "angle": "simple mental model",
                "cta": "Follow for daily no-fluff habits.",
            },
            {
                "topic": "The 3-minute morning reset",
                "angle": "high energy",
                "cta": "Save this and try it tomorrow.",
            },
        ],
    }
    readme_snippet = """# AutoReels campaign files

1. Copy `.env.example` to `.env` and fill API tokens.
2. Edit `campaign.json` with your niche and topics.
3. Run:
   - Dry-run: `python -m autoreels.cli run --campaign campaign.json`
   - Publish: `python -m autoreels.cli run --campaign campaign.json --publish`
"""
    _write_if_missing(target_dir / ".env.example", env_example)
    _write_if_missing(target_dir / "campaign.json", json.dumps(campaign_example, indent=2))
    _write_if_missing(target_dir / "AUTOREELS.md", readme_snippet)
    print(f"Initialized files in {target_dir}")
    return 0


def cmd_run(campaign_path: Path, dotenv_path: Path, max_items: int, publish: bool) -> int:
    load_dotenv(dotenv_path)
    runtime = RuntimeConfig.from_env()
    if publish:
        runtime.dry_run = False
    campaign = load_campaign(campaign_path)
    pipeline = AutoReelsPipeline(runtime, campaign)
    report_path = pipeline.run(max_items=max_items)
    print(f"Run complete. Report: {report_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autoreels",
        description="Generate and autopublish faceless reels for TikTok, Instagram, and YouTube.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init", help="Create starter config files")
    init_cmd.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="Directory where starter files will be written.",
    )

    run_cmd = subparsers.add_parser("run", help="Generate and publish reels")
    run_cmd.add_argument("--campaign", type=Path, default=Path("campaign.json"))
    run_cmd.add_argument("--dotenv", type=Path, default=Path(".env"))
    run_cmd.add_argument("--max-items", type=int, default=0, help="0 means all topics in campaign.")
    run_cmd.add_argument("--publish", action="store_true", help="Override dry-run and publish.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        return cmd_init(args.dir)
    if args.command == "run":
        return cmd_run(args.campaign, args.dotenv, args.max_items, args.publish)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


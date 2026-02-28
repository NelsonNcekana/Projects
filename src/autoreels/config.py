from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(dotenv_path: Path) -> None:
    """Load key=value pairs from a .env file."""
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class RuntimeConfig:
    output_dir: Path
    dry_run: bool
    openai_api_key: str
    openai_model: str
    openai_tts_model: str
    pexels_api_key: str
    public_base_url: str
    youtube_access_token: str
    instagram_access_token: str
    instagram_user_id: str
    tiktok_access_token: str

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        output_dir = Path(os.getenv("AUTOREELS_OUTPUT_DIR", "output")).resolve()
        return cls(
            output_dir=output_dir,
            dry_run=_as_bool(os.getenv("AUTOREELS_DRY_RUN"), default=True),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv("AUTOREELS_OPENAI_MODEL", "gpt-4o-mini").strip(),
            openai_tts_model=os.getenv("AUTOREELS_OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip(),
            pexels_api_key=os.getenv("PEXELS_API_KEY", "").strip(),
            public_base_url=os.getenv("AUTOREELS_PUBLIC_BASE_URL", "").rstrip("/"),
            youtube_access_token=os.getenv("YOUTUBE_ACCESS_TOKEN", "").strip(),
            instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip(),
            instagram_user_id=os.getenv("INSTAGRAM_IG_USER_ID", "").strip(),
            tiktok_access_token=os.getenv("TIKTOK_ACCESS_TOKEN", "").strip(),
        )


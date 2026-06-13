"""Settings for the lahja pipeline.

All credentials come from environment variables (a local ``.env`` file is
loaded automatically if present). Nothing secret is ever hardcoded here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the current working directory, and (for editable installs
# run from elsewhere) from the project root next to this package. Real
# environment variables always take precedence; missing files are ignored,
# e.g. in production where the host sets the variables directly.
load_dotenv()
_project_env = Path(__file__).resolve().parents[2] / ".env"
if _project_env.exists():
    load_dotenv(_project_env, override=False)


@dataclass
class Settings:
    # --- credentials -----------------------------------------------------
    minimax_api_key: str = field(default_factory=lambda: os.getenv("MINIMAX_API_KEY", ""))
    minimax_group_id: str = field(default_factory=lambda: os.getenv("MINIMAX_GROUP_ID", ""))
    nvidia_api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))

    # --- models ----------------------------------------------------------
    whisper_model: str = "large-v3-turbo"
    minimax_tts_model: str = "speech-2.8-turbo"
    llm_model: str = "minimaxai/minimax-m2.7"

    # --- audio -----------------------------------------------------------
    audio_sample_rate: int = 32000     # TTS / output audio
    whisper_sample_rate: int = 16000   # extraction for transcription

    # --- timeline behaviour ------------------------------------------------
    first_segment_speed: float = 0.9   # ease-in speed for the opening line
    max_segment_deviation: float = 0.08  # max +/- deviation from the global tempo
    min_gap: float = 0.05              # ignore gaps shorter than this (seconds)

    # --- voice cloning -----------------------------------------------------
    clone_sample_start: float = 0.0
    clone_sample_duration: float = 45.0

    # --- LLM refinement ----------------------------------------------------
    refine_batch_size: int = 12
    refine_batch_retries: int = 2
    refine_timeout: float = 300.0

    def require_minimax(self) -> None:
        if not self.minimax_api_key:
            raise RuntimeError(
                "MINIMAX_API_KEY is not set. Copy .env.example to .env and "
                "fill in your keys, or set the environment variable."
            )
        if not self.minimax_group_id:
            raise RuntimeError("MINIMAX_GROUP_ID is not set.")

"""Whisper transcription with word-level timestamps."""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_PAUSE_TAG = re.compile(r"\[PAUSE:[0-9.]+\]")
_WHITESPACE = re.compile(r"\s+")

# Cache loaded models so a long-running server doesn't reload weights
# (several GB) on every job.
_models: dict[str, object] = {}


def clean_text(text: str) -> str:
    text = _PAUSE_TAG.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def _load_model(model_name: str):
    if model_name not in _models:
        import whisper

        logger.info("Loading Whisper model %s ...", model_name)
        _models[model_name] = whisper.load_model(model_name)
    return _models[model_name]


def transcribe(audio_path: Path, model_name: str = "large-v3-turbo") -> list[dict]:
    """Transcribe and return Whisper segments (with accurate timestamps).

    word_timestamps=True makes segment start/end times much more precise,
    which is what keeps the generated voice in sync with the video.
    """
    import torch

    model = _load_model(model_name)
    logger.info("Transcribing %s ...", audio_path.name)
    result = model.transcribe(
        str(audio_path),
        fp16=torch.cuda.is_available(),
        word_timestamps=True,
    )
    segments = result.get("segments", [])
    if not segments:
        raise ValueError("Whisper returned an empty transcription.")
    logger.info("Transcribed %d segments.", len(segments))
    return segments

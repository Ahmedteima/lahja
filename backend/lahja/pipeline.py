"""End-to-end pipeline: video in -> lahjad video out.

This is the function a web backend calls per uploaded video:

    from lahja import process_video
    final_path = process_video(Path("upload.mp4"), Path("result.mp4"))

Each run works in its own (temporary) directory, so concurrent jobs
don't collide.
"""
from __future__ import annotations

import hashlib
import logging
import shutil
import tempfile
from pathlib import Path

from . import audio
from .config import Settings
from .minimax import MiniMaxClient
from .refine import refine_segments
from .timeline import build_voiceover
from .transcribe import transcribe

logger = logging.getLogger(__name__)


def derive_voice_id(video_path: Path) -> str:
    """Stable per-video voice id (same video -> same cloned voice, no re-clone).

    MiniMax custom voice id rules: starts with a letter, contains letters
    AND digits, length >= 8. 'vc' + 10 hex chars + '1' always satisfies them.
    """
    digest = hashlib.md5()
    with video_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return f"vc{digest.hexdigest()[:10]}1"


def process_video(video_path: Path | str,
                output_path: Path | str | None = None,
                  *,
                settings: Settings | None = None,
                workdir: Path | str | None = None,
                keep_workdir: bool = False,
                refine: bool = True,
                voice_id: str | None = None) -> Path:
    """Replace the narration of ``video_path`` with a cloned AI voice.

    Returns the path of the final video. Intermediate files live in
    ``workdir`` (a fresh temporary directory by default) and are removed
    afterwards unless ``keep_workdir`` is True.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    settings = settings or Settings()
    settings.require_minimax()

    output_path = (Path(output_path) if output_path
                else video_path.with_name(f"{video_path.stem}_voiceover.mp4"))

    owns_workdir = workdir is None
    workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="lahja_"))
    workdir.mkdir(parents=True, exist_ok=True)

    client = MiniMaxClient(settings.minimax_api_key, settings.minimax_group_id,
                        tts_model=settings.minimax_tts_model)

    try:
        # 1) Extract the original audio (mono 16 kHz, ideal for Whisper).
        original_audio = audio.extract_audio(
            video_path, workdir / "original_audio.mp3",
            sample_rate=settings.whisper_sample_rate)
        logger.info("Extracted audio: %s", original_audio.name)

        # 2) Transcribe with accurate word-level timestamps.
        segments = transcribe(original_audio, settings.whisper_model)

        # 3) Optionally fix transcription mistakes with the LLM.
        if refine:
            refine_segments(segments, settings)

        # 4) Clone the speaker's voice from a short slice of the original
        #    audio (one-time per video; reused on later runs).
        voice_id = voice_id or derive_voice_id(video_path)
        sample_path = audio.extract_slice(
            original_audio,
            settings.clone_sample_start,
            settings.clone_sample_start + settings.clone_sample_duration,
            workdir / "clone_sample.mp3",
            sample_rate=settings.whisper_sample_rate)
        client.ensure_cloned_voice(sample_path, voice_id)

        # 5) Build the voiceover on the original timeline.
        generated_audio = build_voiceover(
            segments, original_audio, client, voice_id,
            workdir, workdir / "generated_voice.mp3", settings)

        # 6) Merge the new audio into the video.
        audio.merge_video_audio(video_path, generated_audio, output_path)
        logger.info("Final video ready: %s", output_path)
        return output_path
    finally:
        if owns_workdir and not keep_workdir:
            shutil.rmtree(workdir, ignore_errors=True)
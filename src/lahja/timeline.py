"""Build the cloned voiceover on the ORIGINAL timeline.

Design (matches the validated notebook pipeline):
  1. STABLE SPEED : one global tempo factor is computed for the whole
     voiceover; each segment may deviate at most +/-max_segment_deviation
     from it (instead of an arbitrary per-segment atempo -> speed jumps).
  2. INTRO/OUTRO & BACKGROUND KEPT : every non-speech interval (intro
     music, pauses between sentences, outro) is copied from the ORIGINAL
     audio instead of generated silence.
  3. EASE-IN : the first spoken segment is synthesized slightly slower
     and the voice returns to normal speed from the second segment on.
  4. REFINED TEXT : uses seg["refined_text"] when available, otherwise
     falls back to the cleaned Whisper text.
"""
from __future__ import annotations

import logging
from pathlib import Path

from . import audio
from .config import Settings
from .minimax import MiniMaxClient
from .transcribe import clean_text

logger = logging.getLogger(__name__)


def build_voiceover(segments: list[dict], original_audio: Path,
                    client: MiniMaxClient, voice_id: str,
                    workdir: Path, output_path: Path,
                    settings: Settings) -> Path:
    if not segments:
        raise ValueError("No Whisper segments provided.")

    chunk_dir = workdir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    sample_rate = settings.audio_sample_rate

    # Collect speech segments with their (refined) text.
    speech: list[tuple[float, float, str]] = []
    for seg in segments:
        text = (seg.get("refined_text") or clean_text(seg.get("text", ""))).strip()
        if text:
            speech.append((float(seg["start"]), float(seg["end"]), text))
    if not speech:
        raise ValueError("No speech segments with text.")

    # --- 1) Synthesize every segment (first one slightly slower: ease-in) ---
    raw_paths: list[Path] = []
    raw_durations: list[float] = []
    for index, (start, end, text) in enumerate(speech, start=1):
        raw_path = chunk_dir / f"speech_raw_{index:03d}.mp3"
        speed = settings.first_segment_speed if index == 1 else 1.0
        logger.info("TTS segment %d/%d%s", index, len(speech),
                    " (slow start)" if index == 1 else "")
        client.synthesize(text, voice_id, raw_path,
                          speed=speed, sample_rate=sample_rate)
        raw_paths.append(raw_path)
        raw_durations.append(audio.media_duration(raw_path))

    # --- 2) ONE global tempo factor -> stable speaking speed everywhere ---
    total_raw = sum(raw_durations)
    total_target = sum(end - start for start, end, _ in speech)
    global_factor = min(max(total_raw / max(1e-6, total_target), 0.85), 1.4)
    logger.info("Global tempo factor: %.3f (raw TTS %.1fs vs original speech %.1fs)",
                global_factor, total_raw, total_target)

    # --- 3) Walk the original timeline; gaps come from the ORIGINAL audio ---
    original_total = audio.media_duration(original_audio)
    pieces: list[Path] = []
    cursor = 0.0  # current end position of the assembled audio (seconds)

    for index, ((start, end, _text), raw_path, raw_duration) in enumerate(
            zip(speech, raw_paths, raw_durations), start=1):

        # Fill the gap before this segment with the original audio
        # (this is what preserves the intro music and background sounds).
        if start - cursor >= settings.min_gap:
            gap_path = chunk_dir / f"gap_{index:03d}.mp3"
            logger.debug("Keeping original audio %.2fs -> %.2fs", cursor, start)
            pieces.append(audio.extract_slice(
                original_audio, cursor, start, gap_path, sample_rate))
            cursor = start

        # Fit the segment: stay close to the global tempo.
        placement = max(cursor, start)
        adjusted_target = max(0.3, end - placement)
        natural_factor = raw_duration / adjusted_target
        if index == 1:
            # Keep the ease-in: don't speed the opening line back up.
            low, high = 0.9, 1.1
        else:
            low = global_factor * (1.0 - settings.max_segment_deviation)
            high = global_factor * (1.0 + settings.max_segment_deviation)
        factor = min(max(natural_factor, low), high)

        if abs(factor - 1.0) < 0.02:
            fitted_path, fitted_duration = raw_path, raw_duration
        else:
            fitted_path = chunk_dir / f"speech_fit_{index:03d}.mp3"
            audio.retime(raw_path, factor, fitted_path, sample_rate)
            fitted_duration = audio.media_duration(fitted_path)

        pieces.append(fitted_path)
        cursor = placement + fitted_duration

    # --- 4) Keep the original outro (music after the last sentence) ---
    if original_total - cursor >= settings.min_gap:
        logger.debug("Keeping original outro %.2fs -> %.2fs", cursor, original_total)
        pieces.append(audio.extract_slice(
            original_audio, cursor, original_total,
            chunk_dir / "outro_original.mp3", sample_rate))

    result = audio.concat(pieces, output_path, sample_rate,
                          list_file=workdir / "concat_list.txt")
    logger.info("Assembled voiceover: %.1fs (original audio: %.1fs)",
                audio.media_duration(result), original_total)
    return result

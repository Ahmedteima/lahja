"""FFmpeg-based audio helpers.

Requires the ``ffmpeg`` and ``ffprobe`` binaries on PATH (the program, not
the ``ffmpeg-python`` pip package).
"""
from __future__ import annotations

import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise FFmpegError(
            f"ffmpeg failed (args: {' '.join(args)}):\n{result.stderr[-2000:]}"
        )


def media_duration(path: Path) -> float:
    """Duration of an audio/video file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise FFmpegError(f"ffprobe failed for {path}:\n{result.stderr[-2000:]}")
    return float(result.stdout.strip())


def extract_audio(video_path: Path, output_path: Path, sample_rate: int = 16000) -> Path:
    """Extract the audio track as mono mp3 (16 kHz default, ideal for Whisper)."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    run_ffmpeg([
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", str(sample_rate),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path),
    ])
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise FFmpegError(f"Audio was not created: {output_path}")
    return output_path


def extract_slice(src: Path, start: float, end: float, output_path: Path,
                sample_rate: int) -> Path:
    """Copy a piece of an audio file (used for intro music, pauses, outro)."""
    duration = max(0.0, end - start)
    run_ffmpeg([
        "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(src),
        "-ar", str(sample_rate), "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(output_path),
    ])
    return output_path


def atempo_filter_chain(speed_factor: float) -> str:
    """atempo values are safest between 0.5 and 2.0; chain filters beyond that."""
    factors: list[float] = []
    while speed_factor > 2.0:
        factors.append(2.0)
        speed_factor /= 2.0
    while speed_factor < 0.5:
        factors.append(0.5)
        speed_factor /= 0.5
    factors.append(speed_factor)
    return ",".join(f"atempo={factor:.5f}" for factor in factors)


def retime(input_path: Path, factor: float, output_path: Path,
        sample_rate: int) -> Path:
    """Change tempo only - no trimming, no padding, so no words are cut."""
    run_ffmpeg([
        "-i", str(input_path),
        "-filter:a", atempo_filter_chain(factor),
        "-ar", str(sample_rate), "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(output_path),
    ])
    return output_path


def concat(audio_paths: list[Path], output_path: Path, sample_rate: int,
        list_file: Path) -> Path:
    """Concatenate audio files (re-encoded to consistent mono mp3)."""
    if len(audio_paths) == 1:
        output_path.write_bytes(audio_paths[0].read_bytes())
        return output_path
    list_file.write_text(
        "\n".join(f"file '{path.resolve().as_posix()}'" for path in audio_paths),
        encoding="utf-8",
    )
    run_ffmpeg([
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-ar", str(sample_rate), "-ac", "1",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(output_path),
    ])
    return output_path


def merge_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    """Replace the video's audio track with the generated voiceover."""
    if not video_path.exists():
        raise FileNotFoundError(video_path)
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)
    video_duration = media_duration(video_path)
    run_ffmpeg([
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", "apad",
        "-t", f"{video_duration:.3f}",
        str(output_path),
    ])
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise FFmpegError(f"Final video was not created: {output_path}")
    return output_path
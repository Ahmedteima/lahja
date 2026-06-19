"""Command-line interface: lahja <video> [-o output.mp4]"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Settings
from .pipeline import process_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lahja",
        description="Replace a video's narration with a cloned AI voice while "
                    "keeping timing, intro/outro music and pauses.",
    )
    parser.add_argument("video", type=Path, help="input video file")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="output video path (default: <video>_voiceover.mp4)")
    parser.add_argument("--voice-id", default=None,
                        help="use an existing cloned voice id instead of cloning "
                            "from the video's own audio")
    parser.add_argument("--whisper-model", default=None,
                        help="Whisper model name (default: large-v3-turbo)")
    parser.add_argument("--no-refine", action="store_true",
                        help="skip the LLM transcript refinement step")
    parser.add_argument("--keep-workdir", action="store_true",
                        help="keep intermediate files for debugging")
    parser.add_argument("--workdir", type=Path, default=None,
                        help="directory for intermediate files "
                            "(default: a fresh temporary directory)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    # The OpenAI client logs every HTTP request at INFO via httpx - too noisy.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = Settings()
    if args.whisper_model:
        settings.whisper_model = args.whisper_model

    try:
        output = process_video(
            args.video,
            args.output,
            settings=settings,
            workdir=args.workdir,
            keep_workdir=args.keep_workdir,
            refine=not args.no_refine,
            voice_id=args.voice_id,
        )
    except Exception as exc:  # noqa: BLE001 - present a clean CLI error
        logging.error("error: %s", exc)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())